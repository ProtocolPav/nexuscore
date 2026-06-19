import asyncio
import re
import unicodedata
import asyncpg

from src.dependencies.database import Database
from src.errors import AlreadyExists, NotFound

from src.models.projects.project import ProjectDB, ProjectIn, ProjectOut, ProjectUpdate
from src.models.projects.status import StatusDB, StatusEnum, StatusIn

from src.models.users.user import UserOut
from src.models.users.profile import ProfileOut
from src.repositories.user import UserRepository


class ProjectRepository:
    def __init__(self, db: Database, user_repo: UserRepository):
        self.db = db
        self.user_repo = user_repo

    async def _to_out(self, project: ProjectDB) -> ProjectOut:
        owner, profile, stat = await asyncio.gather(
            self.user_repo.fetch(project.guild_id, project.owner_id),
            self.user_repo.fetch_profile(project.guild_id, project.owner_id),
            self.fetch_status(project.project_id)
        )

        return ProjectOut(
            **project.model_dump(),
            owner=UserOut(
                **owner.model_dump(),
                profile=ProfileOut(**profile.model_dump())
            ),
            status=stat.status,
            status_since=stat.since
        )

    async def _fetch_db(self, guild_id: int, project_id: str) -> ProjectDB:
        data = await self.db.pool.fetchrow("""
            SELECT * FROM projects.project p
            WHERE p.project_id = $1
            AND p.guild_id = $2
        """,project_id, guild_id)

        if not data:
            raise NotFound("Project")

        return ProjectDB.model_validate(dict(data))

    async def _fetch_all_db(self, guild_id: int) -> list[ProjectDB]:
        data = await self.db.pool.fetch("""
            SELECT * FROM projects.project p
            WHERE p.guild_id = $1
        """, guild_id)

        if not data:
            raise NotFound("Projects")

        return [ProjectDB.model_validate(dict(row)) for row in data]

    async def _create_db(self, guild_id: int, model: ProjectIn) -> ProjectDB:
        normalized = unicodedata.normalize('NFKD', model.name)
        ascii_str = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
        project_id = re.sub(r'[^a-z0-9_]', '', ascii_str.lower().replace(' ', '_'))

        try:
            data = await self.db.pool.fetchrow("""
                WITH project_table AS (
                    INSERT INTO projects.project(
                        project_id,
                        guild_id,
                        name, 
                        description, 
                        coordinates,
                        owner_id,
                        dimension
                    )
                    VALUES($1, $2, $3, $4, $5, $6, $7)
                    RETURNING *
                ),
                members_table AS (
                    INSERT INTO projects.members(project_id, user_id)
                    VALUES ($1, $5)
                ),
                status_table AS (
                    INSERT INTO projects.status(project_id, status)
                    VALUES ($1, $8)
                )
                SELECT * FROM project_table
            """, project_id, guild_id, model.name, model.description, model.coordinates, model.owner_id, model.dimension,
                StatusEnum.pending.value)
        except asyncpg.UniqueViolationError:
            raise AlreadyExists("Project")

        return ProjectDB.model_validate(dict(data))

    async def _update_db(self, guild_id: int, project_id: str, model: ProjectUpdate) -> ProjectDB:
        project = await self._fetch_db(guild_id, project_id)

        updated = project.model_copy(update=model.model_dump(exclude_none=True))

        await self.db.pool.execute("""
            UPDATE projects.project
            SET name = $1,
               thread_id = $2,
               coordinates = $3,
               description = $4,
               completed_on = $5,
               owner_id = $6,
               pin_id = $7,
               dimension = $8
            WHERE project_id = $9
        """,updated.name, updated.thread_id, updated.coordinates, updated.description,
                                   updated.completed_on, updated.owner_id, updated.pin_id,
                                   updated.dimension, updated.project_id)

        return updated

    async def fetch(self, guild_id: int, project_id: str) -> ProjectOut:
        project_db = await self._fetch_db(guild_id, project_id)
        return await self._to_out(project_db)

    async def fetch_all(self, guild_id: int) -> list[ProjectOut]:
        projects_db = await self._fetch_all_db(guild_id)
        return [await self._to_out(p) for p in projects_db]

    async def create(self, guild_id: int, model: ProjectIn) -> ProjectOut:
        project_db = await self._create_db(guild_id, model)
        return await self._to_out(project_db)

    async def update(self, guild_id: int, project_id: str, model: ProjectUpdate) -> ProjectOut:
        project_db = await self._update_db(guild_id, project_id, model)
        return await self._to_out(project_db)

    async def fetch_status(self, project_id: str) -> StatusDB:
        data = await self.db.pool.fetchrow("""
            SELECT status, since FROM projects.status
            WHERE project_id = $1
            ORDER BY since DESC
        """,project_id)

        if not data:
            raise NotFound("Project Status")

        return StatusDB.model_validate(dict(data))

    async def create_status(self, project_id: str, model: StatusIn) -> StatusDB:
        try:
            data = await self.db.pool.fetchrow("""
                WITH status_table AS (
                    INSERT INTO projects.status(project_id, status)
                    VALUES ($1, $2)
                    
                    RETURNING *
                )
                SELECT * FROM status_table
                ORDER BY since DESC LIMIT 1
            """, project_id, model.status)
        except asyncpg.UniqueViolationError:
            raise AlreadyExists("Project Status")

        return StatusDB.model_validate(dict(data))