from sanic import Blueprint, Request
from sanic import json as sanicjson

from src.db.user import *

project_blueprint = Blueprint("project_routes", url_prefix='/projects')


@project_blueprint.route('/', methods=['POST'])
async def create_project(request: Request):
    ...


@project_blueprint.route('/<project_id:str>', methods=['GET'])
async def get_project(request: Request, project_id: str):
    ...


@project_blueprint.route('/<project_id:str>/status', methods=['GET', 'PATCH'])
async def project_status(request: Request, project_id: str):
    ...


@project_blueprint.route('/<project_id:str>/content', methods=['GET', 'PATCH'])
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
