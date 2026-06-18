import json

from pydantic import Field, model_validator
from typing import Annotated, Literal, Optional

from src.models.quests.objective_customization.customization import Customizations
from src.models.quests.objective_targets.target import Targets
from src.utils.base import BaseModel, BaseList, optional_model

from src.dependencies.database import Database

from src.models.quests.reward import RewardCreateModel, RewardModel, RewardsListModel


from fastapi import HTTPException


QuestID = Annotated[int, Field(
    description="The ID of the quest this objective belongs to",
)]
ObjectiveID = Annotated[int, Field(
    description="The ID of the objective",
)]
Description = Annotated[str, Field(
    description="The description of the objective",
)]
Display = Annotated[str, Field(
    description="Override the task display with a custom text",
)]
OrderIndex = Annotated[int, Field(
    description="The order of the objective. Starts at 0.",
)]
ObjectiveType = Annotated[Literal["kill", "mine", "scriptevent"], Field(
    description="The type of objective: kill, mine or scriptevent",
)]
Logic = Annotated[Literal["and", "or", "sequential"], Field(
    description="The logic to be applied to the objective targets",
)]
TargetCount = Annotated[int, Field(
    description="The total count for `OR` logic",
)]
ObjectiveTargets = Annotated[list[Targets], Field(
    description="The targets of the objective. Target types must be equal to `objective_type`",
)]
ObjectiveCustomizations = Annotated[list[Customizations], Field(
    description="The customizations of the objective",
)]


class ObjectiveDB(BaseModel):
    quest_id: QuestID
    objective_id: ObjectiveID
    description: Description
    display: Display
    order_index: OrderIndex
    objective_type: ObjectiveType
    logic: Logic
    target_count: TargetCount
    targets: ObjectiveTargets
    customizations: ObjectiveCustomizations

    @model_validator(mode='before')
    @classmethod
    def pre_process_json(cls, data):
        if isinstance(data.get('targets'), str):
            data['targets'] = json.loads(data['targets'])

        if isinstance(data.get('customizations'), str):
            data['customizations'] = json.loads(data['customizations'])

        return data

    @model_validator(mode='after')
    def check_targets(self) -> "ObjectiveDB":
        if len(self.targets) == 0:
            raise HTTPException(status_code=400, detail="Objectives must have at least one target")

        for target in self.targets:
            if target.target_type != self.objective_type:
                raise HTTPException(status_code=400, detail=f"All targets must be of the same type. "
                                                            f"Offending target: {target.target_type} != {self.objective_type}")

            if target.count < 1:
                raise HTTPException(status_code=400, detail=f"A target's count must be at least 1.")

        return self


class ObjectiveOut(ObjectiveDB):
    objective_id: ObjectiveID
    description: Description
    display: Display
    order_index: OrderIndex
    objective_type: ObjectiveType
    logic: Logic
    target_count: TargetCount
    targets: ObjectiveTargets
    customizations: ObjectiveCustomizations
    # rewards


class ObjectiveIn(BaseModel):
    description: Description
    display: Display
    order_index: OrderIndex
    objective_type: ObjectiveType
    logic: Logic
    target_count: TargetCount
    targets: ObjectiveTargets
    customizations: ObjectiveCustomizations


class ObjectiveUpdate(BaseModel):
    description: Optional[Description] = None
    display: Optional[Display] = None
    order_index: Optional[OrderIndex] = None
    objective_type: Optional[ObjectiveType] = None
    logic: Optional[Logic] = None
    target_count: Optional[TargetCount] = None
    targets: Optional[ObjectiveTargets] = None
    customizations: Optional[ObjectiveCustomizations] = None


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
            raise HTTPException(status_code=400, detail="Missing required parameters")

        data = await db.pool.fetchrow("""
                                       SELECT * FROM quests_v3.objective
                                       WHERE objective_id = $1
                                       """,
                                      objective_id)

        if data:
            rewards = await RewardsListModel.fetch(db, objective_id)

            return cls(**data, rewards=rewards)
        else:
            raise HTTPException(status_code=404, detail="Objective not found")

    async def update(self, db: Database, model: "ObjectiveUpdateModel"):
        for k in model.model_dump().keys():
            v = getattr(model, k)
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


class ObjectivesListModel(BaseList[ObjectiveModel]):
    @classmethod
    async def fetch(cls, db: Database, quest_id: int = None, *args) -> "ObjectivesListModel":
        if not quest_id:
            raise HTTPException(status_code=400, detail="Missing required parameters")

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


class ObjectiveCreateModel(ObjectiveBaseModel):
    rewards: list[RewardCreateModel] = Field(description="The rewards for this objective, if any")


ObjectiveUpdateModel = optional_model('ObjectiveUpdateModel', ObjectiveBaseModel)