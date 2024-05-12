from sanic import Sanic, Request
from sanic.response import json as sanicjson
from src.model_factory import Factory
import asyncio

from src.blueprints import blueprint_group

app = Sanic("nexuscore")

"""
GET retrieve all or just one resource.

POST is normally for create a new resource.

PUT used to update a resource

DELETE delete a resource
"""


@app.route('/')
async def test(request: Request):
    return sanicjson({'hello': 'world'})


@app.listener('after_server_start')
async def init_db_pool(application: Sanic, loop: asyncio.AbstractEventLoop):
    await Factory.init_pool()

app.blueprint(blueprint_group)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
