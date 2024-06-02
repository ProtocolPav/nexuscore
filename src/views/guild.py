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
    async def new(cls, db: Database, guild_id: int):
        quest_view = await QuestView.build(db, quest_id)

        async with db.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("""
                                   INSERT INTO users.quests(quest_id, thorny_id)
                                   VALUES($1, $2)
                                   """,
                                   quest_id, thorny_id)

                for objective in quest_view.objectives:
                    await conn.execute("""
                                       INSERT INTO users.objectives(quest_id, thorny_id, objective_id)
                                       VALUES($1, $2, $3)
                                       """,
                                       quest_id, thorny_id, objective.objective_id)
