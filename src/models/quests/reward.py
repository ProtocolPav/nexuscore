from pydantic import Field, StringConstraints
from typing import Annotated, Optional
from src.utils.base import BaseModel, BaseList, optional_model

from src.database import Database

from sanic_ext import openapi


InteractionRef = Annotated[str, StringConstraints(pattern='^[a-z]+:[a-z_0-9]+$')]


class RewardBaseModel(BaseModel):
    balance: Optional[int] = Field(description="The balance this reward will add",
                                   json_schema_extra={"example": None})
    item: Optional[InteractionRef] = Field(description="The item this reward will give",
                                          json_schema_extra={"example": 'minecraft:gold_ingot'})
    count: Optional[int] = Field(description="The amount of this item this reward will give",
                                 json_schema_extra={"example": 43})
    display_name: Optional[str] = Field(description="The optional text to display instead of the reward item name",
                                       json_schema_extra={"example": 'Something Shiny'})


@openapi.component()
class RewardModel(RewardBaseModel):
    quest_id: int = Field(description="The ID of the quest this reward belongs to",
                          json_schema_extra={"example": 732})
    objective_id: int = Field(description="The ID of the objective this reward belongs to",
                              json_schema_extra={"example": 43})
    reward_id: int = Field(description="The ID of this reward",
                           json_schema_extra={"example": 345})


    @classmethod
    async def create(cls, db: Database, model: "RewardCreateModel", quest_id: int = None, objective_id: int = None, *args) -> "RewardModel":
        async with db.pool.acquire() as conn:
            async with conn.transaction():
                reward_id = await conn.fetchrow("""
                                                WITH reward_table AS (
                                                    INSERT INTO quests.reward(quest_id, 
                                                                              objective_id,
                                                                              balance,
                                                                              item,
                                                                              count,
                                                                              display_name)
                                                    VALUES($1, $2, $3, $4, $5, $6)
                                                    RETURNING reward_id
                                                )
                                                SELECT reward_id as id FROM reward_table
                                                """,
                                                quest_id, objective_id, model.balance, model.item, model.count,
                                                model.display_name)

                return cls(reward_id=reward_id['id'], quest_id=quest_id, objective_id=objective_id, **model.model_dump())


    @classmethod
    async def fetch(cls, db: Database, reward_id: int = None, *args):
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


class RewardsListModel(BaseList[RewardModel]):
    @classmethod
    async def fetch(cls, db: Database, objective_id: int = None, *args):
        reward_data = await db.pool.fetch("""
                                          SELECT *
                                          FROM quests.reward
                                          WHERE objective_id = $1
                                          """,
                                          objective_id)

        rewards: list[RewardModel] = []
        for reward in reward_data:
            rewards.append(RewardModel(**reward))

        return cls(root=rewards)


@openapi.component()
class RewardCreateModel(RewardBaseModel):
    pass


RewardUpdateModel = optional_model('RewardUpdateModel', RewardBaseModel)