from datetime import datetime, date

from pydantic import BaseModel, Field, StringConstraints, RootModel
from typing import Annotated, Optional, Literal, Union
from typing_extensions import Optional

from src.database import Database

from src.models.quests.reward import RewardCreateModel

from sanic_ext import openapi


InteractionRef = Annotated[str, StringConstraints(pattern='^[a-z]+:[a-z_0-9]+$')]
ObjectiveType = Literal["kill", "mine", "encounter"]


class ObjectiveModel(BaseModel):
    objective_id: int = Field(description="The ID of the objective")
    quest_id: int = Field(description="The ID of the quest")
    description: str = Field(description="The description of the objective")
    objective: InteractionRef = Field(description="The target of the objective",
                                      examples=["minecraft:dirt", 'minecraft:skeleton'])
    order: int = Field(description="The order of the objective",
                       examples=[1])
    objective_count: int = Field(description="How much until the objective is completed",
                                 examples=[32])
    objective_type: ObjectiveType = Field(description="The type of objective: kill, mine or encounter",
                                          examples=['kill', 'mine', 'encounter'])
    natural_block: bool = Field(description="Denotes whether the block mined must be natural or not")
    objective_timer: Optional[float] = Field(description='An optional timer for this objective in seconds',
                                             examples=[3600])
    required_mainhand: Optional[InteractionRef] = Field(description="An optional mainhand requirement for this objective",
                                                        examples=['minecraft:diamond_sword'])
    required_location: Optional[tuple[int, int]] = Field(description="An optional location requirement for this objective",
                                                         examples=[[56, 76]])
    location_radius: Optional[int] = Field(description="The radius for the location requirement",
                                           examples=[100])

    @classmethod
    async def fetch(cls, db: Database, quest_id: int, objective_id: int):
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
                                       AND quest_id = $2
                                       """,
                                      objective_id, quest_id)

        return cls(**data) if data else None

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


class ObjectivesListModel(RootModel):
    root: list[ObjectiveModel]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    @classmethod
    async def fetch(cls, db: Database, quest_id: int):
        objective_ids = await db.pool.fetchrow("""
                                               SELECT array_agg(objective_id) as ids FROM quests.objective
                                               WHERE quest_id = $1
                                               """,
                                              quest_id)

        objectives = []
        for objective_id in objective_ids.get('ids', []):
            objectives.append(await ObjectiveModel.fetch(db, quest_id, objective_id))

        return cls(root=objectives)

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


class ObjectiveCreateModel(BaseModel):
    objective: InteractionRef
    order: int
    description: str
    objective_count: int
    objective_type: ObjectiveType
    natural_block: bool
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
    description: Optional[str]
    objective_count: Optional[int]
    objective_type: Optional[ObjectiveType]
    natural_block: Optional[bool]
    objective_timer: Optional[float]
    required_mainhand: Optional[InteractionRef]
    required_location: Optional[tuple[int, int]]
    location_radius: Optional[int]

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")