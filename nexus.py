import random

from sanic import Sanic, Request, text
from sanic.response import json as sanicjson
from datetime import datetime
from src.pool import webserver_pool
import asyncio
import httpx

import src.user as db

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


@app.route('/preemption/warning')
async def preempt(request: Request):
    """
    Called by the GCP to warn the systems of preemption
    """
    async with httpx.AsyncClient() as client:
        r = await client.get(f"http://thorny-bds:8000/server/preempt", timeout=None)

    return sanicjson({'server': 'preempted'})


@app.get('/api/v1/users/thorny-id/<thorny_id:int>')
async def get_user_thorny_id(request: Request, thorny_id: int):
    user = await db.fetch_user_by_id(thorny_id)
    return sanicjson(user, default=str)


@app.get('/api/v1/users/guild/<guild_id:int>/<gamertag:str>')
async def get_user_gamertag(request: Request, guild_id: int, gamertag: str):
    user = await db.fetch_user_by_gamertag(guild_id, gamertag)
    return sanicjson(user, default=str)


@app.get('/api/v1/users/guild/<guild_id:int>/<discord_id:int>')
async def get_user_discord_id(request: Request, guild_id: int, discord_id: int):
    user = await db.fetch_user_by_discord_id(guild_id, discord_id)
    return sanicjson(user, default=str)


@app.patch('/api/v1/users/thorny-id/<thorny_id:int>')
async def update_user_thorny_id(request: Request, thorny_id: int):
    data = request.json
    user = await db.fetch_user_by_id(thorny_id)
    user = await db.update_user(user, data)

    return sanicjson(user, default=str)




@app.listener('after_server_start')
async def init_db_pool(application: Sanic, loop: asyncio.AbstractEventLoop):
    await webserver_pool.init_pool()

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, single_process=True)
