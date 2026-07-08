from datetime import datetime
from typing import Annotated, Literal, Optional

from pydantic import Field, BaseModel

from src.dependencies.database import Database
from src.models.quests.objective_progress import ObjectiveProgressOut, ObjectiveProgressUpdate

ProgressID = Annotated[int, Field(
    description="The ID of the progress instance of the quest",
    examples=[54]
)]
ThornyID = Annotated[int, Field(
    description="The ThornyID of the user",
    examples=[34]
)]
QuestID = Annotated[int, Field(
    description="The ID of the quest",
    examples=[453]
)]
AcceptTime = Annotated[datetime, Field(
    description="The time that the user accepted this quest",
    examples=['2024-05-05 05:34:21.123456']
)]
StartTime = Annotated[Optional[datetime], Field(
    description="The time the user actually started to complete the quest",
    examples=['2024-05-05 05:34:21.123456']
)]
EndTime = Annotated[Optional[datetime], Field(
    description="The time the user ended the quest, either by failing or completing it",
    examples=['2024-05-05 05:34:21.123456']
)]
Status = Annotated[Literal['active', 'pending', 'completed', 'failed'], Field(
    description="The status of the quest",
    examples=['active']
)]


class QuestProgressDB(BaseModel):
    progress_id: ProgressID
    thorny_id: ThornyID
    quest_id: QuestID
    accept_time: AcceptTime
    start_time: Optional[StartTime]
    end_time: Optional[EndTime]
    status: Status


class QuestProgressOut(QuestProgressDB):
    objectives: list[ObjectiveProgressOut]


class QuestProgressIn(BaseModel):
    thorny_id: ThornyID
    quest_id: QuestID


class QuestProgressUpdate(BaseModel):
    start_time: Optional[StartTime] = None
    end_time: Optional[EndTime] = None
    status: Optional[Status] = None
    objectives: Optional[list[ObjectiveProgressUpdate]] = []
