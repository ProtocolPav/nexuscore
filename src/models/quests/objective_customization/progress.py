from pydantic import Field, BaseModel
from typing import Optional


class DeathCustomizationProgress(BaseModel):
    deaths: int = Field(description="The amount of deaths the player has had so far",
                        default=0,
                        json_schema_extra={"example": 3})


class CustomizationProgress(BaseModel):
    maximum_deaths: Optional[DeathCustomizationProgress] = Field(description="Death count tracking", default=None)


CUSTOMIZATION_TYPE_MAP = {
    "maximum_deaths": DeathCustomizationProgress,
}