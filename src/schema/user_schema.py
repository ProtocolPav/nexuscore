from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict

import asyncpg

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
class User:
    thorny_id: int
    discord_id: int
    guild_id: int
    username: str
    guild_join_date: datetime
    birthday: datetime
    balance: int
    is_in_guild: bool
    profile: Profile | None
    levels: Levels | None
    playtime: Playtime | None
    projects: list[Project] | None

    @classmethod
    def build(cls, user_data: asyncpg.Record, profile_data: asyncpg.Record = None,
              levels_data: asyncpg.Record = None, playtime_data: asyncpg.Record = None,
              project_data: asyncpg.Record = None):
        if profile_data:
            profile_return = ...
        else:
            profile_return = None

        return cls(thorny_id=user_data['thorny_user_id'],
                   discord_id=user_data['user_id'],
                   guild_id=user_data['guild_id'],
                   username=user_data['username'],
                   guild_join_date=user_data['join_date'],
                   birthday=user_data['birthday'],
                   balance=user_data['balance'],
                   is_in_guild=user_data['active'],
                   profile=profile_return,
                   levels=None,
                   playtime=None,
                   projects=None)


@dataclass
class BaseUser(User):
    """
    Used mainly for typing. The BaseUser class can create
    Users with profile, levels and playtime.

    BaseUser and User are essentially identical.
    """
    profile: None
    levels: None
    playtime: None
    projects: None

