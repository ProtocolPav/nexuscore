from sanic import Blueprint, Request
import sanic
from sanic_ext import openapi

from src.database import Database
from src.models import quest
from src.views.quest import QuestView, QuestCreateView

quest_blueprint = Blueprint("quest_routes", url_prefix='/quests')


@quest_blueprint.route('/', methods=['POST'])
@openapi.body(content={'application/json': QuestCreateView.view_schema()})
@openapi.response(status=201, description="Success")
async def create_quest(request: Request, db: Database):
    view = QuestCreateView(**request.json)

    await QuestView.new(db, view)

    return sanic.HTTPResponse(status=201)


@quest_blueprint.get('/<quest_id:int>')
@openapi.response(status=200,
                  content={'application/json': QuestView.view_schema()})
async def get_quest(request: Request, db: Database, quest_id: int):
    quest_view = await QuestView.build(db, quest_id)

    return sanic.json(quest_view.model_dump(), default=str)
