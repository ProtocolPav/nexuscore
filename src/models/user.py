from datetime import datetime

from pydantic import NaiveDatetime, StringConstraints, BaseModel
from typing_extensions import Annotated, Optional

import json

from sanic_ext import openapi

import sanic

from src.database import Database


@openapi.component
class UserModel(BaseModel):
    thorny_id: int
    user_id: int
    guild_id: int
    username: Optional[str]
    join_date: NaiveDatetime
    birthday: Optional[NaiveDatetime]
    balance: int
    active: bool
    role: str
    patron: bool
    level: int
    xp: int
    required_xp: int
    last_message: NaiveDatetime
    gamertag: Optional[str]
    whitelist: Optional[str]

    @classmethod
    async def fetch(cls, db: Database, thorny_id: int):
        data = await db.pool.fetchrow("""
                                       SELECT * FROM users.user
                                       WHERE thorny_id = $1
                                       """,
                                      thorny_id)

        return cls(**data)

    async def update(self, db: Database):
        await db.pool.execute("""
                               UPDATE users.user
                               SET username = $1,
                                   birthday = $2,
                                   balance = $3,
                                   active = $4,
                                   role = $5,
                                   patron = $6,
                                   level = $7,
                                   xp = $8,
                                   required_xp = $9,
                                   last_message = $10,
                                   gamertag = $11,
                                   whitelist = $12
                               WHERE thorny_id = $13
                               """,
                              self.username, self.birthday, self.balance, self.active,
                              self.role, self.patron, self.level, self.xp, self.required_xp,
                              self.last_message, self.gamertag, self.whitelist, self.thorny_id)


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

    @classmethod
    async def fetch(cls, db: Database, thorny_id: int = None):
        data = await db.pool.fetchrow("""
                                       SELECT * FROM users.profile
                                       WHERE thorny_id = $1
                                       """,
                                      thorny_id)

        return cls(**data)


@openapi.component
class DailyPlaytimeDict(BaseModel):
    day: NaiveDatetime
    playtime: int


@openapi.component
class MonthlyPlaytimeDict(BaseModel):
    month: NaiveDatetime
    playtime: int


@openapi.component
class PlaytimeSummary(BaseModel):
    total: int
    session: datetime
    daily: list[DailyPlaytimeDict]
    monthly: list[MonthlyPlaytimeDict]

    @classmethod
    async def fetch(cls, db: Database, thorny_id: int = None):
        data = await db.pool.fetchrow("""
                WITH daily_playtime AS (
                    SELECT t.day, SUM(t.playtime) AS playtime
                    FROM (
                        SELECT SUM(playtime) AS playtime, 
                               DATE(connect_time) AS day
                        FROM thorny.playtime
                        INNER JOIN thorny.user ON thorny.playtime.thorny_user_id = thorny.user.thorny_user_id 
                        WHERE thorny.playtime.thorny_user_id = $1
                        GROUP BY day
                    ) AS t
                    GROUP BY t.day
                    ORDER BY t.day DESC
                    LIMIT 7
                ),
                total_playtime AS (
                    SELECT SUM(EXTRACT(EPOCH FROM playtime)) AS total_playtime
                    FROM thorny.playtime
                    WHERE thorny_user_id = $1
                    GROUP BY thorny_user_id
                ),
                session AS (
                    SELECT connect_time as session
                    FROM thorny.playtime
                    WHERE thorny_user_id = $1
                    GROUP BY thorny_user_id, connect_time
                    order by connect_time DESC
                    limit 1
                ),
                monthly_playtime AS (
                    SELECT t.year || '-' || t.month || '-' || '01' AS month, SUM(t.playtime) AS playtime
                    FROM (
                        SELECT SUM(playtime) AS playtime, 
                               LPAD(extract(month from connect_time)::text, 2, '0') AS month, 
                               DATE_PART('year', connect_time) AS year
                        FROM thorny.playtime
                        INNER JOIN thorny.user ON thorny.playtime.thorny_user_id = thorny.user.thorny_user_id 
                        WHERE thorny.playtime.thorny_user_id = $1
                        GROUP BY year, month
                    ) AS t
                    GROUP BY t.year, t.month
                    ORDER BY t.year DESC, t.month DESC
                    LIMIT 12
                )
                SELECT 
                    $1 AS thorny_id,
                    (SELECT JSON_AGG(JSON_BUILD_OBJECT('day', wp.day, 'playtime', EXTRACT(EPOCH FROM wp.playtime)))
                        FROM daily_playtime wp) AS daily,
                    (SELECT total_playtime
                        FROM total_playtime) AS total,
                    (SELECT session
                        FROM session) AS session,
                    (SELECT JSON_AGG(JSON_BUILD_OBJECT('month', mp.month, 'playtime', EXTRACT(EPOCH FROM mp.playtime)))
                        FROM monthly_playtime mp) AS monthly;
                                      """,
                                      thorny_id)

        processed_dict = {'thorny_id': thorny_id,
                          'total': data['total'],
                          'daily': json.loads(data['daily']),
                          'monthly': json.loads(data['monthly']),
                          'session': data['session']}

        return cls(**processed_dict)


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
