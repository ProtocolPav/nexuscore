import uuid

from pydantic import Field, StringConstraints, UUID4
from typing import Annotated, Literal, Optional, Union

from src.utils.base import BaseModel, BaseList, optional_model

from sanic_ext import openapi


@openapi.component()
class TargetProgressBaseModel(BaseModel):
    target_uuid: UUID4 = Field(description="The target uuid", default_factory=uuid.uuid4)
    target_type: str = Field(description="The type of the target. Must be equal to `objective_type`.",
                             json_schema_extra={"example": "kill"})
    count: int = Field(description="The number of this target to be reached. At least 1.",
                       default=0,
                       json_schema_extra={"example": 50})


@openapi.component()
class MineTargetProgressModel(TargetProgressBaseModel):
    target_type: Literal["mine"] = Field(description="The type of the target. Must be equal to `objective_type`.",
                                         json_schema_extra={"example": "mine"})
    count: int = Field(description="The number of blocks mined so far",
                       default=0,
                       json_schema_extra={"example": 50})


@openapi.component()
class KillTargetProgressModel(TargetProgressBaseModel):
    target_type: Literal["kill"] = Field(description="The type of the target. Must be equal to `objective_type`.",
                                         json_schema_extra={"example": "kill"})
    count: int = Field(description="The number of entities killed so far",
                       default=0,
                       json_schema_extra={"example": 50})


@openapi.component()
class EncounterTargetProgressModel(TargetProgressBaseModel):
    target_type: Literal["encounter"] = Field(description="The type of the target. Must be equal to `objective_type`.",
                                              json_schema_extra={"example": "encounter"})
    count: int = Field(description="The number of Script ID's logged so far",
                       default=0,
                       json_schema_extra={"example": 50})


TargetProgress = Annotated[
    Union[MineTargetProgressModel, KillTargetProgressModel, EncounterTargetProgressModel],
    Field(discriminator="target_type")
]


TARGET_TYPE_MAP = {
    "mine": MineTargetProgressModel,
    "kill": KillTargetProgressModel,
    "encounter": EncounterTargetProgressModel
}