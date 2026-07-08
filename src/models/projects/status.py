from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field


class StatusEnum(str, Enum):
    active = "ongoing"
    inactive = "abandoned"
    pending = "pending"
    completed = "completed"


Status = Annotated[StatusEnum, Field(
    description="The project status",
    examples=['ongoing']
)]
StatusSince = Annotated[datetime, Field(
    description="When the status was last updated",
    examples=['2024-01-01']
)]

class StatusDB(BaseModel):
    status: Status
    since: StatusSince

class StatusOut(StatusDB):
    pass

class StatusIn(BaseModel):
    status: Status
