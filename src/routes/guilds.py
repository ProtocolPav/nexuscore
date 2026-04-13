from datetime import date

from fastapi import APIRouter, HTTPException, Security
from starlette import status

from src.dependencies.auth import get_current_client, get_guild_client
from src.dependencies.database import Database, db
from src.models import guilds
from src.models.auth import TokenPayload

guilds_router = APIRouter(prefix='/guilds', tags=['Guilds'])


@guilds_router.post('', status_code=status.HTTP_201_CREATED)
async def create_guild(
        body: guilds.GuildCreateModel,
        _: TokenPayload = Security(get_current_client, scopes=['admin:guilds'])
) -> guilds.GuildModel:
    """
    Creates a new guild. If a guild with this ID already exists, it returns a 400.
    """
    if await guilds.GuildModel.fetch(db, body.guild_id):
        raise HTTPException(status_code=400, detail='This guild already exists')
    else:
        guild_id = await guilds.GuildModel.create(db, body)
        guild_model = await guilds.GuildModel.fetch(db, guild_id)

    return guild_model


@guilds_router.get('/me')
async def get_guild(
        auth: TokenPayload = Security(get_guild_client, scopes=['guilds:read'])
) -> guilds.GuildModel:
    """
    Fetch your guild information
    """
    model = await guilds.GuildModel.fetch(db, auth.guild_id)

    return model


@guilds_router.patch('/me')
@guilds_router.put('/me')
async def partial_update_guild(
        body: guilds.GuildUpdateModel,
        auth: TokenPayload = Security(get_guild_client, scopes=['guilds:write']),
) -> guilds.GuildModel:
    """
    Partially updates guild information. Both `PATCH` and `PUT` work the same way.
    """
    model = await guilds.GuildModel.fetch(db, auth.guild_id)
    await model.update(db, body)

    return model


@guilds_router.get('/me/features')
async def get_features(
        auth: TokenPayload = Security(get_guild_client, scopes=['guilds:read']),
) -> guilds.FeaturesListModel:
    """
    This returns a list of the guild's features
    """
    model = await guilds.FeaturesListModel.fetch(db, auth.guild_id)

    return model


@guilds_router.get('/me/channels')
async def get_channels(
        auth: TokenPayload = Security(get_guild_client, scopes=['guilds:read']),
) -> guilds.ChannelsListModel:
    """
    This returns a list of the guild's channels
    """
    model = await guilds.ChannelsListModel.fetch(db, auth.guild_id)

    return model


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


@guilds_router.get('/me/leaderboard/playtime/{month}')
async def get_playtime_leaderboard(
        month: date,
        auth: TokenPayload = Security(get_guild_client, scopes=['guilds:read']),
) -> guilds.LeaderboardModel:
    """
    Returns the guild's playtime leaderboard, in order. Playtime is in seconds.
    """
    guild_leaderboard = await guilds.LeaderboardModel.fetch_playtime(db, month, auth.guild_id)

    return guild_leaderboard


@guilds_router.get('/me/leaderboard/currency')
async def get_currency_leaderboard(
        auth: TokenPayload = Security(get_guild_client, scopes=['guilds:read']),
) -> guilds.LeaderboardModel:
    """
    Returns the guild's currency leaderboard, in order.
    """
    guild_leaderboard = await guilds.LeaderboardModel.fetch_currency(db, auth.guild_id)

    return guild_leaderboard


@guilds_router.get('/me/leaderboard/levels')
async def get_levels_leaderboard(
        auth: TokenPayload = Security(get_guild_client, scopes=['guilds:read']),
) -> guilds.LeaderboardModel:
    """
    Returns the guild's playtime leaderboard, in order. Playtime is in seconds.
    """
    guild_leaderboard = await guilds.LeaderboardModel.fetch_levels(db, auth.guild_id)

    return guild_leaderboard


@guilds_router.get('/me/leaderboard/quests')
async def get_quests_leaderboard(
        auth: TokenPayload = Security(get_guild_client, scopes=['guilds:read']),
) -> guilds.LeaderboardModel:
    """
    Returns the guild's playtime leaderboard, in order. Playtime is in seconds.
    """
    guild_leaderboard = await guilds.LeaderboardModel.fetch_quests(db, auth.guild_id)

    return guild_leaderboard


@guilds_router.get('/me/online')
async def get_online_users(
        auth: TokenPayload = Security(get_guild_client, scopes=['guilds:read']),
) -> guilds.OnlineUsersListModel:
    """
    Get a list of ThornyIDs that are currently
    online on the server, along with their session time.
    """
    online = await guilds.OnlineUsersListModel.fetch(db, auth.guild_id)

    return online
