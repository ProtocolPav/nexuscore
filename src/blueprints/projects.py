import re
from typing import Literal

from sanic import Blueprint, Request, HTTPResponse
import sanic
from sanic.views import HTTPMethodView
from sanic_ext import openapi, validate

from src.database import Database
from src.models import projects

project_blueprint = Blueprint("projects", url_prefix='/projects')

class ProjectsBaseRoute(HTTPMethodView):
    @openapi.response(status=200,
                      description="Success",
                      content={'application/json': projects.AllProjectsModel.doc_schema()})
    async def get(self, request: Request, db: Database):
        """
        Get All Projects

        Get a list of Projects
        """
        all_projects = await projects.ProjectModel.fetch_all(db)

        return sanic.json(projects.AllProjectsModel(**{'projects': all_projects}).model_dump(), default=str)

    @openapi.definition(body={'application/json': projects.ProjectCreateModel.doc_schema()})
    @openapi.response(status=200,
                      description='Success',
                      content={'application/json': projects.ProjectModel.doc_schema()})
    @validate(json=projects.ProjectCreateModel)
    async def post(self, request: Request, db: Database, body: projects.ProjectCreateModel):
        """
        Create Project

        Creates a new project, inserts a status and content.
        """
        project_id = re.sub(r'[^a-z0-9_]', '', body.name.lower().replace(' ', '_'))

        model = await projects.ProjectModel.fetch(db, project_id)

        if not model:
            await projects.ProjectModel.new(db, project_id, body)
            model = await projects.ProjectModel.fetch(db, project_id)
            return sanic.json(model.model_dump(), default=str)
        else:
            raise sanic.SanicException(status_code=500, message="This project already exists!")

project_blueprint.add_route(ProjectsBaseRoute.as_view(), '/')


class PinsRoute(HTTPMethodView):
    @openapi.response(status=200,
                      description="Success",
                      content={'application/json': projects.PinsListModel.doc_schema()})
    async def get(self, request: Request, db: Database):
        """
        Get All Pins

        Get a list of all Pins
        """
        all_pins = await projects.PinsListModel.fetch(db)

        return sanic.json(all_pins.model_dump(), default=str)

    @openapi.definition(body={'application/json': projects.PinCreateModel.doc_schema()})
    @openapi.response(status=200,
                      description='Success',
                      content={'application/json': projects.PinModel.doc_schema()})
    @validate(json=projects.PinCreateModel)
    async def post(self, request: Request, db: Database, body: projects.PinCreateModel):
        """
        Create Pin

        Creates a new pin
        """
        pin_id = await projects.PinModel.new(db, body)

        model = await projects.PinModel.fetch(db, pin_id)
        return sanic.json(model.model_dump(), default=str)

project_blueprint.add_route(PinsRoute.as_view(), '/pins')


@project_blueprint.route('/<project_id:str>', methods=['GET'])
@openapi.response(status=200,
                  description='Success',
                  content={'application/json': projects.ProjectModel.doc_schema()})
@openapi.response(status=404, description="Project does not exist")
async def get_project(request: Request, db: Database, project_id: str):
    """
    Get Project

    Returns the project specified
    """
    model = await projects.ProjectModel.fetch(db, project_id)

    if not model:
        raise sanic.NotFound("This project doesn't exist! Are you sure the ID is correct?")

    return sanic.json(model.model_dump(), default=str)


@project_blueprint.route('/<project_id:str>', methods=['PATCH', 'PUT'])
@openapi.body(content={'application/json': projects.ProjectUpdateModel.doc_schema()})
@openapi.response(status=200,
                  description='Success',
                  content={'application/json': projects.ProjectModel.doc_schema()})
@openapi.response(status=404, description="Project does not exist")
@validate(json=projects.ProjectUpdateModel)
async def update_project(request: Request, db: Database, project_id: str, body: projects.ProjectUpdateModel):
    """
    Update Project

    Update the project. Anything that you do not want to update can be left as `null`
    """
    model = await projects.ProjectModel.fetch(db, project_id)

    if not model:
        raise sanic.NotFound("This project doesn't exist! Are you sure the ID is correct?")

    update_dict = {}

    for k, v in body.model_dump().items():
        if v is not None:
            update_dict[k] = v

    model = model.model_copy(update=update_dict)

    await model.update(db)

    return sanic.json(model.model_dump(), default=str)


@project_blueprint.route('/<project_id:str>/status', methods=['GET'])
@openapi.response(status=200,
                  description='Success',
                  content={'application/json': projects.StatusModel.doc_schema()})
@openapi.response(status=404, description="Project does not exist")
async def get_project_status(request: Request, db: Database, project_id: str):
    """
    Get Project Status

    Returns the project's status
    """
    model = await projects.StatusModel.fetch(db, project_id)

    if not model:
        raise sanic.NotFound("This project doesn't exist! Are you sure the ID is correct?")

    return sanic.json(model.model_dump(), default=str)


@project_blueprint.route('/<project_id:str>/status', methods=['POST'])
@openapi.body(content={'application/json': projects.StatusCreateModel.doc_schema()})
@openapi.response(status=201, description='Successfully Added')
@validate(json=projects.StatusCreateModel)
async def project_status(request: Request, db: Database, project_id: str, body: projects.StatusCreateModel):
    """
    New Project Status

    Insert a new project status.
    """
    model = await projects.StatusModel.fetch(db, project_id)
    await model.insert_status(db, project_id, body.status)

    return sanic.HTTPResponse(status=201)


@project_blueprint.route('/<project_id:str>/content', methods=['GET'])
@openapi.response(status=404, description="Project Content is deprecated")
async def get_project_content(request: Request, db: Database, project_id: str):
    """
    Get Project Content

    Project Content is deprecated
    """
    raise sanic.NotFound("Project Content is deprecated.")


@project_blueprint.route('/<project_id:str>/content', methods=['POST'])
@openapi.response(status=404, description="Project Content is deprecated")
async def project_content(request: Request, db: Database, project_id: str):
    """
    New Project Content

    Project Content is deprecated
    """
    raise sanic.NotFound("Project Content is deprecated.")


@project_blueprint.route('/<project_id:str>/members', methods=['GET'])
@openapi.response(status=200,
                  description='Success',
                  content={'application/json': projects.MembersModel.doc_schema()})
@openapi.response(status=404, description="Project does not exist")
async def get_project_members(request: Request, db: Database, project_id: str):
    """
    Get Project Members

    Returns the project's Members
    """
    model = await projects.MembersModel.fetch(db, project_id)

    if not model:
        raise sanic.NotFound("This project doesn't exist! Are you sure the ID is correct?")

    return sanic.json(model.model_dump(), default=str)


@project_blueprint.route('/<project_id:str>/members', methods=['POST'])
@openapi.body(content={'application/json': {'members': list[int]}})
@openapi.response(status=201, description='Successfully Added')
async def update_members(request: Request, db: Database, project_id: str):
    """
    New Project Members

    Insert new members into the project. Must be ThornyIDs
    """
    model = await projects.MembersModel.fetch(db, project_id)
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
