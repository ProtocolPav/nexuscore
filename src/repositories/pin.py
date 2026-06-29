import re
import unicodedata

import asyncpg
from src.dependencies.database import Database
from src.errors import AlreadyExists, NotFound
from src.models.projects.pin import PinDB, PinIn, PinUpdate

from src.models.projects.project import ProjectDB, ProjectIn, ProjectUpdate
from src.models.projects.status import StatusDB, StatusEnum, StatusIn


class PinRepository:
    def __init__(self, db: Database):
        self.db = db

    async def fetch(self, pin_id: int) -> PinDB:
        data = await self.db.pool.fetchrow("""
            SELECT * FROM projects.pins p
            WHERE p.id = $1
        """,pin_id)

        if not data:
            raise NotFound("Pin")

        return PinDB.model_validate(dict(data))

    async def fetch_all(self) -> list[PinDB]:
        data = await self.db.pool.fetch("""
            SELECT * FROM projects.pins p
        """)

        if not data:
            raise NotFound("Pins")

        return [PinDB.model_validate(dict(row)) for row in data]

    async def create(self, model: PinIn) -> PinDB:
        try:
            data = await self.db.pool.fetchrow("""
                WITH pins_table AS (
                    INSERT INTO projects.pins(name,
                                              description,
                                              coordinates,
                                              dimension,
                                              pin_type
                                             )
                    VALUES($1, $2, $3, $4, $5)

                    RETURNING id
                )

                SELECT * FROM pins_table
            """, model.name, model.description, model.coordinates, model.dimension, model.pin_type)
        except asyncpg.UniqueViolationError:
            raise AlreadyExists("Pin")

        return PinDB.model_validate(dict(data))

    async def update(self, pin_id: int, model: PinUpdate) -> PinDB:
        pin = await self.fetch(pin_id)

        updated = pin.model_copy(update=model.model_dump(exclude_none=True))

        await self.db.pool.execute("""
           UPDATE projects.pins
           SET name = $1,
               pin_type = $2,
               coordinates = $3,
               description = $4,
               dimension = $5
           WHERE id = $6
        """,updated.name, updated.pin_type, updated.coordinates, updated.description, updated.dimension, updated.id)

        return updated