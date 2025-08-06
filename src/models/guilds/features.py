from pydantic import Field
from sanic_ext import openapi
from src.database import Database

from src.utils.base import BaseModel, BaseList, optional_model
from src.utils.errors import BadRequest400, NotFound404


@openapi.component()
class Feature(BaseModel):
    feature: str = Field(description="The feature itself",
                         examples=['BASIC', 'PLAYTIME', 'PROFILE'])
    configured: bool = Field(description="Whether the feature is configured or not. "
                                         "This will always be false, as this is un-used.")

class FeaturesListModel(BaseList[Feature]):
    @classmethod
    async def fetch(cls, db: Database, guild_id: int = None, *args) -> "FeaturesListModel":
        data = await db.pool.fetch("""
                                   SELECT feature, configured FROM guilds.features
                                   WHERE guild_id = $1
                                   """,
                                   guild_id)

        features: list[Feature] = []
        for feature in data:
            features.append(Feature(**feature))

        return cls(root=features)
