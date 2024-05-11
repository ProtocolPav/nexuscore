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

    @classmethod
    def build(cls, profile_data: asyncpg.Record):
        return cls(slogan=profile_data['slogan'],
                   gamertag=profile_data['gamertag'],
                   whitelisted_gamertag=profile_data['whitelisted_gamertag'],
                   about=profile_data['aboutme'],
                   character=ProfileCharacter(lore=profile_data['lore'],
                                              name=profile_data['character_name'],
                                              age=profile_data['character_age'],
                                              race=profile_data['character_race'],
                                              role=profile_data['character_role'],
                                              origin=profile_data['character_origin'],
                                              beliefs=profile_data['character_beliefs'],
                                              agility=profile_data['agility'],
                                              valor=profile_data['valor'],
                                              strength=profile_data['strength'],
                                              charisma=profile_data['charisma'],
                                              creativity=profile_data['creativity'],
                                              ingenuity=profile_data['ingenuity']))


@dataclass
class Levels:
    level: int
    xp: int
    required_xp: int
    last_message: datetime

    @classmethod
    def build(cls, levels_data: asyncpg.Record):
        return cls(levels_data['level'],
                   levels_data['xp'],
                   levels_data['required_xp'],
                   levels_data['last_message'])


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
    patron: bool
    role: str
    profile: Profile | None
    levels: Levels | None
    playtime: Playtime | None
    projects: list[Project] | None

    @classmethod
    def build(cls, user_data: asyncpg.Record, profile_data: asyncpg.Record = None,
              levels_data: asyncpg.Record = None, playtime_data: asyncpg.Record = None,
              project_data: asyncpg.Record = None):

        return cls(thorny_id=user_data['thorny_user_id'],
                   discord_id=user_data['user_id'],
                   guild_id=user_data['guild_id'],
                   username=user_data['username'],
                   guild_join_date=user_data['join_date'],
                   birthday=user_data['birthday'],
                   balance=user_data['balance'],
                   is_in_guild=user_data['active'],
                   patron=user_data['patron'],
                   role=user_data['role'],
                   profile=Profile.build(profile_data) if profile_data else None,
                   levels=Levels.build(levels_data) if levels_data else None,
                   playtime=None,
                   projects=[Project.build(x) for x in project_data] if len(project_data) > 0 else None)

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


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

