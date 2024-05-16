from pydantic import NaiveDatetime, BaseModel
from typing import Optional, Literal

from sanic_ext import openapi


@openapi.component
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


@openapi.component
class MembersModel(BaseModel):
    members: list[Optional[int]]


@openapi.component
class ContentModel(BaseModel):
    content: Optional[str]
    content_since: Optional[NaiveDatetime]
    content_edited_by: Optional[int]


@openapi.component
class StatusModel(BaseModel):
    status: Literal["pending", "ongoing", "abandoned", "completed"]
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
