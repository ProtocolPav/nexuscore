import asyncio

from fastapi import APIRouter, Security, status

from src.dependencies.auth import get_guild_client
from src.dependencies.database import db
from src.models.auth import TokenPayload

from src.models.projects.project import ProjectOut, ProjectIn, ProjectUpdate
from src.models.projects.status import StatusIn, StatusOut

from src.models.users.profile import ProfileOut
from src.models.users.user import UserOut

from src.repositories.project import ProjectRepository
from src.repositories.user import UserRepository

projects_router = APIRouter(prefix='/guilds/me/projects', tags=['Projects'])
repo = ProjectRepository(db)
user_repo = UserRepository(db)

@projects_router.get('')
async def list_projects(
        auth: TokenPayload = Security(get_guild_client, scopes=['guilds.projects:read'])
) -> list[ProjectOut]:
    """
    Get a list of Projects
    """
    # TODO: add cursor pagination and filtering
    projects = await repo.fetch_all(auth.guild_id)

    owner_ids = [p.owner_id for p in projects]
    project_ids = [p.project_id for p in projects]

    owners, profiles, statuses = await asyncio.gather(
        asyncio.gather(*[user_repo.fetch(auth.guild_id, oid) for oid in owner_ids]),
        asyncio.gather(*[user_repo.fetch_profile(auth.guild_id, oid) for oid in owner_ids]),
        asyncio.gather(*[repo.fetch_status(pid) for pid in project_ids])
    )

    return [
        ProjectOut(
            **p.model_dump(),
            owner=UserOut(
                **owner.model_dump(),
                profile=ProfileOut(**profile.model_dump())
            ),
            status=stat.status,
            status_since=stat.since
        )
        for p, owner, profile, stat in zip(projects, owners, profiles, statuses)
    ]


@projects_router.post('', status_code=status.HTTP_201_CREATED)
async def create_project(
        body: ProjectIn,
        auth: TokenPayload = Security(get_guild_client, scopes=['guilds.projects:write']),
) -> ProjectOut:
    """
    Creates a new project with a status, members and content.
    """
    # TODO: there is no guild_id check for project creation
    proj = await repo.create(body)

    owner, profile, stat = await asyncio.gather(
        user_repo.fetch(auth.guild_id, proj.owner_id),
        user_repo.fetch_profile(auth.guild_id, proj.owner_id),
        repo.fetch_status(proj.project_id)
    )

    return ProjectOut(
        **proj.model_dump(),
        owner=UserOut(
            **owner.model_dump(),
            profile=ProfileOut(**profile.model_dump())
        ),
        status=stat.status,
        status_since=stat.since
    )


@projects_router.get('/{project_id}')
async def get_project(
        project_id: str,
        auth: TokenPayload = Security(get_guild_client, scopes=['guilds.projects:read']),
) -> ProjectOut:
    """
    Returns the project specified
    """
    # TODO: add on guild_id as secondary check
    proj = await repo.fetch(project_id)

    owner, profile, stat = await asyncio.gather(
        user_repo.fetch(auth.guild_id, proj.owner_id),
        user_repo.fetch_profile(auth.guild_id, proj.owner_id),
        repo.fetch_status(proj.project_id)
    )

    return ProjectOut(
        **proj.model_dump(),
        owner=UserOut(
            **owner.model_dump(),
            profile=ProfileOut(**profile.model_dump())
        ),
        status=stat.status,
        status_since=stat.since
    )


@projects_router.put('/{project_id}')
@projects_router.patch('/{project_id}')
async def update_project(
        project_id: str,
        body: ProjectUpdate,
        auth: TokenPayload = Security(get_guild_client, scopes=['guilds.projects:write']),
) -> ProjectOut:
    """
    Update the project.
    """
    proj = await repo.update(project_id, body)

    owner, profile, stat = await asyncio.gather(
        user_repo.fetch(auth.guild_id, proj.owner_id),
        user_repo.fetch_profile(auth.guild_id, proj.owner_id),
        repo.fetch_status(proj.project_id)
    )

    return ProjectOut(
        **proj.model_dump(),
        owner=UserOut(
            **owner.model_dump(),
            profile=ProfileOut(**profile.model_dump())
        ),
        status=stat.status,
        status_since=stat.since
    )


@projects_router.get('/{project_id}/status', deprecated=True)
async def get_project_status(
        project_id: str,
        auth: TokenPayload = Security(get_guild_client, scopes=['guilds.projects:read']),
) -> StatusOut:
    """
    Returns the project's status
    """
    stat = await repo.fetch_status(project_id)

    return StatusOut(**stat.model_dump())


@projects_router.post('/{project_id}/status', status_code=status.HTTP_201_CREATED)
async def create_project_status(
        project_id: str,
        body: StatusIn
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
