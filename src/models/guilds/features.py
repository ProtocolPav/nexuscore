from typing import Annotated

from pydantic import Field, BaseModel


FeatureField = Annotated[str, Field(
    description="The feature itself",
    examples=['BASIC', 'PLAYTIME', 'PROFILE']
)]
Configured = Annotated[bool, Field(
    description="Whether the feature is configured or not.",
    examples=[False],
    deprecated=True
)]

class FeatureDB(BaseModel):
    feature: FeatureField
    configured: Configured

class FeatureOut(FeatureDB):
    pass
