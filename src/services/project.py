import asyncio
import re
import unicodedata
import asyncpg

from src.dependencies.database import Database
from src.errors import AlreadyExists, NotFound

from src.models.projects.project import ProjectDB, ProjectIn, ProjectOut, ProjectUpdate
from src.models.projects.status import StatusDB, StatusEnum, StatusIn, StatusOut

from src.models.users.user import UserOut
from src.models.users.profile import ProfileOut
from src.repositories.project import ProjectRepository
from src.repositories.user import UserRepository


class ProjectService:
    def __init__(self, project_repo: ProjectRepository, user_repo: UserRepository):
        self.project_repo = project_repo
        self.user_repo = user_repo

    async def _to_out(self, project: ProjectDB) -> ProjectOut:
        owner, profile, stat = await asyncio.gather(
            self.user_repo.fetch(project.guild_id, project.owner_id),
            self.user_repo.fetch_profile(project.guild_id, project.owner_id),
            self.project_repo.fetch_status(project.project_id)
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

    async def get(self, guild_id: int, project_id: str) -> ProjectOut:
        project_db = await self.project_repo.fetch(guild_id, project_id)
        return await self._to_out(project_db)

    async def get_all(self, guild_id: int) -> list[ProjectOut]:
        projects_db = await self.project_repo.fetch_all(guild_id)

        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(self._to_out(p)) for p in projects_db]

        return [t.result() for t in tasks]

    async def new(self, guild_id: int, model: ProjectIn) -> ProjectOut:
        project_db = await self.project_repo.create(guild_id, model)
        return await self._to_out(project_db)

    async def update(self, guild_id: int, project_id: str, model: ProjectUpdate) -> ProjectOut:
        project_db = await self.project_repo.update(guild_id, project_id, model)
        return await self._to_out(project_db)

    async def get_status(self, project_id: str) -> StatusOut:
        status_db = await self.project_repo.fetch_status(project_id)
        return StatusOut(**status_db.model_dump())

    async def new_status(self, project_id: str, model: StatusIn) -> StatusOut:
        status_db = await self.project_repo.create_status(project_id, model)
        return StatusOut(**status_db.model_dump())