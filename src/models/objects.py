from typing import Optional
from src.models.user import UserModel, ProfileModel, PlaytimeSummary
from src.models.project import ProjectModel, MembersModel, ContentModel, StatusModel

from sanic_ext import openapi


@openapi.component
class UserObject(UserModel):
    profile: Optional[ProfileModel]
    playtime: Optional[PlaytimeSummary]


@openapi.component
class UserObjectWithNoOptionals(UserModel):
    profile: Optional[ProfileModel] = None
    playtime: Optional[PlaytimeSummary] = None


@openapi.component
class ProjectObject(ProjectModel, MembersModel, ContentModel, StatusModel):
    owner_id: UserObjectWithNoOptionals | int
    members: list[Optional[UserObjectWithNoOptionals | int]]
    content_edited_by: UserObjectWithNoOptionals | int
