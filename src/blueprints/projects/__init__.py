from sanic import Blueprint, Request
from sanic import json as sanicjson
from sanic_ext import openapi

from src.schema.project_schema import Project

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
    ...


@project_blueprint.route('/<project_id:str>', methods=['PATCH'])
@openapi.body(content={'application/json': Project})
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
