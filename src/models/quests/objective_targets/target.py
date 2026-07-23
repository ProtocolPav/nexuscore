import uuid

from pydantic import Field, UUID4, BaseModel
from typing import Annotated, Literal, Union

from src.utils.minecraft_id import MINECRAFT_REGEX_PATTERN


class TargetBaseModel(BaseModel):
    target_uuid: UUID4 = Field(description="The target uuid", default_factory=uuid.uuid4)
    target_type: str = Field(description="The type of the target. Must be equal to `objective_type`.",
                             json_schema_extra={"example": "kill"})
    count: int = Field(description="The number of this target to be reached. At least 1.",
                       json_schema_extra={"example": 50})


class MineTargetModel(TargetBaseModel):
    target_type: Literal["mine"] = Field(description="The type of the target. Must be equal to `objective_type`.",
                                         json_schema_extra={"example": "mine"})
    block: str = Field(description="The block to be mined",
                       json_schema_extra={"example": "minecraft:dirt"},
                       pattern=MINECRAFT_REGEX_PATTERN)
    count: int = Field(description="The number of blocks to be mined",
                       json_schema_extra={"example": 50})


class KillTargetModel(TargetBaseModel):
    target_type: Literal["kill"] = Field(description="The type of the target. Must be equal to `objective_type`.",
                                         json_schema_extra={"example": "kill"})
    entity: str = Field(description="The entity to be killed",
                        json_schema_extra={"example": "minecraft:skeleton"},
                        pattern=MINECRAFT_REGEX_PATTERN)
    count: int = Field(description="The number of entities to be killed",
                       json_schema_extra={"example": 50})


class ScriptEventTargetModel(TargetBaseModel):
    target_type: Literal["scriptevent"] = Field(description="The type of the target. Must be equal to `objective_type`.",
                                                json_schema_extra={"example": "scriptevent"})
    script_id: str = Field(description="The script_event ID which will trigger the objective",
                           json_schema_extra={"example": "quest:button_1"},
                           pattern=MINECRAFT_REGEX_PATTERN)
    count: int = Field(description="The number of ID's before this objective is completed",
                       json_schema_extra={"example": 50})


class VisitTargetModel(TargetBaseModel):
    target_type: Literal["visit"] = Field(description="The type of the target. Must be equal to `objective_type`.",
                                          examples=["visit"])
    coordinates: tuple[int, int, int] = Field(description="The coordinates",
                                              examples=[[500, -5, 54]])
    horizontal_radius: int = Field(description="The horizontal radius to check for (x and z axis)",
                                   examples=[20])
    vertical_radius: int = Field(description="The vertical radius to check for (y axis)",
                                 examples=[4])
    seconds: int = Field(description="The amount of seconds to stay in the area",
                         examples=[540],
                         default=4)

Targets = Annotated[
    Union[MineTargetModel, KillTargetModel, ScriptEventTargetModel, VisitTargetModel],
    Field(discriminator="target_type")
]