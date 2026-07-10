import asyncio

from src.models.users.profile import ProfileOut
from src.models.users.user import UserOut
from src.models.wiki.content import ContentOut
from src.models.wiki.page import PageDB, PageOut, PageQuery
from src.repositories.project import ProjectRepository
from src.repositories.user import UserRepository
from src.repositories.wiki.content import ContentRepository
from src.repositories.wiki.page import PageRepository


class WikiService:
    def __init__(
            self,
            page_repo: PageRepository,
            content_repo: ContentRepository,
            project_repo: ProjectRepository,
            user_repo: UserRepository
    ):
        self.page_repo = page_repo
        self.content_repo = content_repo
        self.project_repo = project_repo
        self.user_repo = user_repo

    async def _to_out(self, page: PageDB) -> PageOut:
        author_db, profile_db, content_db = await asyncio.gather(
            self.user_repo.fetch(page.guild_id, page.author_id),
            self.user_repo.fetch_profile(page.guild_id, page.author_id),
            self.content_repo.fetch_by_page(page.page_id)
        )

        content_editor_db, content_profile_db = await asyncio.gather(
            self.user_repo.fetch(page.guild_id, content_db.edited_by),
            self.user_repo.fetch_profile(page.guild_id, content_db.edited_by),
        )

        return PageOut(
            **page.model_dump(),
            author=UserOut(
                **author_db.model_dump(),
                profile=ProfileOut(
                    **profile_db.model_dump()
                )
            ),
            content=ContentOut(
                **content_db.model_dump(exclude={"edited_by"}),
                edited_by=UserOut(
                    **content_editor_db.model_dump(),
                    profile=ProfileOut(**content_profile_db.model_dump())
                ),
                data=content_db.content
            )
        )

    async def get(self, guild_id: int, page_id: int) -> PageOut:
        page_db = await self.page_repo.fetch(guild_id, page_id)
        return await self._to_out(page_db)

    async def get_all(self, guild_id: int, query: PageQuery) -> list[PageOut]:
        pages_db = await self.page_repo.fetch_all(guild_id, query)

        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(self._to_out(p)) for p in pages_db]

        return [t.result() for t in tasks]
