from fastapi import APIRouter, HTTPException, status

from src.dependencies.database import db

from src.models.server import items

server = APIRouter(prefix='/server', tags=['Server'])


@server.post('/items', status_code=status.HTTP_201_CREATED)
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


@server.get('/items')
async def get_all_items() -> items.ItemListModel:
    """
    Get All Item

    This returns a list of all Items
    """
    items_model = await items.ItemListModel.fetch(db)

    return items_model


@server.get('/items/{item_id}')
async def get_item(item_id: str) -> items.ItemModel:
    """
    Get Item

    This returns the Item
    """
    item_model = await items.ItemModel.fetch(db, item_id.replace('%3A', ':'))

    return item_model


@server.patch('/items/{item_id}')
@server.put('/items/{item_id}')
async def update_item(item_id: str, body: items.ItemUpdateModel) -> items.ItemModel:
    """
    Update Item

    This updates an item. All fields are optional, meaning you may
    set a field to `null` to not update it.
    """
    model = await items.ItemModel.fetch(db, item_id)
    await model.update(db, body)

    return model