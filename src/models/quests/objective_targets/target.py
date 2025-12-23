import uuid

from pydantic import Field, StringConstraints, UUID4
from typing import Annotated, Literal, Optional, Union

from src.utils.base import BaseModel, BaseList, optional_model

from sanic_ext import openapi

MinecraftID = Annotated[str, StringConstraints(pattern='^[a-z]+:[a-z_0-9]+$')]


@openapi.component()
class TargetBaseModel(BaseModel):
    target_uuid: UUID4 = Field(description="The target uuid", default_factory=uuid.uuid4)
    target_type: str = Field(description="The type of the target. Must be equal to `objective_type`.",
                             json_schema_extra={"example": "kill"})
    count: int = Field(description="The number of this target to be reached. At least 1.",
                       json_schema_extra={"example": 50})


@openapi.component()
class MineTargetModel(TargetBaseModel):
    target_type: Literal["mine"] = Field(description="The type of the target. Must be equal to `objective_type`.",
                                         json_schema_extra={"example": "mine"})
    block: MinecraftID = Field(description="The block to be mined",
                               json_schema_extra={"example": "minecraft:dirt"})
    count: int = Field(description="The number of blocks to be mined",
                       json_schema_extra={"example": 50})


@openapi.component()
class KillTargetModel(TargetBaseModel):
    target_type: Literal["kill"] = Field(description="The type of the target. Must be equal to `objective_type`.",
                                         json_schema_extra={"example": "kill"})
    entity: MinecraftID = Field(description="The entity to be killed",
                                json_schema_extra={"example": "minecraft:skeleton"})
    count: int = Field(description="The number of entities to be killed",
                       json_schema_extra={"example": 50})


@openapi.component()
class EncounterTargetModel(TargetBaseModel):
    target_type: Literal["encounter"] = Field(description="The type of the target. Must be equal to `objective_type`.",
                                              json_schema_extra={"example": "encounter"})
    script_id: MinecraftID = Field(description="The script_event ID which will trigger the objective",
                                   json_schema_extra={"example": "quest:button_1"})
    count: int = Field(description="The number of ID's before this objective is completed",
                       json_schema_extra={"example": 50})

Targets = Annotated[
    Union[MineTargetModel, KillTargetModel, EncounterTargetModel],
    Field(discriminator="target_type")
]