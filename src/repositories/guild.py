import json

import asyncpg
from src.dependencies.database import Database
from src.errors import AlreadyExists, NotFound
from src.models.guilds import GuildPlaytimeAnalysis
from src.models.guilds.channels import ChannelDB
from src.models.guilds.connection import ConnectionDB, ConnectionIn
from src.models.guilds.features import FeatureDB
from src.models.guilds.guild import GuildDB, GuildIn, GuildUpdate
from src.models.guilds.online_members import OnlineMember


class GuildRepository:
    def __init__(self, db: Database):
        self.db = db

    async def fetch(self, guild_id: int) -> GuildDB:
        data = await self.db.pool.fetchrow("""
            SELECT * FROM guilds.guild 
            WHERE guild_id = $1
        """,guild_id)

        if not data:
            raise NotFound("Guild")

        return GuildDB.model_validate(dict(data))

    async def create(self, model: GuildIn) -> GuildDB:
        try:
            data = await self.db.pool.fetchrow("""
                WITH guild_table AS (
                    INSERT INTO guilds.guild(guild_id, name)
                    VALUES ($1, $2)
                    RETURNING *
                ),
                features_table AS (
                    INSERT INTO guilds.features(guild_id, feature)
                        VALUES ($1, 'profile'), ($1, 'levels'), ($1, 'basic')
                )
                SELECT * FROM guild_table
            """, model.guild_id, model.name)
        except asyncpg.UniqueViolationError:
            raise AlreadyExists("Guild")

        return GuildDB.model_validate(dict(data))

    async def update(self, guild_id: int, model: GuildUpdate) -> GuildDB:
        guild = await self.fetch(guild_id)

        updated = guild.model_copy(update=model.model_dump(exclude_none=True))

        await self.db.pool.execute("""
            UPDATE guilds.guild
            SET name=$2, 
                currency_name=$3, 
                currency_emoji=$4,
                level_up_message=$5, 
                join_message=$6, 
                leave_message=$7,
                xp_multiplier=$8, 
                active=$9
            WHERE guild_id = $1
        """,updated.guild_id, updated.name, updated.currency_name,
                                   updated.currency_emoji, updated.level_up_message, updated.join_message,
                                   updated.leave_message, updated.xp_multiplier, updated.active)

        return updated

    async def fetch_features(self, guild_id: int) -> list[FeatureDB]:
        data = await self.db.pool.fetch("""
            SELECT * FROM guilds.features
            WHERE guild_id = $1
        """, guild_id)

        return [FeatureDB.model_validate(dict(row)) for row in data]

    async def fetch_channels(self, guild_id: int) -> list[ChannelDB]:
        data = await self.db.pool.fetch("""
            SELECT * FROM guilds.channels
            WHERE guild_id = $1
        """, guild_id)

        return [ChannelDB.model_validate(dict(row)) for row in data]

    async def fetch_online_members(self, guild_id: int) -> list[OnlineMember]:
        data = await self.db.pool.fetch("""
           SELECT 
                sv.thorny_id, 
                u.user_id, 
                u.username, 
                u.whitelist, 
                sv.connect_time as session,
                u.location,
                u.dimension,
                u.hidden,
                u.xuid
           FROM events.sessions_view sv
           INNER JOIN users.user u ON sv.thorny_id = u.thorny_id
           WHERE u.guild_id = $1
           AND sv.disconnect_time IS NULL
        """, guild_id)

        return [OnlineMember.model_validate(dict(row)) for row in data]

    async def fetch_playtime_analysis(self, guild_id: int) -> GuildPlaytimeAnalysis:
        data = await self.db.pool.fetchrow("""
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
                coalesce((select extract(epoch from total_playtime) from totals), 0) as total_playtime,
                coalesce((select total_unique_players from totals), 0) as total_unique_players,
                coalesce((
                    select json_agg(json_build_object(
                        'week', w.week, 'total', extract(epoch from w.total),
                        'unique_players', w.unique_players, 'total_sessions', w.total_sessions,
                        'average_playtime_per_session', extract(epoch from w.avg_playtime)))
                    from weekly_playtime w
                ), '[]'::json) as weekly_playtime,
                coalesce((
                    select json_agg(json_build_object(
                        'day', d.day, 'total', extract(epoch from d.total),
                        'unique_players', d.unique_players, 'total_sessions', d.total_sessions,
                        'average_playtime_per_session', extract(epoch from d.avg_playtime)))
                    from daily_playtime d
                ), '[]'::json) as daily_playtime,
                coalesce((
                    select json_agg(json_build_object(
                        'month', m.month, 'total', extract(epoch from m.total),
                        'unique_players', m.unique_players))
                    from monthly_playtime m
                ), '[]'::json) as monthly_playtime
        """, guild_id)

        return GuildPlaytimeAnalysis(
            total_playtime=data['total_playtime'],
            total_unique_players=data['total_unique_players'],
            daily_playtime=json.loads(data['daily_playtime']),
            weekly_playtime=json.loads(data['weekly_playtime']),
            monthly_playtime=json.loads(data['monthly_playtime']),
        )

    async def create_connection(self, model: ConnectionIn, ignore: bool = False) -> ConnectionDB:
        data = await self.db.pool.fetchrow("""
            WITH connection_table AS (
                INSERT INTO events.connections(type, thorny_id, ignored)
                VALUES($1, $2, $3)
                RETURNING *
            )
            SELECT * FROM connection_table
        """, model.type, model.thorny_id, ignore)

        return ConnectionDB.model_validate(dict(data))