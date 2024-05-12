from src.models.base import Base
from pydantic import NaiveDatetime, StringConstraints
from typing import Annotated


class UserModel(Base):
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
class ProfileModel(Base):
    thorny_id: int
    slogan: Annotated[str, StringConstraints(max_length=35)]
    aboutme: Annotated[str, StringConstraints(max_length=300)]
    lore: Annotated[str, StringConstraints(max_length=300)]
    character_name: Annotated[str, StringConstraints(max_length=40)]
    character_age: int | None
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


class PlaytimeReport(Base):
    ...


class UserObject(UserModel):
    profile: ProfileModel
