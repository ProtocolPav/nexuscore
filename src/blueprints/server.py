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


@server_blueprint.route('/items', methods=['POST'])
@openapi.response(status=201,
                  content={'application/json': server.ItemModel.doc_schema()},
                  description='Success')
@openapi.response(status=500, description='Item Already Exists')
@openapi.definition(body={'application/json': server.ItemCreateModel.doc_schema()})
@validate(json=server.ItemCreateModel)
async def create_item(request: Request, db: Database, body: server.ItemCreateModel):
    """
    Create New Item

    Creates a new item to be available for sacrificing
    If an item with these ID's already exists, it returns a 500.
    """
    if await server.ItemModel.fetch(db, body.item_id):
        raise exceptions.SanicException(status_code=500, message="This item already exists")
    else:
        await server.ItemModel.new(db, body)

        item_model = await server.ItemModel.fetch(db, body.item_id)

    return sanic.json(status=201, body=item_model.model_dump(), default=str)


@server_blueprint.route('/items', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': server.ItemListModel.doc_schema()},
                  description='Success')
@openapi.response(status=404, description='Item does not exist')
async def get_all_items(request: Request, db: Database):
    """
    Get All Item

    This returns a list of all Items
    """
    item_model = await server.ItemListModel.fetch(db)

    if not item_model:
        raise exceptions.NotFound("Could not find this item. Maybe time to create one?")

    return sanic.json(item_model.model_dump(), default=str)


@server_blueprint.route('/items/<item_id:str>', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': server.ItemModel.doc_schema()},
                  description='Success')
@openapi.response(status=404, description='Item does not exist')
async def get_item(request: Request, db: Database, item_id: str):
    """
    Get Item

    This returns the Item
    """
    item_model = await server.ItemModel.fetch(db, item_id.replace('%3A', ":"))

    if not item_model:
        raise exceptions.NotFound("Could not find this item. Maybe time to create one?")

    return sanic.json(item_model.model_dump(), default=str)


@server_blueprint.route('/items/<item_id:str>', methods=['PATCH', 'PUT'])
@openapi.definition(body={'application/json': server.ItemCreateModel.doc_schema()})
@openapi.response(status=200,
                  content={'application/json': server.ItemModel.doc_schema()},
                  description='Success')
@openapi.response(status=404, description='Item does not exist')
@validate(json=server.ItemUpdateModel)
async def update_item(request: Request, db: Database, item_id: str, body: server.ItemCreateModel):
    """
    Update Item

    This updates an item. All fields are optional, meaning you may
    set a field to `null` to not update it.
    """
    model = await server.ItemModel.fetch(db, item_id.replace('%3A', ":"))

    if not model:
        raise exceptions.NotFound("Could not find this item")

    update_dict = {}

    for k, v in body.model_dump().items():
        if v is not None:
            update_dict[k] = v

    model = model.model_copy(update=update_dict)

    await model.update(db)

    return sanic.json(model.model_dump(), default=str)


@server_blueprint.route('/world/<guild_id:int>', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': server.WorldModel.doc_schema()},
                  description='Success')
@openapi.response(status=404, description='World does not exist')
async def get_world(request: Request, db: Database, guild_id: int):
    """
    Get World

    This returns the World
    """
    world_model = await server.WorldModel.fetch(db, guild_id)

    if not world_model:
        raise exceptions.NotFound("Could not find this world. Maybe time to create one?")

    return sanic.json(world_model.model_dump(), default=str)


@server_blueprint.route('/world/<guild_id:int>', methods=['PATCH', 'PUT'])
@openapi.definition(body={'application/json': server.WorldUpdateModel.doc_schema()})
@openapi.response(status=200,
                  content={'application/json': server.WorldModel.doc_schema()},
                  description='Success')
@openapi.response(status=404, description='Item does not exist')
@validate(json=server.WorldUpdateModel)
async def update_world(request: Request, db: Database, guild_id: int, body: server.WorldUpdateModel):
    """
    Update World

    This updates a world. All fields are optional, meaning you may
    set a field to `null` to not update it.
    """
    model = await server.WorldModel.fetch(db, guild_id)

    if not model:
        raise exceptions.NotFound("Could not find this world")

    update_dict = {}

    for k, v in body.model_dump().items():
        if v is not None:
            update_dict[k] = v

    model = model.model_copy(update=update_dict)

    await model.update(db)

    return sanic.json(model.model_dump(), default=str)
