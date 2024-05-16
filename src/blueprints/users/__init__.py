from sanic import Blueprint, Request
import sanic
from sanic_ext import openapi

from src import model_factory
from src.models import objects, user

user_blueprint = Blueprint("user_routes", url_prefix='/users')


@user_blueprint.route('/', methods=['POST'])
@openapi.response(status=201, content={'application/json': objects.UserObjectWithNoOptionals.model_json_schema(
                                                            ref_template="#/components/schemas/{model}")},
                  description='Creation Successful')
@openapi.response(status=500, description='Error with creating user')
@openapi.definition(body={'application/json': {'guild_id': int, 'discord_user_id': int, 'username': str}})
async def create_user(request: Request):
    """
    Create New User

    Creates a user based on the discord UserID and GuildID provided.
    If a user with these ID's already exists, it returns it.
    """
    try:
        new_user = await model_factory.UserFactory.build_user_model(guild_id=int(request.json['guild_id']),
                                                                    user_id=int(request.json['discord_user_id']))
    except TypeError:
        await model_factory.UserFactory.create_user(int(request.json['guild_id']),
                                                    int(request.json['discord_user_id']),
                                                    request.json.get('username', None))

        new_user = await model_factory.UserFactory.build_user_model(guild_id=int(request.json['guild_id']),
                                                                    user_id=int(request.json['discord_user_id']))

    return sanic.json(status=201, body=objects.UserObjectWithNoOptionals(**new_user).dict(), default=str)


@user_blueprint.route('/thorny-id/<thorny_id:int>', methods=['GET'])
@openapi.parameter('include-profile', bool)
@openapi.parameter('include-playtime', bool)
@openapi.response(status=200, content={'application/json': objects.UserObject.model_json_schema(
                                                            ref_template="#/components/schemas/{model}")},
                  description='Success')
@openapi.response(status=404, description='Error')
async def user_thorny_id(request: Request, thorny_id: int):
    """
    Get User

    This returns the user based on the ThornyID provided.

    Note that all playtime will be returned as seconds. You can process that manually.
    """
    user_model = await model_factory.UserFactory.build_user_model(thorny_id)

    user_data = user_model | {'profile': None} | {'playtime': None}

    if request.args.get('include-profile', 'false').lower() == 'true':
        profile_model = await model_factory.UserFactory.build_profile_model(thorny_id)
        user_data['profile'] = profile_model

    if request.args.get('include-playtime', 'false').lower() == 'true':
        playtime_report = await model_factory.UserFactory.build_playtime_report(thorny_id)
        user_data['playtime'] = playtime_report

    return sanic.json(objects.UserObject(**user_data).dict(), default=str)


@user_blueprint.route('/thorny-id/<thorny_id:int>', methods=['PATCH'])
@openapi.definition(body={'application/json': objects.UserModel.model_json_schema()})
@openapi.response(status=200, content={'application/json': objects.UserObjectWithNoOptionals.model_json_schema(
                                                            ref_template="#/components/schemas/{model}")},
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

    updated_user = objects.UserObjectWithNoOptionals(**user_existing)

    await model_factory.UserFactory.update_user_model(thorny_id, updated_user)

    return sanic.json(updated_user.dict(), default=str)


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
@openapi.response(content={"application/json": objects.ProfileModel.model_json_schema(
                                                ref_template="#/components/schemas/{model}")})
async def get_profile(request: Request, thorny_id: int):
    """
    Get User Profile

    This returns only the user's profile.
    """
    profile_model = await model_factory.UserFactory.build_profile_model(thorny_id)

    return sanic.json(profile_model, default=str)


@user_blueprint.route('/thorny-id/<thorny_id:int>/profile', methods=['PATCH'])
@openapi.definition(body={'application/json': objects.ProfileModel.model_json_schema()})
async def update_profile(request: Request, thorny_id: int):
    """
    Update User Profile

    This updates a user's profile. Include only the request body fields
    that you want to update.
    """
    model = user.ProfileUpdateModel.parse_obj(request.json).dict()

    profile_existing = await model_factory.UserFactory.build_profile_model(thorny_id)

    profile_existing.update([k, v] for k, v in model.items() if v is not None)

    updated_profile = objects.ProfileModel(**profile_existing)

    await model_factory.UserFactory.update_profile_model(thorny_id, updated_profile)

    return sanic.json(updated_profile.dict(), default=str)


@user_blueprint.route('/thorny-id/<thorny_id:int>/playtime', methods=['GET'])
@openapi.response(content={"application/json": objects.PlaytimeReport.model_json_schema(
                                                ref_template="#/components/schemas/{model}")})
async def get_playtime(request: Request, thorny_id: int):
    """
    Get User Playtime

    This returns only the user's playtime.
    """
    playtime_report = await model_factory.UserFactory.build_playtime_report(thorny_id)

    return sanic.json(objects.PlaytimeReport(**playtime_report).dict(), default=str)


@user_blueprint.route('/guild/<guild_id:int>/<gamertag:str>', methods=['GET'])
@openapi.response(status=200, content={'application/json': objects.UserObjectWithNoOptionals.model_json_schema(
                                                            ref_template="#/components/schemas/{model}")},
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
    print(objects.UserObjectWithNoOptionals(**user_model).dict())

    return sanic.json(objects.UserObjectWithNoOptionals(**user_model).dict(), default=str)


@user_blueprint.route('/guild/<guild_id:int>/<discord_id:int>', methods=['GET'])
@openapi.response(status=200, content={'application/json': objects.UserObjectWithNoOptionals.model_json_schema(
                                                            ref_template="#/components/schemas/{model}")},
                  description='Success')
@openapi.response(status=404, description='Error')
async def user_discord_id(request: Request, guild_id: int, discord_id: int):
    """
    Get User by Discord ID

    This returns a bare-bones user object based on the discord user ID and
    guild ID provided.
    """
    user_model = await model_factory.UserFactory.build_user_model(user_id=discord_id, guild_id=guild_id)

    return sanic.json(objects.UserObjectWithNoOptionals(**user_model).dict(), default=str)
