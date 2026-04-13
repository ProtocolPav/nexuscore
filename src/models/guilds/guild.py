from pydantic import Field, BaseModel
from typing_extensions import Annotated

GuildId = Annotated[int, Field(
    description="The Discord guild ID",
    examples=[631936703190440136]
)]
GuildName = Annotated[str, Field(
    description="The name of the guild",
    examples=["Everthorn"]
)]
CurrencyName = Annotated[str, Field(
    description="The guild's currency name (plural)",
    examples=["Nugs"]
)]
CurrencyEmoji = Annotated[str, Field(
    description="The emoji of the guild's currency",
    examples=["<:Nug:884320353202081833>"]
)]
LevelUpMsg = Annotated[str, Field(
    description="Message sent when a user levels up",
    examples=["Yay! You leveled up!"]
)]
JoinMsg = Annotated[str, Field(
    description="Message sent when a user joins",
    examples=["Welcome to our guild!"]
)]
LeaveMsg = Annotated[str, Field(
    description="Message sent when a user leaves",
    examples=["Bye bye :(("]
)]
XpMultiplier = Annotated[float, Field(
    description="XP multiplier for all guild members",
    examples=[1.3]
)]
GuildActive = Annotated[bool, Field(
    description="Whether Thorny is in this guild",
    examples=[True]
)]

class GuildDB(BaseModel):
    guild_id: GuildId
    name: GuildName
    currency_name: CurrencyName
    currency_emoji: CurrencyEmoji
    level_up_message: LevelUpMsg
    join_message: JoinMsg
    leave_message: LeaveMsg
    xp_multiplier: XpMultiplier
    active: GuildActive

class GuildOut(GuildDB):
    pass

class GuildIn(BaseModel):
    guild_id: GuildId
    name: GuildName

class GuildUpdate(BaseModel):
    name: GuildName = None
    currency_name: CurrencyName = None
    currency_emoji: CurrencyEmoji = None
    level_up_message: LevelUpMsg = None
    join_message: JoinMsg = None
    leave_message: LeaveMsg = None
    xp_multiplier: XpMultiplier = None
    active: GuildActive = None