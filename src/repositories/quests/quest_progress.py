from typing import Optional

import asyncpg
from asyncpg.pool import PoolConnectionProxy

from src.dependencies.database import Database
from src.errors import AlreadyExists, NotFound
from src.models.quests.daily import DAILY_QUEST_TYPE
from src.models.quests.quest_progress import QuestProgressDB, QuestProgressIn, QuestProgressUpdate


class QuestProgressRepository:
    def __init__(self, db: Database):
        self.db = db

    async def fetch(self, progress_id: int) -> QuestProgressDB:
        data = await self.db.fetchrow("""
            SELECT * FROM quests_v3.quest_progress
            WHERE progress_id = $1
        """,progress_id)

        if not data:
            raise NotFound("Quest Progress")

        return QuestProgressDB.model_validate(dict(data))

    async def fetch_active(self, thorny_id: int, quest_type: Optional[str] = None) -> QuestProgressDB:
        """
        Fetches the user's active quest progress.
        If `quest_type` is None, daily quests are excluded so that the user's
        regular (accepted) quest is returned. Otherwise, filters by that quest type.
        Daily quests are only considered while they are still running.
        """
        data = await self.db.fetchrow("""
            SELECT qp.* FROM quests_v3.quest_progress qp
            JOIN quests_v3.quest q ON q.quest_id = qp.quest_id
            WHERE qp.thorny_id = $1
                AND qp.status = 'active'
                AND (
                    ($2::varchar IS NULL AND q.quest_type <> $3)
                    OR q.quest_type = $2::varchar
                )
                AND (q.quest_type <> $3 OR q.end_time > now())
            ORDER BY qp.accept_time
            LIMIT 1
        """, thorny_id, quest_type, DAILY_QUEST_TYPE)

        if not data:
            raise NotFound("Quest Progress")

        return QuestProgressDB.model_validate(dict(data))

    async def fetch_users_quest_progress(self, thorny_id: int, quest_id: int) -> Optional[QuestProgressDB]:
        data = await self.db.fetchrow("""
            SELECT * FROM quests_v3.quest_progress
            WHERE thorny_id = $1
                AND quest_id = $2
            ORDER BY accept_time DESC
            LIMIT 1
        """, thorny_id, quest_id)

        return QuestProgressDB.model_validate(dict(data)) if data else None

    async def abandon_expired_progress(self) -> int:
        """
        Marks every unfinished quest progress whose quest has ended (any quest type)
        as abandoned, along with the objective the player was on. Objectives they never
        reached stay pending. Returns the number of quest progress rows abandoned.
        """
        async with self.db.get_transaction() as conn:
            abandoned = await conn.fetch("""
                UPDATE quests_v3.quest_progress qp
                SET status = 'abandoned',
                    end_time = now()
                FROM quests_v3.quest q
                WHERE qp.quest_id = q.quest_id
                    AND q.end_time <= now()
                    AND qp.status IN ('active', 'pending')
                RETURNING qp.progress_id
            """)

            progress_ids = [row['progress_id'] for row in abandoned]

            if progress_ids:
                await conn.execute("""
                    UPDATE quests_v3.objective_progress
                    SET status = 'abandoned',
                        end_time = now()
                    WHERE progress_id = ANY($1::int8[])
                        AND status = 'active'
                """, progress_ids)

        return len(progress_ids)

    @staticmethod
    async def create(
            model: QuestProgressIn,
            conn: PoolConnectionProxy
    ) -> QuestProgressDB:
        try:
            data = await conn.fetchrow("""
                WITH quest_table AS (
                    INSERT INTO quests_v3.quest_progress(
                        quest_id,
                        thorny_id,
                        status
                    )
                    VALUES($1, $2, 'active')

                    RETURNING *
                )
                SELECT * FROM quest_table
            """, model.quest_id, model.thorny_id)
        except asyncpg.UniqueViolationError:
            raise AlreadyExists("Quest Progress")

        return QuestProgressDB.model_validate(dict(data))

    async def update(
            self,
            progress_id: int,
            model: QuestProgressUpdate,
            conn: PoolConnectionProxy
    ) -> QuestProgressDB:
        quest = await self.fetch(progress_id)

        updated = quest.model_copy(update=model.model_dump(exclude_none=True))

        await conn.execute("""
            UPDATE quests_v3.quest_progress
            SET start_time = $1,
                end_time = $2,
                status = $3
            WHERE progress_id = $4
        """, updated.start_time, updated.end_time, updated.status, updated.progress_id)

        return updated

    async def fetch_all_users_progress(self, thorny_id: int) -> list[QuestProgressDB]:
        data = await self.db.fetch("""
            SELECT * from quests_v3.quest_progress
            WHERE thorny_id = $1
        """, thorny_id)

        return [QuestProgressDB.model_validate(dict(o)) for o in data]

    async def fetch_all_quests_progress(self, quest_id: int) -> list[QuestProgressDB]:
        data = await self.db.fetch("""
            SELECT * from quests_v3.quest_progress
            WHERE quest_id = $1
        """, quest_id)

        return [QuestProgressDB.model_validate(dict(o)) for o in data]
