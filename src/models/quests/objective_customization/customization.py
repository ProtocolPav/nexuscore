from pydantic import Field, StringConstraints
from typing import Annotated, Literal, Optional, Union

from src.utils.base import BaseModel

from sanic_ext import openapi

MinecraftID = Annotated[str, StringConstraints(pattern='^[a-z]+:[a-z_0-9]+$')]


@openapi.component()
class MainhandCustomization(BaseModel):
    item: MinecraftID = Field(description="The item which is required to be held",
                              json_schema_extra={"example": "minecraft:diamond_sword"})


@openapi.component()
class LocationCustomization(BaseModel):
    coordinates: tuple[int, int, int] = Field(description="The coordinates",
                                              json_schema_extra={"example": (200, 70, -43)})
    horizontal_radius: int = Field(description="The horizontal radius to check for (x and z axis)",
                                   json_schema_extra={"example": 20})
    vertical_radius: int = Field(description="The vertical radius to check for (y axis)",
                                 json_schema_extra={"example": 3})


@openapi.component()
class TimerCustomization(BaseModel):
    seconds: int = Field(description="The timer's seconds",
                         json_schema_extra={"example": 540})
    fail: bool = Field(description="Fail the quest when the timer ends",
                       json_schema_extra={"example": True})


@openapi.component()
class MaximumDeathsCustomization(BaseModel):
    deaths: int = Field(description="The most deaths a player can have before moving to the next objective",
                        json_schema_extra={"example": 3})
    fail: bool = Field(description="Fail the quest when the death count is exceeded",
                       json_schema_extra={"example": True})


@openapi.component()
class Customizations(BaseModel):
    mainhand: Optional[MainhandCustomization] = Field(description="Mainhand Customization", default=None)
    location: Optional[LocationCustomization] = Field(description="Location Customization", default=None)
    timer: Optional[TimerCustomization] = Field(description="Timer Customization", default=None)
    maximum_deaths: Optional[MaximumDeathsCustomization] = Field(description="Maximum Deaths Customization", default=None)