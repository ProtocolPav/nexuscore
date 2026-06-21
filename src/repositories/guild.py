import json

import asyncpg
from src.dependencies.database import Database
from src.errors import AlreadyExists, NotFound
from src.models.guilds import GuildPlaytimeAnalysis
from src.models.guilds.channels import ChannelDB
from src.models.guilds.connection import ConnectionDB, ConnectionIn
from src.models.guilds.features import FeatureDB
from src.models.guilds.guild import GuildDB, GuildIn, GuildUpdate
from src.models.guilds.interaction import InteractionDB, InteractionIn, InteractionQuery
from src.models.guilds.online_members import OnlineMember
from src.models.guilds.session import SessionDB, SessionQuery


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

    async def fetch_sessions(self, guild_id: int, query: SessionQuery) -> list[SessionDB]:
        query_parts = ["SELECT * FROM events.sessions_view sv", "INNER JOIN users.\"user\" u ON sv.thorny_id = u.thorny_id"]
        conditions = ["guild_id = $1"]
        params: list = [guild_id]

        if query.active:
            conditions.append(f"sv.disconnect_time IS NULL")

        # Handle time filtering
        if query.time_start is not None and query.time_end is not None:
            param_idx = len(params)
            conditions.append(
                f"sv.connect_time < ${param_idx + 1}::timestamptz AND sv.disconnect_time >= ${param_idx + 2}::timestamptz")
            params.extend([
                query.time_end,
                query.time_start
            ])

        elif query.time_start is not None:
            param_idx = len(params)
            conditions.append(f"(sv.disconnect_time >= ${param_idx + 1}::timestamptz OR sv.disconnect_time IS NULL)")
            params.append(query.time_start)

        elif query.time_end is not None:
            param_idx = len(params)
            conditions.append(f"sv.connect_time < ${param_idx + 1}::timestamptz")
            params.append(query.time_end)

        # Add WHERE clause if we have conditions
        if conditions:
            query_parts.append("WHERE")
            query_parts.append(" AND ".join(conditions))

        # Add ORDER BY clause
        if query.active:
            query_parts.append("ORDER BY connect_time DESC")
        else:
            query_parts.append("ORDER BY disconnect_time DESC")

        # Handle pagination with OFFSET and LIMIT
        if query.page is not None and query.page_size is not None:
            # Calculate offset: (page - 1) * page_size
            offset = (query.page - 1) * query.page_size
            param_idx = len(params)

            query_parts.append(f"LIMIT ${param_idx + 1}::int OFFSET ${param_idx + 2}::int")
            params.extend([query.page_size, offset])

        query = " ".join(query_parts)

        # Execute the query
        data = await self.db.pool.fetch(query, *params)

        return [SessionDB.model_validate(dict(row)) for row in data]

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

    async def create_interaction(self, model: InteractionIn) -> InteractionDB:
        data = await self.db.pool.fetchrow("""
            WITH interaction_table AS (
                INSERT INTO events.interactions(
                    thorny_id,
                    type,
                    coordinates,
                    reference,
                    mainhand,
                    dimension
                    )
                VALUES($1, $2, $3, $4, $5, $6)
                RETURNING *
            )
            SELECT * FROM interaction_table
        """, model.thorny_id, model.type, model.coordinates, model.reference, model.mainhand, model.dimension)

        return InteractionDB.model_validate(dict(data))

    async def fetch_interactions(self, query: InteractionQuery) -> list[InteractionDB]:
        # Build the query dynamically
        query_parts = ["SELECT * FROM events.interactions i"]
        conditions = []
        params = []

        # Handle coordinates
        if query.coordinates is not None:
            coordinates_int = [int(x) for x in query.coordinates]

            if query.coordinates_end is not None:
                # Area query - between coordinates and coordinates_end
                param_idx = len(params)
                conditions.append(
                    f"i.coordinates[1] BETWEEN ${param_idx + 1}::smallint AND ${param_idx + 4}::smallint AND "
                    f"i.coordinates[2] BETWEEN ${param_idx + 2}::smallint AND ${param_idx + 5}::smallint AND "
                    f"i.coordinates[3] BETWEEN ${param_idx + 3}::smallint AND ${param_idx + 6}::smallint"
                )

                coordinates_end_int = [int(x) for x in query.coordinates_end]
                params.extend([coordinates_int[0], coordinates_int[1], coordinates_int[2],
                               coordinates_end_int[0], coordinates_end_int[1], coordinates_end_int[2]])
            else:
                # Exact coordinates match
                param_idx = len(params)
                conditions.append(
                    f"i.coordinates = ARRAY[${param_idx + 1}::smallint, ${param_idx + 2}::smallint, ${param_idx + 3}::smallint]")
                params.extend([coordinates_int[0], coordinates_int[1], coordinates_int[2]])

        # Handle thorny_ids (OR condition using ANY)
        if query.thorny_ids is not None and len(query.thorny_ids) > 0:
            param_idx = len(params)
            conditions.append(f"i.thorny_id = ANY(${param_idx + 1}::int[])")

            thorny_ids_int = [int(x) for x in query.thorny_ids]
            params.append(thorny_ids_int)

        # Handle interaction_types (OR condition using ANY)
        if query.interaction_types is not None and len(query.interaction_types) > 0:
            # Convert enum types to their values if needed
            type_values = [t.value if hasattr(t, 'value') else t for t in query.interaction_types]
            param_idx = len(params)
            conditions.append(f"i.type = ANY(${param_idx + 1}::text[])")
            params.append(type_values)

        # Handle references (OR condition using ANY)
        if query.references is not None and len(query.references) > 0:
            # Convert InteractionRef to string if needed
            ref_values = [str(r) for r in query.references]
            ref_conditions = []
            for ref in ref_values:
                param_idx = len(params)
                ref_conditions.append(f"i.reference ILIKE ${param_idx + 1}::text")
                params.append(ref)
            conditions.append(f"({' OR '.join(ref_conditions)})")

        # Handle dimensions (OR condition using ANY)
        if query.dimensions is not None and len(query.dimensions) > 0:
            param_idx = len(params)
            conditions.append(f"i.dimension = ANY(${param_idx + 1}::text[])")
            params.append(query.dimensions)

        # Handle time filtering
        if query.time_start is not None and query.time_end is not None:
            # Both start and end provided - use BETWEEN
            param_idx = len(params)
            conditions.append(f"i.time BETWEEN ${param_idx + 1}::timestamptz AND ${param_idx + 2}::timestamptz")
            params.extend([
                query.time_start,
                query.time_end
            ])
        elif query.time_start is not None:
            # Only start provided - everything after
            param_idx = len(params)
            conditions.append(f"i.time >= ${param_idx + 1}::timestamptz")
            params.append(query.time_start)
        elif query.time_end is not None:
            # Only end provided - everything before
            param_idx = len(params)
            conditions.append(f"i.time <= ${param_idx + 1}::timestamptz")
            params.append(query.time_end)

        # Add WHERE clause if we have conditions
        if conditions:
            query_parts.append("WHERE")
            query_parts.append(" AND ".join(conditions))

        # Add ORDER BY clause
        query_parts.append("ORDER BY i.interaction_id DESC")

        # Handle pagination with OFFSET and LIMIT
        if query.page is not None and query.page_size is not None:
            # Calculate offset: (page - 1) * page_size
            offset = (query.page - 1) * query.page_size
            param_idx = len(params)

            query_parts.append(f"LIMIT ${param_idx + 1}::int OFFSET ${param_idx + 2}::int")
            params.extend([query.page_size, offset])

        query = " ".join(query_parts)

        # Execute the query
        data = await self.db.pool.fetch(query, *params)

        return [InteractionDB.model_validate(dict(itr)) for itr in data]