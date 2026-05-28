from fastapi import APIRouter, HTTPException, Request, Response, Security

from src.dependencies.auth import get_current_client
from src.dependencies.database import Database, db
from src.models.auth import TokenPayload
from src.models.projects import project, status, members
from src.models.projects.project import ProjectOut
from src.repositories.project import ProjectRepository

projects = APIRouter(prefix='/projects', tags=['Projects'])

projects_router = APIRouter(prefix='/guilds/me/projects', tags=['Projects'])
repo = ProjectRepository(db)

@projects_router.get('',)
async def list_projects(
        auth: TokenPayload = Security(get_current_client, scopes=['guilds.projects:read'])
) -> list[project.ProjectOut]:
    """
    Get a list of Projects
    """
    # TODO: add cursor pagination and filtering
    projects_models = await repo.fetch_all(auth.guild_id)

    return [ProjectOut(**p.model_dump()) for p in projects_models]


# @projects.post('', status_code=201)
# async def create_project(body: project.ProjectCreateModel) -> project.ProjectModel:
#     """
#     Creates a new project, inserts a status and content.
#     """
#     project_id = await project.ProjectModel.create(db, body)
#     project_model = await project.ProjectModel.fetch(db, project_id)
#
#     return project_model
#
#
# @projects.get('/{project_id}')
# async def get_project(project_id: str) -> project.ProjectModel:
#     """
#     Returns the project specified
#     """
#     project_model = await project.ProjectModel.fetch(db, project_id)
#
#     return project_model
#
#
# @projects.patch('/{project_id}')
# @projects.put('/{project_id}')
# async def update_project(project_id: str, body: project.ProjectUpdateModel) -> project.ProjectModel:
#     """
#     Update the project. Anything that you do not want to update can be left as `null`
#     """
#     model = await project.ProjectModel.fetch(db, project_id)
#     await model.update(db, body)
#
#     return model
#
#
# @projects.get('/{project_id}/status')
# async def get_project_status(project_id: str) -> status.StatusModel:
#     """
#     Returns the project's status
#     """
#     model = await status.StatusModel.fetch(db, project_id)
#
#     if not model:
#         raise HTTPException(status_code=404, detail="This project doesn't exist! Are you sure the ID is correct?")
#
#     return model
#
#
# @projects.post('/{project_id}/status', status_code=201)
# async def project_status(project_id: str, body: status.StatusCreateModel) -> Response:
#     """
#     New Project Status
#
#     Insert a new project status.
#     """
#     model = await status.StatusModel.fetch(db, project_id)
#     await model.insert_status(db, project_id, body.status)
#
#     return Response(status_code=201)
#
#
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
