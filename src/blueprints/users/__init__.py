import json
from datetime import datetime

from sanic import Blueprint, Request
import sanic
from sanic_ext import openapi

from src.database import Database
from src.models import user
from src.views.user import UserView, UserQuestView

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

    This returns the user, profile and playtime based on ThornyID.
    Playtime is in seconds.
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

    This updates a user. Anything set to NULL will be ignored.
    """
    model: user.UserModel = await user.UserModel.fetch(db, thorny_id)
    update_dict = {}

    for k, v in user.UserUpdateModel(**request.json).model_dump().items():
        if v is not None:
            update_dict[k] = v

    model = model.model_copy(update=update_dict)

    await model.update(db)

    return sanic.json(model.model_dump(), default=str)


@user_blueprint.route('/thorny-id/<thorny_id:int>/profile', methods=['GET'])
@openapi.response(content={"application/json": user.ProfileModel.model_json_schema(ref_template="#/components/schemas/{model}")})
async def get_profile(request: Request, db: Database, thorny_id: int):
    """
    Get User Profile

    This returns the user profile based on ThornyID
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

    This updates a user's profile. Anything set to NULL will be ignored.
    """
    model: user.ProfileModel = await user.ProfileModel.fetch(db, thorny_id)
    update_dict = {}

    for k, v in user.ProfileUpdateModel(**request.json).model_dump().items():
        if v is not None:
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

    This returns the user's playtime, all playtime is in seconds.
    """
    playtime_summary = await user.PlaytimeSummary.fetch(db, thorny_id)

    return sanic.json(playtime_summary.model_dump(), default=str)


@user_blueprint.route('/thorny-id/<thorny_id:int>/interactions', methods=['GET'])
@openapi.response(status=200,
                  content={
                      'application/json': user.InteractionSummary.model_json_schema(ref_template="#/components/schemas/{model}")},
                  description='Success')
async def get_interactions(request: Request, db: Database, thorny_id: int):
    """
    Get User Interactions

    This returns the user's interaction summary.
    This may take long to process, so ensure you have the proper timeouts set.
    """
    summary = await user.InteractionSummary.fetch(db, thorny_id)

    return sanic.json(summary.model_dump(), default=str)


@user_blueprint.route('/guild/<guild_id:int>/<gamertag:str>', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': UserView.view_schema()},
                  description='Success')
@openapi.response(status=404, description='Error')
async def user_gamertag(request: Request, db: Database, guild_id: int, gamertag: str):
    """
    Get User by Gamertag

    This acts the same as `Get by ThornyID`.
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

    This acts the same as `Get by ThornyID`.
    """
    thorny_id = await UserView.get_thorny_id(db, guild_id, user_id=discord_id)
    user_view = await UserView.build(db, thorny_id)

    return sanic.json(user_view.model_dump(), default=str)


@user_blueprint.route('/thorny-id/<thorny_id:int>/quest/active', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': UserQuestView.view_schema()},
                  description='Success')
@openapi.response(status=404, description='Error')
async def active_quest(request: Request, db: Database, thorny_id: int):
    """
    Get User's Active Quest

    Returns the user's currently active quest.
    Data about the quest must be fetched separately.
    """
    quest_id = await user.UserQuestModel.get_active_quest(db, thorny_id)

    if quest_id:
        quest_view = await UserQuestView.build(db, thorny_id, quest_id)
    else:
        quest_view = UserQuestView(**{'quest': None, 'objectives': None})

    return sanic.json(quest_view.model_dump(), default=str)


@user_blueprint.route('/thorny-id/<thorny_id:int>/quest/all', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': {'quests': list[int]}},
                  description='Success')
@openapi.response(status=404, description='Error')
async def all_quests(request: Request, db: Database, thorny_id: int):
    """
    Get All User's Quests

    Returns a list of QuestIDs that the user has previously accepted.
    """
    quest_ids = await user.UserQuestModel.get_all_quests(db, thorny_id)

    return sanic.json({'quests': quest_ids}, default=str)


@user_blueprint.route('/thorny-id/<thorny_id:int>/quest/active', methods=['DELETE'])
@openapi.response(status=204, description='Success')
@openapi.response(status=404, description='Error')
async def fail_active_quest(request: Request, db: Database, thorny_id: int):
    """
    Fail User's Active Quest

    This marks the active quest and all of its objectives as "failed".
    """
    quest_id = await user.UserQuestModel.get_active_quest(db, thorny_id)

    await UserQuestView.mark_failed(db, thorny_id, quest_id)

    return sanic.HTTPResponse(status=204)


@user_blueprint.route('/thorny-id/<thorny_id:int>/quest/<quest_id:int>', methods=['POST'])
@openapi.response(status=201, description='Success')
@openapi.response(status=404, description='Error')
async def new_active_quest(request: Request, db: Database, thorny_id: int, quest_id: int):
    """
    Add Quest to User's Active Quests

    Note, this doesn't check if a user already has an active quest.
    It is recommended to check yourself beforehand.
    """
    await UserQuestView.new(db, thorny_id, quest_id)

    return sanic.HTTPResponse(status=201)


@user_blueprint.route('/thorny-id/<thorny_id:int>/quest/<quest_id:int>', methods=['PUT'])
@openapi.body(content={'application/json': user.UserQuestUpdateModel.model_json_schema()})
@openapi.response(status=200,
                  content={'application/json': user.UserQuestModel.model_json_schema()},
                  description='Success')
@openapi.response(status=404, description='Error')
async def update_quest(request: Request, db: Database, thorny_id: int, quest_id: int):
    """
    Update Specific User's Quest

    Updates a user's quest. Note this does not update objectives, that is separate.
    """
    model: user.UserQuestModel = await user.UserQuestModel.fetch(db, thorny_id, quest_id)
    update_dict = {}

    for k, v in user.UserQuestUpdateModel(**request.json).model_dump().items():
        if v is not None:
            update_dict[k] = v

    model = model.model_copy(update=update_dict)

    await model.update(db, thorny_id)

    return sanic.json(model.model_dump(), default=str)


@user_blueprint.route('/thorny-id/<thorny_id:int>/quest/<quest_id:int>/<objective_id:int>', methods=['PUT'])
@openapi.body(content={'application/json': user.UserObjectiveUpdateModel.model_json_schema()})
@openapi.response(status=200,
                  content={'application/json': user.UserObjectiveModel.model_json_schema()},
                  description='Success')
@openapi.response(status=404, description='Error')
async def update_objective(request: Request, db: Database, thorny_id: int, quest_id: int, objective_id: int):
    """
    Update Specific User's Quest Objective

    Updates a user's quest objective.
    """
    model: user.UserObjectiveModel = await user.UserObjectiveModel.fetch(db, thorny_id, quest_id, objective_id)
    update_dict = {}

    for k, v in user.UserObjectiveUpdateModel(**request.json).model_dump().items():
        if v is not None:
            update_dict[k] = v

    model = model.model_copy(update=update_dict)

    await model.update(db, thorny_id)

    return sanic.json(model.model_dump(), default=str)
