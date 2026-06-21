from fastapi import APIRouter, Depends, HTTPException, Security
from starlette import status

from src.dependencies.auth import Scope, get_guild_client
from src.dependencies.services import get_world_service
from src.dependencies.database import db

from src.models.auth import TokenPayload
from src.models.worlds import world
from src.models import items

from src.services.world import WorldService

world_router = APIRouter(prefix='/guilds/me/worlds', tags=['Worlds'])


@world_router.get('')
async def get_world(
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_READ]),
        service: WorldService = Depends(get_world_service),
) -> world.WorldOut:
    return await service.get(auth.guild_id)


@world_router.patch('')
@world_router.put('')
async def partial_update_world(
        body: world.WorldUpdate,
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_WRITE]),
        service: WorldService = Depends(get_world_service),
) -> world.WorldOut:
    return await service.update(auth.guild_id, body)


@world_router.post('/items', status_code=status.HTTP_201_CREATED)
async def create_item(body: items.ItemCreateModel) -> items.ItemModel:
    """
    Create New Item

    Creates a new item to be available for sacrificing
    If an item with these ID's already exists, it returns a 500.
    """
    try:
        await items.ItemModel.fetch(db, body.item_id)
        raise HTTPException(status_code=400, detail='This item already exists')
    except HTTPException as e:
        if e.status_code == 404:
            await items.ItemModel.create(db, body)

            item_model = await items.ItemModel.fetch(db, body.item_id)
        else:
            raise e

    return item_model


@world_router.get('/items')
async def get_all_items() -> items.ItemListModel:
    """
    Get All Item

    This returns a list of all Items
    """
    items_model = await items.ItemListModel.fetch(db)

    return items_model


@world_router.get('/items/{item_id}')
async def get_item(item_id: str) -> items.ItemModel:
    """
    Get Item

    This returns the Item
    """
    item_model = await items.ItemModel.fetch(db, item_id.replace('%3A', ':'))

    return item_model


@world_router.patch('/items/{item_id}')
@world_router.put('/items/{item_id}')
async def update_item(item_id: str, body: items.ItemUpdateModel) -> items.ItemModel:
    """
    Update Item

    This updates an item. All fields are optional, meaning you may
    set a field to `null` to not update it.
    """
    model = await items.ItemModel.fetch(db, item_id)
    await model.update(db, body)

    return model