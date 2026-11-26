from datetime import date
from typing import Optional

import asyncpg
from asyncpg.pool import PoolConnectionProxy

from src.dependencies.database import Database
from src.errors import AlreadyExists, NotFound
from src.models.quests.daily import DailyQuestDB


class DailyQuestRepository:
    def __init__(self, db: Database):
        self.db = db

    async def fetch(self, guild_id: int, quest_date: date) -> DailyQuestDB:
        data = await self.db.fetchrow("""
            SELECT * FROM quests_v3.daily_quest
            WHERE guild_id = $1
            AND quest_date = $2
        """, guild_id, quest_date)

        if not data:
            raise NotFound("Daily Quest")

        return DailyQuestDB.model_validate(dict(data))

    async def fetch_from(self, guild_id: int, start: date, end: Optional[date] = None) -> list[DailyQuestDB]:
        """Daily quests from `start` onwards (and up to `end`, if given), ordered by date."""
        data = await self.db.fetch("""
            SELECT * FROM quests_v3.daily_quest
            WHERE guild_id = $1
            AND quest_date >= $2
            AND ($3::date IS NULL OR quest_date <= $3::date)
            ORDER BY quest_date
        """, guild_id, start, end)

        return [DailyQuestDB.model_validate(dict(d)) for d in data]

    async def fetch_previous(self, guild_id: int, quest_date: date) -> Optional[DailyQuestDB]:
        data = await self.db.fetchrow("""
            SELECT * FROM quests_v3.daily_quest
            WHERE guild_id = $1
            AND quest_date < $2
            ORDER BY quest_date DESC
            LIMIT 1
        """, guild_id, quest_date)

        return DailyQuestDB.model_validate(dict(data)) if data else None

    @staticmethod
    async def create(
            guild_id: int,
            quest_date: date,
            quest_id: int,
            template_id: Optional[int],
            conn: PoolConnectionProxy,
    ) -> DailyQuestDB:
        try:
            data = await conn.fetchrow("""
                INSERT INTO quests_v3.daily_quest(guild_id, quest_date, quest_id, template_id)
                VALUES($1, $2, $3, $4)
                RETURNING *
            """, guild_id, quest_date, quest_id, template_id)
        except asyncpg.UniqueViolationError:
            raise AlreadyExists("Daily Quest")

        return DailyQuestDB.model_validate(dict(data))

    @staticmethod
    async def replace(
            guild_id: int,
            quest_date: date,
            quest_id: int,
            template_id: Optional[int],
            conn: PoolConnectionProxy,
    ) -> DailyQuestDB:
        data = await conn.fetchrow("""
            UPDATE quests_v3.daily_quest
            SET quest_id = $3,
                template_id = $4
            WHERE guild_id = $1
            AND quest_date = $2
            RETURNING *
        """, guild_id, quest_date, quest_id, template_id)

        if not data:
            raise NotFound("Daily Quest")

        return DailyQuestDB.model_validate(dict(data))
