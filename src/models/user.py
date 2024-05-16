from datetime import datetime

from pydantic import NaiveDatetime, StringConstraints, BaseModel
from typing_extensions import Annotated, Optional, TypedDict

from sanic_ext import openapi


@openapi.component
class UserModel(BaseModel):
    thorny_id: int
    user_id: int
    guild_id: int
    username: str
    join_date: NaiveDatetime
    birthday: NaiveDatetime
    balance: int
    active: bool
    role: str
    patron: bool
    level: int
    xp: int
    required_xp: int
    last_message: NaiveDatetime
    gamertag: str
    whitelist: str


# noinspection PyTypeHints
@openapi.component
class ProfileModel(BaseModel):
    slogan: Annotated[str, StringConstraints(max_length=35)]
    aboutme: Annotated[str, StringConstraints(max_length=300)]
    lore: Annotated[str, StringConstraints(max_length=300)]
    character_name: Annotated[str, StringConstraints(max_length=40)]
    character_age: Optional[int]
    character_race: Annotated[str, StringConstraints(max_length=40)]
    character_role: Annotated[str, StringConstraints(max_length=40)]
    character_origin: Annotated[str, StringConstraints(max_length=40)]
    character_beliefs: Annotated[str, StringConstraints(max_length=40)]
    agility: int
    valor: int
    strength: int
    charisma: int
    creativity: int
    ingenuity: int


@openapi.component
class DailyPlaytimeDict(BaseModel):
    day: NaiveDatetime
    playtime: int


@openapi.component
class MonthlyPlaytimeDict(BaseModel):
    month: NaiveDatetime
    playtime: int


@openapi.component
class PlaytimeReport(BaseModel):
    total: int
    session: datetime
    daily: list[DailyPlaytimeDict]
    monthly: list[MonthlyPlaytimeDict]


@openapi.component
class ServerEventsReport(BaseModel):
    total_placed: int
    total_broken: int
    total_kills: int
    total_player_kills: int


@openapi.component
class UserQuestModel(BaseModel):
    quest_id: int
    accepted_on: NaiveDatetime
    started_on: NaiveDatetime
    completion_count: int
    status: bool | None


class UserUpdateModel(UserModel):
    thorny_id: int = None
    user_id: int = None
    guild_id: int = None
    username: str = None
    join_date: NaiveDatetime = None
    birthday: NaiveDatetime = None
    balance: int = None
    active: bool = None
    role: str = None
    patron: bool = None
    level: int = None
    xp: int = None
    required_xp: int = None
    last_message: NaiveDatetime = None
    gamertag: str = None
    whitelist: str = None


# noinspection PyTypeHints
class ProfileUpdateModel(ProfileModel):
    slogan: Annotated[str, StringConstraints(max_length=35)] = None
    aboutme: Annotated[str, StringConstraints(max_length=300)] = None
    lore: Annotated[str, StringConstraints(max_length=300)] = None
    character_name: Annotated[str, StringConstraints(max_length=40)] = None
    character_age: Optional[int] = None
    character_race: Annotated[str, StringConstraints(max_length=40)] = None
    character_role: Annotated[str, StringConstraints(max_length=40)] = None
    character_origin: Annotated[str, StringConstraints(max_length=40)] = None
    character_beliefs: Annotated[str, StringConstraints(max_length=40)] = None
    agility: int = None
    valor: int = None
    strength: int = None
    charisma: int = None
    creativity: int = None
    ingenuity: int = None
