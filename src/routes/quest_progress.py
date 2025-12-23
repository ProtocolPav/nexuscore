from datetime import datetime

from sanic import Blueprint, Request
import sanic
from sanic_ext import openapi, validate
from sanic_ext.extensions.openapi.definitions import Parameter, RequestBody, Response

from src.utils.errors import BadRequest400, NotFound404

from src.database import Database

from src.models.quests import quest_progress, objective_progress

progress_blueprint = Blueprint("quest_progress", url_prefix='/quests/progress')


@progress_blueprint.route('/', methods=['POST'])
@openapi.definition(body=RequestBody(quest_progress.QuestProgressCreateModel.doc_schema()),
                    response=[
                        Response(quest_progress.QuestProgressModel.doc_schema(), 201),
                        Response(BadRequest400, 400)
                    ])
@validate(json=quest_progress.QuestProgressCreateModel)
async def create_quest_progress(request: Request, db: Database, body: quest_progress.QuestProgressCreateModel):
    """
    Create New Quest Progress

    Adds a new quest to a user, tracking their progress.
    Automatically sets the quest progress to "active".
    """
    quest_id = await quest_progress.QuestProgressModel.create(db, body)
    quest_model = await quest_progress.QuestProgressModel.fetch(db, quest_id)
    await quest_model.update(db, quest_progress.QuestProgressUpdateModel(status='active'))
    await quest_model.objectives[0].update(db, quest_progress.ObjectiveProgressUpdateModel(status='active'))

    return sanic.json(status=201, body=quest_model.model_dump(), default=str)


@progress_blueprint.route('/user/<thorny_id:int>', methods=['GET'])
@openapi.definition(response=[
    Response(quest_progress.QuestProgressListModel.doc_schema(), 200),
    Response(NotFound404, 404)
])
async def get_all_quests(request: Request, db: Database, thorny_id: int):
    """
    Get All User's Quest Progress

    Returns all quest progress belonging to a user
    """
    quests_list = await quest_progress.QuestProgressListModel.fetch(db, thorny_id)

    return sanic.json(quests_list.model_dump(), default=str)


@progress_blueprint.route('/user/<thorny_id:int>/active', methods=['GET'])
@openapi.definition(response=[
    Response(quest_progress.QuestProgressModel.doc_schema(), 200),
    Response(NotFound404, 404)
])
async def get_active_quest(request: Request, db: Database, thorny_id: int):
    """
    Get User's Active Quest

    Returns the user's currently active quest.
    """
    quest = await quest_progress.QuestProgressModel.fetch_active_quest(db, thorny_id)

    return sanic.json(quest.model_dump(), default=str)


@progress_blueprint.route('/user/<thorny_id:int>/active', methods=['DELETE'])
@openapi.definition(response=[
    Response(204),
    Response(BadRequest400, 400),
    Response(NotFound404, 404)
])
async def fail_active_quest(request: Request, db: Database, thorny_id: int):
    """
    Fail User's Active Quest

    This marks the active quest and all of its objectives as "failed".
    """
    quest = await quest_progress.QuestProgressModel.fetch_active_quest(db, thorny_id)
    await quest.mark_failed(db)

    return sanic.empty(status=204)


@progress_blueprint.route('/<progress_id:int>', methods=['PUT'])
@openapi.definition(body=RequestBody(quest_progress.QuestProgressUpdateModel.doc_schema()),
                    response=[
                        Response(quest_progress.QuestProgressModel.doc_schema(), 200),
                        Response(BadRequest400, 400)
                    ])
@validate(json=quest_progress.QuestProgressUpdateModel)
async def update_quest(request: Request, db: Database, progress_id: int, body):
    """
    Update Specific User's Quest

    Updates a user's quest. Note this does not update objectives.
    """
    model = await quest_progress.QuestProgressModel.fetch(db, progress_id)
    await model.update(db, body)

    return sanic.json(model.model_dump(), default=str)


@progress_blueprint.route('/<progress_id:int>/<objective_id:int>', methods=['PUT'])
@openapi.definition(body=RequestBody(objective_progress.ObjectiveProgressUpdateModel.doc_schema()),
                    response=[
                        Response(objective_progress.ObjectiveProgressModel.doc_schema(), 200),
                        Response(BadRequest400, 400)
                    ])
@validate(json=objective_progress.ObjectiveProgressUpdateModel)
async def update_objective(request: Request, db: Database, progress_id: int, objective_id: int, body):
    """
    Update Specific User's Quest Objective

    Updates a user's quest objective.
    """
    model = await objective_progress.ObjectiveProgressModel.fetch(db, progress_id, objective_id)
    await model.update(db, body)

    return sanic.json(model.model_dump(), default=str)
