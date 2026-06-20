import json
from datetime import datetime
from typing import Annotated, Literal, Optional

from pydantic import Field, model_validator, BaseModel

from src.models.quests.objective_customization.progress import CustomizationProgress
from src.models.quests.objective_targets.progress import TargetProgress


ProgressID = Annotated[int, Field(
    description="The quest progress ID",
    examples=[453]
)]
ObjectiveID = Annotated[int, Field(
    description="The objective ID",
    examples=[22]
)]
StartTime = Annotated[datetime, Field(
    description="The time that this objective was started on",
    examples=['2024-05-05T05:34:21Z']
)]
EndTime = Annotated[datetime, Field(
    description="The time that this objective was completed",
    examples=['2024-05-05T05:34:21Z']
)]
ProgressStatus = Annotated[Literal['active', 'pending', 'completed', 'failed'], Field(
    description="The status of this objective",
    examples=['active']
)]
TargetProgressList = Annotated[list[TargetProgress], Field(
    description="List of each objective target's progress"
)]
CustomizationProgressDict = Annotated[CustomizationProgress, Field(
    description="Specific customization info to track"
)]


class ObjectiveProgressDB(BaseModel):
    progress_id: ProgressID
    objective_id: ObjectiveID
    start_time: Optional[StartTime]
    end_time: Optional[EndTime]
    status: ProgressStatus
    target_progress: TargetProgressList
    customization_progress: CustomizationProgressDict

    @model_validator(mode='before')
    @classmethod
    def pre_process_json(cls, data):
        if isinstance(data.get('target_progress'), str):
            data['target_progress'] = json.loads(data['target_progress'])

        if isinstance(data.get('customization_progress'), str):
            data['customization_progress'] = json.loads(data['customization_progress'])

        return data


class ObjectiveProgressOut(ObjectiveProgressDB):
    pass


class ObjectiveProgressIn(BaseModel):
    target_progress: TargetProgressList
    customization_progress: CustomizationProgressDict


class ObjectiveProgressUpdate(BaseModel):
    objective_id: Optional[ObjectiveID] = None
    start_time: Optional[StartTime] = None
    end_time: Optional[EndTime] = None
    status: Optional[ProgressStatus] = None
    target_progress: Optional[TargetProgressList] = None
    customization_progress: Optional[CustomizationProgressDict] = None
