from sanic import Blueprint, Request
from sanic import json as sanicjson

from src.db.user import *

user_blueprint = Blueprint("user_routes", url_prefix='/users')


@user_blueprint.route('/thorny-id/<thorny_id:int>', methods=['GET', 'PUT'])
async def user_thorny_id(request: Request, thorny_id: int):
    if request.method == 'GET':
        return get_user_thorny_id(request, thorny_id)
    elif request.method == 'PUT':
        return update_user_thorny_id(request, thorny_id)


async def get_user_thorny_id(request: Request, thorny_id: int):
    user = await fetch_user_by_id(thorny_id)
    return sanicjson(user, default=str)


async def update_user_thorny_id(request: Request, thorny_id: int):
    data = request.json
    user = await fetch_user_by_id(thorny_id)
    user = await user.update_user(user, data)

    return sanicjson(user, default=str)


@user_blueprint.route('/guild/<guild_id:int>/<gamertag:str>', methods=['GET'])
async def user_gamertag(request: Request, guild_id: int, gamertag: str):
    if request.method == 'GET':
        return await get_user_gamertag(request, guild_id, gamertag)


async def get_user_gamertag(request: Request, guild_id: int, gamertag: str):
    user = await fetch_user_by_gamertag(guild_id, gamertag)
    return sanicjson(user, default=str)


@user_blueprint.route('/guild/<guild_id:int>/<discord_id:int>', methods=['GET'])
async def user_gamertag(request: Request, guild_id: int, discord_id: int):
    if request.method == 'GET':
        return await get_user_discord_id(request, guild_id, discord_id)


async def get_user_discord_id(request: Request, guild_id: int, discord_id: int):
    user = await fetch_user_by_discord_id(guild_id, discord_id)
    return sanicjson(user, default=str)
