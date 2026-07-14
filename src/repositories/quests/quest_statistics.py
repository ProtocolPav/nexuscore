from src.dependencies.database import Database
from src.errors import NotFound


class QuestStatisticsRepository:
    def __init__(self, db: Database):
        self.db = db

    async def fetch_quest_summary(self, quest_id: int, guild_id: int) -> dict:
        """
        Returns top-level funnel counts, timing stats, and player counts for a quest.
        guild_id is used to scope the quest ownership check.
        Raises NotFound if the quest does not exist within the guild.
        """
        data = await self.db.pool.fetchrow("""
            SELECT
                q.quest_id,
                q.title,
                q.quest_type,

                COUNT(qp.progress_id)                                           AS total_accepts,
                COUNT(qp.progress_id) FILTER (WHERE qp.status = 'pending')      AS total_pending,
                COUNT(qp.progress_id) FILTER (WHERE qp.status = 'active'
                                                 OR qp.status = 'completed'
                                                 OR qp.status = 'failed')       AS total_started,
                COUNT(qp.progress_id) FILTER (WHERE qp.status = 'completed')    AS total_completed,
                COUNT(qp.progress_id) FILTER (WHERE qp.status = 'failed')       AS total_failed,

                -- Timing (seconds): only for completed rows that have both start and end
                AVG(
                    EXTRACT(EPOCH FROM (qp.end_time - qp.start_time))
                ) FILTER (WHERE qp.status = 'completed'
                            AND qp.start_time IS NOT NULL
                            AND qp.end_time   IS NOT NULL)                      AS avg_completion_time_seconds,

                PERCENTILE_CONT(0.5) WITHIN GROUP (
                    ORDER BY EXTRACT(EPOCH FROM (qp.end_time - qp.start_time))
                ) FILTER (WHERE qp.status = 'completed'
                            AND qp.start_time IS NOT NULL
                            AND qp.end_time   IS NOT NULL)                      AS median_completion_time_seconds,

                MIN(
                    EXTRACT(EPOCH FROM (qp.end_time - qp.start_time))
                ) FILTER (WHERE qp.status = 'completed'
                            AND qp.start_time IS NOT NULL
                            AND qp.end_time   IS NOT NULL)                      AS fastest_completion_seconds,

                MAX(
                    EXTRACT(EPOCH FROM (qp.end_time - qp.start_time))
                ) FILTER (WHERE qp.status = 'completed'
                            AND qp.start_time IS NOT NULL
                            AND qp.end_time   IS NOT NULL)                      AS slowest_completion_seconds,

                COUNT(DISTINCT qp.thorny_id)                                    AS unique_players,

                COUNT(*) FILTER (WHERE sub.attempt_count > 1)                   AS repeat_attempt_players

            FROM quests_v3.quest q
            LEFT JOIN quests_v3.quest_progress qp ON qp.quest_id = q.quest_id
            LEFT JOIN (
                SELECT thorny_id, COUNT(*) AS attempt_count
                FROM quests_v3.quest_progress
                WHERE quest_id = $1
                GROUP BY thorny_id
            ) sub ON sub.thorny_id = qp.thorny_id
            WHERE q.quest_id = $1
              AND q.guild_id = $2
            GROUP BY q.quest_id, q.title, q.quest_type
        """, quest_id, guild_id)

        if not data:
            raise NotFound("Quest")

        return dict(data)

    async def fetch_objective_statistics(self, quest_id: int) -> list[dict]:
        """
        Returns per-objective funnel and timing stats, sorted by order_index.
        Raises NotFound if no objectives exist for the quest.
        """
        rows = await self.db.pool.fetch("""
            SELECT
                o.objective_id,
                o.order_index,
                o.description,

                COUNT(op.progress_id)                                               AS players_reached,
                COUNT(op.progress_id) FILTER (WHERE op.status = 'completed')        AS players_completed,
                COUNT(op.progress_id) FILTER (WHERE op.status = 'failed')           AS players_failed,

                AVG(
                    EXTRACT(EPOCH FROM (op.end_time - op.start_time))
                ) FILTER (WHERE op.status = 'completed'
                            AND op.start_time IS NOT NULL
                            AND op.end_time   IS NOT NULL)                          AS avg_time_seconds,

                PERCENTILE_CONT(0.5) WITHIN GROUP (
                    ORDER BY EXTRACT(EPOCH FROM (op.end_time - op.start_time))
                ) FILTER (WHERE op.status = 'completed'
                            AND op.start_time IS NOT NULL
                            AND op.end_time   IS NOT NULL)                          AS median_time_seconds

            FROM quests_v3.objective o
            LEFT JOIN quests_v3.objective_progress op ON op.objective_id = o.objective_id
            WHERE o.quest_id = $1
            GROUP BY o.objective_id, o.order_index, o.description
            ORDER BY o.order_index ASC
        """, quest_id)

        if not rows:
            raise NotFound("Quest Objectives")

        return [dict(r) for r in rows]

    async def fetch_completion_times(self, quest_id: int) -> list[float]:
        """
        Returns raw completion durations in seconds for histogram bucketing.
        Returns an empty list if no completions exist yet — not an error condition.
        """
        rows = await self.db.pool.fetch("""
            SELECT EXTRACT(EPOCH FROM (end_time - start_time)) AS duration_seconds
            FROM quests_v3.quest_progress
            WHERE quest_id = $1
              AND status = 'completed'
              AND start_time IS NOT NULL
              AND end_time   IS NOT NULL
        """, quest_id)

        return [float(r['duration_seconds']) for r in rows]

    async def fetch_daily_activity(self, quest_id: int) -> list[dict]:
        """
        Returns daily accept/completion/failure counts for time-series charts.
        Returns an empty list if no activity exists yet — not an error condition.
        """
        rows = await self.db.pool.fetch("""
            SELECT
                accept_time::date                                                       AS date,
                COUNT(*)                                                                AS accepts,
                COUNT(*) FILTER (WHERE status = 'completed')                           AS completions,
                COUNT(*) FILTER (WHERE status = 'failed')                              AS failures
            FROM quests_v3.quest_progress
            WHERE quest_id = $1
            GROUP BY accept_time::date
            ORDER BY accept_time::date ASC
        """, quest_id)

        return [dict(r) for r in rows]
