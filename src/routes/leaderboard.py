from datetime import date

from fastapi import APIRouter, Security

from src.dependencies.auth import Scope, get_guild_client
from src.dependencies.database import db
from src.models import guilds
from src.models.auth import TokenPayload

leaderboard_router = APIRouter(prefix='/guilds/me/leaderboard', tags=['Leaderboards'])

@leaderboard_router.get('/playtime/{month}')
async def get_playtime_leaderboard(
        month: date,
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_READ]),
) -> guilds.LeaderboardModel:
    """
    Returns the guild's playtime leaderboard, in order. Playtime is in seconds.
    """
    guild_leaderboard = await guilds.LeaderboardModel.fetch_playtime(db, month, auth.guild_id)

    return guild_leaderboard


@leaderboard_router.get('/currency')
async def get_currency_leaderboard(
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_READ]),
) -> guilds.LeaderboardModel:
    """
    Returns the guild's currency leaderboard, in order.
    """
    guild_leaderboard = await guilds.LeaderboardModel.fetch_currency(db, auth.guild_id)

    return guild_leaderboard


@leaderboard_router.get('/levels')
async def get_levels_leaderboard(
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_READ]),
) -> guilds.LeaderboardModel:
    """
    Returns the guild's playtime leaderboard, in order. Playtime is in seconds.
    """
    guild_leaderboard = await guilds.LeaderboardModel.fetch_levels(db, auth.guild_id)

    return guild_leaderboard


@leaderboard_router.get('/quests_router')
async def get_quests_leaderboard(
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_READ]),
) -> guilds.LeaderboardModel:
    """
    Returns the guild's playtime leaderboard, in order. Playtime is in seconds.
    """
    guild_leaderboard = await guilds.LeaderboardModel.fetch_quests(db, auth.guild_id)

    return guild_leaderboard