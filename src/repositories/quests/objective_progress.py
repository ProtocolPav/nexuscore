import json

import asyncpg
from asyncpg.pool import PoolConnectionProxy

from src.dependencies.database import Database
from src.errors import AlreadyExists, NotFound
from src.models.quests.objective_progress import ObjectiveProgressDB, ObjectiveProgressIn, ObjectiveProgressUpdate


class ObjectiveProgressRepository:
    def __init__(self, db: Database):
        self.db = db

    async def fetch(self, objective_id: int, progress_id: int) -> ObjectiveProgressDB:
        data = await self.db.pool.fetchrow("""
            SELECT * FROM quests_v3.objective_progress
            WHERE objective_id = $1
            AND progress_id = $2
        """,objective_id, progress_id)

        if not data:
            raise NotFound("Objective Progress")

        return ObjectiveProgressDB.model_validate(dict(data))

    @staticmethod
    async def create(
            progress_id: int,
            objective_id: int,
            model: ObjectiveProgressIn,
            conn: PoolConnectionProxy
    ) -> ObjectiveProgressDB:
        try:
            data = await conn.fetchrow("""
                WITH objective_table AS (
                    INSERT INTO quests_v3.objective_progress(
                        progress_id,
                        objective_id,
                        target_progress,
                        customization_progress
                    )
                    VALUES($1, $2, $3, $4)

                    RETURNING *
                )
                SELECT * FROM objective_table
            """, progress_id, objective_id,
                 json.dumps([t.model_dump() for t in model.target_progress], default=str),
                 model.customization_progress.model_dump_json())
        except asyncpg.UniqueViolationError:
            raise AlreadyExists("Objective Progress")

        return ObjectiveProgressDB.model_validate(dict(data))

    async def update(
            self,
            progress_id: int,
            objective_id: int,
            model: ObjectiveProgressUpdate,
            conn: PoolConnectionProxy
    ) -> ObjectiveProgressDB:
        objective = await self.fetch(objective_id, progress_id)

        updated = objective.model_copy(update=model.model_dump(exclude_none=True))

        await conn.execute("""
            UPDATE quests_v3.objective_progress
            SET start_time = $1,
                end_time = $2,
                target_progress = $3,
                customization_progress = $4,
                status = $5
            WHERE progress_id = $6
            AND objective_id = $7
        """, updated.start_time, updated.end_time, json.dumps([t.model_dump() for t in updated.target_progress], default=str),
             updated.customization_progress.model_dump_json(), updated.status, progress_id, objective_id)

        return updated

    async def fetch_all(self, progress_id: int) -> list[ObjectiveProgressDB]:
        data = await self.db.pool.fetch("""
            SELECT * from quests_v3.objective_progress
            WHERE progress_id = $1
        """, progress_id)

        return [ObjectiveProgressDB.model_validate(dict(o)) for o in data]
