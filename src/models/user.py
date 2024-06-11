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
    username: Optional[str]
    birthday: Optional[date]
    balance: Optional[int]
    active: Optional[bool]
    role: Optional[str]
    patron: Optional[bool]
    level: Optional[int]
    xp: Optional[int]
    required_xp: Optional[int]
    last_message: Optional[datetime]
    gamertag: Optional[str]
    whitelist: Optional[str]


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
    slogan: Optional[ShortString]
    aboutme: Optional[LongString]
    lore: Optional[LongString]
    character_name: Optional[ShortString]
    character_age: Optional[int]
    character_race: Optional[ShortString]
    character_role: Optional[ShortString]
    character_origin: Optional[ShortString]
    character_beliefs: Optional[ShortString]
    agility: Optional[int]
    valor: Optional[int]
    strength: Optional[int]
    charisma: Optional[int]
    creativity: Optional[int]
    ingenuity: Optional[int]


class DailyPlaytime(BaseModel):
    day: date
    playtime: float


class MonthlyPlaytime(BaseModel):
    month: date
    playtime: float


class PlaytimeSummary(BaseModel):
    total: float
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
                        FROM events.sessions_view sv 
                        INNER JOIN users.user ON sv.thorny_id = users.user.thorny_id 
                        WHERE sv.thorny_id = $1
                        GROUP BY day
                    ) AS t
                    GROUP BY t.day
                    ORDER BY t.day DESC
                    LIMIT 7
                ),
                total_playtime AS (
                    SELECT SUM(EXTRACT(EPOCH FROM playtime)) AS total_playtime
                    FROM events.sessions_view sv 
                    WHERE thorny_id = $1
                    GROUP BY thorny_id
                ),
                session AS (
                    SELECT connect_time as session
                    FROM events.sessions_view sv 
                    WHERE thorny_id = $1
                    AND disconnect_time IS NULL
                    GROUP BY thorny_id, connect_time
                    order by connect_time DESC
                    limit 1
                ),
                monthly_playtime AS (
                    SELECT t.month AS month, SUM(t.playtime) AS playtime
                    FROM (
                        SELECT SUM(playtime) AS playtime,
                               date_trunc('month', connect_time)::date as month
                        FROM events.sessions_view sv 
                        INNER JOIN users.user ON sv.thorny_id = users.user.thorny_id 
                        WHERE sv.thorny_id = $1
                        GROUP BY month
                    ) AS t
                    GROUP BY t.month
                    ORDER BY t.month DESC
                    LIMIT 12
                )
                SELECT 
                    $1 AS thorny_id,
                    COALESCE(
                        (
                         SELECT JSON_AGG(JSON_BUILD_OBJECT('day', wp.day,
                                                           'playtime', COALESCE(EXTRACT(EPOCH FROM wp.playtime), 0)))
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
                         SELECT JSON_AGG(JSON_BUILD_OBJECT('month', mp.month,
                                                           'playtime', COALESCE(EXTRACT(EPOCH FROM mp.playtime), 0)))
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


class InteractionStatistic(BaseModel):
    reference: str
    type: str
    count: int


class InteractionSummary(BaseModel):
    blocks_mined: Optional[list[InteractionStatistic]]
    blocks_placed: Optional[list[InteractionStatistic]]
    kills: Optional[list[InteractionStatistic]]
    deaths: Optional[list[InteractionStatistic]]
    uses: Optional[list[InteractionStatistic]]
    totals: dict

    @classmethod
    async def fetch(cls, db: Database, thorny_id: int):
        data = await db.pool.fetchrow("""
                                    with blocks_mined as (
                                        select "type", reference, count(reference) as "count" from events.interactions i 
                                        where i.thorny_id = $1
                                        and i.type = 'mine'
                                        group by type, reference
                                        order by "count" desc
                                    ),
                                    blocks_placed as (
                                        select "type", reference, count(reference) as "count" from events.interactions i 
                                        where i.thorny_id = $1
                                        and i.type = 'place'
                                        group by type, reference
                                        order by "count" desc
                                    ),
                                    kills as (
                                        select "type", reference, count(reference) as "count" from events.interactions i 
                                        where i.thorny_id = $1
                                        and i.type = 'kill'
                                        group by type, reference
                                        order by "count" desc
                                    ),
                                    deaths as (
                                        select "type", reference, count(reference) as "count" from events.interactions i 
                                        where i.thorny_id = $1
                                        and i.type = 'die'
                                        group by type, reference
                                        order by "count" desc
                                    ),
                                    uses as (
                                        select "type", reference, count(reference) as "count" from events.interactions i 
                                        where i.thorny_id = $1
                                        and i.type = 'use'
                                        group by type, reference
                                        order by "count" desc
                                    )
                                    
                                    select 
                                        $1 as thorny_id,
                                        coalesce(
                                            (select json_agg(json_build_object('reference', t.reference,
                                                                               'type', t."type",
                                                                               'count', t."count"))
                                             from blocks_mined as t
                                            ),
                                            '[]'::json
                                        ) as blocks_mined,
                                        coalesce(
                                            (select json_agg(json_build_object('reference', t.reference,
                                                                               'type', t."type",
                                                                               'count', t."count"))
                                             from blocks_placed as t
                                            ),
                                            '[]'::json
                                        ) as blocks_placed,
                                        coalesce(
                                            (select json_agg(json_build_object('reference', t.reference,
                                                                               'type', t."type",
                                                                               'count', t."count"))
                                             from kills as t
                                            ),
                                            '[]'::json
                                        ) as kills,
                                        coalesce(
                                            (select json_agg(json_build_object('reference', t.reference,
                                                                               'type', t."type",
                                                                               'count', t."count"))
                                             from deaths as t
                                            ),
                                            '[]'::json
                                        ) as deaths,
                                        coalesce(
                                            (select json_agg(json_build_object('reference', t.reference,
                                                                               'type', t."type",
                                                                               'count', t."count"))
                                             from uses as t
                                            ),
                                            '[]'::json
                                        ) as uses,
                                        coalesce(
                                            (select json_build_object('mine', m."sum",
                                                                      'place', p."sum",
                                                                      'kill', k."sum",
                                                                      'die', d."sum",
                                                                      'use', u."sum")
                                             from (select sum("count") as "sum" from blocks_mined) as m,
                                                  (select sum("count") as "sum" from blocks_placed) as p,
                                                  (select sum("count") as "sum" from kills) as k,
                                                  (select sum("count") as "sum" from deaths) as d,
                                                  (select sum("count") as "sum" from uses) as u
                                            ),
                                            '[]'::json
                                        ) as totals
                                        """,
                                      thorny_id)

        processed_dict = {'thorny_id': thorny_id,
                          'totals': json.loads(data['totals']),
                          'blocks_mined': json.loads(data['blocks_mined']),
                          'blocks_placed': json.loads(data['blocks_placed']),
                          'kills': json.loads(data['kills']),
                          'deaths': json.loads(data['deaths']),
                          'uses': json.loads(data['uses'])}

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

    @classmethod
    async def get_all_quests(cls, db: Database, thorny_id: int):
        data = await db.pool.fetchrow("""
                                      SELECT ARRAY_AGG(quest_id) AS quests from users.quests
                                      WHERE thorny_id = $1
                                      """,
                                      thorny_id)

        return data['quests'] if data else None

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
    status: Optional[Literal['completed']]


class UserObjectiveModel(BaseModel):
    quest_id: int
    objective_id: int
    start: datetime
    end: Optional[datetime]
    completion: int
    status: Literal['in_progress', 'completed', 'failed']

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
                               SET "start" = $1,
                                   "end" = $2,
                                   "completion" = $3,
                                   "status" = $4
                               WHERE thorny_id = $5
                               AND quest_id = $6
                               AND objective_id = $7
                               """,
                              self.start, self.end, self.completion,
                              self.status, thorny_id, self.quest_id, self.objective_id)


class UserObjectiveUpdateModel(BaseModel):
    start: Optional[datetime]
    end: Optional[datetime]
    completion: Optional[int]
    status: Optional[Literal['completed', 'failed']]


# Define components in the OpenAPI schema
# This can be done via a decorator, but for some reason
# the decorator stops intellisense from working
openapi.component(UserModel)
openapi.component(ProfileModel)
openapi.component(DailyPlaytime)
openapi.component(MonthlyPlaytime)
openapi.component(PlaytimeSummary)
openapi.component(UserQuestModel)
openapi.component(UserObjectiveModel)
openapi.component(InteractionStatistic)
