from datetime import datetime

from sanic import Blueprint, Request
import sanic
from sanic_ext import openapi, validate
from sanic_ext.extensions.openapi.definitions import Parameter, RequestBody, Response

from src.utils.errors import BadRequest400, NotFound404

from src.database import Database

from src.models.quests import objective, quest, reward

quest_blueprint = Blueprint("quests", url_prefix='/quests')


@quest_blueprint.route('/', methods=['POST'])
@openapi.definition(body=RequestBody(quest.QuestCreateModel.doc_schema()),
                    response=[
                        Response(quest.QuestModel.doc_schema(), 201),
                        Response(BadRequest400, 400)
                    ])
@validate(json=quest.QuestCreateModel)
async def create_quest(request: Request, db: Database, body: quest.QuestCreateModel):
    """
    Create New Quest

    Creates a new quest based on the information provided.
    Some fields are optional and can be `null` while others are required.
    Check the schema for more info on that.
    """
    quest_id = await quest.QuestModel.create(db, body)
    quest_model = await quest.QuestModel.fetch(db, quest_id)

    return sanic.json(status=201, body=quest_model.model_dump(), default=str)


@quest_blueprint.route('/', methods=['GET'])
@openapi.definition(response=[
    Response(quest.QuestListModel.doc_schema(), 200),
],
    parameter=[
        Parameter('creator_thorny_ids', list[int], description="Filter by creator"),
        Parameter('quest_types', list[str], description="Filter by quest type"),
        Parameter('time_start', datetime, description="The start time to filter by"),
        Parameter('time_end', datetime, description="The end time to filter by"),
        Parameter('page', int, description="The page to return. Default: 1"),
        Parameter('page_size', int, description="The size of each page in items. Default: 100")
    ])
async def get_all_quests(request: Request, db: Database):
    """
    Get All Quests

    Returns all quests ordered by start date, recent first
    """
    creator_thorny_ids = request.args.getlist('creator_thorny_ids')
    quest_types = request.args.getlist('quest_types')
    time_start = request.args.get('time_start')
    time_end = request.args.get('time_end')

    page = request.args.get('page')
    page_size = request.args.get('page_size')

    quests_model = await quest.QuestListModel.fetch(db,
                                                    time_start,
                                                    time_end,
                                                    creator_thorny_ids,
                                                    quest_types)

    return sanic.json(quests_model.model_dump(), default=str)


@quest_blueprint.route('/<quest_id:int>', methods=['GET'])
@openapi.definition(response=[
                        Response(quest.QuestModel.doc_schema(), 200),
                        Response(NotFound404, 404)
                    ])
async def get_quest(request: Request, db: Database, quest_id: int):
    """
    Get Quest

    Returns a specific quest, objectives and rewards
    """
    quest_model = await quest.QuestModel.fetch(db, quest_id)

    return sanic.json(quest_model.model_dump(), default=str)


@quest_blueprint.route('/<quest_id:int>/objectives', methods=['GET'])
@openapi.definition(response=[
                        Response(objective.ObjectivesListModel.doc_schema(), 200)
                    ])
async def get_objectives(request: Request, db: Database, quest_id: int):
    """
    Get All Objectives

    Returns a list of all the objectives a quest has
    """
    objectives_model = await objective.ObjectivesListModel.fetch(db, quest_id)

    return sanic.json(objectives_model.model_dump(), default=str)


@quest_blueprint.route('/<quest_id:int>/objectives/<objective_id:int>', methods=['GET'])
@openapi.definition(response=[
                        Response(objective.ObjectiveModel.doc_schema(), 200),
                        Response(NotFound404, 404)
                    ])
async def get_objective(request: Request, db: Database, quest_id: int, objective_id: int):
    """
    Get Objective

    Returns the specified objective
    """
    objective_model = await objective.ObjectiveModel.fetch(db, quest_id, objective_id)

    return sanic.json(objective_model.model_dump(), default=str)


@quest_blueprint.route('/<quest_id:int>/objectives/<objective_id:int>/rewards', methods=['GET'])
@openapi.definition(response=[
                        Response(reward.RewardsListModel.doc_schema(), 200)
                    ])
async def get_rewards(request: Request, db: Database, quest_id: int, objective_id: int):
    """
    Get All Rewards

    Returns all the rewards of the specified objective
    """
    rewards_model = await reward.RewardsListModel.fetch(db, quest_id, objective_id)

    return sanic.json(rewards_model.model_dump(), default=str)


@quest_blueprint.route('/<quest_id:int>', methods=['PATCH', 'PUT'])
@openapi.definition(body=RequestBody(quest.QuestUpdateModel.doc_schema()),
                    response=[
                        Response(quest.QuestModel.doc_schema(), 200),
                        Response(BadRequest400, 400),
                        Response(NotFound404, 404)
                    ])
@validate(json=quest.QuestUpdateModel)
async def update_quest(request: Request, db: Database, quest_id: int, body: quest.QuestUpdateModel):
    """
    Update Quest

    Update a quest
    """
    model = await quest.QuestModel.fetch(db, quest_id)
    await model.update(db, body)

    return sanic.json(model.model_dump(), default=str)


@quest_blueprint.route('/reward/<reward_id:int>', methods=['PATCH', 'PUT'])
@openapi.definition(body=RequestBody(reward.RewardUpdateModel.doc_schema()),
                    response=[
                        Response(reward.RewardModel.doc_schema(), 200),
                        Response(BadRequest400, 400),
                        Response(NotFound404, 404)
                    ])
@validate(json=reward.RewardUpdateModel)
async def update_reward(request: Request, db: Database, reward_id: int, body: reward.RewardUpdateModel):
    """
    Update Reward

    Update an objective's reward
    """
    model = await reward.RewardModel.fetch(db, reward_id)
    await model.update(db, body)

    return sanic.json(model.model_dump(), default=str)


@quest_blueprint.route('/objective/<objective_id:int>', methods=['PATCH', 'PUT'])
@openapi.definition(body=RequestBody(objective.ObjectiveUpdateModel.doc_schema()),
                    response=[
                        Response(objective.ObjectiveModel.doc_schema(), 200),
                        Response(BadRequest400, 400),
                        Response(NotFound404, 404)
                    ])
@validate(json=objective.ObjectiveUpdateModel)
async def update_objective(request: Request, db: Database, objective_id: int, body: objective.ObjectiveUpdateModel):
    """
    Update Objective

    Update a quest's objective
    """
    model = await objective.ObjectiveModel.fetch(db, objective_id)
    await model.update(db, body)

    return sanic.json(model.model_dump(), default=str)
