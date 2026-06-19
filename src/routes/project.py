from fastapi import APIRouter, Depends, Security, status

from src.dependencies.auth import Scope, get_guild_client
from src.dependencies.repositories import get_project_repo
from src.models.auth import TokenPayload

from src.models.projects.project import ProjectOut, ProjectIn, ProjectUpdate
from src.models.projects.status import StatusIn, StatusOut

from src.repositories.project import ProjectRepository

projects_router = APIRouter(prefix='/guilds/me/projects', tags=['Projects'])

@projects_router.get('')
async def list_projects(
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_PROJECTS_READ]),
        repo: ProjectRepository = Depends(get_project_repo),
) -> list[ProjectOut]:
    """
    Get a list of Projects
    """
    # TODO: add cursor pagination and filtering
    projects = await repo.fetch_all(auth.guild_id)

    return projects


@projects_router.post('', status_code=status.HTTP_201_CREATED)
async def create_project(
        body: ProjectIn,
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_PROJECTS_WRITE]),
        repo: ProjectRepository = Depends(get_project_repo),
) -> ProjectOut:
    """
    Creates a new project with a status, members and content.
    """
    proj = await repo.create(auth.guild_id, body)

    return proj


@projects_router.get('/{project_id}')
async def get_project(
        project_id: str,
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_PROJECTS_READ]),
        repo: ProjectRepository = Depends(get_project_repo),
) -> ProjectOut:
    """
    Returns the project specified
    """
    proj = await repo.fetch(auth.guild_id, project_id)

    return proj


@projects_router.put('/{project_id}')
@projects_router.patch('/{project_id}')
async def update_project(
        project_id: str,
        body: ProjectUpdate,
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_PROJECTS_WRITE]),
        repo: ProjectRepository = Depends(get_project_repo),
) -> ProjectOut:
    """
    Update the project.
    """
    proj = await repo.update(auth.guild_id, project_id, body)

    return proj


@projects_router.get('/{project_id}/status', deprecated=True)
async def get_project_status(
        project_id: str,
        _: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_PROJECTS_READ]),
        repo: ProjectRepository = Depends(get_project_repo),
) -> StatusOut:
    """
    Returns the project's status
    """
    stat = await repo.fetch_status(project_id)

    return StatusOut(**stat.model_dump())


@projects_router.post('/{project_id}/status', status_code=status.HTTP_201_CREATED)
async def create_project_status(
        project_id: str,
        body: StatusIn,
        _: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_PROJECTS_WRITE]),
        repo: ProjectRepository = Depends(get_project_repo),
) -> StatusOut:
    """
    New Project Status

    Insert a new project status.
    """
    stat = await repo.create_status(project_id, body)

    return StatusOut(**stat.model_dump())


# @projects.get('/{project_id}/members')
# async def get_project_members(project_id: str) -> members.MembersListModel:
#     """
#     Returns the project's Members
#     """
#     model = await members.MembersListModel.fetch(db, project_id)
#
#     if not model:
#         raise HTTPException(status_code=404, detail="This project doesn't exist! Are you sure the ID is correct?")
#
#     return model
#
#
# @projects.post('/{project_id}/members', deprecated=True)
# async def update_members(project_id: str) -> Response:
#     """
#     Insert new members into the project. Must be ThornyIDs
#     """
#     return Response(status_code=501)
