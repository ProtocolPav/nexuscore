from datetime import datetime
from typing import Annotated, Optional

from fastapi import HTTPException

from pydantic import Field, BaseModel

from src.models.quests.objective import ObjectiveCreateModel, ObjectiveModel, ObjectivesListModel
from src.models.users.user import UserOut

QuestID = Annotated[int, Field(
    description="The Quest ID",
    examples=[732]
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


class QuestOut(QuestBase):
    created_by: UserOut
    # objectives (out)


class QuestIn(BaseModel):
    start_time: StartTime
    end_time: EndTime
    title: Title
    description: Description
    tags: Tags
    quest_type: QuestType
    created_by: CreatedBy
    # objectives (in)


class QuestUpdate(BaseModel):
    start_time: StartTime
    end_time: EndTime
    title: Title
    description: Description
    tags: Tags
    quest_type: QuestType
    created_by: CreatedBy
    # objectives (update)


class QuestListModel(BaseList[QuestModel]):
    @classmethod
    async def fetch(cls,
                    db: Database,
                    time_start: str = None,
                    time_end: str = None,
                    creator_thorny_ids: list[str] = None,
                    quest_types: list[str] = None,
                    active: bool = None,
                    future: bool = None,
                    past: bool = None,
                    *args) -> "QuestListModel":
        # Build the query dynamically
        query_parts = ["SELECT * FROM quests_v3.quest q"]
        conditions = []
        params = []

        # Handle thorny_ids (OR condition using ANY)
        if creator_thorny_ids is not None and len(creator_thorny_ids) > 0:
            param_idx = len(params)
            conditions.append(f"q.created_by = ANY(${param_idx + 1}::int[])")

            thorny_ids_int = [int(x) for x in creator_thorny_ids]
            params.append(thorny_ids_int)

        # Handle interaction_types (OR condition using ANY)
        if quest_types is not None and len(quest_types) > 0:
            param_idx = len(params)
            conditions.append(f"q.quest_type = ANY(${param_idx + 1})")

            params.append(quest_types)

        # Handle time filtering
        if time_start is not None and time_end is not None:
            # Both start and end provided - filter between range
            param_idx = len(params)
            conditions.append(f"q.start_time >= ${param_idx + 1}::timestamptz AND q.end_time <= ${param_idx + 2}::timestamptz")
            params.extend([
                datetime.fromisoformat(time_start),
                datetime.fromisoformat(time_end)
            ])

        elif time_start is not None:
            # Only start time provided - filter after this time
            param_idx = len(params)
            conditions.append(f"q.start_time >= ${param_idx + 1}::timestamptz")
            params.append(datetime.fromisoformat(time_start))

        elif time_end is not None:
            # Only end time provided - filter before this time
            param_idx = len(params)
            conditions.append(f"q.end_time <= ${param_idx + 1}::timestamptz")
            params.append(datetime.fromisoformat(time_end))

        # Handle "active", "future" and "past" quests
        if active:
            conditions.append(f"NOW() BETWEEN q.start_time AND q.end_time")

        if future:
            conditions.append(f"q.start_time > NOW()")

        if past:
            conditions.append(f"q.end_time < NOW()")

        # Add WHERE clause if we have conditions
        if conditions:
            query_parts.append("WHERE")
            query_parts.append(" AND ".join(conditions))

        # Add ORDER BY clause
        query_parts.append("ORDER BY q.quest_id DESC")

        query = " ".join(query_parts)

        # Execute the query
        data = await db.pool.fetch(query, *params)

        quests: list[QuestModel] = []
        for quest in data:
            objectives = await ObjectivesListModel.fetch(db, quest['quest_id'])
            quests.append(QuestModel(**quest, objectives=objectives))

        return cls(root=quests)


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
