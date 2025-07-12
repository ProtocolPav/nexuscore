from sanic import Blueprint, Request, HTTPResponse
import sanic
from sanic.views import HTTPMethodView
from sanic_ext import openapi, validate
from sanic_ext.extensions.openapi.definitions import RequestBody, Response

from src.database import Database
from src.models.projects import project, status, members, pin
from src.utils.errors import BadRequest400, NotFound404

project_blueprint = Blueprint("projects", url_prefix='/projects')

@project_blueprint.route('/', methods=['GET'])
@openapi.definition(response=[
    Response(project.ProjectsListModel.doc_schema(), 200)
])
async def get_all_projects(request: Request, db: Database):
    """
    Get All Projects

    Get a list of Projects
    """
    projects_model = await project.ProjectsListModel.fetch(db)

    return sanic.json(projects_model.model_dump(), default=str)


@project_blueprint.route('/', methods=['POST'])
@openapi.definition(body=RequestBody(project.ProjectCreateModel.doc_schema()),
                    response=[
                        Response(project.ProjectModel.doc_schema(), 201),
                        Response(BadRequest400, 400)
                    ])
@validate(json=project.ProjectCreateModel)
async def create_project(request: Request, db: Database, body: project.ProjectCreateModel):
    """
    Create Project

    Creates a new project, inserts a status and content.
    """
    project_id = await project.ProjectModel.create(db, body)
    project_model = await project.ProjectModel.fetch(db, project_id)

    return sanic.json(status=201, body=project_model.model_dump(), default=str)


class PinsRoute(HTTPMethodView):
    @openapi.response(status=200,
                      description="Success",
                      content={'application/json': pin.PinsListModel.doc_schema()})
    async def get(self, request: Request, db: Database):
        """
        Get All Pins

        Get a list of all Pins
        """
        all_pins = await pin.PinsListModel.fetch(db)

        return sanic.json(all_pins.model_dump(), default=str)

    @openapi.definition(body={'application/json': pin.PinCreateModel.doc_schema()})
    @openapi.response(status=200,
                      description='Success',
                      content={'application/json': pin.PinModel.doc_schema()})
    @validate(json=pin.PinCreateModel)
    async def post(self, request: Request, db: Database, body: pin.PinCreateModel):
        """
        Create Pin

        Creates a new pin
        """
        pin_id = await pin.PinModel.new(db, body)

        model = await pin.PinModel.fetch(db, pin_id)
        return sanic.json(model.model_dump(), default=str)

project_blueprint.add_route(PinsRoute.as_view(), '/pins')


@project_blueprint.route('/<project_id:str>', methods=['GET'])
@openapi.definition(response=[
    Response(project.ProjectModel.doc_schema(), 200),
    Response(NotFound404, 404)
])
async def get_project(request: Request, db: Database, project_id: str):
    """
    Get Project

    Returns the project specified
    """
    project_model = await project.ProjectModel.fetch(db, project_id)

    return sanic.json(project_model.model_dump(), default=str)


@project_blueprint.route('/<project_id:str>', methods=['PATCH', 'PUT'])
@openapi.definition(body=RequestBody(project.ProjectUpdateModel.doc_schema()),
                    response=[
                        Response(project.ProjectModel.doc_schema(), 200),
                        Response(BadRequest400, 400),
                        Response(NotFound404, 404)
                    ])
@validate(json=project.ProjectUpdateModel)
async def update_project(request: Request, db: Database, project_id: str, body: project.ProjectUpdateModel):
    """
    Update Project

    Update the project. Anything that you do not want to update can be left as `null`
    """
    model = await project.ProjectModel.fetch(db, project_id)
    await model.update(db, body)

    return sanic.json(model.model_dump(), default=str)


@project_blueprint.route('/<project_id:str>/status', methods=['GET'])
@openapi.response(status=200,
                  description='Success',
                  content={'application/json': status.StatusModel.doc_schema()})
@openapi.response(status=404, description="Project does not exist")
async def get_project_status(request: Request, db: Database, project_id: str):
    """
    Get Project Status

    Returns the project's status
    """
    model = await status.StatusModel.fetch(db, project_id)

    if not model:
        raise sanic.NotFound("This project doesn't exist! Are you sure the ID is correct?")

    return sanic.json(model.model_dump(), default=str)


@project_blueprint.route('/<project_id:str>/status', methods=['POST'])
@openapi.body(content={'application/json': status.StatusCreateModel.doc_schema()})
@openapi.response(status=201, description='Successfully Added')
@validate(json=status.StatusCreateModel)
async def project_status(request: Request, db: Database, project_id: str, body: status.StatusCreateModel):
    """
    New Project Status

    Insert a new project status.
    """
    model = await status.StatusModel.fetch(db, project_id)
    await model.insert_status(db, project_id, body.status)

    return sanic.HTTPResponse(status=201)


@project_blueprint.route('/<project_id:str>/members', methods=['GET'])
@openapi.response(status=200,
                  description='Success',
                  content={'application/json': members.MembersListModel.doc_schema()})
@openapi.response(status=404, description="Project does not exist")
async def get_project_members(request: Request, db: Database, project_id: str):
    """
    Get Project Members

    Returns the project's Members
    """
    model = await members.MembersListModel.fetch(db, project_id)

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
    model = await members.MembersListModel.fetch(db, project_id)
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
