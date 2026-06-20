import json

import asyncpg
from asyncpg.pool import PoolConnectionProxy

from src.dependencies.database import Database
from src.errors import AlreadyExists, NotFound
from src.models.quests.reward import RewardDB, RewardIn, RewardUpdate


class RewardRepository:
    def __init__(self, db: Database):
        self.db = db

    async def fetch(self, reward_id: int) -> RewardDB:
        data = await self.db.pool.fetchrow("""
            SELECT * FROM quests_v3.reward
            WHERE reward_id = $1
        """, reward_id)

        if not data:
            raise NotFound("Reward")

        return RewardDB.model_validate(dict(data))

    @staticmethod
    async def create(quest_id: int, objective_id: int, model: RewardIn, conn: PoolConnectionProxy) -> RewardDB:
        try:
            data = await conn.fetchrow("""
                WITH reward_table AS (
                    INSERT INTO quests_v3.reward (
                        quest_id,
                        objective_id,
                        balance,
                        item,
                        count,
                        display_name,
                        item_metadata
                        )
                        
                    VALUES($1, $2, $3, $4, $5, $6, $7)

                    RETURNING *
                )
                SELECT * FROM reward_table
            """, quest_id, objective_id, model.balance, model.item, model.count,
                   model.display_name, json.dumps([m.model_dump() for m in model.item_metadata], default=str))
        except asyncpg.UniqueViolationError:
            raise AlreadyExists("Reward")

        return RewardDB.model_validate(dict(data))

    async def update(self, objective_id: int, reward_id: int, model: RewardUpdate, conn: PoolConnectionProxy) -> RewardDB:
        reward = await self.fetch(reward_id)

        updated = reward.model_copy(update=model.model_dump(exclude_none=True))

        await conn.execute("""
            UPDATE quests_v3.reward
            SET objective_id = $1,
                balance = $2,
                item = $3,
                count = $4,
                display_name = $5,
                item_metadata = $6
            WHERE reward_id = $7
            AND objective_id = $8
        """, updated.objective_id, updated.balance, updated.item, updated.count, updated.display_name,
            json.dumps(updated.item_metadata, default=str), updated.reward_id, objective_id)

        return updated

    async def fetch_all(self, objective_id: int) -> list[RewardDB]:
        data = await self.db.pool.fetch("""
            SELECT * FROM quests_v3.reward
            WHERE objective_id = $1
            ORDER BY reward_id
        """, objective_id)

        return [RewardDB.model_validate(dict(r)) for r in data]