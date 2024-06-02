from sanic import Blueprint, Request
import sanic
from sanic_ext import openapi

from src.database import Database
from src.models import quest
from src.views.quest import QuestView, QuestCreateView, AllQuestsView

quest_blueprint = Blueprint("quest_routes", url_prefix='/quests')


@quest_blueprint.route('/', methods=['POST'])
@openapi.body(content={'application/json': QuestCreateView.view_schema()})
@openapi.response(status=201, description="Success")
async def create_quest(request: Request, db: Database):
    """
    Create New Quest

    Creates a new quest based on the information provided.
    Some fields are optional and can be `null` while others are required.
    Check the schema for more info on that.
    """
    view = QuestCreateView(**request.json)

    await QuestView.new(db, view)

    return sanic.HTTPResponse(status=201)


@quest_blueprint.route('/', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': AllQuestsView.view_schema()})
async def get_all_quests(request: Request, db: Database):
    view = await AllQuestsView.build(db)

    return sanic.json(view.model_dump(), default=str)


@quest_blueprint.route('/<quest_id:int>', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': QuestView.view_schema()})
async def get_quest(request: Request, db: Database, quest_id: int):
    quest_view = await QuestView.build(db, quest_id)

    return sanic.json(quest_view.model_dump(), default=str)


@quest_blueprint.route('/<quest_id:int>', methods=['PATCH'])
@openapi.body(content={'application/json': quest.QuestUpdateModel.model_json_schema()})
@openapi.response(status=200,
                  content={'application/json': QuestView.view_schema()})
async def update_quest(request: Request, db: Database, quest_id: int):
    model: quest.QuestModel = await quest.QuestModel.fetch(db, quest_id)
    update_dict = {}

    for k, v in quest.QuestUpdateModel(**request.json).model_dump().items():
        if v is not None:
            update_dict[k] = v

    model = model.model_copy(update=update_dict)

    await model.update(db)

    return sanic.json(model.model_dump(), default=str)


@quest_blueprint.route('/reward/<reward_id:int>', methods=['PATCH'])
@openapi.body(content={'application/json': quest.RewardUpdateModel.model_json_schema()})
@openapi.response(status=200,
                  content={'application/json': QuestView.view_schema()})
async def update_reward(request: Request, db: Database, reward_id: int):
    model: quest.RewardModel = await quest.RewardModel.fetch(db, reward_id)
    update_dict = {}

    for k, v in quest.RewardUpdateModel(**request.json).model_dump().items():
        if v is not None:
            update_dict[k] = v

    model = model.model_copy(update=update_dict)

    await model.update(db)

    return sanic.json(model.model_dump(), default=str)


@quest_blueprint.route('/objective/<objective_id:int>', methods=['PATCH'])
@openapi.body(content={'application/json': quest.ObjectiveUpdateModel.model_json_schema()})
@openapi.response(status=200,
                  content={'application/json': QuestView.view_schema()})
async def update_objective(request: Request, db: Database, objective_id: int):
    model: quest.ObjectiveModel = await quest.ObjectiveModel.fetch(db, objective_id)
    update_dict = {}

    for k, v in quest.ObjectiveUpdateModel(**request.json).model_dump().items():
        if v is not None:
            update_dict[k] = v

    model = model.model_copy(update=update_dict)

    await model.update(db)

    return sanic.json(model.model_dump(), default=str)
