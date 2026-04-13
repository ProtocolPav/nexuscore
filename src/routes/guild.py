from fastapi import APIRouter, HTTPException, Security
from starlette import status

from src.dependencies.auth import get_current_client, get_guild_client
from src.dependencies.database import db
from src.models import guilds
from src.models.auth import TokenPayload
from src.repositories.guild import GuildRepository

guilds_router = APIRouter(prefix='/guilds', tags=['Guilds'])
repo = GuildRepository(db)


@guilds_router.post('', status_code=status.HTTP_201_CREATED)
async def create_guild(
        body: guilds.GuildIn,
        _: TokenPayload = Security(get_current_client, scopes=['admin:guilds'])
) -> guilds.GuildOut:
    """
    Creates a new guild. If a guild with this ID already exists, it returns a 400.
    """
    guild = await repo.create(body)

    return guilds.GuildOut.model_validate(guild.model_dump())


@guilds_router.get('/me')
async def get_guild(
        auth: TokenPayload = Security(get_guild_client, scopes=['guilds:read'])
) -> guilds.GuildOut:
    """
    Fetch your guild information
    """
    guild = await repo.fetch(auth.guild_id)

    return guilds.GuildOut.model_validate(guild.model_dump())


@guilds_router.patch('/me')
@guilds_router.put('/me')
async def partial_update_guild(
        body: guilds.GuildUpdate,
        auth: TokenPayload = Security(get_guild_client, scopes=['guilds:write']),
) -> guilds.GuildOut:
    """
    Partially updates guild information. Both `PATCH` and `PUT` work the same way.
    """
    guild = await repo.update(auth.guild_id, body)

    return guilds.GuildOut.model_validate(guild.model_dump())


@guilds_router.get('/me/features')
async def get_features(
        auth: TokenPayload = Security(get_guild_client, scopes=['guilds:read']),
) -> list[guilds.FeatureOut]:
    """Returns a list of features enabled for the authenticated guild."""
    features = await repo.fetch_features(auth.guild_id)

    return [guilds.FeatureOut.model_validate(f.model_dump()) for f in features]


@guilds_router.get('/me/channels')
async def get_channels(
        auth: TokenPayload = Security(get_guild_client, scopes=['guilds:read']),
) -> list[guilds.ChannelOut]:
    """
    This returns a list of the guild's channels
    """
    channels = await repo.fetch_channels(auth.guild_id)

    return [guilds.ChannelOut.model_validate(c.model_dump()) for c in channels]


@guilds_router.get('/me/playtime')
async def get_guild_playtime(
        auth: TokenPayload = Security(get_guild_client, scopes=['guilds:read']),
) -> guilds.GuildPlaytimeAnalysis:
    """
    This returns the guild's playtime summary. Playtime is in seconds.

    > [!warning]
    > The playtime analysis is currently a work in progress, and may not have all data.
    > Data shape might change in the future.
    """
    guild_analysis = await guilds.GuildPlaytimeAnalysis.fetch(db, auth.guild_id)

    return guild_analysis


@guilds_router.get('/me/online')
async def get_online_users(
        auth: TokenPayload = Security(get_guild_client, scopes=['guilds:read']),
) -> list[guilds.OnlineMember]:
    """
    Get a list of ThornyIDs that are currently
    online on the server, along with their session time.
    """
    players = await repo.fetch_online_members(auth.guild_id)

    return [guilds.OnlineMember.model_validate(p.model_dump()) for p in players]
