from typing import Optional
from src.models.user import UserModel, ProfileModel, PlaytimeReport
from src.models.project import ProjectModel, MembersModel, ContentModel, StatusModel


class UserObject(UserModel):
    profile: Optional[ProfileModel] = None
    playtime: Optional[PlaytimeReport] = None


class ProjectObject(ProjectModel, MembersModel, ContentModel, StatusModel):
    owner_id: UserObject | int = 0
    members: list[Optional[UserObject | int]] = None
    content_edited_by: UserObject | int = 0
