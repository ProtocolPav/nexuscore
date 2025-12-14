from pydantic import Field, StringConstraints
from typing import Annotated, Literal, Optional, Union

from src.utils.base import BaseModel, BaseList, optional_model

from sanic_ext import openapi

MinecraftID = Annotated[str, StringConstraints(pattern='^[a-z]+:[a-z_0-9]+$')]


@openapi.component()
class CustomizationBaseModel(BaseModel):
    customization_type: str = Field(description="The customization type",
                                    json_schema_extra={"example": "mainhand"})


@openapi.component()
class MainhandCustomization(CustomizationBaseModel):
    customization_type: Literal["mainhand"] = Field(description="The customization type",
                                                    json_schema_extra={"example": "mainhand"})
    item: MinecraftID = Field(description="The item which is required to be held",
                              json_schema_extra={"example": "minecraft:diamond_sword"})


@openapi.component()
class LocationCustomization(CustomizationBaseModel):
    customization_type: Literal["location"] = Field(description="The customization type",
                                                    json_schema_extra={"example": "location"})
    coordinates: tuple[int, int, int] = Field(description="The coordinates",
                                              json_schema_extra={"example": (200, 70, -43)})
    horizontal_radius: int = Field(description="The horizontal radius to check for (x and z axis)",
                                   json_schema_extra={"example": 20})
    vertical_radius: int = Field(description="The vertical radius to check for (y axis)",
                                 json_schema_extra={"example": 3})


@openapi.component()
class NaturalBlockCustomization(CustomizationBaseModel):
    customization_type: Literal["natural_blocks"] = Field(description="The customization type",
                                                          json_schema_extra={"example": "natural_blocks"})


@openapi.component()
class TimerCustomization(CustomizationBaseModel):
    customization_type: Literal["timer"] = Field(description="The customization type",
                                                 json_schema_extra={"example": "timer"})
    seconds: int = Field(description="The timer's seconds",
                         json_schema_extra={"example": 540})
    fail: bool = Field(description="Fail the quest when the timer ends",
                       json_schema_extra={"example": True})


@openapi.component()
class MaximumDeathsCustomization(CustomizationBaseModel):
    customization_type: Literal["maximum_deaths"] = Field(description="The customization type",
                                                          json_schema_extra={"example": "maximum_deaths"})
    deaths: int = Field(description="The most deaths a player can have before moving to the next objective",
                        json_schema_extra={"example": 3})
    fail: bool = Field(description="Fail the quest when the death count is exceeded",
                       json_schema_extra={"example": True})


Customizations = Union[
    MainhandCustomization,
    LocationCustomization,
    NaturalBlockCustomization,
    TimerCustomization,
    MaximumDeathsCustomization
]