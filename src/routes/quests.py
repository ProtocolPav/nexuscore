from sanic import Blueprint, Request
import sanic
from sanic_ext import openapi, validate
from sanic_ext.extensions.openapi.definitions import RequestBody, Response

from src.utils.errors import BadRequest400, NotFound404

from src.database import Database

from src.models import quests

quest_blueprint = Blueprint("quests", url_prefix='/quests')


@quest_blueprint.route('/', methods=['POST'])
@openapi.definition(body=RequestBody(quests.QuestCreateModel.doc_schema()),
                    response=[
                        Response(quests.QuestModel.doc_schema(), 201),
                        Response(BadRequest400, 400)
                    ])
@validate(json=quests.QuestCreateModel)
async def create_quest(request: Request, db: Database, body: quests.QuestCreateModel):
    """
    Create New Quest

    Creates a new quest based on the information provided.
    Some fields are optional and can be `null` while others are required.
    Check the schema for more info on that.
    """
    quest_id = await quests.QuestModel.create(db, body)
    quest_model = await quests.QuestModel.fetch(db, quest_id)

    return sanic.json(status=201, body=quest_model.model_dump(), default=str)


@quest_blueprint.route('/', methods=['GET'])
@openapi.definition(response=[
                        Response(quests.QuestListModel.doc_schema(), 200),
                        Response(NotFound404, 404)
                    ])
async def get_all_quests(request: Request, db: Database):
    """
    Get All Quests

    Returns all quests ordered by start date, recent first
    """
    quests_model = await quests.QuestListModel.fetch(db)

    return sanic.json(quests_model.model_dump(), default=str)


@quest_blueprint.route('/<quest_id:int>', methods=['GET'])
@openapi.definition(response=[
                        Response(quests.QuestModel.doc_schema(), 200),
                        Response(NotFound404, 404)
                    ])
async def get_quest(request: Request, db: Database, quest_id: int):
    """
    Get Quest

    Returns a specific quest, objectives and rewards
    """
    quest_model = await quests.QuestModel.fetch(db, quest_id)

    return sanic.json(quest_model.model_dump(), default=str)


@quest_blueprint.route('/<quest_id:int>/objectives', methods=['GET'])
@openapi.definition(response=[
                        Response(quests.ObjectivesListModel.doc_schema(), 200),
                        Response(NotFound404, 404)
                    ])
async def get_objectives(request: Request, db: Database, quest_id: int):
    """
    Get All Objectives

    Returns a list of all the objectives a quest has
    """
    objectives_model = await quests.ObjectivesListModel.fetch(db, quest_id)

    return sanic.json(objectives_model.model_dump(), default=str)


@quest_blueprint.route('/<quest_id:int>/objectives/<objective_id:int>', methods=['GET'])
@openapi.definition(response=[
                        Response(quests.ObjectiveModel.doc_schema(), 200),
                        Response(NotFound404, 404)
                    ])
async def get_objective(request: Request, db: Database, quest_id: int, objective_id: int):
    """
    Get Objective

    Returns the specified objective
    """
    objective_model = await quests.ObjectiveModel.fetch(db, quest_id, objective_id)

    return sanic.json(objective_model.model_dump(), default=str)


@quest_blueprint.route('/<quest_id:int>/objectives/<objective_id:int>/rewards', methods=['GET'])
@openapi.definition(response=[
                        Response(quests.RewardsListModel.doc_schema(), 200),
                        Response(NotFound404, 404)
                    ])
async def get_rewards(request: Request, db: Database, quest_id: int, objective_id: int):
    """
    Get All Rewards

    Returns all the rewards of the specified objective
    """
    rewards_model = await quests.RewardsListModel.fetch(db, quest_id, objective_id)

    return sanic.json(rewards_model.model_dump(), default=str)


@quest_blueprint.route('/<quest_id:int>', methods=['PATCH', 'PUT'])
@openapi.definition(body=RequestBody(quests.QuestUpdateModel.doc_schema()),
                    response=[
                        Response(quests.QuestModel.doc_schema(), 200),
                        Response(BadRequest400, 400),
                        Response(NotFound404, 404)
                    ])
@validate(json=quests.QuestUpdateModel)
async def update_quest(request: Request, db: Database, quest_id: int, body: quests.QuestUpdateModel):
    """
    Update Quest

    Update a quest
    """
    model: quests.QuestModel = await quests.QuestModel.fetch(db, quest_id)
    update_dict = {}

    for k, v in body.model_dump().items():
        if v is not None:
            update_dict[k] = v

    model = model.model_copy(update=update_dict)

    await model.update(db)

    return sanic.json(model.model_dump(), default=str)


@quest_blueprint.route('/reward/<reward_id:int>', methods=['PATCH', 'PUT'])
@openapi.definition(body=RequestBody(quests.RewardUpdateModel.doc_schema()),
                    response=[
                        Response(quests.RewardModel.doc_schema(), 200),
                        Response(BadRequest400, 400),
                        Response(NotFound404, 404)
                    ])
@validate(json=quests.RewardUpdateModel)
async def update_reward(request: Request, db: Database, reward_id: int, body: quests.RewardUpdateModel):
    """
    Update Reward

    Update an objective's reward
    """
    model: quests.RewardModel = await quests.RewardModel.fetch(db, reward_id)
    update_dict = {}

    for k, v in body.model_dump().items():
        if v is not None:
            update_dict[k] = v

    model = model.model_copy(update=update_dict)

    await model.update(db)

    return sanic.json(model.model_dump(), default=str)


@quest_blueprint.route('/objective/<objective_id:int>', methods=['PATCH', 'PUT'])
@openapi.definition(body=RequestBody(quests.ObjectiveUpdateModel.doc_schema()),
                    response=[
                        Response(quests.ObjectiveModel.doc_schema(), 200),
                        Response(BadRequest400, 400),
                        Response(NotFound404, 404)
                    ])
@validate(json=quests.ObjectiveUpdateModel)
async def update_objective(request: Request, db: Database, objective_id: int, body: quests.ObjectiveUpdateModel):
    """
    Update Objective

    Update a quest's objective
    """
    model: quests.ObjectiveModel = await quests.ObjectiveModel.fetch(db, objective_id)
    update_dict = {}

    for k, v in body.model_dump().items():
        if v is not None:
            update_dict[k] = v

    model = model.model_copy(update=update_dict)

    await model.update(db)

    return sanic.json(model.model_dump(), default=str)
