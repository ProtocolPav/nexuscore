from datetime import datetime
from typing import Literal, Optional

from pydantic import Field, BaseModel
from typing_extensions import Annotated

GuildID = Annotated[int, Field(
    description="The guild ID that corresponds to this world",
    examples=[123456789012345678]
)]
OverworldBorder = Annotated[float, Field(
    description="The Overworld border size",
    examples=[4000]
)]
NetherBorder = Annotated[float, Field(
    description="The Nether border size",
    examples=[1500]
)]
EndBorder = Annotated[float, Field(
    description="The End border size",
    examples=[134.54]
)]


class WorldDB(BaseModel):
    guild_id: GuildID
    overworld_border: OverworldBorder
    nether_border: NetherBorder
    end_border: EndBorder


class WorldOut(WorldDB):
    pass


class WorldUpdate(BaseModel):
    overworld_border: Optional[OverworldBorder] = None
    nether_border: Optional[NetherBorder] = None
    end_border: Optional[EndBorder] = None
