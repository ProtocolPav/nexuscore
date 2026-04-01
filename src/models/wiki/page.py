import re
from datetime import datetime

from pydantic import Field
from typing import List
from typing_extensions import Optional

from src.database import Database
from src.models.users import user
from src.models.wiki.content import PageContentModel, PageContentCreateModel
from src.utils.base import BaseModel, BaseList, optional_model

from sanic_ext import openapi

from src.utils.errors import BadRequest400, NotFound404


class PageBaseModel(BaseModel):
    title: str = Field(description="The title of the wiki page",
                       json_schema_extra={"example": "Getting Started Guide"})
    summary: Optional[str] = Field(description="A short summary of the page",
                                   json_schema_extra={"example": "An introduction to the server"})
    category: Optional[str] = Field(description="The category this page belongs to",
                                    json_schema_extra={"example": "guides"})
    tags: List[str] = Field(description="Tags for categorizing the page",
                            json_schema_extra={"example": ["beginner", "tutorial"]},
                            default_factory=list)
    cover_image: Optional[str] = Field(description="URL of the cover image",
                                       json_schema_extra={"example": "https://example.com/cover.png"})
    published: bool = Field(description="Whether the page is publicly visible",
                            json_schema_extra={"example": False})
    locked: bool = Field(description="Whether the page is locked to prevent unauthorized edits",
                         json_schema_extra={"example": False})


@openapi.component()
class PageModel(PageBaseModel):
    page_id: str = Field(description="The URL-safe slug ID of the page",
                         json_schema_extra={"example": "getting_started_guide"})
    author_id: int = Field(description="The ThornyID of the page author",
                           json_schema_extra={"example": 12})
    author: user.UserModel = Field(description="The author of the page, in the form of a User object")
    created_at: datetime = Field(description="When the page was created",
                                 json_schema_extra={"example": "2024-07-05 15:15:00+00:00"})
    updated_at: datetime = Field(description="When the page was last updated",
                                 json_schema_extra={"example": "2024-07-05 15:15:00+00:00"})
    view_count: int = Field(description="The number of times this page has been viewed",
                            json_schema_extra={"example": 42})
    content: Optional[PageContentModel] = Field(description="The latest content version of the page, if requested")

    @classmethod
    async def create(cls, db: Database, model: "PageCreateModel", *args) -> str:
        page_id = re.sub(r'[^a-z0-9_]', '', model.title.lower().replace(' ', '_'))

        await db.pool.execute("""
                              INSERT INTO wiki.page(page_id, title, summary, category, tags, cover_image, author_id, published, locked)
                              VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9)
                              """,
                              page_id, model.title, model.summary, model.category, model.tags, model.cover_image,
                              model.author_id, model.published, model.locked)

        return page_id

    @classmethod
    async def fetch(cls, db: Database, page_id: str, include_content: bool = False, *args) -> "PageModel":
        if not page_id:
            raise BadRequest400(extra={'ids': ['page_id']})

        data = await db.pool.fetchrow("""
                                      SELECT * FROM wiki.page
                                      WHERE page_id = $1
                                      """,
                                      page_id)

        if data:
            page_author = await user.UserModel.fetch(db, data['author_id'])

            content = None
            if include_content:
                content = await PageContentModel.fetch_latest(db, page_id)

            return cls(**data, author=page_author, content=content)
        else:
            raise NotFound404(extra={'resource': 'wiki page', 'id': page_id})

    async def update(self, db: Database, model: "PageUpdateModel", *args):
        for k, v in model.model_dump().items():
            setattr(self, k, v) if v is not None else None

        await db.pool.execute("""
                              UPDATE wiki.page
                              SET title = $1,
                                  summary = $2,
                                  category = $3,
                                  tags = $4,
                                  cover_image = $5,
                                  published = $6,
                                  locked = $7,
                                  updated_at = now()
                              WHERE page_id = $8
                              """,
                              self.title, self.summary, self.category, self.tags, self.cover_image,
                              self.published, self.locked, self.page_id)

    async def increment_views(self, db: Database):
        await db.pool.execute("""
                              UPDATE wiki.page
                              SET view_count = view_count + 1
                              WHERE page_id = $1
                              """,
                              self.page_id)


class PagesListModel(BaseList[PageModel]):
    @classmethod
    async def fetch(cls, db: Database, category: Optional[str] = None, published_only: bool = True,
                    *args) -> "PagesListModel":
        conditions = []
        params = []

        if category:
            params.append(category)
            conditions.append(f"category = ${len(params)}")

        if published_only:
            conditions.append("published = TRUE")

        where_clause = ""
        if conditions:
            where_clause = f"WHERE {' AND '.join(conditions)}"

        data = await db.pool.fetch(f"""
                                   SELECT * FROM wiki.page
                                   {where_clause}
                                   ORDER BY created_at ASC
                                   """,
                                   *params)

        pages: list[PageModel] = []
        for page in data:
            page_author = await user.UserModel.fetch(db, page['author_id'])
            pages.append(PageModel(**page, author=page_author, content=None))

        return cls(root=pages)


class PageCreateModel(PageBaseModel):
    author_id: int = Field(description="The ThornyID of the page author",
                           json_schema_extra={"example": 12})


PageUpdateModel = optional_model("PageUpdateModel", PageBaseModel)
