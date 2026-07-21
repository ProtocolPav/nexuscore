import json

import asyncpg
from asyncpg.pool import PoolConnectionProxy

from src.dependencies.database import Database
from src.errors import AlreadyExists, NotFound
from src.models.wiki.page import PageDB, PageIn, PageQuery, PageUpdate


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

    async def fetch_by_slug(self, guild_id: int, slug: str) -> PageDB:
        data = await self.db.pool.fetchrow("""
            SELECT * FROM wiki.page
            WHERE guild_id = $1
            AND slug = $2
        """, guild_id, slug)

        if not data:
            raise NotFound("Wiki Page")

        return PageDB.model_validate(dict(data))

    async def fetch_all(self, guild_id: int, query: PageQuery) -> list[PageDB]:
        # Build the query dynamically
        query_parts = ["SELECT * FROM wiki.page p"]
        conditions = ["p.guild_id = $1"]
        params: list = [guild_id]

        # Handle published (exact match)
        if query.published is not None:
            param_idx = len(params)
            conditions.append(f"p.published = ${param_idx + 1}")
            params.append(query.published)

        # Handle category (exact match)
        if query.category is not None:
            param_idx = len(params)
            conditions.append(f"p.category = ${param_idx + 1}")
            params.append(query.category)

        # Handle tags (match ANY of the given tags - array overlap)
        if query.tags is not None and len(query.tags) > 0:
            param_idx = len(params)
            conditions.append(f"p.tags && ${param_idx + 1}::text[]")
            params.append(query.tags)

        # Handle fuzzy search on title
        if query.search is not None and len(query.search) > 0:
            param_idx = len(params)
            conditions.append(f"p.title ILIKE ${param_idx + 1}")
            params.append(f"%{query.search}%")

        # Add a WHERE clause if we have conditions
        if conditions:
            query_parts.append("WHERE")
            query_parts.append(" AND ".join(conditions))

        # Add ORDER BY clause (whitelist columns to avoid SQL injection via sort_by)
        sort_column_map = {
            "created_at": "p.created_at",
            "updated_at": "p.updated_at",
            "title": "p.title",
        }
        if query.sort_by:
            sort_column = sort_column_map.get(query.sort_by, "p.created_at")
            sort_direction = "ASC" if query.sort_order == "asc" else "DESC"
            query_parts.append(f"ORDER BY {sort_column} {sort_direction}")

        # Handle pagination with OFFSET and LIMIT
        if query.page is not None and query.page_size is not None:
            offset = (query.page - 1) * query.page_size
            param_idx = len(params)
            query_parts.append(f"LIMIT ${param_idx + 1}::int OFFSET ${param_idx + 2}::int")
            params.extend([query.page_size, offset])

        sql = " ".join(query_parts)

        # Execute the query
        data = await self.db.pool.fetch(sql, *params)

        return [PageDB.model_validate(dict(p)) for p in data]

    @staticmethod
    async def create(guild_id: int, model: PageIn, conn: PoolConnectionProxy) -> PageDB:
        try:
            data = await conn.fetchrow("""
                WITH page_table AS (
                    INSERT INTO wiki.page(
                        author_id,
                        guild_id,
                        project_id,
                        slug,
                        title,
                        summary,
                        category,
                        tags,
                        cover_image,
                        published,
                        locked
                    )
                    VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)

                    RETURNING *
                )
                SELECT * from page_table
            """, model.author_id, guild_id, model.project_id,
               model.slug, model.title, model.summary, model.category, model.tags,
               model.cover_image, model.published, model.locked)

        except asyncpg.UniqueViolationError:
            raise AlreadyExists("Wiki Page")

        return PageDB.model_validate(dict(data))

    async def update(self, guild_id: int, page_id: int, model: PageUpdate, conn: PoolConnectionProxy) -> PageDB:
        page = await self.fetch(guild_id, page_id)

        updated = page.model_copy(update=model.model_dump(exclude_none=True))

        await conn.execute("""
            UPDATE wiki.page
            SET title = $2,
                project_id = $3,
                summary = $4,
                category = $5,
                tags = $6,
                cover_image = $7,
                published = $8,
                locked = $9,
                updated_at = NOW()
            
            WHERE page_id = $1
        """, page_id, updated.title, updated.project_id,
                           updated.summary, updated.category, updated.tags, updated.cover_image,
                           updated.published, updated.locked)

        return updated