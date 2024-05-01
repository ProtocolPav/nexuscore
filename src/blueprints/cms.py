from sanic import Blueprint, Request
from sanic import json as sanicjson

content_blueprint = Blueprint('content', '/cms')


@content_blueprint.get('/<page_uid:str>')
async def get_page_data(request: Request):
    ...


@content_blueprint.put('/<page_uid:str>')
async def update_page_data(request: Request):
    ...


@content_blueprint.post('/<page_uid:str>')
async def create_page(request: Request):
    ...
