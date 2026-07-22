import json

import asyncpg
from asyncpg.pool import PoolConnectionProxy

from src.dependencies.database import Database
from src.errors import AlreadyExists, NotFound
from src.models.wiki.content import ContentDB, ContentIn


class ContentRepository:
    def __init__(self, db: Database):
        self.db = db

    async def fetch(self, content_id: int) -> ContentDB:
        data = await self.db.pool.fetchrow("""
            SELECT * FROM wiki.content
            WHERE content_id = $1
        """, content_id)

        if not data:
            raise NotFound("Wiki Content")

        return ContentDB.model_validate(dict(data))

    async def fetch_by_page(self, page_id: int) -> ContentDB:
        data = await self.db.pool.fetchrow("""
            SELECT * FROM wiki.content
            Where page_id = $1
            ORDER BY version DESC
            LIMIT 1
        """, page_id)

        if not data:
            raise NotFound("Wiki Content")

        return ContentDB.model_validate(dict(data))

    @staticmethod
    async def create(page_id: int, model: ContentIn, current_version: int, conn: PoolConnectionProxy) -> ContentDB:
        try:
            data = await conn.fetchrow("""
                INSERT INTO wiki.content(page_id, content, edited_by, change_note, editor_type, version)
                VALUES ($1, $2, $3, $4, $5, $6)
                
                RETURNING *
            """, page_id, json.dumps(model.data), model.edited_by, model.change_note, model.editor_type, current_version + 1)

        except asyncpg.UniqueViolationError:
            raise AlreadyExists("Wiki Content")

        return ContentDB.model_validate(dict(data))
