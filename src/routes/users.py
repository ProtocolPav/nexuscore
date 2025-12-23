from sanic import Blueprint, Request, exceptions
import sanic
from sanic_ext import openapi, validate
from sanic_ext.extensions.openapi.definitions import RequestBody, Response

from src.database import Database
from src.models.users import user, profile, playtime, interactions
from src.utils.errors import BadRequest400, Forbidden403, NotFound404

user_blueprint = Blueprint("users", url_prefix='/users')


@user_blueprint.route('/', methods=['POST'])
@openapi.definition(body=RequestBody(user.UserCreateModel.doc_schema()),
                    response=[
                        Response(user.UserModel.doc_schema(), 201),
                        Response(BadRequest400, 400)
                    ])
@validate(json=user.UserCreateModel)
async def create_user(request: Request, db: Database, body: user.UserCreateModel):
    """
    Create New User

    Creates a user based on the discord UserID and GuildID provided.
    If a user with these ID's already exists, it returns a 400.
    """
    if await user.UserModel.get_thorny_id(db, body.guild_id, body.user_id):
        raise BadRequest400('This user already exists')
    else:
        thorny_id = await user.UserModel.create(db, body)
        user_model = await user.UserModel.fetch(db, thorny_id)

    return sanic.json(status=201, body=user_model.model_dump(), default=str)


@user_blueprint.route('/<thorny_id:int>', methods=['GET'])
@openapi.definition(response=[
                        Response(user.UserModel.doc_schema(), 200),
                        Response(NotFound404, 404)
                    ])
async def get_user(request: Request, db: Database, thorny_id: int):
    """
    Get User

    This returns the User object
    """
    user_model = await user.UserModel.fetch(db, thorny_id)

    return sanic.json(user_model.model_dump(), default=str)


@user_blueprint.route('/<thorny_id:int>', methods=['PATCH', 'PUT'])
@openapi.definition(body=RequestBody(user.UserUpdateModel.doc_schema()),
                    response=[
                        Response(user.UserModel.doc_schema(), 200),
                        Response(BadRequest400, 400)
                    ])
@validate(json=user.UserUpdateModel)
async def update_thorny_id(request: Request, db: Database, thorny_id: int, body: user.UserUpdateModel):
    """
    Update User

    This updates a user. All fields are optional, meaning you may
    set a field to `null` to not update it.

    `whitelist` does not apply to this. If you set it to null, it will become null.
    """
    model = await user.UserModel.fetch(db, thorny_id)
    await model.update(db, body)

    return sanic.json(model.model_dump(), default=str)


@user_blueprint.route('/<thorny_id:int>/profile', methods=['GET'])
@openapi.definition(response=[
                        Response(profile.ProfileModel.doc_schema(), 200),
                        Response(NotFound404, 404)
                    ])
async def get_profile(request: Request, db: Database, thorny_id: int):
    """
    Get User Profile

    This returns the user's profile
    """
    profile_model = await profile.ProfileModel.fetch(db, thorny_id)

    return sanic.json(profile_model.model_dump(), default=str)


@user_blueprint.route('/<thorny_id:int>/profile', methods=['PATCH', 'PUT'])
@openapi.definition(body=RequestBody(profile.ProfileUpdateModel.doc_schema()),
                    response=[
                        Response(profile.ProfileModel.doc_schema(), 200),
                        Response(BadRequest400, 400)
                    ])
@validate(json=profile.ProfileUpdateModel)
async def update_profile(request: Request, db: Database, thorny_id: int, body: profile.ProfileUpdateModel):
    """
    Update User Profile

    This updates a user's profile. Anything set to NULL will be ignored.
    """
    model = await profile.ProfileModel.fetch(db, thorny_id)
    await model.update(db, body)

    return sanic.json(model.model_dump(), default=str)


@user_blueprint.route('/<thorny_id:int>/playtime', methods=['GET'])
@openapi.definition(response=[
                        Response(playtime.PlaytimeSummary.doc_schema(), 200),
                        Response(NotFound404, 404)
                    ])
async def get_playtime(request: Request, db: Database, thorny_id: int):
    """
    Get User Playtime

    This returns the user's playtime. Note that all playtime is in seconds!
    """
    playtime_summary = await playtime.PlaytimeSummary.fetch(db, thorny_id)

    return sanic.json(playtime_summary.model_dump(), default=str)


@user_blueprint.route('/<thorny_id:int>/interactions', methods=['GET'])
@openapi.definition(response=[
                        Response(interactions.InteractionSummary.doc_schema(), 200),
                        Response(NotFound404, 404)
                    ])
async def get_interactions(request: Request, db: Database, thorny_id: int):
    """
    Get User Interactions

    This returns the user's interaction summary.
    This may take long to process, so ensure you have the proper timeouts set.
    """
    summary = await interactions.InteractionSummary.fetch(db, thorny_id)

    return sanic.json(summary.model_dump(), default=str)


@user_blueprint.route('/guild/<guild_id:int>/<gamertag:str>', methods=['GET'])
@openapi.definition(response=[
                        Response(user.UserModel.doc_schema(), 200),
                        Response(NotFound404, 404)
                    ])
async def user_by_gamertag(request: Request, db: Database, guild_id: int, gamertag: str):
    """
    Get User by Gamertag

    This acts the same as `Get by ThornyID`.
    This will check either the whitelisted gamertag or the user-entered gamertag.
    """
    thorny_id = await user.UserModel.get_thorny_id(db, guild_id, gamertag=gamertag.replace('%20', ' '))
    user_view = await user.UserModel.fetch(db, thorny_id)

    return sanic.json(user_view.model_dump(), default=str)


@user_blueprint.route('/guild/<guild_id:int>/<discord_id:int>', methods=['GET'])
@openapi.definition(response=[
                        Response(user.UserModel.doc_schema(), 200),
                        Response(NotFound404, 404)
                    ])
async def user_discord_id(request: Request, db: Database, guild_id: int, discord_id: int):
    """
    Get User by Discord ID

    This acts the same as `Get by ThornyID`.
    """
    thorny_id = await user.UserModel.get_thorny_id(db, guild_id, user_id=discord_id)
    user_view = await user.UserModel.fetch(db, thorny_id)

    return sanic.json(user_view.model_dump(), default=str)
