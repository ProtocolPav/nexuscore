from typing import Optional, Self

from src.database import Database
from src.models.project import ProjectModel, StatusModel, MembersModel, ContentModel

from pydantic import BaseModel, model_serializer


class ProjectView(BaseModel):
    project: ProjectModel
    members: MembersModel
    status: StatusModel
    content: ContentModel


