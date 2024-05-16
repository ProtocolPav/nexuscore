from sanic import Blueprint, Request
from sanic import json as sanicjson
from sanic_ext import openapi

from src import model_factory
from src.models import objects, user

user_blueprint = Blueprint("user_routes", url_prefix='/users')


@user_blueprint.route('/', methods=['POST'])
@openapi.response(status=200, content={'application/json': {}}, description='Success')
@openapi.response(status=500, description='Error with creating user')
async def create_user(request: Request):
    ...


@user_blueprint.route('/thorny-id/<thorny_id:int>', methods=['GET'])
@openapi.parameter('include-profile', bool)
@openapi.parameter('include-playtime', bool)
@openapi.response(status=200, content={'application/json': objects.UserObject.model_json_schema()},
                  description='Success')
@openapi.response(status=404, description='Error')
async def user_thorny_id(request: Request, thorny_id: int):
    """
    Get User

    This returns the user based on the ThornyID provided.

    Note that all playtime will be returned as seconds. You can process that manually.
    """
    user_model = await model_factory.UserFactory.build_user_model(thorny_id)

    user_data = user_model

    if request.args.get('include-profile', 'false').lower() == 'true':
        profile_model = await model_factory.UserFactory.build_profile_model(thorny_id)
        user_data['profile'] = profile_model

    if request.args.get('include-playtime', 'false').lower() == 'true':
        playtime_report = await model_factory.UserFactory.build_playtime_report(thorny_id)
        user_data['playtime'] = playtime_report

    return sanicjson(objects.UserObject(**user_data).dict(), default=str)


@user_blueprint.route('/thorny-id/<thorny_id:int>', methods=['PATCH'])
@openapi.definition(body={'application/json': objects.UserModel.model_json_schema()})
@openapi.response(status=200, content={'application/json': objects.UserObject.model_json_schema()},
                  description='Update Successful')
@openapi.response(status=404, description='Error')
async def update_thorny_id(request: Request, thorny_id: int):
    """
    Update User

    This updates a user. You can omit the fields that you do not want to update.

    Note: ThornyID, UserID, GuildID and Join Date will not update even if specified.
    Note: Balance updates will trigger a `Transaction` Event. It is preferred to use the `/balance`
    route to be able to enter comments, otherwise, a default comment will be generated to the `Transaction`.
    """
    model = user.UserUpdateModel.parse_obj(request.json).dict()

    model['thorny_id'], model['user_id'], model['guild_id'], model['join_date'] = None, None, None, None

    user_existing = await model_factory.UserFactory.build_user_model(thorny_id)

    # Log balance transaction here.

    user_existing.update([k, v] for k, v in model.items() if v is not None)

    updated_user = objects.UserObject(**user_existing)

    await model_factory.UserFactory.update_user_model(thorny_id, updated_user)

    return sanicjson(updated_user.dict(), default=str)


@user_blueprint.route('/thorny-id/<thorny_id:int>/balance', methods=['PATCH'])
@openapi.definition(body={'application/json': {'balance': int, 'comment': str}})
async def update_balance(request: Request, thorny_id: int):
    """
    Update User Balance

    This updates the user's balance. If you do not include a comment,
    one will be auto-generated for you. This operation gets logged as a
    Transaction.
    """
    ...


@user_blueprint.route('/thorny-id/<thorny_id:int>/profile', methods=['GET'])
@openapi.response(content={"application/json": {}})
async def get_profile(request: Request, thorny_id: int):
    """
    Get User Profile

    This returns only the user's profile.
    """
    ...


@user_blueprint.route('/thorny-id/<thorny_id:int>/profile', methods=['PATCH'])
@openapi.body(content={"application/json": {}})
async def update_profile(request: Request, thorny_id: int):
    """
    Update User Profile

    This updates a user's profile. Include only the request body fields
    that you want to update.
    """
    ...


@user_blueprint.route('/guild/<guild_id:int>/<gamertag:str>', methods=['GET'])
@openapi.response(status=200, content={'application/json': objects.UserObject.model_json_schema()},
                  description='Success')
@openapi.response(status=404, description='Error')
async def user_gamertag(request: Request, guild_id: int, gamertag: str):
    """
    Get User by Gamertag

    This returns a bare-bones user object based on the gamertag and
    guild ID provided.

    This will check either the whitelisted gamertag or the user-entered gamertag.
    """
    user_model = await model_factory.UserFactory.build_user_model(gamertag=gamertag, guild_id=guild_id)

    return sanicjson(objects.UserObject(**user_model).dict(), default=str)


@user_blueprint.route('/guild/<guild_id:int>/<discord_id:int>', methods=['GET'])
@openapi.response(status=200, content={'application/json': objects.UserObject.model_json_schema()},
                  description='Success')
@openapi.response(status=404, description='Error')
async def user_discord_id(request: Request, guild_id: int, discord_id: int):
    """
    Get User by Discord ID

    This returns a bare-bones user object based on the discord user ID and
    guild ID provided.
    """
    user_model = await model_factory.UserFactory.build_user_model(user_id=discord_id, guild_id=guild_id)

    return sanicjson(objects.UserObject(**user_model).dict(), default=str)
