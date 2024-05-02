from sanic import Blueprint, Request
from sanic import json as sanicjson

content_blueprint = Blueprint('content', '/cms')


@content_blueprint.route('/<page_uid:str>', methods=['GET', 'PUT', 'POST'])
async def page_data(request: Request):
    if request.method == 'GET':
        ...
    elif request.method == 'POST':
        ...
    elif request.method == 'PUT':
        ...


async def get_page_data(request: Request):
    ...


async def update_page_data(request: Request):
    ...


async def create_page(request: Request):
    ...