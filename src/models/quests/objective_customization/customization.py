from pydantic import Field, BaseModel
from typing import Optional

from src.utils.minecraft_id import MINECRAFT_REGEX_PATTERN


class MainhandCustomization(BaseModel):
    item: str = Field(description="The item which is required to be held",
                      json_schema_extra={"example": "minecraft:diamond_sword"},
                      pattern=MINECRAFT_REGEX_PATTERN)


class LocationCustomization(BaseModel):
    coordinates: tuple[int, int, int] = Field(description="The coordinates",
                                              json_schema_extra={"example": (200, 70, -43)})
    horizontal_radius: int = Field(description="The horizontal radius to check for (x and z axis)",
                                   json_schema_extra={"example": 20})
    vertical_radius: int = Field(description="The vertical radius to check for (y axis)",
                                 json_schema_extra={"example": 3})


class TimerCustomization(BaseModel):
    seconds: int = Field(description="The timer's seconds",
                         json_schema_extra={"example": 540})
    fail: bool = Field(description="Fail the quest when the timer ends",
                       json_schema_extra={"example": True})


class MaximumDeathsCustomization(BaseModel):
    deaths: int = Field(description="The most deaths a player can have before moving to the next objective",
                        json_schema_extra={"example": 3})
    fail: bool = Field(description="Fail the quest when the death count is exceeded",
                       json_schema_extra={"example": True})

class NaturalBlockCustomization(BaseModel):
    pass


class Customizations(BaseModel):
    mainhand: Optional[MainhandCustomization] = Field(description="Mainhand Customization", default=None)
    location: Optional[LocationCustomization] = Field(description="Location Customization", default=None)
    timer: Optional[TimerCustomization] = Field(description="Timer Customization", default=None)
    maximum_deaths: Optional[MaximumDeathsCustomization] = Field(description="Maximum Deaths Customization", default=None)
    natural_block: Optional[NaturalBlockCustomization] = Field(description="Natural Block Customization", default=None)