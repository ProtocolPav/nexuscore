from sanic import Sanic, Request, text
from sanic.response import json as sanicjson
from datetime import datetime
import asyncio
import httpx

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


@app.post('/connect')
async def log_connect(request: Request):
    """
    Arguments: gamertag, guild_id
    :param request:
    :return:
    """
    async with webserver_pool.connection() as conn:
        if request.args.get('gamertag', None) and request.args.get('guild_id', None):
            gamertag = request.args['gamertag'][0]
            try:
                guild_id = int(request.args['guild_id'][0])

                await conn.execute("""
                                   INSERT INTO webserver.webevent(event_time, event, description)
                                   VALUES($1, $2, $3)
                                   """,
                                   datetime.now(), 'connect', f'{guild_id},{gamertag}')

                print(f'[WEBSERVER] Sent Connect Event for processing...')

            except TypeError:
                return text('Make sure guild_id is an integer')
        else:
            return text('Include args gamertag and guild_id. Example: thorny-wbs:8000/connect?gamertag=ABC&guild_id=123')
    return sanicjson({"Accept": True})


@app.post('/disconnect')
async def log_disconnect(request: Request):
    """
    Arguments: gamertag, guild_id
    :param request:
    :return:
    """
    async with webserver_pool.connection() as conn:
        if request.args.get('gamertag', None) and request.args.get('guild_id', None):
            gamertag = request.args['gamertag'][0]
            try:
                guild_id = int(request.args['guild_id'][0])

                await conn.execute("""
                                   INSERT INTO webserver.webevent(event_time, event, description)
                                   VALUES($1, $2, $3)
                                   """,
                                   datetime.now(), 'disconnect', f'{guild_id},{gamertag}')

                print(f'[WEBSERVER] Sent Connect Event for processing...')

            except TypeError:
                return text('Make sure guild_id is an integer')
        else:
            return text('Include args gamertag and guild_id. Example: thorny-wbs:8000/connect?gamertag=ABC&guild_id=123')
    return sanicjson({"Accept": True})


@app.post('/disconnect/all')
async def log_disconnect_all(request: Request):
    """
    Arguments: guild_id
    :param request:
    :return:
    """
    async with webserver_pool.connection() as conn:
        if request.args.get('guild_id', None):
            try:
                guild_id = int(request.args['guild_id'][0])

                await conn.execute("""
                                   INSERT INTO webserver.webevent(event_time, event, description)
                                   VALUES($1, $2, $3)
                                   """,
                                   datetime.now(), 'disconnect all', f'{guild_id}')

                print(f'[WEBSERVER] Sent Connect Event for processing...')

            except TypeError:
                return text('Make sure guild_id is an integer')
        else:
            return text('Include args guild_id. Example: thorny-wbs:8000/connect?gamertag=ABC&guild_id=123')
    return sanicjson({"Accept": True})


@app.get('/player/playtime')
async def get_playtime(request: Request):
    """
    Arguments: gamertag, guild_id
    :param request:
    :return:
    """
    ...


@app.get('/player/stats')
async def get_player_statistics(request: Request):
    """
    Arguments: gamertag, guild_id

    Returns the entirety of the player's statistics (blocks placed/broken, kills, deaths)
    :param request:
    :return:
    """
    ...


@app.post('/player/stats')
async def log_player_statistics(request: Request):
    """
    Arguments: gamertag, guild_id, posx, posy, posz, type, ref, mainhand

    type must be either one of: place, mine, kill, die
    ref will be either the block affected, entity affected or the cause of death if it is a fall for example

    Logs a player statistic. Based on world events.
    :param request:
    :return:
    """
    async with webserver_pool.connection() as conn:
        if request.args.get('gamertag', None) and request.args.get('guild_id', None):
            gamertag = request.args['gamertag'][0]
            try:
                guild_id = int(request.args['guild_id'][0])

                thorny_user = await conn.fetchrow("""
                                                  SELECT thorny.user.thorny_user_id FROM thorny.user
                                                  INNER JOIN thorny.profile
                                                  ON thorny.user.thorny_user_id = thorny.profile.thorny_user_id
                                                  WHERE whitelisted_gamertag = $1
                                                  AND thorny.user.guild_id = $2
                                                  """,
                                                  gamertag, guild_id)

                type = request.args.get('type', None)
                posx = int(request.args.get('posx', None))
                posy = int(request.args.get('posy', None))
                posz = int(request.args.get('posz', None))
                ref = request.args.get('ref', None)
                mainhand = request.args.get('mainhand', None)

                await conn.execute("""
                                   INSERT INTO thorny.gamestats(thorny_id, type, position_x, position_y, position_z, 
                                                                reference, mainhand, time)
                                   VALUES($1, $2, $3, $4, $5, $6, $7, $8)
                                   """,
                                   int(thorny_user['thorny_user_id']), type, posx, posy, posz, ref, mainhand, datetime.now()
                                   )


                print(f'[WEBSERVER] Log game stat {type}, {ref}')

            except TypeError:
                return text('Make sure guild_id is an integer')
        else:
            return text('Include args gamertag and guild_id. Example: thorny-wbs:8000/connect?gamertag=ABC&guild_id=123')
    return sanicjson({"Accept": True})



@app.get('/api/v1/users/thorny-id/<thorny_id:int>')
async def get_user_thorny_id(request: Request, thorny_id: int):



@app.listener('after_server_start')
async def start_bot(application: Sanic, loop: asyncio.AbstractEventLoop):
    # await client.login(TOKEN)
    # await application.add_task(client.connect(reconnect=True), name="Thorny Discord Client")
    # asyncio.get_event_loop().create_task(coro=client.connect(reconnect=True),
    #                                      name="Thorny Discord Client")
    #
    # birthday_checker.start()
    # day_counter.start()
    # interruption_check.start()

    await webserver_pool.init_pool()

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, single_process=True)
