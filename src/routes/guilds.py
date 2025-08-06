from datetime import date

from sanic import Blueprint, Request, exceptions
import sanic
from sanic_ext import openapi, validate
from sanic_ext.extensions.openapi.definitions import RequestBody, Response

from src.database import Database
from src.models import guilds
from src.utils.errors import BadRequest400, NotFound404

guild_blueprint = Blueprint("guilds", url_prefix='/guilds')


@guild_blueprint.route('/', methods=['POST'])
@openapi.definition(body=RequestBody(guilds.GuildCreateModel.doc_schema()),
                    response=[
                        Response(guilds.GuildModel.doc_schema(), 201),
                        Response(BadRequest400, 400)
                    ])
@validate(json=guilds.GuildCreateModel)
async def create_guild(request: Request, db: Database, body: guilds.GuildCreateModel):
    """
    Create New Guild

    Creates a new guild. This should never be called, only by thorny.
    """
    if await guilds.GuildModel.fetch(db, body.guild_id):
        raise BadRequest400('This guild already exists')
    else:
        guild_id = await guilds.GuildModel.create(db, body)
        guild_model = await guilds.GuildModel.fetch(db, guild_id)

    return sanic.json(status=201, body=guild_model.model_dump(), default=str)


@guild_blueprint.route('/<guild_id:int>', methods=['GET'])
@openapi.definition(response=[
    Response(guilds.GuildModel.doc_schema(), 201),
    Response(NotFound404, 404)
])
async def get_guild(request: Request, db: Database, guild_id: int):
    """
    Get Guild

    This returns the guild object
    """
    model = await guilds.GuildModel.fetch(db, guild_id)

    return sanic.json(model.model_dump(), default=str)


@guild_blueprint.route('/<guild_id:int>', methods=['PATCH', 'PUT'])
@openapi.definition(body=RequestBody(guilds.GuildUpdateModel.doc_schema()),
                    response=[
                        Response(guilds.GuildModel.doc_schema(), 200),
                        Response(BadRequest400, 400)
                    ])
@validate(json=guilds.GuildUpdateModel)
async def update_guild(request: Request, db: Database, guild_id: int, body: guilds.GuildUpdateModel):
    """
    Update Guild

    Anything that you include as `null` will be omitted and not updated
    """
    model = await guilds.GuildModel.fetch(db, guild_id)
    await model.update(db, body)

    return sanic.json(model.model_dump(), default=str)


@guild_blueprint.route('/<guild_id:int>/features', methods=['GET'])
@openapi.definition(response=[
    Response(guilds.FeaturesListModel.doc_schema(), 201),
    Response(NotFound404, 404)
])
async def get_features(request: Request, db: Database, guild_id: int):
    """
    Get Guild Features

    This returns a list of the guild's features
    """
    model = await guilds.FeaturesListModel.fetch(db, guild_id)

    return sanic.json(model.model_dump(), default=str)


@guild_blueprint.route('/<guild_id:int>/channels', methods=['GET'])
@openapi.definition(response=[
    Response(guilds.ChannelsListModel.doc_schema(), 201),
    Response(NotFound404, 404)
])
async def get_channels(request: Request, db: Database, guild_id: int):
    """
    Get Guild Channels

    This returns a list of the guild's channels
    """
    model = await guilds.ChannelsListModel.fetch(db, guild_id)

    return sanic.json(model.model_dump(), default=str)


@guild_blueprint.route('/<guild_id:int>/playtime', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': guilds.GuildPlaytimeAnalysis.doc_schema()},
                  description='Success')
@openapi.response(status=404, description='Error')
async def get_guild_playtime(request: Request, db: Database, guild_id: int):
    """
    Get Guild Playtime Analysis

    This returns the guild's playtime summary. Playtime is in seconds.

    FOR NOW IT IS NOT FULLY COMPLETE
    """
    guild_analysis = await guilds.GuildPlaytimeAnalysis.fetch(db, guild_id)

    return sanic.json(guild_analysis.model_dump(), default=str)


@guild_blueprint.route('/<guild_id:int>/leaderboard/playtime/<month:ymd>', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': guilds.LeaderboardModel.doc_schema()},
                  description='Success')
@openapi.response(status=404, description='Error')
async def get_playtime_leaderboard(request: Request, db: Database, guild_id: int, month: date):
    """
    Get Guild Playtime Leaderboard

    Returns the guild's playtime leaderboard, in order. Playtime is in seconds.
    """
    guild_leaderboard = await guilds.LeaderboardModel.fetch_playtime(db, month, guild_id)

    return sanic.json(guild_leaderboard.model_dump(), default=str)


@guild_blueprint.route('/<guild_id:int>/leaderboard/currency', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': guilds.LeaderboardModel.doc_schema()},
                  description='Success')
@openapi.response(status=404, description='Error')
async def get_currency_leaderboard(request: Request, db: Database, guild_id: int):
    """
    Get Guild Currency Leaderboard

    Returns the guild's currency leaderboard, in order.
    """
    guild_leaderboard = await guilds.LeaderboardModel.fetch_currency(db, guild_id)

    return sanic.json(guild_leaderboard.model_dump(), default=str)


@guild_blueprint.route('/<guild_id:int>/leaderboard/levels', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': guilds.LeaderboardModel.doc_schema()},
                  description='Success')
@openapi.response(status=404, description='Error')
async def get_levels_leaderboard(request: Request, db: Database, guild_id: int):
    """
    Get Guild Levels Leaderboard

    Returns the guild's playtime leaderboard, in order. Playtime is in seconds.
    """
    guild_leaderboard = await guilds.LeaderboardModel.fetch_levels(db, guild_id)

    return sanic.json(guild_leaderboard.model_dump(), default=str)


@guild_blueprint.route('/<guild_id:int>/leaderboard/quests', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': guilds.LeaderboardModel.doc_schema()},
                  description='Success')
@openapi.response(status=404, description='Error')
async def get_quests_leaderboard(request: Request, db: Database, guild_id: int):
    """
    Get Guild Quests Leaderboard

    Returns the guild's playtime leaderboard, in order. Playtime is in seconds.
    """
    guild_leaderboard = await guilds.LeaderboardModel.fetch_quests(db, guild_id)

    return sanic.json(guild_leaderboard.model_dump(), default=str)


@guild_blueprint.route('/<guild_id:int>/online', methods=['GET'])
@openapi.definition(response=[
    Response(guilds.OnlineUsersListModel.doc_schema(), 201),
    Response(NotFound404, 404)
])
async def get_online_users(request: Request, db: Database, guild_id: int):
    """
    Get Guild Online Users

    Get a list of ThornyIDs that are currently
    online on the server, along with their session time.
    """
    online = await guilds.OnlineUsersListModel.fetch(db, guild_id)

    return sanic.json(online.model_dump(), default=str)
