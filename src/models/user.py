from datetime import datetime, date
from typing import Literal

from pydantic import StringConstraints, BaseModel
from typing_extensions import Annotated, Optional

import json

from sanic_ext import openapi

from src.database import Database


class UserModel(BaseModel):
    thorny_id: int
    user_id: int
    guild_id: int
    username: Optional[str]
    join_date: date
    birthday: Optional[date]
    balance: int
    active: bool
    role: str
    patron: bool
    level: int
    xp: int
    required_xp: int
    last_message: datetime
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


class UserUpdateModel(BaseModel):
    username: Optional[str] = None
    birthday: Optional[date] = None
    balance: int = None
    active: bool = None
    role: str = None
    patron: bool = None
    level: int = None
    xp: int = None
    required_xp: int = None
    last_message: datetime = None
    gamertag: Optional[str] = None
    whitelist: Optional[str] = None


ShortString = Annotated[str, StringConstraints(max_length=35)]
LongString = Annotated[str, StringConstraints(max_length=300)]


class ProfileModel(BaseModel):
    slogan: ShortString
    aboutme: LongString
    lore: LongString
    character_name: ShortString
    character_age: Optional[int]
    character_race: ShortString
    character_role: ShortString
    character_origin: ShortString
    character_beliefs: ShortString
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

    async def update(self, db: Database, thorny_id: int):
        await db.pool.execute("""
                               UPDATE users.profile
                               SET slogan = $1,
                                   aboutme = $2,
                                   lore = $3,
                                   character_name = $4,
                                   character_age = $5,
                                   character_race = $6,
                                   character_role = $7,
                                   character_origin = $8,
                                   character_beliefs = $9,
                                   agility = $10,
                                   valor = $11,
                                   strength = $12,
                                   charisma = $13,
                                   creativity = $14,
                                   ingenuity = $15
                               WHERE thorny_id = $16
                               """,
                              self.slogan, self.aboutme, self.lore, self.character_name,
                              self.character_age, self.character_race, self.character_role, self.character_origin,
                              self.character_beliefs, self.agility, self.valor, self.strength, self.charisma,
                              self.creativity, self.ingenuity, thorny_id)


class ProfileUpdateModel(BaseModel):
    slogan: ShortString = None
    aboutme: LongString = None
    lore: LongString = None
    character_name: ShortString = None
    character_age: Optional[int] = None
    character_race: ShortString = None
    character_role: ShortString = None
    character_origin: ShortString = None
    character_beliefs: ShortString = None
    agility: int = None
    valor: int = None
    strength: int = None
    charisma: int = None
    creativity: int = None
    ingenuity: int = None


class DailyPlaytime(BaseModel):
    day: date
    playtime: int


class MonthlyPlaytime(BaseModel):
    month: date
    playtime: int


class PlaytimeSummary(BaseModel):
    total: int
    session: Optional[datetime]
    daily: list[DailyPlaytime]
    monthly: list[MonthlyPlaytime]

    @classmethod
    async def fetch(cls, db: Database, thorny_id: int):
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
                    COALESCE(
                        (
                         SELECT JSON_AGG(JSON_BUILD_OBJECT('day', wp.day, 'playtime', EXTRACT(EPOCH FROM wp.playtime)))
                         FROM daily_playtime wp
                         ),
                         '[]'::json
                    ) AS daily,
                    COALESCE(
                        (
                         SELECT total_playtime
                         FROM total_playtime
                         ),
                         0
                    ) AS total,
                    (SELECT session
                        FROM session) AS session,
                    COALESCE(
                        (
                         SELECT JSON_AGG(JSON_BUILD_OBJECT('month', mp.month, 'playtime', EXTRACT(EPOCH FROM mp.playtime)))
                         FROM monthly_playtime mp
                         ),
                         '[]'::json
                    ) AS monthly;
                                      """,
                                      thorny_id)

        processed_dict = {'thorny_id': thorny_id,
                          'total': data['total'],
                          'daily': json.loads(data['daily']),
                          'monthly': json.loads(data['monthly']),
                          'session': data['session']}

        return cls(**processed_dict)


class UserQuestModel(BaseModel):
    quest_id: int
    accepted_on: datetime
    started_on: Optional[datetime]
    objectives_completed: int
    status: Literal['in_progress', 'completed', 'failed']

    @classmethod
    async def fetch(cls, db: Database, thorny_id: int, quest_id: int):
        data = await db.pool.fetchrow("""
                                      SELECT * from users.quests
                                      WHERE thorny_id = $1 AND quest_id = $2
                                      """,
                                      thorny_id, quest_id)

        return cls(**data)

    @classmethod
    async def get_active_quest(cls, db: Database, thorny_id: int):
        data = await db.pool.fetchrow("""
                                      SELECT quest_id from users.quests
                                      WHERE thorny_id = $1
                                      AND status = 'in_progress'
                                      """,
                                      thorny_id)

        return data['quest_id'] if data else None

    async def update(self, db: Database, thorny_id: int):
        await db.pool.execute("""
                               UPDATE users.quests
                               SET accepted_on = $1,
                                   started_on = $2,
                                   objectives_completed = $3,
                                   status = $4
                               WHERE thorny_id = $5
                               AND quest_id = $6
                               """,
                              self.accepted_on, self.started_on, self.objectives_completed,
                              self.status, thorny_id, self.quest_id)


class UserQuestUpdateModel(BaseModel):
    accepted_on: Optional[datetime]
    started_on: Optional[datetime]
    objectives_completed: Optional[int]
    status: Optional[Literal['in_progress', 'completed', 'failed']]


class UserObjectiveModel(BaseModel):
    quest_id: int
    objective_id: int
    start: datetime
    end: Optional[datetime]
    completion: int
    status: str

    @classmethod
    async def fetch(cls, db: Database, thorny_id: int, quest_id: int, objective_id: int):
        data = await db.pool.fetchrow("""
                                      SELECT * from users.objectives
                                      WHERE thorny_id = $1
                                      AND quest_id = $2
                                      AND objective_id = $3
                                      """,
                                      thorny_id, quest_id, objective_id)

        return cls(**data)

    @classmethod
    async def get_all_objectives(cls, db: Database, thorny_id: int, quest_id: int):
        data = await db.pool.fetchrow("""
                                      SELECT COALESCE(ARRAY_AGG(objective_id), ARRAY[]::INTEGER[]) AS ids
                                      FROM users.objectives
                                      WHERE thorny_id = $1
                                      AND quest_id = $2
                                      """,
                                      thorny_id, quest_id)

        return data['ids']

    async def update(self, db: Database, thorny_id: int):
        await db.pool.execute("""
                               UPDATE users.objectives
                               SET start = $1,
                                   end = $2,
                                   completion = $3,
                                   status = $4
                               WHERE thorny_id = $5
                               AND quest_id = $6
                               AND objective_id = $7
                               """,
                              self.accepted_on, self.started_on, self.objectives_completed,
                              self.status, thorny_id, self.quest_id, self.objective_id)


class UserObjectiveUpdateModel(BaseModel):
    start: Optional[datetime]
    end: Optional[datetime]
    completion: Optional[int]
    status: Optional[str]


# Define components in the OpenAPI schema
# This can be done via a decorator, but for some reason
# the decorator stops intellisense from working
openapi.component(UserModel)
openapi.component(ProfileModel)
openapi.component(DailyPlaytime)
openapi.component(MonthlyPlaytime)
openapi.component(PlaytimeSummary)
