from sanic import Blueprint, Request
import sanic
from sanic_ext import openapi, validate
from sanic_ext.extensions.openapi.definitions import RequestBody, Response

from src.database import Database
from src.models.server import players, items, world
from src.utils.errors import BadRequest400, NotFound404

server_blueprint = Blueprint("server", url_prefix='/server')

@server_blueprint.route('/players', methods=['POST'])
@openapi.definition(body={'application/json': players.PlayerListCreateModel.doc_schema()})
@openapi.response(status=201,
                  description='Success',
                  content={'application/json': players.PlayerListModel.doc_schema()})
async def create_player(request: Request, db: Database):
    """
    Add or update player's location
    """
    body = players.PlayerListCreateModel(**{'root': request.json})
    await players.PlayerListModel.update(db, body)

    return sanic.json(status=201, body={}, default=str)


@server_blueprint.route('/players', methods=['GET'])
@openapi.response(status=200,
                  description='Success',
                  content={'application/json': players.PlayerListModel.doc_schema()})
async def get_players(request: Request, db: Database):
    data = await players.PlayerListModel.fetch(db)

    return sanic.json(status=200, body=data.model_dump(), default=str)


@server_blueprint.route('/items', methods=['POST'])
@openapi.definition(body=RequestBody(items.ItemCreateModel.doc_schema()),
                    response=[
                        Response(items.ItemModel.doc_schema(), 201),
                        Response(BadRequest400, 400)
                    ])
@validate(json=items.ItemCreateModel)
async def create_item(request: Request, db: Database, body: items.ItemCreateModel):
    """
    Create New Item

    Creates a new item to be available for sacrificing
    If an item with these ID's already exists, it returns a 500.
    """
    try:
        await items.ItemModel.fetch(db, body.item_id)
        raise BadRequest400('This item already exists')
    except NotFound404:
        await items.ItemModel.create(db, body)

        item_model = await items.ItemModel.fetch(db, body.item_id)

    return sanic.json(status=201, body=item_model.model_dump(), default=str)


@server_blueprint.route('/items', methods=['GET'])
@openapi.definition(response=[
                        Response(items.ItemListModel.doc_schema(), 200)
                    ])
async def get_all_items(request: Request, db: Database):
    """
    Get All Item

    This returns a list of all Items
    """
    items_model = await items.ItemListModel.fetch(db)

    return sanic.json(items_model.model_dump(), default=str)


@server_blueprint.route('/items/<item_id:str>', methods=['GET'])
@openapi.definition(response=[
                        Response(items.ItemModel.doc_schema(), 200),
                        Response(NotFound404, 404)
                    ])
async def get_item(request: Request, db: Database, item_id: str):
    """
    Get Item

    This returns the Item
    """
    item_model = await items.ItemModel.fetch(db, item_id.replace('%3A', ":"))

    return sanic.json(item_model.model_dump(), default=str)


@server_blueprint.route('/items/<item_id:str>', methods=['PATCH', 'PUT'])
@openapi.definition(body=RequestBody(items.ItemUpdateModel.doc_schema()),
                    response=[
                        Response(items.ItemModel.doc_schema(), 201),
                        Response(BadRequest400, 400)
                    ])
@validate(json=items.ItemUpdateModel)
async def update_item(request: Request, db: Database, item_id: str, body: items.ItemUpdateModel):
    """
    Update Item

    This updates an item. All fields are optional, meaning you may
    set a field to `null` to not update it.
    """
    model = await items.ItemModel.fetch(db, item_id)
    await model.update(db, body)

    return sanic.json(body.model_dump(), default=str)


@server_blueprint.route('/world/<guild_id:int>', methods=['GET'])
@openapi.definition(response=[
                        Response(world.WorldModel.doc_schema(), 200),
                        Response(NotFound404, 404)
                    ])
async def get_world(request: Request, db: Database, guild_id: int):
    """
    Get World

    This returns the World
    """
    world_model = await world.WorldModel.fetch(db, guild_id)

    return sanic.json(world_model.model_dump(), default=str)


@server_blueprint.route('/world/<guild_id:int>', methods=['PATCH', 'PUT'])
@openapi.definition(body=RequestBody(world.WorldUpdateModel.doc_schema()),
                    response=[
                        Response(world.WorldModel.doc_schema(), 201),
                        Response(BadRequest400, 400)
                    ])
@validate(json=world.WorldUpdateModel)
async def update_world(request: Request, db: Database, guild_id: int, body: world.WorldUpdateModel):
    """
    Update World

    This updates a world. All fields are optional, meaning you may
    set a field to `null` to not update it.
    """
    model = await world.WorldModel.fetch(db, guild_id)
    await model.update(db, body)

    return sanic.json(model.model_dump(), default=str)
