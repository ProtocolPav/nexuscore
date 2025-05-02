import datetime

from pydantic import Field, StringConstraints
from typing import Annotated, Literal, Optional

from src.utils.base import BaseModel, BaseList, optional_model

from src.database import Database

from src.models.quests.reward import RewardCreateModel, RewardModel, RewardsListModel

from sanic_ext import openapi

from src.utils.errors import BadRequest400, NotFound404

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
    rewards: Optional[BaseList[RewardModel]] = Field(description="The rewards for this objective, if any")

    @classmethod
    async def create(cls, db: Database, model: "ObjectiveCreateModel", quest_id: int = None, *args) -> "ObjectiveModel":
        async with db.pool.acquire() as conn:
            async with conn.transaction():
                objective_id = await conn.fetchrow("""
                                                    with objective_table as (
                                                        insert into quests.objective(quest_id,
                                                                                     objective,
                                                                                     objective_count,
                                                                                     objective_type,
                                                                                     objective_timer,
                                                                                     required_mainhand,
                                                                                     required_location,
                                                                                     location_radius,
                                                                                     "order",
                                                                                     description,
                                                                                     natural_block,
                                                                                     display)
                                                        values($1, 
                                                               $2, 
                                                               $3, 
                                                               $4, 
                                                               CASE WHEN $5::double precision IS NULL THEN NULL
                                                               ELSE make_interval(secs => $5::double precision)
                                                               END, 
                                                               $6, 
                                                               $7, 
                                                               $8, 
                                                               $9,
                                                               $10,
                                                               $11,
                                                               $12)
        
                                                        returning objective_id
                                                    )
                                                    select objective_id as id from objective_table
                                                   """,
                                                   quest_id, model.objective, model.objective_count,
                                                   model.objective_type, model.objective_timer,
                                                   model.required_mainhand, model.required_location,
                                                   model.location_radius, model.order, model.description,
                                                   model.natural_block, model.display)

        for reward in model.rewards:
            await RewardModel.create(db=db, model=reward, quest_id=quest_id, objective_id=objective_id['id'])

    @classmethod
    async def fetch(cls, db: Database, objective_id: int = None, *args) -> "ObjectiveModel":
        if not objective_id:
            raise BadRequest400('No objective ID provided. Please provide an ID to fetch an objective by')

        data = await db.pool.fetchrow("""
                                       SELECT * FROM quests.objective
                                       WHERE objective_id = $1
                                       """,
                                      objective_id)

        rewards = await RewardsListModel.fetch(db, objective_id)

        if data:
            return cls(**data, rewards=rewards)
        else:
            raise NotFound404(extra={'resource': 'objective', 'id': objective_id})

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


@openapi.component()
class ObjectivesListModel(BaseList[ObjectiveModel]):
    @classmethod
    async def fetch(cls, db: Database, quest_id: int = None, *args):
        objective_data = await db.pool.fetch("""
                                             SELECT * FROM quests.objective
                                             WHERE quest_id = $1
                                             ORDER BY "order"
                                             """,
                                             quest_id)

        objectives: list[ObjectiveModel] = []
        for objective in objective_data:
            rewards = await RewardsListModel.fetch(db, objective['objective_id'])
            objectives.append(ObjectiveModel(**objective, rewards=rewards))

        return cls(root=objectives)


@openapi.component()
class ObjectiveCreateModel(ObjectiveBaseModel):
    rewards: Optional[list[RewardCreateModel]] = Field(description="The rewards for this objective, if any")


ObjectiveUpdateModel = optional_model('ObjectiveUpdateModel', ObjectiveBaseModel)