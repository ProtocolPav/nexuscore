import uuid

from pydantic import Field, UUID4, BaseModel
from typing import Annotated, Literal, Union


class TargetProgressBaseModel(BaseModel):
    target_uuid: UUID4 = Field(description="The target uuid", default_factory=uuid.uuid4)
    target_type: str = Field(description="The type of the target. Must be equal to `objective_type`.",
                             json_schema_extra={"example": "kill"})
    count: int = Field(description="The number of this target to be reached. At least 1.",
                       default=0,
                       json_schema_extra={"example": 50})


class MineTargetProgressModel(TargetProgressBaseModel):
    target_type: Literal["mine"] = Field(description="The type of the target. Must be equal to `objective_type`.",
                                         json_schema_extra={"example": "mine"})
    count: int = Field(description="The number of blocks mined so far",
                       default=0,
                       json_schema_extra={"example": 50})


class KillTargetProgressModel(TargetProgressBaseModel):
    target_type: Literal["kill"] = Field(description="The type of the target. Must be equal to `objective_type`.",
                                         json_schema_extra={"example": "kill"})
    count: int = Field(description="The number of entities killed so far",
                       default=0,
                       json_schema_extra={"example": 50})


class ScriptEventTargetProgressModel(TargetProgressBaseModel):
    target_type: Literal["scriptevent"] = Field(description="The type of the target. Must be equal to `objective_type`.",
                                                json_schema_extra={"example": "scriptevent"})
    count: int = Field(description="The number of Script ID's logged so far",
                       default=0,
                       json_schema_extra={"example": 50})


class VisitTargetProgressModel(TargetProgressBaseModel):
    target_type: Literal["visit"]
    seconds: int = Field(description="The number of seconds spent in the area so far",
                         default=0,
                         examples=[50])


TargetProgress = Annotated[
    Union[MineTargetProgressModel, KillTargetProgressModel, ScriptEventTargetProgressModel, VisitTargetProgressModel],
    Field(discriminator="target_type")
]


TARGET_TYPE_MAP = {
    "mine": MineTargetProgressModel,
    "kill": KillTargetProgressModel,
    "scriptevent": ScriptEventTargetProgressModel,
    "visit": VisitTargetProgressModel,
}