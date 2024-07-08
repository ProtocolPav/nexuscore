from pydantic import BaseModel, Field

from typing import Optional

from sanic_ext import openapi

from src.database import Database


@openapi.component()
class Feature(BaseModel):
    feature: str = Field(description="The feature",
                         examples=['BASIC', 'PLAYTIME', 'PROFILE'])
    configured: bool = Field(description="Whether the feature is configured or not. "
                                         "This will always be false, as this is un-used.")


class FeaturesModel(BaseModel):
    features: list[Feature]

    @classmethod
    async def fetch(cls, db: Database, guild_id: int) -> Optional["FeaturesModel"]:
        data = await db.pool.fetch("""
                                   SELECT feature, configured FROM guilds.features
                                   WHERE guild_id = $1
                                   """,
                                   guild_id)

        features_list = []
        for i in data:
            features_list.append(Feature(**i))

        return cls(**{'features': features_list}) if data else None

    @classmethod
    async def add(cls, db: Database, guild_id: int, feature: str):
        await db.pool.execute("""
                              INSERT INTO guilds.features(guild_id, feature)
                              VALUES($1, $2)
                              """,
                              guild_id, feature)

    @classmethod
    async def remove(cls, db: Database, guild_id: int, feature: str):
        await db.pool.execute("""
                              DELETE FROM guilds.features
                              WHERE guild_id = $1 AND feature = $2
                              """,
                              guild_id, feature)

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")
