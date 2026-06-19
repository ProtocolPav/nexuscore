from datetime import date

from pydantic import Field, BaseModel
from typing_extensions import Annotated, Optional

from src.models.projects.status import Status, StatusSince
from src.models.users import user


ProjectID = Annotated[str, Field(
    description="The string ID of the project",
    examples=['my_project']
)]
ThreadID = Annotated[int, Field(
    description="The discord thread ID of the project",
)]
GuildID = Annotated[int, Field(
    description="The discord guild ID this project is a part of",
)]
ProjectName = Annotated[str, Field(
    description="The name of the project",
    examples=['My Project']
)]
ProjectDescription = Annotated[str, Field(
    description="A short description of the project",
    examples=['This project will have houses']
)]
ProjectCoordinates = Annotated[list[int], Field(
    description="The coordinates of the project",
    examples=[[132, 65, 33]]
)]
ProjectOwnerID = Annotated[int, Field(
    description="The project owner ID",
)]
ProjectDimension = Annotated[str, Field(
    description="The dimension of the project",
)]
ProjectPinID = Annotated[int, Field(
    description="If set, the project will not show up as a project but rather as a pin.",
)]
StartedOn = Annotated[date, Field(
    description="The date the project was started on",
)]
CompletedOn = Annotated[date, Field(
    description="The date the project was completed on",
)]
Owner = Annotated[user.UserOut, Field(
    description="The owner of the project, in the form of a User object",
)]


class ProjectBase(BaseModel):
    project_id: ProjectID
    guild_id: GuildID
    name: ProjectName
    thread_id: Optional[ThreadID]
    coordinates: ProjectCoordinates
    description: ProjectDescription
    completed_on: Optional[CompletedOn]
    pin_id: Optional[ProjectPinID]
    dimension: ProjectDimension
    started_on: Optional[StartedOn]

class ProjectDB(ProjectBase):
    owner_id: ProjectOwnerID

class ProjectOut(ProjectBase):
    status: Status
    status_since: StatusSince
    owner: Owner

class ProjectIn(BaseModel):
    owner_id: ProjectOwnerID
    guild_id: GuildID
    coordinates: ProjectCoordinates
    description: ProjectDescription
    dimension: ProjectDimension
    name: ProjectName
    pin_id: Optional[ProjectPinID]

class ProjectUpdate(BaseModel):
    guild_id: Optional[GuildID] = None
    name: Optional[ProjectName] = None
    thread_id: Optional[ThreadID] = None
    coordinates: Optional[ProjectCoordinates] = None
    description: Optional[ProjectDescription] = None
    completed_on: Optional[CompletedOn] = None
    pin_id: Optional[ProjectPinID] = None
    dimension: Optional[ProjectDimension] = None
    owner_id: Optional[ProjectOwnerID] = None
