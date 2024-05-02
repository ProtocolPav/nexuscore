from sanic import Blueprint, Request
from sanic import json as sanicjson

from src.db.event import *

amethyst_blueprint = Blueprint('amethyst', '/amethyst')


@amethyst_blueprint.post('/connect')
async def post_connect_event(request: Request):
    data = request.json
    await connect(data['guild'], data['gamertag'])


@amethyst_blueprint.post('/disconnect')
async def post_disconnect_event(request: Request):
    data = request.json
    await connect(data['guild'], data['gamertag'])


@amethyst_blueprint.post('/interaction')
async def post_interaction_event(request: Request):
    ...