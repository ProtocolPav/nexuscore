from datetime import datetime

from pydantic import BaseModel, Field
from typing_extensions import Optional, Annotated

from src.models.projects.project import ProjectOut
from src.models.users.user import UserOut
from src.models.wiki.content import PageContentModel


PageID = Annotated[int, Field(
    description="The page ID",
    examples=[432]
)]
Slug = Annotated[str, Field(
    description="The URL-safe slug ID of the page",
    examples=["getting_started_guide"]
)]
ProjectID = Annotated[int, Field(
    description="The linked project ID for this wiki page",
    examples=[123]
)]
AuthorID = Annotated[int, Field(
    description="The ThornyID of the page author",
    examples=[12]
)]
Title = Annotated[str, Field(
    description="The title of the wiki page",
    examples=["Getting Started Guide"]
)]
Summary = Annotated[str, Field(
    description="A short summary of the page",
    examples=["An introduction to the server"]
)]
Category = Annotated[Optional[str], Field(
    description="The category this page belongs to",
    examples=["guides"]
)]
Tags = Annotated[list[str], Field(
    description="Tags for categorizing the page",
)]
CoverImage = Annotated[str, Field(
    description="URL of the cover image",
    examples=["https://example.com/cover.png"]
)]
Published = Annotated[bool, Field(
    description="Whether the page is publicly visible",
    examples=[False]
)]
Locked = Annotated[bool, Field(
    description="Whether the page is locked to prevent unauthorized edits",
    examples=[False]
)]
ViewCount = Annotated[int, Field(
    description="The number of times this page has been viewed",
    examples=[42]
)]
CreatedAt = Annotated[datetime, Field(
    description="When the page was created",
    examples=['2024-07-05 15:15:00+00:00']
)]
UpdatedAt = Annotated[datetime, Field(
    description="When the page was last updated",
    examples=['2024-07-05 15:15:00+00:00']
)]
Content = Annotated[PageContentModel, Field(
    description="The latest content version of the page"
)]


class PageBase(BaseModel):
    slug: Slug
    title: Title
    summary: Optional[Summary]
    category: Category
    tags: Tags
    cover_image: Optional[CoverImage]
    published: Published
    locked: Locked


class PageDB(PageBase):
    author_id: AuthorID
    project_id: ProjectID
    view_count: ViewCount
    created_at: CreatedAt
    updated_at: UpdatedAt


class PageOut(PageBase):
    author: UserOut
    content: Content
    project: ProjectOut

