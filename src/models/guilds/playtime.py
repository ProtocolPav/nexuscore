import json
from datetime import date, datetime

from pydantic import Field

from sanic_ext import openapi

from src.database import Database

from src.utils.base import BaseModel, BaseList, optional_model


@openapi.component()
class DailyPlaytime(BaseModel):
    day: date = Field(description="The day this data is about",
                      examples=['2024-05-05'])
    total: float = Field(description="The total playtime that day in seconds",
                         examples=[44544.4322])
    unique_players: int = Field(description="How many unique players played that day",
                                examples=[43])
    total_sessions: int = Field(description="The total amount of sessions that day. "
                                            "(A session is when a user connects and disconnects)",
                                examples=[443])
    average_playtime_per_session: float = Field(description="The average playtime per session today in seconds",
                                                examples=[405.325])


@openapi.component()
class WeeklyPlaytime(BaseModel):
    week: int = Field(description="The week of the year this data is about",
                      examples=[23])
    total: float = Field(description="The total playtime that week in seconds",
                         examples=[44544.4322])
    unique_players: int = Field(description="How many unique players played that week",
                                examples=[43])
    total_sessions: int = Field(description="The total amount of sessions that week. "
                                            "(A session is when a user connects and disconnects)",
                                examples=[443])
    average_playtime_per_session: float = Field(description="The average playtime per session this week in seconds",
                                                examples=[405.325])


@openapi.component()
class MonthlyPlaytime(BaseModel):
    month: date = Field(description="The month this data is about. Always the first day of that month",
                        examples=['2024-05-01'])
    total: float = Field(description="The total playtime that month in seconds",
                         examples=[4554544.4322])
    unique_players: int = Field(description="How many unique players played that month",
                                examples=[432])


class GuildPlaytimeAnalysis(BaseModel):
    total_playtime: float = Field(description="The total playtime of this guild in seconds",
                                  examples=[1999432544.55433])
    total_unique_players: int = Field(description="The total unique players that have played on this guild",
                                      examples=[4433])
    daily_playtime: list[DailyPlaytime] = Field(description="Data about the last 7 days of playtime")
    weekly_playtime: list[WeeklyPlaytime] = Field(description="Data about the last 8 weeks of playtime")
    monthly_playtime: list[MonthlyPlaytime] = Field(description="Data about the last 12 months of playtime")
    peak_playtime_periods: None = None
    peak_active_periods: None = None
    daily_playtime_distribution: None = None
    anomalies: None = None
    predictive_insights: None = None

    @classmethod
    async def fetch(cls, db: Database, guild_id: int, *args) -> "GuildPlaytimeAnalysis":
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
                            extract(year from sv.connect_time) as year,
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
                        group by year, week
                        order by year desc, week desc 
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


@openapi.component()
class OnlineEntry(BaseModel):
    thorny_id: int = Field(description="The ThornyID of the user",
                           examples=[543])
    discord_id: int = Field(description="The Discord ID of the user",
                            examples=[18463748938364])
    session: datetime = Field(description="The date and time when the session started",
                              examples=['2024-05-05 13:44:33.123456'])
    username: str = Field(description="The username of the user",
                          examples=['protocolpav'])
    whitelist: str = Field(description="The gamertag of the user",
                          examples=['ProtocolPav'])
    location: tuple[int, int, int] = Field(description="The last in-game location of the user",
                                           json_schema_extra={"example": (544, 18, -432)})
    dimension: str = Field(description="The last in-game dimension the user was in",
                           json_schema_extra={"example": 'minecraft:overworld'})


class OnlineUsersListModel(BaseList[OnlineEntry]):
    @classmethod
    async def fetch(cls, db: Database, guild_id: int = None, *args) -> "OnlineUsersListModel":
        data = await db.pool.fetch("""
                                   SELECT 
                                        sv.thorny_id, 
                                        u.user_id, 
                                        u.username, 
                                        u.whitelist, 
                                        sv.connect_time as session,
                                        u.location,
                                        u.dimension
                                   FROM events.sessions_view sv
                                   INNER JOIN users.user u ON sv.thorny_id = u.thorny_id
                                   WHERE u.guild_id = $1
                                   AND sv.disconnect_time IS NULL
                                   """,
                                   guild_id)

        online_users: list[OnlineEntry] = []
        for user in data:
            online_users.append(OnlineEntry(**user))

        return cls(root=online_users)
