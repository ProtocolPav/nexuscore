from sanic import Blueprint, Request
from sanic import json as sanicjson
from sanic_ext import openapi

from src import model_factory
from src.models.objects import ProjectObject

project_blueprint = Blueprint("project_routes", url_prefix='/projects')


@project_blueprint.route('/', methods=['POST'])
async def create_project(request: Request):
    ...


@project_blueprint.route('/', methods=['GET'])
@openapi.parameter('users_as_object', bool)
async def get_all_projects(request: Request):
    """
    Get All Projects

    Get all projects as a list of objects.

    By default, the `lead` and `members` of the project are
    returned as ThornyIDs, however you can specify in the URL
    parameter to get a bare-bones User object for each member instead.
    """
    ...


@project_blueprint.route('/<project_id:str>', methods=['GET'])
@openapi.parameter('users_as_object', bool)
async def get_project(request: Request, project_id: str):
    """
    Get Project

    Get the project and its info based on the ID provided.
    Project IDs are strings.

    By default, the `lead` and `members` of the project are
    returned as ThornyIDs, however you can specify in the URL
    parameter to get a bare-bones User object for each member instead.
    """
    project_model = await model_factory.ProjectFactory.build_project_model(project_id)
    content_model = await model_factory.ProjectFactory.build_content_model(project_id)
    status_model = await model_factory.ProjectFactory.build_status_model(project_id)
    members_model = await model_factory.ProjectFactory.build_members_model(project_id)

    if request.args.get('users_as_object', False):
        members_dict = {'members': []}
        for member in members_model['members']:
            members_dict['members'].append(await model_factory.UserFactory.build_user_model(member))

        project_model['owner_id'] = await model_factory.UserFactory.build_user_model(project_model['owner_id'])

        members_model = members_dict

    return sanicjson(project_model | content_model | status_model | members_model, default=str)


@project_blueprint.route('/<project_id:str>', methods=['PATCH'])
@openapi.body(content={'application/json': {}})
async def update_project(request: Request, project_id: str):
    """
    Update Project

    Update the project. You can include only the fields
    that you are updating in the request body.
    """
    ...


@project_blueprint.route('/<project_id:str>/status', methods=['PATCH'])
async def project_status(request: Request, project_id: str):
    ...


@project_blueprint.route('/<project_id:str>/content', methods=['PATCH'])
async def project_content(request: Request, project_id: str):
    ...


@project_blueprint.route('/<project_id:str>/members', methods=['PATCH'])
async def update_members(request: Request, project_id: str):
    ...


@project_blueprint.route('/<project_id:str>/thread', methods=['PATCH'])
async def update_thread(request: Request, project_id: str):
    ...


@project_blueprint.route('/<project_id:str>/description', methods=['PATCH'])
async def update_description(request: Request, project_id: str):
    ...
