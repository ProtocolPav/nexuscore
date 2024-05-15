from datetime import datetime

from pydantic import NaiveDatetime, StringConstraints, BaseModel
from typing import Annotated, Optional


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


class PlaytimeReport(BaseModel):
    total: int
    session: datetime
    daily: list[dict]
    monthly: list[dict]


class ServerEventsReport(BaseModel):
    total_placed: int
    total_broken: int
    total_kills: int
    total_player_kills: int
