import asyncpg

from asyncpg.pool import PoolConnectionProxy

from src.dependencies.database import Database
from src.errors import AlreadyExists, NotFound
from src.models.quests.quest import QuestDB, QuestIn, QuestQuery, QuestUpdate


class QuestRepository:
    def __init__(self, db: Database):
        self.db = db

    async def fetch(self, quest_id: int, guild_id: int) -> QuestDB:
        data = await self.db.pool.fetchrow("""
            SELECT * FROM quests_v3.quest
            WHERE quest_id = $1
            AND guild_id = $2
        """,quest_id, guild_id)

        if not data:
            raise NotFound("Quest")

        return QuestDB.model_validate(dict(data))

    @staticmethod
    async def create(guild_id: int, model: QuestIn, conn: PoolConnectionProxy) -> QuestDB:
        try:
            data = await conn.fetchrow("""
                WITH quest_table AS (
                    INSERT INTO quests_v3.quest(
                        start_time, 
                        end_time, 
                        title, 
                        description,
                        created_by,
                        tags,
                        quest_type,
                        guild_id
                    )
                    VALUES($1, $2, $3, $4, $5, $6, $7, $8)

                    RETURNING *
                )
                SELECT * from quest_table
            """, model.start_time, model.end_time, model.title, model.description, model.created_by,
                                               model.tags, model.quest_type, guild_id)
        except asyncpg.UniqueViolationError:
            raise AlreadyExists("Quest")

        return QuestDB.model_validate(dict(data))

    async def update(self, quest_id: int, guild_id: int, model: QuestUpdate, conn: PoolConnectionProxy) -> QuestDB:
        quest = await self.fetch(quest_id, guild_id)

        updated = quest.model_copy(update=model.model_dump(exclude_none=True))

        await conn.execute("""
            UPDATE quests_v3.quest
            SET start_time = $1,
                end_time = $2,
                title = $3,
                description = $4,
                created_by = $5,
                tags = $6,
                quest_type = $7
            WHERE quest_id = $8
        """, updated.start_time, updated.end_time, updated.title, updated.description, updated.created_by,
                                   updated.tags, updated.quest_type, updated.quest_id)

        return updated

    async def fetch_all(self, guild_id: int, query: QuestQuery) -> list[QuestDB]:
        # Build the query dynamically
        query_parts = ["SELECT * FROM quests_v3.quest q"]
        conditions = ["q.guild_id = $1"]
        params: list = [guild_id]

        # Handle thorny_ids (OR condition using ANY)
        if query.creator_thorny_ids is not None and len(query.creator_thorny_ids) > 0:
            param_idx = len(params)
            conditions.append(f"q.created_by = ANY(${param_idx + 1}::int[])")

            thorny_ids_int = [int(x) for x in query.creator_thorny_ids]
            params.append(thorny_ids_int)

        # Handle interaction_types (OR condition using ANY)
        if query.quest_types is not None and len(query.quest_types) > 0:
            param_idx = len(params)
            conditions.append(f"q.quest_type = ANY(${param_idx + 1})")

            params.append(query.quest_types)

        # Handle time filtering
        if query.time_start is not None and query.time_end is not None:
            # Both start and end provided - filter between range
            param_idx = len(params)
            conditions.append(f"q.start_time >= ${param_idx + 1}::timestamptz AND q.end_time <= ${param_idx + 2}::timestamptz")
            params.extend([
                query.time_start,
                query.time_end
            ])

        elif query.time_start is not None:
            # Only start time provided - filter after this time
            param_idx = len(params)
            conditions.append(f"q.start_time >= ${param_idx + 1}::timestamptz")
            params.append(query.time_start)

        elif query.time_end is not None:
            # Only end time provided - filter before this time
            param_idx = len(params)
            conditions.append(f"q.end_time <= ${param_idx + 1}::timestamptz")
            params.append(query.time_end)

        # Handle "active", "future" and "past" quests_router
        if query.active:
            conditions.append(f"NOW() BETWEEN q.start_time AND q.end_time")

        if query.future:
            conditions.append(f"q.start_time > NOW()")

        if query.past:
            conditions.append(f"q.end_time < NOW()")

        # Add a WHERE clause if we have conditions
        if conditions:
            query_parts.append("WHERE")
            query_parts.append(" AND ".join(conditions))

        # Add ORDER BY clause
        query_parts.append("ORDER BY q.quest_id DESC")

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

        return [QuestDB.model_validate(dict(q)) for q in data]