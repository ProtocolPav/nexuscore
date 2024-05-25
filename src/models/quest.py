import sanic
from pydantic import BaseModel
from typing import Optional, Literal, Union

from datetime import date, datetime, timedelta

from sanic_ext import openapi

from src.database import Database


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


class ObjectiveModel(BaseModel):
    objective_id: int
    quest_id: int
    objective: str
    order: int
    objective_count: int
    objective_type: str
    objective_timer: Optional[timedelta]
    required_mainhand: Optional[str]
    required_location: Optional[tuple[int, int]]
    location_radius: int

    @classmethod
    async def fetch(cls, db: Database, objective_id: int):
        data = await db.pool.fetchrow("""
                                       SELECT * FROM quests.objective
                                       WHERE objective_id = $1
                                       """,
                                      objective_id)

        return cls(**data)


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
