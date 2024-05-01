from sanic import Blueprint, Request
from sanic import json as sanicjson

from src.db.user import *

user_blueprint = Blueprint("user_routes", url_prefix='/users')


@user_blueprint.get('/thorny-id/<thorny_id:int>')
async def get_user_thorny_id(request: Request, thorny_id: int):
    user = await fetch_user_by_id(thorny_id)
    return sanicjson(user, default=str)


@user_blueprint.patch('/thorny-id/<thorny_id:int>')
async def update_user_thorny_id(request: Request, thorny_id: int):
    data = request.json
    user = await fetch_user_by_id(thorny_id)
    user = await user.update_user(user, data)

    return sanicjson(user, default=str)


@user_blueprint.get('/guild/<guild_id:int>/<gamertag:str>')
async def get_user_gamertag(request: Request, guild_id: int, gamertag: str):
    user = await fetch_user_by_gamertag(guild_id, gamertag)
    return sanicjson(user, default=str)


@user_blueprint.get('/guild/<guild_id:int>/<discord_id:int>')
async def get_user_discord_id(request: Request, guild_id: int, discord_id: int):
    user = await fetch_user_by_discord_id(guild_id, discord_id)
    return sanicjson(user, default=str)
