from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict
from src.schema.project_schema import Project


@dataclass
class ProfileCharacter:
    lore: str
    name: str
    age: int
    race: str
    role: str
    origin: str
    beliefs: str
    agility: int
    valor: int
    strength: int
    charisma: int
    creativity: int
    ingenuity: int


@dataclass
class Profile:
    slogan: str
    gamertag: str
    whitelisted_gamertag: str
    about: str
    character: ProfileCharacter


@dataclass
class Levels:
    level: int
    xp: int
    required_xp: int
    last_message: datetime


class MonthPlaytime(TypedDict):
    year: int
    month: int
    playtime: int


class DayPlaytime(TypedDict):
    day: datetime
    playtime: int


@dataclass
class Playtime:
    monthly: list[MonthPlaytime] | list[None]
    daily: list[DayPlaytime] | list[None]
    total: int
    current_connection: datetime | None


@dataclass
class BaseUser:
    thorny_id: int
    discord_id: int
    guild_id: int
    username: str
    guild_join_date: datetime
    birthday: datetime
    balance: int
    is_in_guild: bool
    profile: None
    levels: None
    playtime: None
    projects: None


@dataclass
class User(BaseUser):
    profile: Profile
    levels: Levels
    playtime: Playtime
    projects: list[Project]
