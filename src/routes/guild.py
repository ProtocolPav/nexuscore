from typing import Annotated

from fastapi import APIRouter, Depends, Security, Query
from starlette import status

from src.dependencies.auth import get_current_client, get_guild_client
from src.dependencies.services import get_guild_service

from src.models import guilds
from src.models.auth import TokenPayload, Scope
from src.models.guilds.interaction import InteractionQuery
from src.models.guilds.session import SessionQuery

from src.services.guild import GuildService

guilds_router = APIRouter(prefix='/guilds', tags=['Guilds'])


@guilds_router.post('', status_code=status.HTTP_201_CREATED)
async def create_guild(
        body: guilds.GuildIn,
        _: TokenPayload = Security(get_current_client, scopes=[Scope.ADMIN_GUILDS]),
        service: GuildService = Depends(get_guild_service)
) -> guilds.GuildOut:
    """
    Creates a new guild. If a guild with this ID already exists, it returns a 400.
    """
    return await service.new(body)


@guilds_router.get('/me')
async def get_guild(
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_READ]),
        service: GuildService = Depends(get_guild_service)
) -> guilds.GuildOut:
    """
    Fetch your guild information
    """
    return await service.get(auth.guild_id)


@guilds_router.patch('/me')
@guilds_router.put('/me')
async def partial_update_guild(
        body: guilds.GuildUpdate,
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_WRITE]),
        service: GuildService = Depends(get_guild_service)
) -> guilds.GuildOut:
    """
    Partially updates guild information. Both `PATCH` and `PUT` work the same way.
    """
    return await service.update(auth.guild_id, body)


@guilds_router.get('/me/features', deprecated=True)
async def list_features(
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_READ]),
        service: GuildService = Depends(get_guild_service)
) -> list[guilds.FeatureOut]:
    """Returns a list of features enabled for the authenticated guild."""
    return await service.get_features(auth.guild_id)


@guilds_router.get('/me/channels', deprecated=True)
async def list_channels(
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_READ]),
        service: GuildService = Depends(get_guild_service)
) -> list[guilds.ChannelOut]:
    """
    This returns a list of the guild's channels
    """
    return await service.get_channels(auth.guild_id)


@guilds_router.get('/me/playtime')
async def get_guild_playtime(
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_READ]),
        service: GuildService = Depends(get_guild_service)
) -> guilds.GuildPlaytimeAnalysis:
    """
    This returns the guild's playtime summary. Playtime is in seconds.

    > [!warning]
    > The playtime analysis is currently a work in progress, and may not have all data.
    > Data shape might change in the future.
    """
    return await service.get_playtime_analysis(auth.guild_id)


@guilds_router.get('/me/online', deprecated=True, description="Use /me/sessions instead for more accurate sessions data")
async def get_online_members(
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_READ]),
        service: GuildService = Depends(get_guild_service)
) -> list[guilds.OnlineMember]:
    """
    Returns a list of all players currently connected to Geode.
    """
    return await service.get_online_members(auth.guild_id)


@guilds_router.get('/me/sessions')
async def get_all_sessions(
        filter_query: Annotated[SessionQuery, Query()],
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_READ]),
        service: GuildService = Depends(get_guild_service)
) -> list[guilds.SessionOut]:
    """
    Returns a list of all sessions for the guild.
    """
    return await service.get_sessions(auth.guild_id, filter_query)


@guilds_router.post('/me/connection', status_code=status.HTTP_201_CREATED)
async def create_connection(
        body: guilds.ConnectionIn,
        _: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_MEMBERS_WRITE]),
        service: GuildService = Depends(get_guild_service)
) -> guilds.ConnectionOut:
    """
    Creates a connection event.
    """
    return await service.new_connection(body)


@guilds_router.post('/me/interaction', status_code=status.HTTP_201_CREATED)
async def create_interaction(
        body: guilds.InteractionIn,
        _: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_MEMBERS_WRITE]),
        service: GuildService = Depends(get_guild_service)
) -> guilds.InteractionOut:
    """
    Creates an interaction event.
    """
    return await service.new_interaction(body)

@guilds_router.get('/me/interactions')
async def list_interactions(
        filter_query: Annotated[InteractionQuery, Query()],
        _: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_READ]),
        service: GuildService = Depends(get_guild_service)
) -> list[guilds.InteractionOut]:
    """
    Filter interactions by various criteria.
    """
    return await service.get_interactions(filter_query)
