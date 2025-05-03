from sanic import Blueprint, Request, exceptions
import sanic
from sanic_ext import openapi, validate
from sanic_ext.extensions.openapi.definitions import RequestBody, Response

from src.database import Database
from src.models.users import user, profile, playtime, interactions, quests
from src.utils.errors import BadRequest400, NotFound404

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
                        Response(user.UserModel.doc_schema(), 201),
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
                        Response(profile.ProfileModel.doc_schema(), 201),
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
@openapi.response(status=200,
                  content={'application/json': playtime.PlaytimeSummary.doc_schema()},
                  description='Success')
@openapi.response(status=404, description='User does not exist')
async def get_playtime(request: Request, db: Database, thorny_id: int):
    """
    Get User Playtime

    This returns the user's playtime. Note that all playtime is in seconds!
    """
    playtime_summary = await playtime.PlaytimeSummary.fetch(db, thorny_id)

    if not playtime_summary:
        raise exceptions.NotFound("Could not find this user, are you sure the ID is correct?")

    return sanic.json(playtime_summary.model_dump(), default=str)


@user_blueprint.route('/<thorny_id:int>/interactions', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': interactions.InteractionSummary.doc_schema()},
                  description='Success')
@openapi.response(status=404, description='User does not exist')
async def get_interactions(request: Request, db: Database, thorny_id: int):
    """
    Get User Interactions

    This returns the user's interaction summary.
    This may take long to process, so ensure you have the proper timeouts set.
    """
    summary = await interactions.InteractionSummary.fetch(db, thorny_id)

    if not summary:
        raise exceptions.NotFound("Could not find this user, are you sure the ID is correct?")

    return sanic.json(summary.model_dump(), default=str)


@user_blueprint.route('/guild/<guild_id:int>/<gamertag:str>', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': user.UserModel.doc_schema()},
                  description='Success')
@openapi.response(status=404, description='User does not exist')
async def user_by_gamertag(request: Request, db: Database, guild_id: int, gamertag: str):
    """
    Get User by Gamertag

    This acts the same as `Get by ThornyID`.
    This will check either the whitelisted gamertag or the user-entered gamertag.
    """
    thorny_id = await user.UserModel.get_thorny_id(db, guild_id, gamertag=gamertag.replace('%20', ' '))

    if not thorny_id:
        raise exceptions.NotFound("Could not find this user, are you sure the guild and gamertag is correct?")

    user_view = await user.UserModel.fetch(db, thorny_id)

    return sanic.json(user_view.model_dump(), default=str)


@user_blueprint.route('/guild/<guild_id:int>/<discord_id:int>', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': user.UserModel.doc_schema()},
                  description='Success')
@openapi.response(status=404, description='User does not exist')
async def user_discord_id(request: Request, db: Database, guild_id: int, discord_id: int):
    """
    Get User by Discord ID

    This acts the same as `Get by ThornyID`.
    """
    thorny_id = await user.UserModel.get_thorny_id(db, guild_id, user_id=discord_id)

    if not thorny_id:
        raise exceptions.NotFound("Could not find this user, are you sure the guild and discord ID is correct?")

    user_view = await user.UserModel.fetch(db, thorny_id)

    return sanic.json(user_view.model_dump(), default=str)


@user_blueprint.route('/<thorny_id:int>/quest/active', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': quests.UserQuestModel.doc_schema()},
                  description='Success')
@openapi.response(status=404, description='No active quest found')
async def active_quest(request: Request, db: Database, thorny_id: int):
    """
    Get User's Active Quest

    Returns the user's currently active quest.
    Data about the quest must be fetched separately.
    """
    quest = await quests.UserQuestModel.fetch_active_quest(db, thorny_id)

    if not quest:
        raise exceptions.NotFound("This user either does not exist or does not have a quest active")

    return sanic.json(quest.model_dump(), default=str)


@user_blueprint.route('/<thorny_id:int>/quest/all', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': list[int]},
                  description='Success')
@openapi.response(status=404, description='User does not exist')
async def all_quests(request: Request, db: Database, thorny_id: int):
    """
    Get All User's Quests

    Returns a list of QuestIDs that the user has previously accepted.
    """
    quest_ids = await quests.UserQuestModel.get_all_quest_ids(db, thorny_id)

    return sanic.json(quest_ids, default=str)


@user_blueprint.route('/<thorny_id:int>/quest/active', methods=['DELETE'])
@openapi.response(status=204, description='Success')
@openapi.response(status=404, description='Error')
async def fail_active_quest(request: Request, db: Database, thorny_id: int):
    """
    Fail User's Active Quest

    This marks the active quest and all of its objectives as "failed".
    """
    quest = await quests.UserQuestModel.fetch_active_quest(db, thorny_id)

    if quest:
        await quest.mark_failed(db, thorny_id)

    return sanic.HTTPResponse(status=204)


@user_blueprint.route('/<thorny_id:int>/quest/<quest_id:int>', methods=['POST'])
@openapi.response(status=201, description='Success')
@openapi.response(status=400, description='User already has quest active')
@openapi.response(status=404, description='Error')
async def new_active_quest(request: Request, db: Database, thorny_id: int, quest_id: int):
    """
    Add Quest to User's Active Quests

    This will return a 400 if the user already has a quest active.
    """
    quest = await quests.UserQuestModel.fetch_active_quest(db, thorny_id)

    if not quest:
        await quests.UserQuestModel.new(db, thorny_id, quest_id)
        return sanic.HTTPResponse(status=201)

    return sanic.HTTPResponse(status=400)


@user_blueprint.route('/<thorny_id:int>/quest/<quest_id:int>', methods=['PUT'])
@openapi.body(content={'application/json': quests.UserQuestUpdateModel.doc_schema()})
@openapi.response(status=200,
                  content={'application/json': quests.UserQuestModel.doc_schema()},
                  description='Success')
@openapi.response(status=404, description='Error')
@validate(json=quests.UserQuestUpdateModel)
async def update_quest(request: Request, db: Database, thorny_id: int, quest_id: int, body: quests.UserQuestUpdateModel):
    """
    Update Specific User's Quest

    Updates a user's quest. Note this does not update objectives, that is separate.
    """
    model = await quests.UserQuestModel.fetch(db, thorny_id, quest_id)
    update_dict = {}

    for k, v in body.model_dump().items():
        if v is not None:
            update_dict[k] = v

    model = model.model_copy(update=update_dict)

    await model.update(db, thorny_id)

    return sanic.json(model.model_dump(), default=str)


@user_blueprint.route('/<thorny_id:int>/quest/<quest_id:int>/<objective_id:int>', methods=['PUT'])
@openapi.body(content={'application/json': quests.UserObjectiveUpdateModel.doc_schema()})
@openapi.response(status=200,
                  content={'application/json': quests.UserObjectiveModel.doc_schema()},
                  description='Success')
@openapi.response(status=404, description='Error')
@validate(json=quests.UserObjectiveUpdateModel)
async def update_objective(request: Request, db: Database, thorny_id: int, quest_id: int, objective_id: int,
                           body: quests.UserObjectiveUpdateModel):
    """
    Update Specific User's Quest Objective

    Updates a user's quest objective.
    """
    model = await quests.UserObjectiveModel.fetch(db, thorny_id, quest_id, objective_id)
    update_dict = {}

    for k, v in body.model_dump().items():
        if v is not None:
            update_dict[k] = v

    model = model.model_copy(update=update_dict)

    await model.update(db, thorny_id)

    return sanic.json(model.model_dump(), default=str)
