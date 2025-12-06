from datetime import datetime

from sanic import Blueprint, Request
import sanic
from sanic_ext.extensions.openapi.definitions import Response, RequestBody, Parameter

from src.database import Database

from sanic_ext import openapi, validate

from src.models.users import playtime
from src.models.server import interactions, connections, relay
from src.models.wrapped.wrapped import EverthornWrapped2025
from src.utils.errors import NotFound404, BadRequest400

wrapped_blueprint = Blueprint('wrapped', '/wrapped')


@wrapped_blueprint.route('/<thorny_id:int>', methods=['GET'])
@openapi.definition(
    response=[
        Response(EverthornWrapped2025.doc_schema(), 200),
        Response(BadRequest400, 400),
        Response(NotFound404, 404)
    ]
)
async def get_wrapped(request: Request, db: Database, thorny_id: int):
    """
    Get Everthorn Wrapped 2025

    Returns the wrapped statistics for a user for the year 2025.
    Includes playtime, quests, rewards, interactions, projects, and grind day metrics.
    """
    wrapped_data = await EverthornWrapped2025.fetch(db, thorny_id)

    return sanic.json(wrapped_data.model_dump(), default=str)
