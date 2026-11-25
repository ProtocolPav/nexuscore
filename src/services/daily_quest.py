import asyncio
import random
from datetime import date, timedelta
from typing import Optional

from opentelemetry import trace

from src.errors import AlreadyExists, BadRequest, NotFound
from src.models.quests.daily import (
    DAILY_QUEST_TYPE,
    DailyQuestDB,
    DailyQuestIn,
    DailyQuestOut,
    DailyTemplateDB,
    DailyTemplateIn,
    DailyTemplateOut,
    DailyTemplateUpdate,
)
from src.models.quests.quest import QuestOut
from src.models.quests.quest_progress import QuestProgressOut
from src.repositories.quests.daily_quest import DailyQuestRepository
from src.repositories.quests.daily_template import DailyTemplateRepository
from src.repositories.user import UserRepository
from src.services.quest import QuestService
from src.services.quest_progress import QuestProgressService
from src.utils.daily_generator import generate_daily_quest, utc_today
from src.utils.tracing import traced


class DailyQuestService:
    """
    Daily-quest specific logic: the template pool, choosing and generating each
    guild's daily quest, and finding today's quest.

    Generic quest and progress behaviour (creating quests, accepting, expiring)
    lives in QuestService and QuestProgressService, which this service uses.
    """

    def __init__(
            self,
            template_repo: DailyTemplateRepository,
            daily_repo: DailyQuestRepository,
            quest_service: QuestService,
            quest_progress_service: QuestProgressService,
            user_repo: UserRepository,
            duration_hours: int = 24,
    ):
        self.template_repo = template_repo
        self.daily_repo = daily_repo
        self.quest_service = quest_service
        self.quest_progress_service = quest_progress_service
        self.user_repo = user_repo
        self.duration_hours = duration_hours

    # ---------- Templates ----------

    async def _check_creator(self, guild_id: int, thorny_id: int) -> None:
        # Generated quests are attributed to the creator, so they must be in this guild
        try:
            await self.user_repo.fetch(guild_id, thorny_id)
        except NotFound:
            raise BadRequest("`created_by` must be a user in this guild")

    @traced
    async def get_template(self, guild_id: int, template_id: int) -> DailyTemplateOut:
        template_db = await self.template_repo.fetch(template_id, guild_id)
        return DailyTemplateOut(**template_db.model_dump())

    @traced
    async def get_templates(self, guild_id: int, enabled: Optional[bool] = None) -> list[DailyTemplateOut]:
        templates_db = await self.template_repo.fetch_all(guild_id, enabled)
        return [DailyTemplateOut(**t.model_dump()) for t in templates_db]

    @traced
    async def new_template(self, guild_id: int, model: DailyTemplateIn) -> DailyTemplateOut:
        await self._check_creator(guild_id, model.created_by)
        template_db = await self.template_repo.create(guild_id, model)
        return DailyTemplateOut(**template_db.model_dump())

    @traced
    async def update_template(self, guild_id: int, template_id: int, model: DailyTemplateUpdate) -> DailyTemplateOut:
        template_db = await self.template_repo.fetch(template_id, guild_id)

        # Re-validate the merged template so cross-field rules still hold
        try:
            merged = DailyTemplateIn.model_validate({
                **template_db.model_dump(include=set(DailyTemplateIn.model_fields)),
                **model.model_dump(exclude_unset=True),
            })
        except ValueError as e:
            raise BadRequest(str(e))

        await self._check_creator(guild_id, merged.created_by)
        template_db = await self.template_repo.update(template_id, guild_id, merged)
        return DailyTemplateOut(**template_db.model_dump())

    @traced
    async def delete_template(self, guild_id: int, template_id: int) -> None:
        await self.template_repo.delete(template_id, guild_id)

    def preview_template(self, model: DailyTemplateIn) -> DailyQuestIn:
        """Rolls a quest from a (possibly unsaved) template without saving anything."""
        return generate_daily_quest(model, utc_today(), duration_hours=self.duration_hours)

    # ---------- Generation ----------

    @staticmethod
    def _choose_template(
            templates: list[DailyTemplateDB],
            previous_template_id: Optional[int],
            rng: random.Random,
    ) -> DailyTemplateDB:
        # Avoid repeating yesterday's template when there is a choice
        candidates = [t for t in templates if t.template_id != previous_template_id] or templates
        return rng.choices(candidates, weights=[t.weight for t in candidates], k=1)[0]

    async def _fetch_daily(self, guild_id: int, quest_date: date) -> Optional[DailyQuestDB]:
        try:
            return await self.daily_repo.fetch(guild_id, quest_date)
        except NotFound:
            return None

    @traced
    async def generate(self, guild_id: int, quest_date: Optional[date] = None, force: bool = False) -> QuestOut:
        """
        Generates the daily quest for a guild.
        If one already exists for that day, it is returned unless `force` is set,
        in which case the old one is ended (its unfinished progress is abandoned) and replaced.
        """
        span = trace.get_current_span()
        span.set_attribute("guild.id", guild_id)

        quest_date = quest_date or utc_today()
        span.set_attribute("daily.date", quest_date.isoformat())

        if quest_date < utc_today():
            raise BadRequest("Daily quests cannot be generated for past days")

        existing = await self._fetch_daily(guild_id, quest_date)

        if existing and not force:
            return await self.quest_service.get(guild_id, existing.quest_id)

        templates = await self.template_repo.fetch_all(guild_id, enabled=True)
        if not templates:
            raise NotFound("Daily Template")

        rng = random.Random()
        previous = existing or await self.daily_repo.fetch_previous(guild_id, quest_date)
        template = self._choose_template(templates, previous.template_id if previous else None, rng)
        span.set_attribute("daily.template_id", template.template_id)

        quest_in = generate_daily_quest(template, quest_date, rng, duration_hours=self.duration_hours)

        # The quest and its daily_quest row are written atomically
        async with self.daily_repo.db.get_transaction() as conn:
            quest_db = await self.quest_service.create_in_transaction(guild_id, quest_in, conn)

            if existing:
                await self.quest_service.end_now(guild_id, existing.quest_id, conn)
                await self.daily_repo.replace(guild_id, quest_date, quest_db.quest_id, template.template_id, conn)
            else:
                await self.daily_repo.create(guild_id, quest_date, quest_db.quest_id, template.template_id, conn)

        span.set_attribute("quest.id", quest_db.quest_id)

        if existing:
            # Abandon progress on the replaced quest right away instead of waiting for the loop
            await self.quest_progress_service.abandon_expired()

        return await self.quest_service.get(guild_id, quest_db.quest_id)

    @traced
    async def ensure_upcoming_quests(self, days: int) -> None:
        """
        Makes sure every guild with enabled templates has daily quests generated for
        today and the following days, `days` in total. Pre-generating lets admins
        customise upcoming dailies. Called periodically by the background loop.
        """
        span = trace.get_current_span()

        today = utc_today()
        dates = [today + timedelta(days=i) for i in range(max(days, 1))]

        guild_ids = await self.template_repo.fetch_guilds_with_enabled_templates()
        span.set_attribute("daily.guilds", len(guild_ids))
        span.set_attribute("daily.backlog_days", len(dates))

        for guild_id in guild_ids:
            existing = {d.quest_date for d in await self.daily_repo.fetch_from(guild_id, dates[0], dates[-1])}

            # Oldest first, so each day avoids the previous day's template
            for quest_date in dates:
                if quest_date in existing:
                    continue

                try:
                    await self.generate(guild_id, quest_date)
                except AlreadyExists:
                    pass  # Generated concurrently by another worker

    # ---------- Today's quest ----------

    @traced
    async def get_day(self, guild_id: int, quest_date: Optional[date] = None) -> QuestOut:
        """The daily quest for a day, today by default."""
        daily_db = await self.daily_repo.fetch(guild_id, quest_date or utc_today())
        return await self.quest_service.get(guild_id, daily_db.quest_id)

    @traced
    async def get_upcoming(self, guild_id: int) -> list[DailyQuestOut]:
        """All generated daily quests from today onwards, ordered by date."""
        dailies_db = await self.daily_repo.fetch_from(guild_id, utc_today())
        quests = await asyncio.gather(*[self.quest_service.get(guild_id, d.quest_id) for d in dailies_db])

        return [
            DailyQuestOut(quest_date=d.quest_date, template_id=d.template_id, quest=q)
            for d, q in zip(dailies_db, quests)
        ]

    @traced
    async def accept_current(self, guild_id: int, thorny_id: int) -> QuestProgressOut:
        """
        Returns the user's current daily quest progress, accepting today's daily if needed.
        Players only ever have one daily at a time:

        - If they have an unfinished daily that is still running (e.g. yesterday's, while
          dailies overlap), that is returned.
        - Otherwise today's daily is accepted. If they already accepted it, their existing
          progress is returned, whatever its status.
        """
        try:
            return await self.quest_progress_service.get_active(thorny_id, DAILY_QUEST_TYPE)
        except NotFound:
            pass

        daily_db = await self.daily_repo.fetch(guild_id, utc_today())
        return await self.quest_progress_service.accept_once(guild_id, thorny_id, daily_db.quest_id)
