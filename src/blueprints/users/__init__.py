from sanic import Blueprint, Request, exceptions
import sanic
from sanic_ext import openapi, validate

from src.database import Database
from src.models import users

user_blueprint = Blueprint("user_routes", url_prefix='/users')


@user_blueprint.route('/', methods=['POST'])
@openapi.response(status=201,
                  content={'application/json': users.UserModel.doc_schema()},
                  description='Success')
@openapi.response(status=500, description='User Already Exists')
@openapi.definition(body={'application/json': users.UserCreateModel.doc_schema()})
@validate(json=users.UserCreateModel)
async def create_user(request: Request, db: Database, body: users.UserCreateModel):
    """
    Create New User

    Creates a user based on the discord UserID and GuildID provided.
    If a user with these ID's already exists, it returns a 500.
    """
    if await users.UserModel.get_thorny_id(db, body.guild_id, body.discord_id):
        raise exceptions.ServerError(message="Could not create the user as it already exists")
    else:
        await users.UserModel.new(db, body.guild_id, body.discord_id, body.username)

        thorny_id = await users.UserModel.get_thorny_id(db, body.guild_id, body.discord_id)
        user_view = await users.UserModel.build(db, thorny_id)

    return sanic.json(status=201, body=user_view.model_dump(), default=str)


@user_blueprint.route('/<thorny_id:int>', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': users.UserModel.doc_schema()},
                  description='Success')
@openapi.response(status=404, description='User does not exist')
async def get_user(request: Request, db: Database, thorny_id: int):
    """
    Get User

    This returns the User object
    """
    user_model = await users.UserModel.fetch(db, thorny_id)

    if not user_model:
        raise exceptions.NotFound("Could not find this user, are you sure the ID is correct?")

    return sanic.json(user_model.model_dump(), default=str)


@user_blueprint.route('/<thorny_id:int>', methods=['PATCH'])
@openapi.definition(body={'application/json': users.UserUpdateModel.doc_schema()})
@openapi.response(status=200,
                  content={'application/json': users.UserModel.doc_schema()},
                  description='Success')
@openapi.response(status=404, description='User does not exist')
@validate(json=users.UserUpdateModel)
async def update_thorny_id(request: Request, db: Database, thorny_id: int, body: users.UserUpdateModel):
    """
    Update User

    This updates a user. All fields are optional, meaning you may
    set a field to `null` to not update it.
    """
    model = await users.UserModel.fetch(db, thorny_id)

    if not model:
        raise exceptions.NotFound("Could not find this user, are you sure the ID is correct?")

    update_dict = {}

    for k, v in body.model_dump().items():
        if v is not None:
            update_dict[k] = v

    model = model.model_copy(update=update_dict)

    await model.update(db)

    return sanic.json(model.model_dump(), default=str)


@user_blueprint.route('/<thorny_id:int>/profile', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': users.ProfileModel.doc_schema()},
                  description='Success')
@openapi.response(status=404, description='User does not exist')
async def get_profile(request: Request, db: Database, thorny_id: int):
    """
    Get User Profile

    This returns the user's profile
    """
    profile_model = await users.ProfileModel.fetch(db, thorny_id)

    if not profile_model:
        raise exceptions.NotFound("Could not find this user, are you sure the ID is correct?")

    return sanic.json(profile_model.model_dump(), default=str)


@user_blueprint.route('/<thorny_id:int>/profile', methods=['PATCH'])
@openapi.definition(body={'application/json': users.ProfileUpdateModel.doc_schema()})
@openapi.response(status=200,
                  content={'application/json': users.ProfileModel.doc_schema()},
                  description='Success')
@openapi.response(status=404, description='User does not exist')
@validate(json=users.ProfileUpdateModel)
async def update_profile(request: Request, db: Database, thorny_id: int, body: users.ProfileUpdateModel):
    """
    Update User Profile

    This updates a user's profile. Anything set to NULL will be ignored.
    """
    model = await users.ProfileModel.fetch(db, thorny_id)

    if not model:
        raise exceptions.NotFound("Could not find this user, are you sure the ID is correct?")

    update_dict = {}

    for k, v in body.model_dump().items():
        if v is not None:
            update_dict[k] = v

    model = model.model_copy(update=update_dict)

    await model.update(db, thorny_id)

    return sanic.json(model.model_dump(), default=str)


@user_blueprint.route('/<thorny_id:int>/playtime', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': users.PlaytimeSummary.doc_schema()},
                  description='Success')
@openapi.response(status=404, description='User does not exist')
async def get_playtime(request: Request, db: Database, thorny_id: int):
    """
    Get User Playtime

    This returns the user's playtime. Note that all playtime is in seconds!
    """
    playtime_summary = await users.PlaytimeSummary.fetch(db, thorny_id)

    if not playtime_summary:
        raise exceptions.NotFound("Could not find this user, are you sure the ID is correct?")

    return sanic.json(playtime_summary.model_dump(), default=str)


@user_blueprint.route('/<thorny_id:int>/interactions', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': users.InteractionSummary.doc_schema()},
                  description='Success')
@openapi.response(status=404, description='User does not exist')
async def get_interactions(request: Request, db: Database, thorny_id: int):
    """
    Get User Interactions

    This returns the user's interaction summary.
    This may take long to process, so ensure you have the proper timeouts set.
    """
    summary = await users.InteractionSummary.fetch(db, thorny_id)

    if not summary:
        raise exceptions.NotFound("Could not find this user, are you sure the ID is correct?")

    return sanic.json(summary.model_dump(), default=str)


@user_blueprint.route('/guild/<guild_id:int>/<gamertag:str>', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': users.UserModel.doc_schema()},
                  description='Success')
@openapi.response(status=404, description='User does not exist')
async def user_by_gamertag(request: Request, db: Database, guild_id: int, gamertag: str):
    """
    Get User by Gamertag

    This acts the same as `Get by ThornyID`.
    This will check either the whitelisted gamertag or the user-entered gamertag.
    """
    thorny_id = await users.UserModel.get_thorny_id(db, guild_id, gamertag=gamertag)

    if not thorny_id:
        raise exceptions.NotFound("Could not find this user, are you sure the guild and gamertag is correct?")

    user_view = await users.UserModel.fetch(db, thorny_id)

    return sanic.json(user_view.model_dump(), default=str)


@user_blueprint.route('/guild/<guild_id:int>/<discord_id:int>', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': users.UserModel.doc_schema()},
                  description='Success')
@openapi.response(status=404, description='User does not exist')
async def user_discord_id(request: Request, db: Database, guild_id: int, discord_id: int):
    """
    Get User by Discord ID

    This acts the same as `Get by ThornyID`.
    """
    thorny_id = await users.UserModel.get_thorny_id(db, guild_id, user_id=discord_id)

    if not thorny_id:
        raise exceptions.NotFound("Could not find this user, are you sure the guild and discord ID is correct?")

    user_view = await users.UserModel.fetch(db, thorny_id)

    return sanic.json(user_view.model_dump(), default=str)


@user_blueprint.route('/<thorny_id:int>/quest/active', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': users.UserQuestModel.doc_schema()},
                  description='Success')
@openapi.response(status=404, description='No active quest found')
async def active_quest(request: Request, db: Database, thorny_id: int):
    """
    Get User's Active Quest

    Returns the user's currently active quest.
    Data about the quest must be fetched separately.
    """
    quest = await users.UserQuestModel.fetch_active_quest(db, thorny_id)

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
    quest_ids = await users.UserQuestModel.get_all_quest_ids(db, thorny_id)

    return sanic.json(quest_ids, default=str)


@user_blueprint.route('/<thorny_id:int>/quest/active', methods=['DELETE'])
@openapi.response(status=204, description='Success')
@openapi.response(status=404, description='Error')
async def fail_active_quest(request: Request, db: Database, thorny_id: int):
    """
    Fail User's Active Quest

    This marks the active quest and all of its objectives as "failed".
    """
    quest = await users.UserQuestModel.fetch_active_quest(db, thorny_id)

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
    quest = await users.UserQuestModel.fetch_active_quest(db, thorny_id)

    if not quest:
        await users.UserQuestModel.new(db, thorny_id, quest_id)
        return sanic.HTTPResponse(status=201)

    return sanic.HTTPResponse(status=400)


@user_blueprint.route('/<thorny_id:int>/quest/<quest_id:int>', methods=['PUT'])
@openapi.body(content={'application/json': users.UserQuestUpdateModel.doc_schema()})
@openapi.response(status=200,
                  content={'application/json': users.UserQuestModel.doc_schema()},
                  description='Success')
@openapi.response(status=404, description='Error')
@validate(json=users.UserQuestUpdateModel)
async def update_quest(request: Request, db: Database, thorny_id: int, quest_id: int, body: users.UserQuestUpdateModel):
    """
    Update Specific User's Quest

    Updates a user's quest. Note this does not update objectives, that is separate.
    """
    model = await users.UserQuestModel.fetch(db, thorny_id, quest_id)
    update_dict = {}

    for k, v in body.model_dump().items():
        if v is not None:
            update_dict[k] = v

    model = model.model_copy(update=update_dict)

    await model.update(db, thorny_id)

    return sanic.json(model.model_dump(), default=str)


@user_blueprint.route('/<thorny_id:int>/quest/<quest_id:int>/<objective_id:int>', methods=['PUT'])
@openapi.body(content={'application/json': users.UserObjectiveUpdateModel.doc_schema()})
@openapi.response(status=200,
                  content={'application/json': users.UserObjectiveModel.doc_schema()},
                  description='Success')
@openapi.response(status=404, description='Error')
@validate(json=users.UserObjectiveUpdateModel)
async def update_objective(request: Request, db: Database, thorny_id: int, quest_id: int, objective_id: int,
                           body: users.UserObjectiveUpdateModel):
    """
    Update Specific User's Quest Objective

    Updates a user's quest objective.
    """
    model = await users.UserObjectiveModel.fetch(db, thorny_id, quest_id, objective_id)
    update_dict = {}

    for k, v in body.model_dump().items():
        if v is not None:
            update_dict[k] = v

    model = model.model_copy(update=update_dict)

    await model.update(db, thorny_id)

    return sanic.json(model.model_dump(), default=str)
