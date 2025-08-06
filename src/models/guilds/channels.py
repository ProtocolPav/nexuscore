from sanic_ext import openapi
from pydantic import Field
from src.database import Database

from src.utils.base import BaseModel, BaseList, optional_model
from src.utils.errors import BadRequest400, NotFound404


@openapi.component()
class Channel(BaseModel):
    channel_type: str = Field(description="The type of channel",
                              examples=['project_forum'])
    channel_id: int = Field(description="The channel ID",
                            examples=[965579894652222618])


class ChannelsListModel(BaseList[Channel]):
    @classmethod
    async def fetch(cls, db: Database, guild_id: int = None, *args) -> "ChannelsListModel":
        data = await db.pool.fetch("""
                                   SELECT channel_type, channel_id FROM guilds.channels
                                   WHERE guild_id = $1
                                   """,
                                   guild_id)

        channels: list[Channel] = []
        for channel in data:
            channels.append(Channel(**channel))

        return cls(root=channels)
