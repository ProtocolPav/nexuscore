from typing import Optional
from src.models.user import UserModel, ProfileModel, PlaytimeReport
from src.models.project import ProjectModel, MembersModel, ContentModel, StatusModel

from sanic_ext import openapi


@openapi.component
class UserObject(UserModel):
    profile: Optional[ProfileModel]
    playtime: Optional[PlaytimeReport]


@openapi.component
class ProjectObject(ProjectModel, MembersModel, ContentModel, StatusModel):
    owner_id: UserModel | int
    members: list[Optional[UserModel | int]]
    content_edited_by: UserModel | int
