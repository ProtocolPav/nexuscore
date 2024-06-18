from typing import Optional

from src.database import Database
from src.models.guild import GuildModel, FeatureModel, ChannelModel

from pydantic import BaseModel

from sanic_ext import openapi


class GuildView(BaseModel):
    guild: GuildModel
    features: list[FeatureModel]
    channels: list[ChannelModel]

    @classmethod
    async def build(cls, db: Database, guild_id: int):
        guild = await GuildModel.fetch(db, guild_id)
        channels = await ChannelModel.fetch_all_channels(db, guild_id)
        features = await FeatureModel.fetch_all_features(db, guild_id)

        return cls(guild=guild, features=features, channels=channels)

    @classmethod
    def view_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")

    @classmethod
    async def new(cls, db: Database, guild_id: int, name: str, ):
        await db.pool.execute("""
                                with guild_table as (
                                    insert into guilds.guild(guild_id, name)
                                    values($1, $2)
                                )
                                insert into guilds.features(guild_id, feature)
                                    values ($1, 'profile'),
                                           ($1, 'levels'),
                                           ($1, 'basic')
                               """,
                              guild_id, name)
