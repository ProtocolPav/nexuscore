from datetime import datetime, date

from pydantic import BaseModel, Field, StringConstraints
from typing import Annotated, Optional, Literal, Union
from typing_extensions import Optional

from src.database import Database

from src.models.quest_templates.reward import RewardCreateModel

from sanic_ext import openapi


InteractionRef = Annotated[str, StringConstraints(pattern='^[a-z]+:[a-z_]+$')]


class ObjectiveModel(BaseModel):
    objective_id: int
    quest_id: int
    objective: InteractionRef
    order: int
    objective_count: int
    objective_type: Literal["kill", "mine"]
    objective_timer: Optional[float]
    required_mainhand: Optional[InteractionRef]
    required_location: Optional[tuple[int, int]]
    location_radius: Optional[int]

    @classmethod
    async def fetch(cls, db: Database, objective_id: int):
        data = await db.pool.fetchrow("""
                                       SELECT objective_id,
                                              quest_id,
                                              objective,
                                              "order",
                                              objective_count,
                                              objective_type,
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

        return data['array_agg'] if data else None

    async def update(self, db: Database):
        await db.pool.execute("""
                              UPDATE quests.objective
                              SET objective = $1,
                                  objective_count = $2,
                                  objective_type = $3,
                                  objective_timer = $4,
                                  required_mainhand = $5,
                                  required_location = $6,
                                  location_radius = $7
                              WHERE objective_id = $8
                              """,
                              self.objective, self.objective_count, self.objective_type,
                              self.objective_timer, self.required_mainhand, self.required_location,
                              self.location_radius, self.objective_id)

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


class AllObjectivesModel(BaseModel):
    objectives: list[ObjectiveModel]

    @classmethod
    async def fetch(cls, db: Database, quest_id: int):
        ...



class ObjectiveCreateModel(BaseModel):
    objective: InteractionRef
    order: int
    objective_count: int
    objective_type: Literal["kill", "mine"]
    objective_timer: Optional[int]
    required_mainhand: Optional[InteractionRef]
    required_location: Optional[tuple[int, int]]
    location_radius: Optional[int]
    rewards: Optional[list[RewardCreateModel]]

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


class ObjectiveUpdateModel(BaseModel):
    objective: Optional[InteractionRef]
    objective_count: Optional[int]
    objective_type: Optional[Literal["kill", "mine"]]
    objective_timer: Optional[float]
    required_mainhand: Optional[InteractionRef]
    required_location: Optional[tuple[int, int]]
    location_radius: Optional[int]

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")