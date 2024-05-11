import datetime

from sanic import Blueprint, Request
from sanic import json as sanicjson
from sanic_ext import openapi

from src.db.user import *
from src.schema.user_schema import User, BaseUser, Profile, Levels

user_blueprint = Blueprint("user_routes", url_prefix='/users')


@user_blueprint.route('/', methods=['POST'])
@openapi.response(status=200, content={'application/json': BaseUser}, description='Success')
@openapi.response(status=500, description='Error with creating user')
async def create_user(request: Request):
    ...


@user_blueprint.route('/thorny-id/<thorny_id:int>', methods=['GET'])
@openapi.parameter('include', str)
@openapi.response(status=200, content={'application/json': User}, description='Success')
@openapi.response(status=404, description='Error')
async def user_thorny_id(request: Request, thorny_id: int):
    """
    Get User

    This returns the user based on the ThornyID provided.

    In the include parameters, you can specify any of:
    - profile
    - levels
    - projects
    - playtime

    These are not automatically included in the response object and must be manually selected.

    Note that all playtime will be returned as seconds. You can process that manually.
    """
    arguments = request.args.get('include', [])
    user = await fetch_user_by_id(thorny_id, arguments)
    return sanicjson(user, default=str)


@user_blueprint.route('/thorny-id/<thorny_id:int>', methods=['PATCH'])
@openapi.definition(body={'application/json': {
                                    'username': str,
                                    'birthday': datetime.datetime,
                                    'is_in_guild': bool,
                                    'patron': bool,
                                    'role': str
                                    }})
async def update_thorny_id(request: Request, thorny_id: int):
    """
    Update User

    This updates a user. You may include all body arguments
    or just one.
    """
    data = request.json
    user = await fetch_user_by_id(thorny_id)
    user.update(data)

    return sanicjson(user, default=str)


@user_blueprint.route('/thorny-id/<thorny_id:int>/balance', methods=['PATCH'])
@openapi.definition(body={'application/json': {
                                    'to_add': int,
                                    'to_remove': int,
                                    'comment': str
                                    }})
async def update_balance(request: Request, thorny_id: int):
    """
    Update User Balance

    This updates the user's balance. If you do not include a comment,
    one will be auto-generated for you. This operation gets logged as a
    Transaction.
    """
    ...


@user_blueprint.route('/thorny-id/<thorny_id:int>/profile', methods=['GET'])
@openapi.response(content={"application/json": Profile})
async def get_profile(request: Request, thorny_id: int):
    """
    Get User Profile

    This returns only the user's profile.
    """
    ...


@user_blueprint.route('/thorny-id/<thorny_id:int>/profile', methods=['PATCH'])
@openapi.body(content={"application/json": Profile})
async def update_profile(request: Request, thorny_id: int):
    """
    Update User Profile

    This updates a user's profile. Include only the request body fields
    that you want to update.
    """
    ...


@user_blueprint.route('/thorny-id/<thorny_id:int>/levels', methods=['GET'])
@openapi.response(content={"application/json": Levels})
async def get_levels(request: Request, thorny_id: int):
    """
    Get User Levels

    This returns only the user's levels and info about it.
    """
    ...


@user_blueprint.route('/thorny-id/<thorny_id:int>/levels', methods=['PATCH'])
@openapi.body(content={"application/json": Levels})
async def update_levels(request: Request, thorny_id: int):
    """
    Update User Levels

    This updates a user's levels. Note that there is no logic on the
    webserver for this, the logic is expected to be handled by the
    application.
    """
    ...


async def update_user_thorny_id(request: Request, thorny_id: int):
    data = request.json
    user = await fetch_user_by_id(thorny_id)
    user = await user.update_user(user, data)

    return sanicjson(user, default=str)


@user_blueprint.route('/guild/<guild_id:int>/<gamertag:str>', methods=['GET'])
async def user_gamertag(request: Request, guild_id: int, gamertag: str):
    """
    Get User by Gamertag

    This returns a bare-bones user object based on the gamertag and
    guild ID provided. Note, that this checks the whitelisted gamertag only.
    """
    user = await fetch_user_by_gamertag(guild_id, gamertag)
    return sanicjson(user, default=str)


@user_blueprint.route('/guild/<guild_id:int>/<discord_id:int>', methods=['GET'])
async def user_discord_id(request: Request, guild_id: int, discord_id: int):
    """
    Get User by Discord ID

    This returns a bare-bones user object based on the discord user ID and
    guild ID provided.
    """
    user = await fetch_user_by_discord_id(guild_id, discord_id)
    return sanicjson(user, default=str)
