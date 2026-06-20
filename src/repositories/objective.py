import json

import asyncpg
from asyncpg.pool import PoolConnectionProxy

from src.dependencies.database import Database
from src.errors import AlreadyExists, NotFound
from src.models.quests.objective import ObjectiveDB, ObjectiveIn, ObjectiveUpdate


class ObjectiveRepository:
    def __init__(self, db: Database):
        self.db = db

    async def fetch(self, objective_id: int) -> ObjectiveDB:
        data = await self.db.pool.fetchrow("""
            SELECT * FROM quests_v3.objective
            WHERE objective_id = $1
        """,objective_id)

        if not data:
            raise NotFound("Objective")

        return ObjectiveDB.model_validate(dict(data))

    @staticmethod
    async def create(quest_id: int, model: ObjectiveIn, conn: PoolConnectionProxy) -> ObjectiveDB:
        try:
            data = await conn.fetchrow("""
                WITH objective_table AS (
                    INSERT INTO quests_v3.objective (
                        quest_id, 
                        objective_type, 
                        order_index, 
                        description, 
                        display, 
                        logic, 
                        target_count, 
                        targets, 
                        customizations
                        )
                        
                    VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9)

                    RETURNING *
                )
                SELECT * FROM objective_table
            """, quest_id, model.objective_type, model.order_index, model.description, model.display, model.logic,
                       model.target_count, json.dumps([t.model_dump() for t in model.targets], default=str), model.customizations.model_dump_json())
        except asyncpg.UniqueViolationError:
            raise AlreadyExists("Objective")

        return ObjectiveDB.model_validate(dict(data))

    async def update(self, objective_id: int, model: ObjectiveUpdate) -> ObjectiveDB:
        objective = await self.fetch(objective_id)

        updated = objective.model_copy(update=model.model_dump(exclude_none=True))

        await self.db.pool.execute("""
            UPDATE quests_v3.objective
            SET objective_type = $1,
                order_index = $2,
                description = $3,
                display = $4,
                logic = $5,
                target_count = $6,
                targets = $7,
                customizations = $8
              
            WHERE objective_id = $9
        """,updated.objective_type, updated.order_index, updated.description, updated.display,
                                   updated.logic, updated.target_count, json.dumps([t.model_dump() for t in updated.targets], default=str),
                                   updated.customizations.model_dump_json(), updated.objective_id)

        return updated

    async def fetch_all(self, quest_id: int) -> list[ObjectiveDB]:
        data = await self.db.pool.fetch("""
            SELECT * FROM quests_v3.objective
            WHERE quest_id = $1
            ORDER BY order_index
        """, quest_id)

        return [ObjectiveDB.model_validate(dict(o)) for o in data]
