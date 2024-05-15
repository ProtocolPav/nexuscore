from datetime import datetime

from pydantic import NaiveDatetime, StringConstraints, BaseModel
from typing import Annotated, Optional


class ProjectModel(BaseModel):
    project_id: str
    name: str
    description: str
    coordinates: list[int]
    thread_id: Optional[int]
    accepted_on: Optional[NaiveDatetime]
    completed_on: Optional[NaiveDatetime]
    owner_id: int


class MembersModel(BaseModel):
    members: list[Optional[int]]


class ContentModel(BaseModel):
    content: Optional[str]
    content_since: Optional[NaiveDatetime]
    content_edited_by: Optional[int]


class StatusModel(BaseModel):
    status: str
    status_since: NaiveDatetime
