from typing import Literal

from sanic import Blueprint, Request, HTTPResponse
import sanic
from sanic_ext import openapi

from src.views.project import ProjectView
from src.models import project

from src.database import Database

project_blueprint = Blueprint("project_routes", url_prefix='/projects')


@project_blueprint.route('/', methods=['POST'])
@openapi.definition(body={'application/json': project.ProjectUpdateModel.model_json_schema()})
@openapi.response(status=200,
                  description='Return Project',
                  content={'application/json': ProjectView.view_schema()})
async def create_project(request: Request, db: Database):
    """
    Create Project

    Creates a new project, inserts a status and content.
    """
    model = project.ProjectUpdateModel(**request.json)

    try:
        project_id = await ProjectView.new(db, model)

        project_view = await ProjectView.build(db, project_id)
        return sanic.json(project_view.model_dump(), default=str)
    except TypeError:
        return HTTPResponse(status=500, body="Project already exists!")


@project_blueprint.route('/', methods=['GET'])
@openapi.parameter('users-as-object', bool)
@openapi.response(status=501)
async def get_all_projects(request: Request):
    """
    Get All Projects

    Get a list of Projects, their content, members and status.

    NOT IMPLEMENTED YET
    """
    ...


@project_blueprint.route('/<project_id:str>', methods=['GET'])
@openapi.response(status=200,
                  description='Return Project',
                  content={'application/json': ProjectView.view_schema()})
async def get_project(request: Request, db: Database, project_id: str):
    """
    Get Project

    Get the project, its content, members and current status.
    """
    project_view = await ProjectView.build(db, project_id)

    return sanic.json(project_view.model_dump(), default=str)


@project_blueprint.route('/<project_id:str>', methods=['PATCH'])
@openapi.body(content={'application/json': project.ProjectUpdateModel.model_json_schema()})
@openapi.response(status=200, description='Returns Bare Project',
                  content={'application/json': ProjectView.view_schema()})
async def update_project(request: Request, db: Database, project_id: str):
    """
    Update Project

    Update the project
    """
    model: project.ProjectModel = await project.ProjectModel.fetch(db, project_id)
    update_dict = {}

    for k, v in project.ProjectUpdateModel(**request.json).model_dump().items():
        if v is not None:
            update_dict[k] = v

    model = model.model_copy(update=update_dict)

    await model.update(db)

    return sanic.json(model.model_dump(), default=str)


@project_blueprint.route('/<project_id:str>/status', methods=['POST'])
@openapi.body(content={'application/json': {'status': str}})
@openapi.response(status=201, description='Successfully Added')
async def project_status(request: Request, db: Database, project_id: str):
    """
    New Project Status

    Insert a new project status.
    """
    model: project.StatusModel = await project.StatusModel.fetch(db, project_id)
    await model.insert_status(db, project_id, request.json['status'])

    return HTTPResponse(status=201)


@project_blueprint.route('/<project_id:str>/content', methods=['POST'])
@openapi.body(content={'application/json': {'content': str, 'edited_by': int}})
@openapi.response(status=201, description='Successfully Added')
async def project_content(request: Request, db: Database, project_id: str):
    """
    New Project Content

    Insert a new project content. `edited_by` is a ThornyID
    """
    model: project.ContentModel = await project.ContentModel.fetch(db, project_id)
    await model.insert_content(db, project_id, request.json['content'], request.json['edited_by'])

    return HTTPResponse(status=201)


@project_blueprint.route('/<project_id:str>/members', methods=['POST'])
@openapi.body(content={'application/json': {'members': list[int]}})
@openapi.response(status=201, description='Successfully Added')
async def update_members(request: Request, db: Database, project_id: str):
    """
    New Project Members

    Insert new members into the project. Must be ThornyIDs
    """
    model: project.MembersModel = await project.MembersModel.fetch(db, project_id)
    await model.insert_members(db, project_id, request.json['members'])

    return HTTPResponse(status=201)


@project_blueprint.route('/<project_id:str>/members', methods=['DELETE'])
@openapi.response(status=501, description="Not Implemented")
async def delete_members(request: Request, project_id: str):
    """
    Remove Project Members

    Remove existing project members from the project member list.

    NOT IMPLEMENTED
    """
    return HTTPResponse(status=501)
