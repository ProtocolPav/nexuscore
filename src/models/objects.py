from typing import Optional
from src.models.user import UserModel, ProfileModel, PlaytimeReport
from src.models.project import ProjectModel, MembersModel, ContentModel, StatusModel


class UserObject(UserModel):
    profile: Optional[ProfileModel]
    playtime: Optional[PlaytimeReport]


class ProjectObject(ProjectModel, MembersModel, ContentModel, StatusModel):
    owner_id: UserObject
    members: list[UserObject]
    content_edited_by: UserObject
