from typing import Optional
from src.models.user import UserModel, ProfileModel, PlaytimeReport, UserProjectReport


class UserObject(UserModel):
    profile: Optional[ProfileModel]
    playtime: Optional[PlaytimeReport]
    projects: Optional[UserProjectReport]
