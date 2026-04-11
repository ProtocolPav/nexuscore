from datetime import date

from fastapi import APIRouter, HTTPException

from src.dependencies.database import Database, db
from src.models import guilds

guild = APIRouter(prefix='/guilds', tags=['Guilds'])


@guild.post('', status_code=201)
async def create_guild(body: guilds.GuildCreateModel) -> guilds.GuildModel:
    """
    Creates a new guild. This should never be called, only by thorny.
    """
    if await guilds.GuildModel.fetch(db, body.guild_id):
        raise HTTPException(status_code=400, detail='This guild already exists')
    else:
        guild_id = await guilds.GuildModel.create(db, body)
        guild_model = await guilds.GuildModel.fetch(db, guild_id)

    return guild_model


@guild.get('/{guild_id}')
async def get_guild(guild_id: int) -> guilds.GuildModel:
    """
    This returns the guild object
    """
    model = await guilds.GuildModel.fetch(db, guild_id)

    return model


@guild.patch('/{guild_id}')
@guild.put('/{guild_id}')
async def update_guild(guild_id: int, body: guilds.GuildUpdateModel) -> guilds.GuildModel:
    """
    Anything that you include as `null` will be omitted and not updated
    """
    model = await guilds.GuildModel.fetch(db, guild_id)
    await model.update(db, body)

    return model


@guild.get('/{guild_id}/features')
async def get_features(guild_id: int) -> guilds.FeaturesListModel:
    """
    This returns a list of the guild's features
    """
    model = await guilds.FeaturesListModel.fetch(db, guild_id)

    return model


@guild.get('/{guild_id}/channels')
async def get_channels(guild_id: int) -> guilds.ChannelsListModel:
    """
    This returns a list of the guild's channels
    """
    model = await guilds.ChannelsListModel.fetch(db, guild_id)

    return model


@guild.get('/{guild_id}/playtime')
async def get_guild_playtime(guild_id: int) -> guilds.GuildPlaytimeAnalysis:
    """
    This returns the guild's playtime summary. Playtime is in seconds.

    > [!warning]
    > The playtime analysis is currently a work in progress, and may not have all data.
    > Data might change in the future.
    """
    guild_analysis = await guilds.GuildPlaytimeAnalysis.fetch(db, guild_id)

    return guild_analysis


@guild.get('/{guild_id}/leaderboard/playtime/{month}')
async def get_playtime_leaderboard(guild_id: int, month: date) -> guilds.LeaderboardModel:
    """
    Returns the guild's playtime leaderboard, in order. Playtime is in seconds.
    """
    guild_leaderboard = await guilds.LeaderboardModel.fetch_playtime(db, month, guild_id)

    return guild_leaderboard


@guild.get('/{guild_id}/leaderboard/currency')
async def get_currency_leaderboard(guild_id: int) -> guilds.LeaderboardModel:
    """
    Returns the guild's currency leaderboard, in order.
    """
    guild_leaderboard = await guilds.LeaderboardModel.fetch_currency(db, guild_id)

    return guild_leaderboard


@guild.get('/{guild_id}/leaderboard/levels')
async def get_levels_leaderboard(guild_id: int) -> guilds.LeaderboardModel:
    """
    Returns the guild's playtime leaderboard, in order. Playtime is in seconds.
    """
    guild_leaderboard = await guilds.LeaderboardModel.fetch_levels(db, guild_id)

    return guild_leaderboard


@guild.get('/{guild_id}/leaderboard/quests')
async def get_quests_leaderboard(guild_id: int) -> guilds.LeaderboardModel:
    """
    Returns the guild's playtime leaderboard, in order. Playtime is in seconds.
    """
    guild_leaderboard = await guilds.LeaderboardModel.fetch_quests(db, guild_id)

    return guild_leaderboard


@guild.get('/{guild_id}/online')
async def get_online_users(guild_id: int) -> guilds.OnlineUsersListModel:
    """
    Get a list of ThornyIDs that are currently
    online on the server, along with their session time.
    """
    online = await guilds.OnlineUsersListModel.fetch(db, guild_id)

    return online
