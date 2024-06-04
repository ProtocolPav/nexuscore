import json
from datetime import datetime, date

from pydantic import BaseModel

from sanic_ext import openapi

from src.database import Database


class GuildModel(BaseModel):
    guild_id: int
    name: str
    currency_name: str
    currency_emoji: str
    level_up_message: str
    join_message: str
    leave_message: str
    xp_multiplier: float
    active: bool

    @classmethod
    async def fetch(cls, db: Database, guild_id: int):
        data = await db.pool.fetchrow("""
                                      SELECT * FROM guilds.guild
                                      WHERE guild_id = $1
                                      """,
                                      guild_id)

        return cls(**data)


class FeatureModel(BaseModel):
    feature: str
    configured: bool

    @classmethod
    async def fetch_all_features(cls, db: Database, guild_id: int):
        data = await db.pool.fetch("""
                                   SELECT feature, configured FROM guilds.features
                                   WHERE guild_id = $1
                                   """,
                                   guild_id)

        features = []
        for i in data:
            features.append(cls(**i))

        return features


class ChannelModel(BaseModel):
    channel_type: str
    channel_id: int

    @classmethod
    async def fetch_all_channels(cls, db: Database, guild_id: int):
        data = await db.pool.fetch("""
                                   SELECT channel_type, channel_id FROM guilds.channels
                                   WHERE guild_id = $1
                                   """,
                                   guild_id)

        channels = []
        for i in data:
            channels.append(cls(**i))

        return channels


class DailyPlaytime(BaseModel):
    day: date
    total: float
    unique_players: int
    total_sessions: int
    average_playtime_per_session: float


class WeeklyPlaytime(BaseModel):
    week: int
    total: float
    unique_players: int
    total_sessions: int
    average_playtime_per_session: float


class MonthlyPlaytime(BaseModel):
    month: date
    total: float
    unique_players: int


class GuildPlaytimeAnalysis(BaseModel):
    total_playtime: float
    total_unique_players: int
    daily_playtime: list[DailyPlaytime]
    weekly_playtime: list[WeeklyPlaytime]
    monthly_playtime: list[MonthlyPlaytime]
    peak_playtime_periods: None = None
    peak_active_periods: None = None
    daily_playtime_distribution: None = None
    anomalies: None = None
    predictive_insights: None = None

    @classmethod
    async def fetch(cls, db: Database, guild_id: int):
        data = await db.pool.fetchrow("""
                    with totals as (
                        select 
                            sum(sv.playtime) as total_playtime,
                            count(distinct sv.thorny_id) as total_unique_players
                        from 
                            events.sessions_view sv 
                        inner join
                            users."user"
                        on
                            users."user".thorny_id = sv.thorny_id
                        where
                            users."user".guild_id = $1
                            and sv.connect_time >= '2022-07-29'
                    ),
                    daily_playtime as (
                        select 
                            date(sv.connect_time) as day,
                            sum(sv.playtime) as total,
                            count(distinct sv.thorny_id) as unique_players,
                            count(*) as total_sessions,
                            avg(sv.playtime) as avg_playtime
                        from
                            events.sessions_view sv
                        inner join
                            users."user"
                        on
                            users."user".thorny_id = sv.thorny_id
                        where
                            users."user".guild_id = $1
                        group by day
                        order by day desc
                        limit 7
                    ),
                    weekly_playtime as (
                        select 
                            extract(week from sv.connect_time) as week,
                            sum(sv.playtime) as total,
                            count(distinct sv.thorny_id) as unique_players,
                            count(*) as total_sessions,
                            avg(sv.playtime) as avg_playtime
                        from
                            events.sessions_view sv
                        inner join
                            users."user"
                        on
                            users."user".thorny_id = sv.thorny_id
                        where
                            users."user".guild_id = $1
                        group by week
                        order by week desc 
                        limit 8
                    ),
                    monthly_playtime as (
                        select 
                            date_trunc('month', sv.connect_time)::date as month,
                            sum(sv.playtime) as total,
                            count(distinct sv.thorny_id) as unique_players
                        from
                            events.sessions_view sv
                        inner join
                            users."user"
                        on
                            users."user".thorny_id = sv.thorny_id
                        where
                            users."user".guild_id = $1
                        group by month
                        order by month desc 
                        limit 12
                    )
                    
                    select 
                        $1 as guild_id,
                        coalesce(
                            (
                             select extract(epoch from total_playtime) from totals
                            ), 0) as total_playtime,
                        coalesce(
                            (
                             select total_unique_players from totals
                            ), 0) as total_unique_players,
                        coalesce(
                            (
                            select json_agg(json_build_object('week', w.week,
                                                              'total', extract(epoch from w.total),
                                                              'unique_players', w.unique_players,
                                                              'total_sessions', w.total_sessions,
                                                              'average_playtime_per_session', extract(epoch from w.avg_playtime)))
                            from weekly_playtime w
                            ),
                            '[]'::json) as weekly_playtime,
                            coalesce(
                            (
                            select json_agg(json_build_object('day', d.day,
                                                              'total', extract(epoch from d.total),
                                                              'unique_players', d.unique_players,
                                                              'total_sessions', d.total_sessions,
                                                              'average_playtime_per_session', extract(epoch from d.avg_playtime)))
                            from daily_playtime d
                            ),
                            '[]'::json) as daily_playtime,
                            coalesce(
                            (
                            select json_agg(json_build_object('month', m.month,
                                                              'total', extract(epoch from m.total),
                                                              'unique_players', m.unique_players))
                            from monthly_playtime m
                            ),
                            '[]'::json) as monthly_playtime
                            """, guild_id)

        processed_dict = {'total_playtime': data['total_playtime'],
                          'total_unique_players': data['total_unique_players'],
                          'daily_playtime': json.loads(data['daily_playtime']),
                          'weekly_playtime': json.loads(data['weekly_playtime']),
                          'monthly_playtime': json.loads(data['monthly_playtime'])
                          }

        return cls(**processed_dict)

    @classmethod
    def view_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


class LeaderboardEntry(BaseModel):
    value: float | int | str
    thorny_id: int
    discord_id: int


class LeaderboardModel(BaseModel):
    leaderboard: list[LeaderboardEntry]

    @classmethod
    async def get_playtime(cls, db: Database, month_start: date, guild_id: int):
        month_end = datetime(year=month_start.year, month=month_start.month+1, day=1)
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

        return cls(**{'leaderboard': json.loads(data['leaderboard'])})

    @classmethod
    def view_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


class OnlineEntry(BaseModel):
    thorny_id: int
    discord_id: int
    session: datetime


class OnlineUsersSummary(BaseModel):
    users: list[OnlineEntry]

    @classmethod
    async def build(cls, db: Database, guild_id: int):
        data = await db.pool.fetchrow("""
                                      SELECT COALESCE(
                                                      JSON_AGG(JSON_BUILD_OBJECT('thorny_id', sv.thorny_id,
                                                                                 'discord_id', u.user_id,
                                                                                 'session', sv.connect_time)),
                                                      '[]'::json
                                                      ) AS users
                                      FROM events.sessions_view sv
                                      INNER JOIN users.user u ON sv.thorny_id = u.thorny_id
                                      WHERE u.guild_id = $1
                                      AND sv.disconnect_time IS NULL
                                      """,
                                      guild_id)

        return cls(**{'users': json.loads(data['users'])})

    @classmethod
    def view_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


openapi.component(MonthlyPlaytime)
openapi.component(DailyPlaytime)
openapi.component(WeeklyPlaytime)
openapi.component(GuildModel)
openapi.component(FeatureModel)
openapi.component(ChannelModel)
openapi.component(LeaderboardEntry)
