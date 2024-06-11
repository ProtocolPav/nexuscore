from datetime import  date

from sanic import Blueprint, Request
import sanic
from sanic_ext import openapi

from src.database import Database
from src.models import guild
from src.views.guild import GuildView


guild_blueprint = Blueprint("guild_routes", url_prefix='/guilds')


@guild_blueprint.route('/', methods=['POST'])
@openapi.response(status=201,
                  content={'application/json': GuildView.view_schema()},
                  description='Success')
@openapi.response(status=500, description='Guild Already Exists')
@openapi.definition(body={'application/json': {'guild_id': int, 'guild_name': str}})
async def create_guild(request: Request, db: Database):
    """
    Create New Guild

    Creates a new guild. This should never be called, only by thorny.
    """
    try:
        await GuildView.build(db, guild_id=int(request.json['guild_id']))
        return sanic.HTTPResponse(status=500, body="Guild Already Exists!")
    except TypeError:
        await GuildView.new(db, int(request.json['guild_id']), request.json['guild_name'])

        guild_view = await GuildView.build(db, guild_id=int(request.json['guild_id']))

    return sanic.json(status=201, body=guild_view.model_dump(), default=str)


@guild_blueprint.route('/<guild_id:int>', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': GuildView.view_schema()},
                  description='Success')
@openapi.response(status=404, description='Error')
async def get_guild(request: Request, db: Database, guild_id: int):
    """
    Get Guild

    This returns the guild, its channels and features
    """
    guild_view = await GuildView.build(db, guild_id)

    return sanic.json(guild_view.model_dump(), default=str)


@guild_blueprint.route('/<guild_id:int>/playtime', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': guild.GuildPlaytimeAnalysis.view_schema()},
                  description='Success')
@openapi.response(status=404, description='Error')
async def get_guild_playtime(request: Request, db: Database, guild_id: int):
    """
    Get Guild Playtime Analysis

    This returns the guild's playtime summary. Playtime is in seconds.

    FOR NOW IT IS NOT FULLY COMPLETE
    """
    guild_analysis = await guild.GuildPlaytimeAnalysis.fetch(db, guild_id)

    return sanic.json(guild_analysis.model_dump(), default=str)


@guild_blueprint.route('/<guild_id:int>/leaderboard/playtime/<month:ymd>', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': guild.LeaderboardModel.view_schema()},
                  description='Success')
@openapi.response(status=404, description='Error')
async def get_playtime_leaderboard(request: Request, db: Database, guild_id: int, month: date):
    """
    Get Guild Playtime Leaderboard

    Returns the guild's playtime leaderboard, in order. Playtime is in seconds.
    """
    guild_leaderboard = await guild.LeaderboardModel.get_playtime(db, month, guild_id)

    return sanic.json(guild_leaderboard.model_dump(), default=str)


@guild_blueprint.route('/<guild_id:int>/online', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': guild.OnlineUsersSummary.view_schema()},
                  description='Success')
@openapi.response(status=404, description='Error')
async def get_online_users(request: Request, db: Database, guild_id: int):
    """
    Get Guild Online Users

    Get a list of ThornyIDs that are currently
    online on the server, along with their session time.
    """
    online = await guild.OnlineUsersSummary.build(db, guild_id)

    return sanic.json(online.model_dump(), default=str)
