import json
from datetime import datetime, date

from pydantic import BaseModel, Field, schema

from sanic_ext import openapi

from src.database import Database


@openapi.component()
class LeaderboardEntry(BaseModel):
    value: float | int = Field(description="The value of the leaderboard, if it's playtime then it is seconds, etc.")
    thorny_id: int
    discord_id: int

    @classmethod
    async def fetch_playtime(cls, db: Database, month_start: date, guild_id: int) -> list["LeaderboardEntry"]:
        month_end = datetime(year=month_start.year, month=month_start.month + 1, day=1)
        data = await db.pool.fetchrow("""
                    with t as (
                    select extract(epoch from sum(playtime)) as playtime, sv.thorny_id, u.user_id from events.sessions_view sv 
                    inner join users."user" u 
                    on u.thorny_id = sv.thorny_id 
                    where sv.connect_time between $1 and $2
                    and u.guild_id = $3
                    group by sv.thorny_id, u.user_id
                    order by playtime desc
                    )

                    select coalesce(
                        (
                        select json_agg(json_build_object('value', t.playtime,
                                                          'thorny_id', t.thorny_id,
                                                          'discord_id', t.user_id))
                        from t
                        ),
                        '[]'::json
                    ) as leaderboard
                    """, month_start, month_end, guild_id)

        leaderboard = []
        for entry in json.loads(data['leaderboard']):
            leaderboard.append(cls(**entry))

        return leaderboard

    @classmethod
    async def fetch_currency(cls, db: Database, guild_id: int) -> list["LeaderboardEntry"]:
        data = await db.pool.fetchrow("""
                                        with t as (
                                            select thorny_id, user_id, balance
                                            from users."user"
                                            where guild_id = $1
                                            order by balance desc
                                        )

                                        select coalesce(
                                            (
                                            select
                                            json_agg(json_build_object('thorny_id', t.thorny_id,
                                                                       'discord_id', t.user_id,
                                                                       'value', t.balance))
                                            from t
                                            ),
                                            '[]'::json
                                        ) as leaderboard
                                      """,
                                      guild_id)

        leaderboard = []
        for entry in json.loads(data['leaderboard']):
            leaderboard.append(cls(**entry))

        return leaderboard

    @classmethod
    async def fetch_levels(cls, db: Database, guild_id: int) -> list["LeaderboardEntry"]:
        data = await db.pool.fetchrow("""
                                        with t as (
                                            select thorny_id, user_id, level
                                            from users."user"
                                            where guild_id = $1
                                            order by level desc
                                        )

                                        select coalesce(
                                            (
                                            select
                                            json_agg(json_build_object('thorny_id', t.thorny_id,
                                                                       'discord_id', t.user_id,
                                                                       'value', t.level))
                                            from t
                                            ),
                                            '[]'::json
                                        ) as leaderboard
                                      """,
                                      guild_id)

        leaderboard = []
        for entry in json.loads(data['leaderboard']):
            leaderboard.append(cls(**entry))

        return leaderboard

    @classmethod
    async def fetch_quests(cls, db: Database, guild_id: int) -> list["LeaderboardEntry"]:
        data = await db.pool.fetchrow("""
                                        with t as (
                                            select u.thorny_id, u.user_id, count(q.status) as quests
                                            from users."user" u
                                            inner join users.quests q on q.thorny_id = u.thorny_id
                                            where u.guild_id = $1
                                            and q.status = 'completed'
                                            group by u.thorny_id
                                            order by quests desc
                                        )

                                        select coalesce(
                                            (
                                            select
                                            json_agg(json_build_object('thorny_id', t.thorny_id,
                                                                       'discord_id', t.user_id,
                                                                       'value', t.quests))
                                            from t
                                            ),
                                            '[]'::json
                                        ) as leaderboard
                                      """,
                                      guild_id)

        leaderboard = []
        for entry in json.loads(data['leaderboard']):
            leaderboard.append(cls(**entry))

        return leaderboard

    @classmethod
    def doc_schema(cls):
        return schema.schema(list[cls.model_json_schema(ref_template="#/components/schemas/{model}")])