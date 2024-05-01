from src.db.pool import webserver_pool
from src.db.user import fetch_user_by_gamertag


async def connect(gamertag: str, guild_id: int):
    user = fetch_user_by_gamertag(guild_id, gamertag)

    async with webserver_pool.connection() as conn:
        ...


async def disconnect(gamertag: str, guild_id: int):
    user = fetch_user_by_gamertag(guild_id, gamertag)

    async with webserver_pool.connection() as conn:
        ...