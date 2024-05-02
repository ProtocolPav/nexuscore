from sanic import Blueprint, Request
from sanic import json as sanicjson

from src.db.user import *

quest_blueprint = Blueprint("quest_routes", url_prefix='/quests')


@quest_blueprint.route('/', methods=['GET', 'POST'])
async def quests(request: Request):
    if request.method == 'GET':
        ...
    elif request.method == 'POST':
        ...


@quest_blueprint.get('/<quest_id:int>')
async def get_quest(request: Request, quest_id: int):
    ...


async def get_all_quests(request: Request):
    ...


async def create_quest(request: Request):
    ...
