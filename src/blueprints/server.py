from sanic import Blueprint, Request, exceptions
import sanic
from sanic_ext import openapi, validate

from src.database import Database
from src.models import server

server_blueprint = Blueprint("server", url_prefix='/server')

@server_blueprint.route('/players', methods=['POST'])
@openapi.definition(body={'application/json': server.PlayerListCreateModel.doc_schema()})
@openapi.response(status=201,
                  description='Success',
                  content={'application/json': server.PlayerListModel.doc_schema()})
async def create_player(request: Request, db: Database):
    """
    Add or update player's location
    """
    body = server.PlayerListCreateModel(**{'root': request.json})
    await server.PlayerListModel.update(db, body)

    return sanic.json(status=201, body={}, default=str)


@server_blueprint.route('/players', methods=['GET'])
@openapi.response(status=200,
                  description='Success',
                  content={'application/json': server.PlayerListModel.doc_schema()})
async def get_players(request: Request, db: Database):
    data = await server.PlayerListModel.fetch(db)

    return sanic.json(status=200, body=data.model_dump(), default=str)