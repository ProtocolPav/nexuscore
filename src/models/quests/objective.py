from pydantic import Field, StringConstraints
from typing import Annotated, Literal, Optional
from src.utils.base import BaseModel, BaseList, optional_model

from src.database import Database

from src.models.quests.reward import RewardCreateModel

from sanic_ext import openapi


InteractionRef = Annotated[str, StringConstraints(pattern='^[a-z]+:[a-z_0-9]+$')]
ObjectiveType = Literal["kill", "mine", "encounter"]


class ObjectiveBaseModel(BaseModel):
    objective_type: ObjectiveType = Field(description="The type of objective: kill, mine or encounter",
                                          json_schema_extra={"example": 'kill'})
    objective_count: int = Field(description="How much until the objective is completed",
                                 json_schema_extra={"example": 32})
    objective: InteractionRef = Field(description="The target of the objective",
                                      json_schema_extra={"example": 'minecraft:skeleton'})
    description: str = Field(description="The description of the objective",
                             json_schema_extra={"example": 'Did you know skeletons hate diamonds...'})
    display: Optional[str] = Field(description="Override with a custom objective task display",
                                   json_schema_extra={"example": None})
    order: int = Field(description="The order of the objective",
                       json_schema_extra={"example": 0})
    natural_block: bool = Field(description="Denotes whether the block mined must be natural or not",
                                json_schema_extra={"example": False})
    objective_timer: Optional[float] = Field(description='An optional timer for this objective in seconds',
                                             json_schema_extra={"example": 30})
    required_mainhand: Optional[InteractionRef] = Field(description="An optional mainhand requirement for this objective",
                                                        json_schema_extra={"example": 'minecraft:diamond_sword'})
    required_location: Optional[list[int]] = Field(description="An optional location requirement for this objective",
                                                   json_schema_extra={"example": [56, 76]})
    location_radius: Optional[int] = Field(description="The radius for the location requirement",
                                           json_schema_extra={"example": 100})

@openapi.component()
class ObjectiveModel(ObjectiveBaseModel):
    quest_id: int = Field(description="The ID of the quest this objective belongs to",
                          json_schema_extra={"example": 732})
    objective_id: int = Field(description="The ID of this objective",
                              json_schema_extra={"example": 43})

    @classmethod
    async def fetch(cls, db: Database, quest_id: int = None, objective_id: int = None, *args):
        data = await db.pool.fetchrow("""
                                       SELECT objective_id,
                                              quest_id,
                                              description,
                                              objective,
                                              display,
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


class ObjectivesListModel(BaseList[ObjectiveModel]):
    @classmethod
    async def fetch(cls, db: Database, quest_id: int = None, *args):
        objective_ids = await db.pool.fetchrow("""
                                               SELECT array_agg(objective_id) as ids FROM quests.objective
                                               WHERE quest_id = $1
                                               """,
                                              quest_id)

        objectives = []
        for objective_id in objective_ids.get('ids', []):
            objectives.append(await ObjectiveModel.fetch(db, quest_id, objective_id))

        objectives.sort(key=lambda x: x.order)

        return cls(root=objectives)


@openapi.component()
class ObjectiveCreateModel(ObjectiveBaseModel):
    rewards: Optional[list[RewardCreateModel]] = Field(description="The rewards for this objective, if any")


ObjectiveUpdateModel = optional_model('ObjectiveUpdateModel', ObjectiveBaseModel)