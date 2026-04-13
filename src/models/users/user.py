from datetime import datetime, date

from pydantic import Field, BaseModel
from typing_extensions import Annotated, Optional

from src.models.users.profile import ProfileOut

ThornyID = Annotated[int, Field(
    description="The ThornyID of a user. This is a unique number",
    examples=[34]
)]
UserID = Annotated[int, Field(
    description="The Discord user ID.",
    examples=[123456789012345678]
)]
GuildID = Annotated[int, Field(
    description="The Discord guild ID this user is registered in.",
    examples=[123456789012345678]
)]
JoinDate = Annotated[date, Field(
    description="The date the ThornyID was created. Usually when a user joins the guild",
    examples=['2024-03-03']
)]
Username = Annotated[str, Field(
    description="The discord username this user has. Same format as discord usernames",
    examples=["protocolpav"]
)]
Birthday = Annotated[date, Field(
    description="The user's birthday. This is optional.",
    examples=["2005-03-03"]
)]
Balance = Annotated[int, Field(
    description="The user's balance on the guild.",
    examples=[2]
)]
Active = Annotated[bool, Field(
    description="If the user is in the guild or not.",
    examples=[True]
)]
Role = Annotated[str, Field(
    description="The role of the user",
)]
Patron = Annotated[bool, Field(
    description="Whether the user is a patron or not",
    examples=[True]
)]
Level = Annotated[int, Field(
    description="The user's level",
    examples=[32]
)]
Xp = Annotated[int, Field(
    description="The user's xp",
    examples=[1023]
)]
RequiredXp = Annotated[int, Field(
    description="The xp required to reach the next level",
    examples=[3044]
)]
LastMessage = Annotated[datetime, Field(
    description="The last time the user gained XP",
    examples=['2024-03-03 04:00:00+00:00']
)]
Gamertag = Annotated[str, Field(
    description="The user's gamertag",
    examples=["ProtocolPav"]
)]
Whitelist = Annotated[str, Field(
    description="The gamertag that this user is whitelisted under",
    examples=["ProtocolPav"]
)]
Xuid = Annotated[str, Field(
    description="The user's XUID, determined from Geode",
    examples=['1234567890']
)]
Location = Annotated[tuple[int, int, int], Field(
    description="The last in-game location of the user",
    examples=[(544, 18, -432)]
)]
Dimension = Annotated[str, Field(
    description="The last in-game dimension the user was in",
    examples=['minecraft:overworld']
)]
Hidden = Annotated[bool, Field(
    description="Whether the user should be hidden on the Live Map",
    examples=[True]
)]

class UserDB(BaseModel):
    thorny_id: ThornyID
    user_id: UserID
    guild_id: GuildID
    join_date: JoinDate
    username: Optional[Username]
    birthday: Optional[Birthday]
    balance: Balance
    active: Active
    role: Optional[Role]
    patron: Patron
    level: Level
    xp: Xp
    required_xp: RequiredXp
    last_message: Optional[LastMessage]
    gamertag: Optional[Gamertag]
    whitelist: Optional[Whitelist]
    xuid: Optional[Xuid]
    location: Optional[Location]
    dimension: Optional[Dimension]
    hidden: Hidden

class UserOut(UserDB):
    profile: ProfileOut

class UserIn(BaseModel):
    user_id: UserID
    username: Optional[Username]

class UserUpdate(BaseModel):
    username: Optional[Username] = None
    birthday: Optional[Birthday] = None
    balance: Optional[Balance] = None
    active: Optional[Active] = None
    role: Optional[Role] = None
    patron: Optional[Patron] = None
    level: Optional[Level] = None
    xp: Optional[Xp] = None
    required_xp: Optional[RequiredXp] = None
    last_message: Optional[LastMessage] = None
    gamertag: Optional[Gamertag] = None
    whitelist: Optional[Whitelist] = None
    location: Optional[Location] = None
    dimension: Optional[Dimension] = None
    hidden: Optional[Hidden] = None
    xuid: Optional[Xuid] = None