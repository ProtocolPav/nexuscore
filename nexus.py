from sanic import Sanic, Request, HTTPResponse
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


@app.route('/healthcheck')
async def health_check(request: Request):
    """
    Used by GCP to check for instance health,
    GCP will automatically restart the instance if this health check
    returns a 404 3 times in a row
    """
    return HTTPResponse(status=200)


@app.listener('after_server_start')
async def init_db_pool(application: Sanic, loop: asyncio.AbstractEventLoop):
    await Factory.init_pool()

app.blueprint(blueprint_group)

if __name__ == "__main__":
    app.run(host="0.0.0.0", dev=True)
    # app.run(host="0.0.0.0", auto_reload=True, fast=True)
