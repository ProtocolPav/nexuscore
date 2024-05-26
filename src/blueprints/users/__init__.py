import json
from datetime import datetime

from sanic import Blueprint, Request
import sanic
from sanic_ext import openapi

from src.database import Database
from src.models import user
from src.views.user import UserView

user_blueprint = Blueprint("user_routes", url_prefix='/users')


@user_blueprint.route('/', methods=['POST'])
@openapi.response(status=201,
                  content={'application/json': UserView.view_schema()},
                  description='Success')
@openapi.response(status=500, description='User Already Exists')
@openapi.definition(body={'application/json': {'guild_id': int, 'discord_user_id': int, 'username': str}})
async def create_user(request: Request, db: Database):
    """
    Create New User

    Creates a user based on the discord UserID and GuildID provided.
    If a user with these ID's already exists, it returns a 500.
    """
    if await UserView.get_thorny_id(db, int(request.json['guild_id']), int(request.json['discord_user_id'])):
        return sanic.HTTPResponse(status=500, body="User Already Exists!")
    else:
        await UserView.new(db, int(request.json['guild_id']),
                           int(request.json['discord_user_id']),
                           request.json.get('username', None))

        thorny_id = await UserView.get_thorny_id(db, int(request.json['guild_id']), int(request.json['discord_user_id']))
        user_view = await UserView.build(db, thorny_id)

    return sanic.json(status=201, body=user_view.model_dump(), default=str)


@user_blueprint.route('/thorny-id/<thorny_id:int>', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': UserView.view_schema()},
                  description='Success')
@openapi.response(status=404, description='Error')
async def user_thorny_id(request: Request, db: Database, thorny_id: int):
    """
    Get User

    This returns the user based on the ThornyID provided.

    Note that all playtime will be returned as seconds. You can process that manually.
    """
    user_view: UserView = await UserView.build(db, thorny_id)

    return sanic.json(user_view.model_dump(), default=str)


@user_blueprint.route('/thorny-id/<thorny_id:int>', methods=['PATCH'])
@openapi.definition(body={'application/json': user.UserUpdateModel.model_json_schema()})
@openapi.response(status=200,
                  content={'application/json': UserView.view_schema()},
                  description='Success')
@openapi.response(status=404, description='Error')
async def update_thorny_id(request: Request, db: Database, thorny_id: int):
    """
    Update User

    This updates a user. You can omit the fields that you do not want to update.

    Note: ThornyID, UserID, GuildID and Join Date will not update even if specified.
    Note: Balance updates will trigger a `Transaction` Event. It is preferred to use the `/balance`
    route to be able to enter comments, otherwise, a default comment will be generated to the `Transaction`.
    """
    model: user.UserModel = await user.UserModel.fetch(db, thorny_id)
    update_dict = {}

    for k, v in user.UserUpdateModel(**request.json).model_dump().items():
        if v:
            update_dict[k] = v

    model = model.model_copy(update=update_dict)

    await model.update(db)

    return sanic.json(model.model_dump(), default=str)


@user_blueprint.route('/thorny-id/<thorny_id:int>/balance', methods=['PATCH'])
@openapi.definition(body={'application/json': {'balance': int, 'comment': str}})
@openapi.response(status=501, description='Not Implemented')
async def update_balance(request: Request, thorny_id: int):
    """
    Update User Balance

    This updates the user's balance. If you do not include a comment,
    one will be auto-generated for you. This operation gets logged as a
    Transaction.
    """
    return sanic.HTTPResponse(status=501)


@user_blueprint.route('/thorny-id/<thorny_id:int>/profile', methods=['GET'])
@openapi.response(content={"application/json": user.ProfileModel.model_json_schema(ref_template="#/components/schemas/{model}")})
async def get_profile(request: Request, db: Database, thorny_id: int):
    """
    Get User Profile

    This returns only the user's profile.
    """
    profile_model = await user.ProfileModel.fetch(db, thorny_id)

    return sanic.json(profile_model.model_dump(), default=str)


@user_blueprint.route('/thorny-id/<thorny_id:int>/profile', methods=['PATCH'])
@openapi.definition(body={'application/json': user.ProfileUpdateModel.model_json_schema(
    ref_template="#/components/schemas/{model}"
)})
@openapi.response(status=200,
                  content={'application/json': user.ProfileModel.model_json_schema(ref_template="#/components/schemas/{model}")},
                  description='Success')
async def update_profile(request: Request, db: Database, thorny_id: int):
    """
    Update User Profile

    This updates a user's profile. Include only the request body fields
    that you want to update.
    """
    model: user.ProfileModel = await user.ProfileModel.fetch(db, thorny_id)
    update_dict = {}

    for k, v in user.ProfileUpdateModel(**request.json).model_dump().items():
        if v:
            update_dict[k] = v

    model = model.model_copy(update=update_dict)

    await model.update(db, thorny_id)

    return sanic.json(model.model_dump(), default=str)


@user_blueprint.route('/thorny-id/<thorny_id:int>/playtime', methods=['GET'])
@openapi.response(status=200,
                  content={
                      'application/json': user.PlaytimeSummary.model_json_schema(ref_template="#/components/schemas/{model}")},
                  description='Success')
async def get_playtime(request: Request, db: Database, thorny_id: int):
    """
    Get User Playtime

    This returns only the user's playtime.
    """
    playtime_summary = await user.PlaytimeSummary.fetch(db, thorny_id)

    return sanic.json(playtime_summary.model_dump(), default=str)


@user_blueprint.route('/guild/<guild_id:int>/<gamertag:str>', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': UserView.view_schema()},
                  description='Success')
@openapi.response(status=404, description='Error')
async def user_gamertag(request: Request, db: Database, guild_id: int, gamertag: str):
    """
    Get User by Gamertag

    This returns a bare-bones user object based on the gamertag and
    guild ID provided.

    This will check either the whitelisted gamertag or the user-entered gamertag.
    """
    thorny_id = await UserView.get_thorny_id(db, guild_id, gamertag=gamertag)
    user_view = await UserView.build(db, thorny_id)

    return sanic.json(user_view.model_dump(), default=str)


@user_blueprint.route('/guild/<guild_id:int>/<discord_id:int>', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': UserView.view_schema()},
                  description='Success')
@openapi.response(status=404, description='Error')
async def user_discord_id(request: Request, db: Database, guild_id: int, discord_id: int):
    """
    Get User by Discord ID

    This returns a bare-bones user object based on the discord user ID and
    guild ID provided.
    """
    thorny_id = await UserView.get_thorny_id(db, guild_id, user_id=discord_id)
    user_view = await UserView.build(db, thorny_id)

    return sanic.json(user_view.model_dump(), default=str)
