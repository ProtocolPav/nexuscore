from datetime import datetime, date

from pydantic import BaseModel, Field, StringConstraints, RootModel
from typing import Annotated, Optional, Literal, Union
from typing_extensions import Optional

from src.database import Database

from sanic_ext import openapi


InteractionRef = Annotated[str, StringConstraints(pattern='^[a-z]+:[a-z_0-9]+$')]


@openapi.component()
class RewardModel(BaseModel):
    reward_id: int
    quest_id: int
    objective_id: int
    balance: Optional[int]
    item: Optional[InteractionRef]
    count: Optional[int]
    display_name: Optional[str]

    @classmethod
    async def fetch(cls, db: Database, reward_id: int):
        data = await db.pool.fetchrow("""
                                       SELECT * FROM quests.reward
                                       WHERE reward_id = $1
                                       """,
                                      reward_id)

        return cls(**data) if data else None

    async def update(self, db: Database):
        await db.pool.execute("""
                              UPDATE quests.reward
                              SET objective_id = $1,
                                  balance = $2,
                                  item = $3,
                                  count = $4,
                                  display_name = $5
                              WHERE reward_id = $6
                              """,
                              self.objective_id, self.balance, self.item, self.count, self.display_name, self.reward_id)

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


class RewardsListModel(RootModel):
    root: list[RewardModel]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    @classmethod
    async def fetch(cls, db: Database, quest_id: int, objective_id: int):
        reward_ids = await db.pool.fetchrow("""
                                            SELECT array_agg(reward_id) as ids FROM quests.reward
                                            WHERE quest_id = $1
                                            AND objective_id = $2
                                            """,
                                            quest_id, objective_id)

        rewards = []
        for reward_id in reward_ids.get('ids', []):
            rewards.append(await RewardModel.fetch(db, reward_id))

        return cls(root=rewards)

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


@openapi.component()
class RewardCreateModel(BaseModel):
    balance: Optional[int]
    display_name: Optional[str]
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