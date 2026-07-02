import asyncpg
from src.dependencies.database import Database
from src.errors import AlreadyExists, NotFound
from src.models.events.event import EventDB, EventIn, EventUpdate


class EventRepository:
    def __init__(self, db: Database):
        self.db = db

    async def fetch(self, event_id: int) -> EventDB:
        data = await self.db.pool.fetchrow("""
            SELECT * FROM events.event e
            WHERE e.event_id = $1
        """,event_id)

        if not data:
            raise NotFound("Event")

        return EventDB.model_validate(dict(data))

    async def fetch_all(self) -> list[EventDB]:
        data = await self.db.pool.fetch("""
            SELECT * FROM events.event
        """)

        return [EventDB.model_validate(dict(row)) for row in data]

    async def create(self, guild_id: int, model: EventIn) -> EventDB:
        try:
            data = await self.db.pool.fetchrow("""
                WITH events_table AS (
                    INSERT INTO events.event(
                                             guild_id,
                                             slug,
                                             title,
                                             description,
                                             image_url,
                                             start_time,
                                             end_time,
                                             blocks
                                            )
                    VALUES($1, $2, $3, $4, $5, $6, $7, $8)

                    RETURNING event_id
                )

                SELECT * FROM events_table
            """, guild_id, model.slug, model.title, model.description, model.image_url, model.start_time, model.end_time, model.blocks)
        except asyncpg.UniqueViolationError:
            raise AlreadyExists("Event")

        return EventDB.model_validate(dict(data))

    async def update(self, event_id: int, model: EventUpdate) -> EventDB:
        event = await self.fetch(event_id)

        updated = event.model_copy(update=model.model_dump(exclude_none=True))

        await self.db.pool.execute("""
           UPDATE events.event
           SET title = $1,
               description = $2,
               image_url = $3,
               start_time = $4,
               end_time = $5,
               blocks = $6,
               status = $7
           WHERE event_id = $8
        """, updated.title, updated.description, updated.image_url, updated.start_time, updated.end_time, updated.blocks, updated.status, updated.event_id)

        return updated