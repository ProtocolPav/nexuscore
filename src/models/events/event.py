from pydantic import Field, BaseModel
from typing_extensions import Annotated, Literal, Optional

from src.models.events.event_blocks import Blocks

EventID = Annotated[int, Field(
    description="The ID of the event",
    examples=[3422]
)]
GuildID = Annotated[int, Field(
    description="The guild this event is part of",
    examples=[123456789012345678]
)]
Slug = Annotated[str, Field(
    description="The url slug of the event",
    examples=["test-event"]
)]
Title = Annotated[str, Field(
    description="The title of the event",
    examples=["Test Event"]
)]
Description = Annotated[str, Field(
    description="A short description of the event",
    examples=["This is a test event"]
)]
ImageURL = Annotated[Optional[str], Field(
    description="The URL of the card image",
)]
StartTime = Annotated[str, Field(
    description="The start time of the event",
    examples=["2024-05-05 05:34:21.123456"]
)]
EndTime = Annotated[str, Field(
    description="The end time of the event",
    examples=["2024-05-05 05:34:21.123456"]
)]
Status = Annotated[Literal['draft', 'published', 'archived'], Field(
    description="The status of the event",
    examples=['draft']
)]
EventBlocks = Annotated[list[Blocks], Field(
    description="The blocks used for the event page display"
)]
CreatedAt = Annotated[str, Field(
    description="The time the event was created",
    examples=["2024-05-05 05:34:21.123456"]
)]
UpdatedAt = Annotated[str, Field(
    description="The time the event was last updated",
    examples=["2024-05-05 05:34:21.123456"]
)]


class EventBase(BaseModel):
    slug: Slug
    title: Title
    description: Description
    image_url: ImageURL
    start_time: StartTime
    end_time: EndTime
    status: Status
    blocks: EventBlocks


class EventDB(EventBase):
    event_id: EventID
    guild_id: GuildID
    created_at: CreatedAt
    updated_at: UpdatedAt


class EventOut(EventBase):
    pass


class EventIn(EventBase):
    pass


class EventUpdate(BaseModel):
    title: Optional[Title] = None
    description: Optional[Description] = None
    image_url: Optional[ImageURL] = None
    start_time: Optional[StartTime] = None
    end_time: Optional[EndTime] = None
    status: Optional[Status] = None
    blocks: Optional[EventBlocks] = None