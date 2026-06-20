import json

from pydantic import Field, model_validator, ValidationError, BaseModel
from typing import Annotated, Literal, Optional

from src.models.quests.objective_customization.customization import Customizations
from src.models.quests.objective_targets.target import Targets


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
ObjectiveCustomizations = Annotated[Customizations, Field(
    description="The customizations of the objective",
)]


class ObjectiveDB(BaseModel):
    quest_id: QuestID
    objective_id: ObjectiveID
    description: Description
    display: Optional[Display]
    order_index: OrderIndex
    objective_type: ObjectiveType
    logic: Logic
    target_count: Optional[TargetCount]
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


class ObjectiveOut(ObjectiveDB):
    objective_id: ObjectiveID
    description: Description
    display: Optional[Display]
    order_index: OrderIndex
    objective_type: ObjectiveType
    logic: Logic
    target_count: Optional[TargetCount]
    targets: ObjectiveTargets
    customizations: ObjectiveCustomizations
    # rewards (out)


class ObjectiveIn(BaseModel):
    description: Description
    display: Optional[Display]
    order_index: OrderIndex
    objective_type: ObjectiveType
    logic: Logic
    target_count: Optional[TargetCount]
    targets: ObjectiveTargets
    customizations: ObjectiveCustomizations
    # rewards (in)

    @model_validator(mode='after')
    def check_targets(self) -> "ObjectiveIn":
        if len(self.targets) == 0:
            raise ValidationError("Objectives must have at least one target")

        for target in self.targets:
            if target.target_type != self.objective_type:
                raise ValidationError(f"All targets must be of the same type. "
                                      f"Offending target: {target.target_type} != {self.objective_type}")

            if target.count < 1:
                raise ValidationError(f"A target's count must be at least 1.")

        return self


class ObjectiveUpdate(BaseModel):
    description: Optional[Description] = None
    display: Optional[Display] = None
    order_index: Optional[OrderIndex] = None
    objective_type: Optional[ObjectiveType] = None
    logic: Optional[Logic] = None
    target_count: Optional[TargetCount] = None
    targets: Optional[ObjectiveTargets] = None
    customizations: Optional[ObjectiveCustomizations] = None
    # rewards (update)
