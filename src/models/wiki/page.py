from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field
from typing_extensions import Optional, Annotated

from src.models.projects.project import ProjectOut
from src.models.users.user import UserOut
from src.models.wiki.content import ContentIn, ContentOut


PageID = Annotated[int, Field(
    description="The page ID",
    examples=[432]
)]
Slug = Annotated[str, Field(
    description="The URL-safe slug ID of the page",
    examples=["getting_started_guide"]
)]
ProjectID = Annotated[str, Field(
    description="The linked project ID for this wiki page",
    examples=["my-project"]
)]
AuthorID = Annotated[int, Field(
    description="The ThornyID of the page author",
    examples=[12]
)]
GuildID = Annotated[int, Field(
    description="The Discord guild ID this page is registered in.",
    examples=[123456789012345678]
)]
Title = Annotated[str, Field(
    description="The title of the wiki page",
    examples=["Getting Started Guide"]
)]
Summary = Annotated[str, Field(
    description="A short summary of the page",
    examples=["An introduction to the server"]
)]
Category = Annotated[str, Field(
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


class PageBase(BaseModel):
    slug: Slug
    title: Title
    summary: Optional[Summary]
    category: Category
    tags: Tags
    cover_image: Optional[CoverImage]
    published: Published
    locked: Locked
    view_count: ViewCount
    created_at: CreatedAt
    updated_at: UpdatedAt


class PageDB(PageBase):
    page_id: PageID
    author_id: AuthorID
    guild_id: GuildID
    project_id: Optional[ProjectID]


class PageOut(PageBase):
    author: UserOut
    project: Optional[ProjectOut] = None
    content: ContentOut


class PageIn(BaseModel):
    author_id: AuthorID
    project_id: Optional[ProjectID]
    slug: Slug
    title: Title
    summary: Optional[Summary]
    category: Category
    tags: Tags
    cover_image: Optional[CoverImage]
    published: Published
    locked: Locked
    content: ContentIn


class PageUpdate(BaseModel):
    title: Optional[Title] = None
    project_id: Optional[ProjectID] = None
    summary: Optional[Summary] = None
    category: Optional[Category] = None
    tags: Optional[Tags] = None
    cover_image: Optional[CoverImage] = None
    published: Optional[Published] = None
    locked: Optional[Locked] = None
    content: Optional[ContentIn] = None


class PageQuery(BaseModel):
    published: Optional[bool] = Field(
        description="Filter by published status",
        examples=[True],
        default=None
    )
    category: Optional[str] = Field(
        description="Filter by category",
        examples=["guides"],
        default=None
    )
    tags: Optional[list[str]] = Field(
        description="Filter by tags",
        examples=[["python", "django"]],
        default=[]
    )
    search: Optional[str] = Field(
        description="Fuzzy search by page title (summary and content comes later)",
        examples=["python"],
        default=None
    )
    sort_by: Optional[Literal["created_at", "updated_at", "title"]] = Field(
        description="Sort by field",
        examples=["created_at"],
        default=None
    )
    sort_order: Optional[Literal["asc", "desc"]] = Field(
        description="Sort order",
        examples=["asc"],
        default=None
    )
    page: Optional[int] = Field(
        description="The page number to return",
        examples=[1],
        default=1
    )
    page_size: Optional[int] = Field(
        description="The number of items per page",
        examples=[10],
        default=10
    )
