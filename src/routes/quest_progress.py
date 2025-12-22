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

