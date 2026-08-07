import asyncio

from opentelemetry import trace

from src.models.quests.objective import ObjectiveOut
from src.models.quests.quest import QuestDB, QuestIn, QuestOut, QuestQuery, QuestUpdate
from src.models.quests.quest_statistics import (
    DailyActivityEntry,
    ObjectiveStatistics,
    QuestCompletionBucket,
    QuestStatisticsOut,
)
from src.models.quests.reward import RewardOut
from src.models.users.profile import ProfileOut
from src.models.users.user import UserOut
from src.repositories.quests.objective import ObjectiveRepository
from src.repositories.quests.quest import QuestRepository
from src.repositories.quests.quest_statistics import QuestStatisticsRepository
from src.repositories.quests.reward import RewardRepository
from src.repositories.user import UserRepository
from src.utils.tracing import traced


class QuestService:
    def __init__(
            self,
            quest_repo: QuestRepository,
            objective_repo: ObjectiveRepository,
            reward_repo: RewardRepository,
            user_repo: UserRepository,
            statistics_repo: QuestStatisticsRepository,
    ):
        self.quest_repo = quest_repo
        self.objective_repo = objective_repo
        self.reward_repo = reward_repo
        self.user_repo = user_repo
        self.statistics_repo = statistics_repo

    async def _to_out(self, quest: QuestDB) -> QuestOut:
        creator_db, profile_db, objectives_db = await asyncio.gather(
            self.user_repo.fetch(quest.guild_id, quest.created_by),
            self.user_repo.fetch_profile(quest.guild_id, quest.created_by),
            self.objective_repo.fetch_all(quest.quest_id)
        )

        rewards_db = await asyncio.gather(
            *[self.reward_repo.fetch_all(o.objective_id) for o in objectives_db]
        )

        return QuestOut(
            **quest.model_dump(exclude={"created_by"}),
            created_by=UserOut(
                **creator_db.model_dump(),
                profile=ProfileOut(**profile_db.model_dump())
            ),
            objectives=[
                ObjectiveOut(
                    **o.model_dump(),
                    rewards=[RewardOut(**r.model_dump()) for r in objective_rewards]
                )
                for o, objective_rewards in zip(objectives_db, rewards_db)
            ]
        )

    @traced
    async def get(self, guild_id: int, quest_id: int) -> QuestOut:
        span = trace.get_current_span()
        span.set_attribute("guild.id", guild_id)
        span.set_attribute("quest.id", quest_id)

        quest_db = await self.quest_repo.fetch(quest_id, guild_id)
        return await self._to_out(quest_db)

    @traced
    async def get_all(self, guild_id: int, query: QuestQuery) -> list[QuestOut]:
        span = trace.get_current_span()
        span.set_attribute("guild.id", guild_id)

        quests_db = await self.quest_repo.fetch_all(guild_id, query)
        span.set_attribute("quests.count", len(quests_db))

        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(self._to_out(q)) for q in quests_db]

        return [t.result() for t in tasks]

    @traced
    async def new(self, guild_id: int, model: QuestIn) -> QuestOut:
        span = trace.get_current_span()
        span.set_attribute("guild.id", guild_id)
        span.set_attribute("quest.objectives_count", len(model.objectives))

        async with self.quest_repo.db.get_transaction() as conn:
            quest_db = await self.quest_repo.create(guild_id, model, conn)
            span.set_attribute("quest.id", quest_db.quest_id)

            for o in model.objectives:
                objective_db = await self.objective_repo.create(quest_db.quest_id, o, conn)

                for r in o.rewards:
                    await self.reward_repo.create(objective_db.quest_id, objective_db.objective_id, r, conn)

        return await self._to_out(quest_db)

    @traced
    async def update(self, guild_id: int, quest_id: int, model: QuestUpdate) -> QuestOut:
        span = trace.get_current_span()
        span.set_attribute("guild.id", guild_id)
        span.set_attribute("quest.id", quest_id)
        span.set_attribute("quest.objectives_submitted", len(model.objectives))

        objectives_updated = 0
        objectives_created = 0
        rewards_updated = 0
        rewards_created = 0

        async with self.quest_repo.db.get_transaction() as conn:
            quest_db = await self.quest_repo.update(quest_id, guild_id, model, conn)

            for o in model.objectives:
                if o.objective_id:
                    objective_db = await self.objective_repo.update(quest_db.quest_id, o.objective_id, o, conn)
                    objectives_updated += 1
                else:
                    objective_db = await self.objective_repo.create(quest_id, o, conn)
                    objectives_created += 1

                for r in o.rewards:
                    if r.reward_id:
                        await self.reward_repo.update(objective_db.objective_id, r.reward_id, r, conn)
                        rewards_updated += 1
                    else:
                        await self.reward_repo.create(quest_db.quest_id, objective_db.objective_id, r, conn)
                        rewards_created += 1

        span.set_attribute("quest.objectives_updated", objectives_updated)
        span.set_attribute("quest.objectives_created", objectives_created)
        span.set_attribute("quest.rewards_updated", rewards_updated)
        span.set_attribute("quest.rewards_created", rewards_created)

        return await self._to_out(quest_db)

    @traced
    async def get_statistics(self, guild_id: int, quest_id: int) -> QuestStatisticsOut:
        span = trace.get_current_span()
        span.set_attribute("guild.id", guild_id)
        span.set_attribute("quest.id", quest_id)

        summary, objective_rows, completion_times, daily_rows = await asyncio.gather(
            self.statistics_repo.fetch_quest_summary(quest_id, guild_id),
            self.statistics_repo.fetch_objective_statistics(quest_id),
            self.statistics_repo.fetch_completion_times(quest_id),
            self.statistics_repo.fetch_daily_activity(quest_id),
        )

        total_accepts = summary['total_accepts'] or 0
        total_completed = summary['total_completed'] or 0
        total_started = summary['total_started'] or 0

        completion_rate = total_completed / total_accepts if total_accepts > 0 else 0.0
        started_rate = total_started / total_accepts if total_accepts > 0 else 0.0

        histogram = _build_histogram(completion_times)

        objectives = [
            ObjectiveStatistics(
                objective_id=row['objective_id'],
                order_index=row['order_index'],
                description=row['description'],
                players_reached=row['players_reached'] or 0,
                players_completed=row['players_completed'] or 0,
                players_failed=row['players_failed'] or 0,
                completion_rate=(
                    (row['players_completed'] or 0) / row['players_reached']
                    if row['players_reached'] else 0.0
                ),
                drop_rate=(
                    (row['players_failed'] or 0) / row['players_reached']
                    if row['players_reached'] else 0.0
                ),
                avg_time_seconds=int(row['avg_time_seconds']) if row['avg_time_seconds'] is not None else None,
                median_time_seconds=int(row['median_time_seconds']) if row['median_time_seconds'] is not None else None,
            )
            for row in objective_rows
        ]

        return QuestStatisticsOut(
            quest_id=summary['quest_id'],
            title=summary['title'],
            quest_type=summary['quest_type'],
            total_accepts=total_accepts,
            total_pending=summary['total_pending'] or 0,
            total_started=total_started,
            total_completed=total_completed,
            total_failed=summary['total_failed'] or 0,
            completion_rate=completion_rate,
            started_rate=started_rate,
            avg_completion_time_seconds=int(summary['avg_completion_time_seconds']) if summary['avg_completion_time_seconds'] is not None else None,
            median_completion_time_seconds=int(summary['median_completion_time_seconds']) if summary['median_completion_time_seconds'] is not None else None,
            fastest_completion_seconds=int(summary['fastest_completion_seconds']) if summary['fastest_completion_seconds'] is not None else None,
            slowest_completion_seconds=int(summary['slowest_completion_seconds']) if summary['slowest_completion_seconds'] is not None else None,
            unique_players=summary['unique_players'] or 0,
            repeat_attempt_players=summary['repeat_attempt_players'] or 0,
            objectives=objectives,
            completion_time_histogram=histogram,
            daily_activity=[
                DailyActivityEntry(
                    date=row['date'],
                    accepts=row['accepts'] or 0,
                    completions=row['completions'] or 0,
                    failures=row['failures'] or 0,
                )
                for row in daily_rows
            ],
        )


def _build_histogram(durations: list[float], num_buckets: int = 10) -> list[QuestCompletionBucket]:
    """Splits completion durations into evenly-spaced buckets."""
    if not durations:
        return []

    min_d = min(durations)
    max_d = max(durations)

    if min_d == max_d:
        return [QuestCompletionBucket(
            bucket_start_seconds=int(min_d),
            bucket_end_seconds=int(max_d),
            count=len(durations)
        )]

    bucket_size = (max_d - min_d) / num_buckets
    buckets: list[QuestCompletionBucket] = []

    for i in range(num_buckets):
        start = min_d + i * bucket_size
        end = min_d + (i + 1) * bucket_size
        count = sum(1 for d in durations if start <= d < end)
        if i == num_buckets - 1:
            count = sum(1 for d in durations if start <= d <= end)
        buckets.append(QuestCompletionBucket(
            bucket_start_seconds=int(start),
            bucket_end_seconds=int(end),
            count=count,
        ))

    return buckets