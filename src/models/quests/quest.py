from datetime import datetime
from typing import Annotated, Optional

from pydantic import Field, BaseModel

from src.models.quests.objective import ObjectiveIn, ObjectiveOut, ObjectiveUpdate
from src.models.users.user import UserOut

QuestID = Annotated[int, Field(
    description="The Quest ID",
    examples=[732]
)]
GuildID = Annotated[int, Field(
    description="The Discord guild ID this quest is a part of",
)]
StartTime = Annotated[datetime, Field(
    description="The time that this quest begins to be able to be accepted",
)]
EndTime = Annotated[datetime, Field(
    description="The time that this quest will no longer be available to be accepted"
)]
Title = Annotated[str, Field(
    description="The quest title",
)]
Description = Annotated[str, Field(
    description="The quest description",
)]
CreatedBy = Annotated[int, Field(
    description="The Thorny ID that created this quest",
)]
Tags = Annotated[list[str], Field(
    description="A list of tags describing this quest",
)]
QuestType = Annotated[str, Field(
    description="The quest type",
    examples=["side"]
)]


class QuestBase(BaseModel):
    quest_id: QuestID
    start_time: StartTime
    end_time: EndTime
    title: Title
    description: Description
    tags: Tags
    quest_type: QuestType


class QuestDB(QuestBase):
    created_by: CreatedBy
    guild_id: GuildID


class QuestOut(QuestBase):
    created_by: UserOut
    objectives: list[ObjectiveOut]


class QuestIn(BaseModel):
    start_time: StartTime
    end_time: EndTime
    title: Title
    description: Description
    tags: Tags
    quest_type: QuestType
    created_by: CreatedBy
    objectives: list[ObjectiveIn]


class QuestUpdate(BaseModel):
    start_time: Optional[StartTime] = None
    end_time: Optional[EndTime] = None
    title: Optional[Title] = None
    description: Optional[Description] = None
    tags: Optional[Tags] = None
    quest_type: Optional[QuestType] = None
    created_by: Optional[CreatedBy] = None
    objectives: Optional[list[ObjectiveUpdate]] = None


class QuestQuery(BaseModel):
    creator_thorny_ids: Optional[list[int]] = Field(
        description="Filter by creator Thorny IDs",
        examples=[[1, 2021, 543]],
        default=None,
    )
    quest_types: Optional[list[str]] = Field(
        description="Filter by quest type",
        examples=[["side", "main", "minor"]],
        default=None,
    )
    time_start: Optional[datetime] = Field(
        description="The start time to filter by",
        examples=["2024-01-01 04:00:00+00:00"],
        default=None,
    )
    time_end: Optional[datetime] = Field(
        description="The end time to filter by",
        examples=["2024-12-31 04:00:00+00:00"],
        default=None,
    )
    active: Optional[bool] = Field(
        description="Filter by active quests",
        examples=[True],
        default=None,
    )
    future: Optional[bool] = Field(
        description="Filter by future quests",
        examples=[True],
        default=None,
    )
    past: Optional[bool] = Field(
        description="Filter by past quests",
        examples=[True],
        default=None,
    )
    page: Optional[int] = Field(
        description="The page to return. Default: 1",
        examples=[1],
        default=1,
    )
    page_size: Optional[int] = Field(
        description="The size of each page in items. Default: 100",
        examples=[10],
        default=100,
    )
