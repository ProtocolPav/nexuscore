import json

from pydantic import Field, model_validator
from typing import Literal, Optional

from src.models.quests.objective_customization.customization import Customizations
from src.models.quests.objective_targets.target import Targets
from src.utils.base import BaseModel, BaseList, optional_model

from src.database import Database

from src.models.quests.reward import RewardCreateModel, RewardModel, RewardsListModel

from sanic_ext import openapi

from src.utils.errors import BadRequest400, NotFound404

Logic = Literal["and", "or", "sequential"]
ObjectiveTypes = Literal["kill", "mine", "encounter"]


class ObjectiveBaseModel(BaseModel):
    description: str = Field(description="The description of the objective",
                             json_schema_extra={"example": 'This is an objective description!'})
    display: Optional[str] = Field(description="Override with a custom objective task display",
                                   json_schema_extra={"example": "Find and speak to Alan Carr"})
    order_index: int = Field(description="The order of the objective. Starts at 0.",
                             json_schema_extra={"example": 0})
    objective_type: ObjectiveTypes = Field(description="The type of objective: kill, mine or encounter",
                                           json_schema_extra={"example": 'kill'})
    logic: Logic = Field(description="The logic to be applied to the objective targets",
                         json_schema_extra={"example": "or"})
    target_count: Optional[int] = Field(description="Total count for `OR` logic. If `null`, each target must meet its own count",
                                        json_schema_extra={"example": 54})
    targets: list[Targets] = Field(description="The targets of the objective. Target types must be equal to `objective_type`")
    customizations: Customizations = Field(description="The customizations of the objective")

    @model_validator(mode='before')
    @classmethod
    def pre_process_json(cls, data):
        if isinstance(data.get('targets'), str):
            data['targets'] = json.loads(data['targets'])

        if isinstance(data.get('customizations'), str):
            data['customizations'] = json.loads(data['customizations'])

        return data

    @model_validator(mode='after')
    def check_targets(self) -> "ObjectiveBaseModel":
        if len(self.targets) == 0:
            raise BadRequest400("Objectives must have at least one target")

        for target in self.targets:
            if target.target_type != self.objective_type:
                raise BadRequest400(f"All targets must be of the same type. "
                                    f"Offending target: {target.target_type} != {self.objective_type}")

            if target.count < 1:
                raise BadRequest400(f"A target's count must be at least 1.")

        return self


@openapi.component()
class ObjectiveModel(ObjectiveBaseModel):
    quest_id: int = Field(description="The ID of the quest this objective belongs to",
                          json_schema_extra={"example": 732})
    objective_id: int = Field(description="The ID of this objective",
                              json_schema_extra={"example": 43})
    rewards: RewardsListModel = Field(description="The rewards for this objective, if any")

    @classmethod
    async def create(cls, db: Database, model: "ObjectiveCreateModel", quest_id: int = None, *args) -> int:
        async with db.pool.acquire() as conn:
            async with conn.transaction():
                targets = list(map(lambda x: x.model_dump(), model.targets))

                objective_id = await conn.fetchrow("""
                                                    with objective_table as (
                                                        insert into quests_v3.objective (
                                                            quest_id, 
                                                            objective_type, 
                                                            order_index, 
                                                            description, 
                                                            display, 
                                                            logic, 
                                                            target_count, 
                                                            targets, 
                                                            customizations
                                                            )
                                                        values($1, $2, $3, $4, $5, $6, $7, $8, $9)
        
                                                        returning objective_id
                                                    )
                                                    select objective_id as id from objective_table
                                                   """,
                                                   quest_id, model.objective_type, model.order_index, model.description,
                                                   model.display, model.logic, model.target_count,
                                                   json.dumps(targets, default=str), model.customizations.model_dump_json())

        for reward in model.rewards:
            await RewardModel.create(db=db, model=reward, quest_id=quest_id, objective_id=objective_id['id'])

        return objective_id['id']

    @classmethod
    async def fetch(cls, db: Database, objective_id: int = None, *args) -> "ObjectiveModel":
        if not objective_id:
            raise BadRequest400(extra={'ids': ['objective_id']})

        data = await db.pool.fetchrow("""
                                       SELECT * FROM quests_v3.objective
                                       WHERE objective_id = $1
                                       """,
                                      objective_id)

        if data:
            rewards = await RewardsListModel.fetch(db, objective_id)

            return cls(**data, rewards=rewards)
        else:
            raise NotFound404(extra={'resource': 'objective', 'id': objective_id})

    async def update(self, db: Database, model: "ObjectiveUpdateModel"):
        for k, v in model.model_dump().items():
            setattr(self, k, v) if v is not None else None

        targets = list(map(lambda x: x.model_dump(), self.targets))

        await db.pool.execute("""
                              UPDATE quests_v3.objective
                              SET objective_type = $1,
                                  order_index = $2,
                                  description = $3,
                                  display = $4,
                                  logic = $5,
                                  target_count = $6,
                                  targets = $7,
                                  customizations = $8
                                  
                              WHERE objective_id = $9
                              """,
                              self.objective_type, self.order_index, self.description, self.display,
                              self.logic, self.target_count, json.dumps(targets, default=str),
                              self.customizations.model_dump_json(), self.objective_id)


@openapi.component()
class ObjectivesListModel(BaseList[ObjectiveModel]):
    @classmethod
    async def fetch(cls, db: Database, quest_id: int = None, *args) -> "ObjectivesListModel":
        if not quest_id:
            raise BadRequest400(extra={'ids': ['quest_id']})

        data = await db.pool.fetch("""
                                 SELECT * FROM quests_v3.objective
                                 WHERE quest_id = $1
                                 ORDER BY order_index
                                 """,
                                 quest_id)

        objectives: list[ObjectiveModel] = []
        for objective in data:
            rewards = await RewardsListModel.fetch(db, objective['objective_id'])
            objectives.append(ObjectiveModel(**objective, rewards=rewards))

        return cls(root=objectives)


@openapi.component()
class ObjectiveCreateModel(ObjectiveBaseModel):
    rewards: list[RewardCreateModel] = Field(description="The rewards for this objective, if any")


ObjectiveUpdateModel = optional_model('ObjectiveUpdateModel', ObjectiveBaseModel)