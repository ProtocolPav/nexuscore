from datetime import datetime, date

from pydantic import BaseModel, Field, StringConstraints
from typing import Annotated, Optional, Literal, Union
from typing_extensions import Optional

from src.database import Database

from sanic_ext import openapi


InteractionRef = Annotated[str, StringConstraints(pattern='^[a-z]+:[a-z_]+$')]


class RewardModel(BaseModel):
    reward_id: int
    quest_id: int
    objective_id: int
    balance: Optional[int]
    item: Optional[InteractionRef]
    count: Optional[int]

    @classmethod
    async def fetch(cls, db: Database, reward_id: int):
        data = await db.pool.fetchrow("""
                                       SELECT * FROM quests.reward
                                       WHERE reward_id = $1
                                       """,
                                      reward_id)

        return cls(**data)

    @classmethod
    async def get_all_rewards(cls, db: Database, quest_id: int):
        data = await db.pool.fetchrow("""
                                       SELECT array_agg(reward_id) FROM quests.reward
                                       WHERE quest_id = $1
                                       """,
                                      quest_id)

        return data['array_agg']

    async def update(self, db: Database):
        await db.pool.execute("""
                              UPDATE quests.reward
                              SET objective_id = $1,
                                  balance = $2,
                                  item = $3,
                                  count = $4
                              WHERE reward_id = $5
                              """,
                              self.objective_id, self.balance, self.item, self.count, self.reward_id)

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


class RewardCreateModel(BaseModel):
    balance: Optional[int]
    item: Optional[InteractionRef]
    count: Optional[int]

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


class RewardUpdateModel(BaseModel):
    balance: Optional[int]
    item: Optional[InteractionRef]
    count: Optional[int]

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")