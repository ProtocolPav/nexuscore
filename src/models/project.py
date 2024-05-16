from pydantic import NaiveDatetime, BaseModel
from typing import Optional


class ProjectModel(BaseModel):
    project_id: str
    name: str
    description: str
    coordinates_x: int
    coordinates_y: int
    coordinates_z: int
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


class ProjectUpdateModel(ProjectModel):
    project_id: str = None
    name: str = None
    description: str = None
    coordinates_x: int = None
    coordinates_y: int = None
    coordinates_z: int = None
    thread_id: Optional[int] = None
    accepted_on: Optional[NaiveDatetime] = None
    completed_on: Optional[NaiveDatetime] = None
    owner_id: int = None
