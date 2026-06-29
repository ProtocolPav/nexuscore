import json

from pydantic import Field, model_validator, BaseModel
from typing import Annotated, Literal, Optional

from src.models.quests.objective_customization.customization import Customizations
from src.models.quests.objective_targets.target import Targets
from src.models.quests.reward import RewardIn, RewardOut, RewardUpdate

QuestID = Annotated[int, Field(
    description="The ID of the quest this objective belongs to",
    examples=[732]
)]
ObjectiveID = Annotated[int, Field(
    description="The ID of the objective",
    examples=[12345]
)]
Description = Annotated[str, Field(
    description="The description of the objective",
    examples=["Kill 100 of the most powerful Thorns"],
)]
Display = Annotated[str, Field(
    description="Override the task display with a custom text",
    examples=["Kill 100 Thorns"],
)]
OrderIndex = Annotated[int, Field(
    description="The order of the objective. Starts at 0.",
    examples=[0],
)]
ObjectiveType = Annotated[Literal["kill", "mine", "scriptevent"], Field(
    description="The type of objective: kill, mine or scriptevent",
    examples=["mine"]
)]
Logic = Annotated[Literal["and", "or", "sequential"], Field(
    description="The logic to be applied to the objective targets",
    examples=["and"]
)]
TargetCount = Annotated[int, Field(
    description="The total count for `OR` logic",
    examples=[100],
)]
ObjectiveTargets = Annotated[list[Targets], Field(
    description="The targets of the objective. Target types must be equal to `objective_type`",
)]
ObjectiveCustomizations = Annotated[Customizations, Field(
    description="The customizations of the objective",
)]

class ObjectiveBase(BaseModel):
    objective_id: ObjectiveID
    description: Description
    display: Optional[Display]
    order_index: OrderIndex
    objective_type: ObjectiveType
    logic: Logic
    target_count: Optional[TargetCount]
    targets: ObjectiveTargets
    customizations: ObjectiveCustomizations


class ObjectiveDB(ObjectiveBase):
    quest_id: QuestID

    @model_validator(mode='before')
    @classmethod
    def pre_process_json(cls, data):
        if isinstance(data.get('targets'), str):
            data['targets'] = json.loads(data['targets'])

        if isinstance(data.get('customizations'), str):
            data['customizations'] = json.loads(data['customizations'])

        return data


class ObjectiveOut(ObjectiveBase):
    rewards: list[RewardOut]


class ObjectiveIn(BaseModel):
    description: Description
    display: Optional[Display]
    order_index: OrderIndex
    objective_type: ObjectiveType
    logic: Logic
    target_count: Optional[TargetCount]
    targets: ObjectiveTargets
    customizations: ObjectiveCustomizations
    rewards: list[RewardIn]

    @model_validator(mode='after')
    def check_targets(self) -> "ObjectiveIn":
        if len(self.targets) == 0:
            raise ValueError("Objectives must have at least one target")

        for target in self.targets:
            if target.target_type != self.objective_type:
                raise ValueError(f"All targets must be of the same type. "
                                      f"Offending target: {target.target_type} != {self.objective_type}")

            if target.count < 1:
                raise ValueError(f"A target's count must be at least 1.")

        return self


class ObjectiveUpdate(BaseModel):
    objective_id: Optional[ObjectiveID] = None
    description: Optional[Description] = None
    display: Optional[Display] = None
    order_index: Optional[OrderIndex] = None
    objective_type: Optional[ObjectiveType] = None
    logic: Optional[Logic] = None
    target_count: Optional[TargetCount] = None
    targets: Optional[ObjectiveTargets] = None
    customizations: Optional[ObjectiveCustomizations] = None
    rewards: Optional[list[RewardUpdate]] = []
