from sanic import Blueprint, Request
from sanic import json as sanicjson

from src.db.user import *

user_blueprint = Blueprint("user_routes", url_prefix='/users')


@user_blueprint.route('/', methods=['POST'])
async def create_user(request: Request):
    ...


@user_blueprint.route('/thorny-id/<thorny_id:int>', methods=['GET', 'DELETE', 'PATCH'])
async def user_thorny_id(request: Request, thorny_id: int):
    if request.method == 'GET':
        user = await fetch_user_by_id(thorny_id)
        return sanicjson(user, default=str)
    elif request.method == 'DELETE':
        ...
    elif request.method == 'PATCH':
        ...


@user_blueprint.route('/thorny-id/<thorny_id:int>/username', methods=['PATCH'])
async def update_username(request: Request, thorny_id: int):
    ...


@user_blueprint.route('/thorny-id/<thorny_id:int>/birthday', methods=['PATCH'])
async def update_birthday(request: Request, thorny_id: int):
    ...


@user_blueprint.route('/thorny-id/<thorny_id:int>/balance', methods=['PATCH'])
async def update_balance(request: Request, thorny_id: int):
    ...


@user_blueprint.route('/thorny-id/<thorny_id:int>/profile', methods=['GET'])
async def get_profile(request: Request, thorny_id: int):
    ...


@user_blueprint.route('/thorny-id/<thorny_id:int>/profile/slogan', methods=['PATCH'])
async def update_profile_slogan(request: Request, thorny_id: int):
    ...


@user_blueprint.route('/thorny-id/<thorny_id:int>/profile/gamertag', methods=['PATCH'])
async def update_profile_gamertag(request: Request, thorny_id: int):
    ...


@user_blueprint.route('/thorny-id/<thorny_id:int>/profile/gamertag/whitelist', methods=['PATCH'])
async def update_profile_whitelist(request: Request, thorny_id: int):
    ...


@user_blueprint.route('/thorny-id/<thorny_id:int>/profile/about', methods=['PATCH'])
async def update_profile_about(request: Request, thorny_id: int):
    ...


@user_blueprint.route('/thorny-id/<thorny_id:int>/profile/character/lore', methods=['PATCH'])
async def update_profile_lore(request: Request, thorny_id: int):
    ...


@user_blueprint.route('/thorny-id/<thorny_id:int>/profile/character/name', methods=['PATCH'])
async def update_profile_name(request: Request, thorny_id: int):
    ...


@user_blueprint.route('/thorny-id/<thorny_id:int>/profile/character/age', methods=['PATCH'])
async def update_profile_age(request: Request, thorny_id: int):
    ...


@user_blueprint.route('/thorny-id/<thorny_id:int>/profile/character/race', methods=['PATCH'])
async def update_profile_race(request: Request, thorny_id: int):
    ...


@user_blueprint.route('/thorny-id/<thorny_id:int>/profile/character/role', methods=['PATCH'])
async def update_profile_role(request: Request, thorny_id: int):
    ...


@user_blueprint.route('/thorny-id/<thorny_id:int>/profile/character/origin', methods=['PATCH'])
async def update_profile_origin(request: Request, thorny_id: int):
    ...


@user_blueprint.route('/thorny-id/<thorny_id:int>/profile/character/beliefs', methods=['PATCH'])
async def update_profile_beliefs(request: Request, thorny_id: int):
    ...


@user_blueprint.route('/thorny-id/<thorny_id:int>/profile/character/stats', methods=['PATCH'])
async def update_profile_stats(request: Request, thorny_id: int):
    ...


@user_blueprint.route('/thorny-id/<thorny_id:int>/levels/level', methods=['PATCH'])
async def update_levels_level(request: Request, thorny_id: int):
    ...


@user_blueprint.route('/thorny-id/<thorny_id:int>/levels/xp', methods=['PATCH'])
async def update_levels_xp(request: Request, thorny_id: int):
    ...


@user_blueprint.route('/thorny-id/<thorny_id:int>/levels/xp/required', methods=['PATCH'])
async def update_levels_required_xp(request: Request, thorny_id: int):
    ...


@user_blueprint.route('/thorny-id/<thorny_id:int>/levels/message', methods=['PATCH'])
async def update_levels_message(request: Request, thorny_id: int):
    ...


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
