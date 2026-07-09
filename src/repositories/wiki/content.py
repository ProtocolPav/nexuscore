import json

import asyncpg
from asyncpg.pool import PoolConnectionProxy

from src.dependencies.database import Database
from src.errors import AlreadyExists, NotFound
from src.models.wiki.content import ContentDB


class ContentRepository:
    def __init__(self, db: Database):
        self.db = db

    async def fetch(self, guild_id: int, content_id: int) -> ContentDB:
        data = await self.db.pool.fetchrow("""
            SELECT * FROM wiki.content
            WHERE guild_id = $1
            AND content_id = $2
        """, guild_id, content_id)

        if not data:
            raise NotFound("Wiki Content")

        return ContentDB.model_validate(dict(data))

    async def fetch_by_page(self, guild_id: int, page_id: int) -> ContentDB:
        data = await self.db.pool.fetchrow("""
            SELECT * FROM wiki.content
            WHERE guild_id = $1
            AND page_id = $2
            ORDER BY version DESC
            LIMIT 1
        """, guild_id, page_id)

        if not data:
            raise NotFound("Wiki Content")

        return ContentDB.model_validate(dict(data))
