from sanic_ext import openapi

from typing import Optional

from pydantic import BaseModel, Field

from src.database import Database


@openapi.component()
class Channel(BaseModel):
    channel_type: str = Field(description="The type of channel",
                              examples=['project_forum'])
    channel_id: int = Field(description="The channel ID",
                            examples=[965579894652222618])


class ChannelsModel(BaseModel):
    channels: list[Channel]

    @classmethod
    async def fetch(cls, db: Database, guild_id: int) -> Optional["ChannelsModel"]:
        data = await db.pool.fetch("""
                                   SELECT channel_type, channel_id FROM guilds.channels
                                   WHERE guild_id = $1
                                   """,
                                   guild_id)

        channels_list = []
        for i in data:
            channels_list.append(Channel(**i))

        return cls(**{'channels': channels_list}) if data else None

    @classmethod
    async def add(cls, db: Database, guild_id: int, channel_type: str, channel_id: int):
        await db.pool.execute("""
                              INSERT INTO guilds.channels(guild_id, channel_type, channel_id)
                              VALUES($1, $2, $3)
                              """,
                              guild_id, channel_type, channel_id)

    @classmethod
    async def remove(cls, db: Database, guild_id: int, channel_type: str):
        await db.pool.execute("""
                              DELETE FROM guilds.channels
                              WHERE guild_id = $1
                              AND channel_type = $2
                              """,
                              guild_id, channel_type)

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")
