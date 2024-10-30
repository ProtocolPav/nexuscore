import sanic
from pydantic import BaseModel, StringConstraints
from typing import Annotated, Optional, Literal, Union

from datetime import date, datetime, timedelta

from sanic_ext import openapi

from src.database import Database


class QuestModel(BaseModel):
    quest_id: int
    start_time: datetime
    end_time: datetime
    title: str
    description: str

    @classmethod
    async def fetch(cls, db: Database, quest_id: int):
        data = await db.pool.fetchrow("""
                                       SELECT quest_id,
                                              start_time,
                                              end_time,
                                              title,
                                              description
                                       FROM quests.quest
                                       WHERE quest_id = $1
                                       """,
                                      quest_id)

        return cls(**data)

    async def update(self, db: Database):
        await db.pool.execute("""
                              UPDATE quests.quest
                              SET start_time = $1,
                                  end_time = $2,
                                  title = $3,
                                  description = $4
                              WHERE quest_id = $5
                              """,
                              self.start_time, self.end_time,
                              self.title, self.description, self.quest_id)


class QuestUpdateModel(BaseModel):
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    title: Optional[str]
    description: Optional[str]


# minecraft:your_id_name
InteractionRef = Annotated[str, StringConstraints(pattern='^[a-z]+:[0-9a-z_]+$')]


class ObjectiveModel(BaseModel):
    objective_id: int
    quest_id: int
    description: str
    objective: InteractionRef
    order: int
    objective_count: int
    objective_type: Literal["kill", "mine"]
    natural_block: bool
    objective_timer: Optional[float]
    required_mainhand: Optional[InteractionRef]
    required_location: Optional[tuple[int, int]]
    location_radius: Optional[int]

    @classmethod
    async def fetch(cls, db: Database, objective_id: int):
        data = await db.pool.fetchrow("""
                                       SELECT objective_id,
                                              quest_id,
                                              description,
                                              objective,
                                              "order",
                                              objective_count,
                                              objective_type,
                                              natural_block,
                                              EXTRACT(EPOCH from objective_timer) as objective_timer,
                                              required_mainhand,
                                              required_location,
                                              location_radius
                                       FROM quests.objective
                                       WHERE objective_id = $1
                                       """,
                                      objective_id)

        return cls(**data)

    @classmethod
    async def get_all_objectives(cls, db: Database, quest_id: int):
        data = await db.pool.fetchrow("""
                                       SELECT array_agg(objective_id) FROM quests.objective
                                       WHERE quest_id = $1
                                       """,
                                      quest_id)

        return data['array_agg']

    async def update(self, db: Database):
        await db.pool.execute("""
                              UPDATE quests.objective
                              SET objective = $1,
                                  objective_count = $2,
                                  objective_type = $3,
                                  objective_timer = $4,
                                  required_mainhand = $5,
                                  required_location = $6,
                                  location_radius = $7,
                                  description = $8,
                                  natural_block = $9
                              WHERE objective_id = $10
                              """,
                              self.objective, self.objective_count, self.objective_type,
                              self.objective_timer, self.required_mainhand, self.required_location,
                              self.location_radius, self.description, self.natural_block, self.objective_id)


class ObjectiveUpdateModel(BaseModel):
    objective: Optional[InteractionRef]
    description: Optional[str]
    objective_count: Optional[int]
    objective_type: Optional[Literal["kill", "mine"]]
    natural_block: Optional[bool]
    objective_timer: Optional[float]
    required_mainhand: Optional[InteractionRef]
    required_location: Optional[tuple[int, int]]
    location_radius: Optional[int]


class RewardModel(BaseModel):
    reward_id: int
    quest_id: int
    objective_id: int
    display_name: Optional[str]
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
                                  count = $4,
                                  display_name = $5
                              WHERE reward_id = $6
                              """,
                              self.objective_id, self.balance, self.item, self.count,
                              self.display_name, self.reward_id)


class RewardUpdateModel(BaseModel):
    display_name: Optional[str]
    balance: Optional[int]
    item: Optional[InteractionRef]
    count: Optional[int]


class RewardCreateModel(BaseModel):
    display_name: Optional[str]
    balance: Optional[int]
    item: Optional[InteractionRef]
    count: Optional[int]


class QuestCreateModel(BaseModel):
    start_time: datetime
    end_time: datetime
    title: str
    description: str


class ObjectiveCreateModel(BaseModel):
    objective: InteractionRef
    order: int
    description: str
    objective_count: int
    objective_type: Literal["kill", "mine"]
    natural_block: bool
    objective_timer: Optional[int]
    required_mainhand: Optional[InteractionRef]
    required_location: Optional[tuple[int, int]]
    location_radius: Optional[int]
    rewards: Optional[list[RewardCreateModel]]


# Define components in the OpenAPI schema
# This can be done via a decorator, but for some reason
# the decorator stops intellisense from working
openapi.component(QuestModel)
openapi.component(ObjectiveModel)
openapi.component(RewardModel)
openapi.component(QuestCreateModel)
openapi.component(RewardCreateModel)
openapi.component(ObjectiveCreateModel)
