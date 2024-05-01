from sanic import Blueprint, Request
from sanic import json as sanicjson

from src.db.user import *

quest_blueprint = Blueprint("quest_routes", url_prefix='/quests')


@quest_blueprint.get('/')
async def get_all_quests(request: Request):
    ...


@quest_blueprint.get('/<quest_id:int>')
async def get_quest(request: Request, quest_id: int):
    ...


@quest_blueprint.post('/')
async def create_quest(request: Request):
    ...
