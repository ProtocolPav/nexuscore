from sanic import Blueprint, Request
import sanic
from sanic_ext import openapi, validate

from src.database import Database

from src.models import quests

quest_blueprint = Blueprint("quests", url_prefix='/quests')


@quest_blueprint.route('/', methods=['POST'])
@openapi.body(content={'application/json': quests.QuestCreateModel.doc_schema()})
@openapi.response(status=201,
                  content={'application/json': quests.QuestModel.doc_schema()},
                  description='Success')
async def create_quest(request: Request, db: Database):
    """
    Create New Quest

    Creates a new quest based on the information provided.
    Some fields are optional and can be `null` while others are required.
    Check the schema for more info on that.
    """
    quest_create_model = quests.QuestCreateModel(**request.json)

    quest_id = await quests.QuestModel.new(db, quest_create_model)
    quest_model = await quests.QuestModel.fetch(db, quest_id)

    return sanic.json(status=201, body=quest_model.model_dump(), default=str)


@quest_blueprint.route('/', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': quests.QuestListModel.doc_schema()})
async def get_all_quests(request: Request, db: Database):
    """
    Get All Quests

    Returns all quests ordered by start date, recent first
    """
    quests_model = await quests.QuestListModel.fetch(db)

    return sanic.json(quests_model.model_dump(), default=str)


@quest_blueprint.route('/<quest_id:int>', methods=['GET'])
@openapi.response(status=200, content={'application/json': quests.QuestModel.doc_schema()})
async def get_quest(request: Request, db: Database, quest_id: int):
    """
    Get Quest

    Returns a specific quest, objectives and rewards
    """
    quest_model = await quests.QuestModel.fetch(db, quest_id)

    return sanic.json(quest_model.model_dump(), default=str)


@quest_blueprint.route('/<quest_id:int>/objectives', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': quests.ObjectivesListModel.doc_schema()})
async def get_objectives(request: Request, db: Database, quest_id: int):
    """
    Get All Objectives

    Returns a list of all the objectives a quest has
    """
    objectives_model = await quests.ObjectivesListModel.fetch(db, quest_id)

    return sanic.json(objectives_model.model_dump(), default=str)


@quest_blueprint.route('/<quest_id:int>/objectives/<objective_id:int>', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': quests.ObjectiveModel.doc_schema()})
async def get_objective(request: Request, db: Database, quest_id: int, objective_id: int):
    """
    Get Objective

    Returns the specified objective
    """
    objective_model = await quests.ObjectiveModel.fetch(db, quest_id, objective_id)

    return sanic.json(objective_model.model_dump(), default=str)


@quest_blueprint.route('/<quest_id:int>/objectives/<objective_id:int>/rewards', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': quests.RewardsListModel.doc_schema()})
async def get_rewards(request: Request, db: Database, quest_id: int, objective_id: int):
    """
    Get All Rewards

    Returns all the rewards of the specified objective
    """
    rewards_model = await quests.RewardsListModel.fetch(db, quest_id, objective_id)

    return sanic.json(rewards_model.model_dump(), default=str)


@quest_blueprint.route('/<quest_id:int>', methods=['PATCH', 'PUT'])
@openapi.body(content={'application/json': quests.QuestUpdateModel.doc_schema()})
@openapi.response(status=200, content={'application/json': quests.QuestModel.doc_schema()})
async def update_quest(request: Request, db: Database, quest_id: int):
    """
    Update Quest

    Update a quest
    """
    model: quests.QuestModel = await quests.QuestModel.fetch(db, quest_id)
    update_dict = {}

    for k, v in quests.QuestUpdateModel(**request.json).model_dump().items():
        if v is not None:
            update_dict[k] = v

    model = model.model_copy(update=update_dict)

    await model.update(db)

    return sanic.json(model.model_dump(), default=str)


@quest_blueprint.route('/reward/<reward_id:int>', methods=['PATCH', 'PUT'])
@openapi.body(content={'application/json': quests.RewardUpdateModel.doc_schema()})
@openapi.response(status=200, content={'application/json': quests.RewardModel.doc_schema()})
async def update_reward(request: Request, db: Database, reward_id: int):
    """
    Update Reward

    Update an objective's reward
    """
    model: quests.RewardModel = await quests.RewardModel.fetch(db, reward_id)
    update_dict = {}

    for k, v in quests.RewardUpdateModel(**request.json).model_dump().items():
        if v is not None:
            update_dict[k] = v

    model = model.model_copy(update=update_dict)

    await model.update(db)

    return sanic.json(model.model_dump(), default=str)


@quest_blueprint.route('/objective/<objective_id:int>', methods=['PATCH', 'PUT'])
@openapi.body(content={'application/json': quests.ObjectiveUpdateModel.doc_schema()})
@openapi.response(status=200, content={'application/json': quests.ObjectiveModel.doc_schema()})
async def update_objective(request: Request, db: Database, objective_id: int):
    """
    Update Objective

    Update a quest's objective
    """
    model: quests.ObjectiveModel = await quests.ObjectiveModel.fetch(db, objective_id)
    update_dict = {}

    for k, v in quests.ObjectiveUpdateModel(**request.json).model_dump().items():
        if v is not None:
            update_dict[k] = v

    model = model.model_copy(update=update_dict)

    await model.update(db)

    return sanic.json(model.model_dump(), default=str)
