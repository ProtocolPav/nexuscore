import sanic
from pydantic import BaseModel
from typing import Optional, Literal, Union

from datetime import date, datetime, timedelta

from sanic_ext import openapi

from src.database import Database


@openapi.component
class QuestModel(BaseModel):
    quest_id: int
    start_time: datetime
    end_time: datetime
    timer: Optional[timedelta]
    title: str
    description: str

    @classmethod
    async def fetch(cls, db: Database, quest_id: int):
        data = await db.pool.fetchrow("""
                                       SELECT * FROM quests.quest
                                       WHERE quest_id = $1
                                       """,
                                      quest_id)

        return cls(**data)


class QuestUpdateModel(BaseModel):
    start_time: datetime
    end_time: datetime
    timer: Optional[timedelta]
    title: str
    description: str


@openapi.component
class ObjectiveModel(BaseModel):
    objective_id: int
    quest_id: int
    objective: str
    order: int
    objective_count: int
    objective_type: Literal["kill", "mine"]
    objective_timer: Optional[timedelta]
    required_mainhand: Optional[str]
    required_location: Optional[tuple[int, int]]
    location_radius: Optional[int]

    @classmethod
    async def fetch(cls, db: Database, objective_id: int):
        data = await db.pool.fetchrow("""
                                       SELECT * FROM quests.objective
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


class ObjectiveUpdateModel(BaseModel):
    objective: str
    order: int
    objective_count: int
    objective_type: Literal["kill", "mine"]
    objective_timer: Optional[timedelta]
    required_mainhand: Optional[str]
    required_location: Optional[tuple[int, int]]
    location_radius: Optional[int]


@openapi.component
class RewardModel(BaseModel):
    reward_id: int
    quest_id: int
    objective_id: Optional[int]
    balance: Optional[int]
    item: Optional[str]
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


class RewardUpdateModel(BaseModel):
    objective_id: Optional[int]
    balance: Optional[int]
    item: Optional[str]
    count: Optional[int]


@openapi.component
class RewardCreateModel(BaseModel):
    balance: Optional[int]
    item: Optional[str]
    count: Optional[int]


@openapi.component
class QuestCreateModel(BaseModel):
    start_time: datetime
    end_time: datetime
    timer: Optional[timedelta]
    title: str
    description: str
    rewards: Optional[list[RewardCreateModel]]


@openapi.component
class ObjectiveCreateModel(BaseModel):
    objective: str
    order: int
    objective_count: int
    objective_type: Literal["kill", "mine"]
    objective_timer: Optional[timedelta]
    required_mainhand: Optional[str]
    required_location: Optional[tuple[int, int]]
    location_radius: Optional[int]
    rewards: Optional[list[RewardCreateModel]]
