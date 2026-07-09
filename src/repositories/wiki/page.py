import json

import asyncpg
from asyncpg.pool import PoolConnectionProxy

from src.dependencies.database import Database
from src.errors import AlreadyExists, NotFound
from src.models.wiki.page import PageDB


class PageRepository:
    def __init__(self, db: Database):
        self.db = db

    async def fetch(self, guild_id: int, page_id: int) -> PageDB:
        data = await self.db.pool.fetchrow("""
            SELECT * FROM wiki.page
            WHERE guild_id = $1
            AND page_id = $2
        """, guild_id, page_id)

        if not data:
            raise NotFound("Wiki Page")

        return PageDB.model_validate(dict(data))

    async def fetch_all(self, guild_id: int) -> list[PageDB]:
        data = await self.db.pool.fetch("""
            SELECT * FROM wiki.page
            WHERE guild_id = $1
            ORDER BY updated_at DESC
        """, guild_id)

        return [PageDB.model_validate(dict(o)) for o in data]
