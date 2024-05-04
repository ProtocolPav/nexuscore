from sanic import Sanic, Request
from sanic.response import json as sanicjson
from src.db.pool import webserver_pool
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
    print("All routes ")
    for key, route in app.router.routes_all.items():
        print(f"/{route.path:60} - {route.name:70} -  {route.methods} [{route.router}]")

    for key, route in app.router.routes_all.items():
        print(f"```{' | '.join(list(route.methods)):20}   /{route.path}```")

    # await webserver_pool.init_pool()

app.blueprint(blueprint_group)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, single_process=True)