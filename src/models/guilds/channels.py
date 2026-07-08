from typing import Annotated

from pydantic import Field, BaseModel

ChannelType = Annotated[str, Field(
    description="The type of channel",
    examples=['project_forum']
)]
ChannelId = Annotated[int, Field(
    description="The channel ID",
    examples=[965579894652222618]
)]

class ChannelDB(BaseModel):
    channel_type: ChannelType
    channel_id: ChannelId

class ChannelOut(ChannelDB):
    pass
