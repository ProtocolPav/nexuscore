from fastapi import APIRouter, HTTPException, Security, Query
from starlette import status

from src.dependencies.auth import get_guild_client
from src.dependencies.database import db
from src.models.auth import TokenPayload
from src.models.worlds import world
from src.repositories.world import WorldRepository

world_router = APIRouter(prefix='/guilds/me/worlds', tags=['Worlds'])
repo = WorldRepository(db)

@world_router.get('')
async def get_world(
        auth: TokenPayload = Security(get_guild_client, scopes=['guilds:read'])
) -> world.WorldOut:
    wrld = await repo.fetch(auth.guild_id)

    return world.WorldOut(**wrld.model_dump())


@world_router.patch('')
@world_router.put('')
async def partial_update_world(
        body: world.WorldUpdate,
        auth: TokenPayload = Security(get_guild_client, scopes=['guilds:write'])
) -> world.WorldOut:
    wrld = await repo.update(auth.guild_id, body)

    return world.WorldOut(**wrld.model_dump())