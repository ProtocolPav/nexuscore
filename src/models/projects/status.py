from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field
from typing_extensions import Optional, Literal

from src.dependencies.database import Database
from fastapi import HTTPException


class StatusEnum(str, Enum):
    active = "ongoing"
    inactive = "abandoned"
    pending = "pending"
    completed = "completed"


Status = Annotated[StatusEnum, Field(
    description="The project status",
)]
StatusSince = Annotated[datetime, Field(
    description="When the status was last updated",
)]

class StatusDB(BaseModel):
    status: Status
    since: StatusSince

class StatusOut(StatusDB):
    pass

class StatusIn(BaseModel):
    status: Status


class StatusModel(BaseModel):
    status: Literal["pending", "ongoing", "abandoned", "completed"]
    status_since: datetime

    @classmethod
    async def fetch(cls, db: Database, project_id: str) -> Optional["StatusModel"]:
        data = await db.pool.fetchrow("""
                                       SELECT status, since AS status_since
                                       FROM projects.status
                                       WHERE project_id = $1
                                       ORDER BY status_since DESC
                                       """,
                                      project_id)

        return cls(**data) if data else None

    @staticmethod
    async def insert_status(db: Database, project_id: str, status: Literal["pending", "ongoing", "abandoned", "completed"]):
        if status in ['pending', 'ongoing', 'abandoned', 'completed']:
            await db.pool.execute("""
                                   INSERT INTO projects.status(project_id, status, since)
                                   VALUES($1, $2, NOW())
                                   """,
                                  project_id, status)
        else:
            raise HTTPException(status_code=400, detail="Invalid status")

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


class StatusCreateModel(BaseModel):
    status: Literal["pending", "ongoing", "abandoned", "completed"]

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")
