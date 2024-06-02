import json
from datetime import datetime

from sanic import Blueprint, Request
import sanic
from sanic_ext import openapi

from src.database import Database
from src.models import guild
from src.views.guild import GuildView


guild_blueprint = Blueprint("guild_routes", url_prefix='/guilds')


@guild_blueprint.route('/<guild_id:int>', methods=['GET'])
@openapi.response(status=200,
                  content={'application/json': GuildView.view_schema()},
                  description='Success')
@openapi.response(status=404, description='Error')
async def get_guild(request: Request, db: Database, guild_id: int):
    """
    Get Guild

    This returns the guild
    """
    guild_view = await GuildView.build(db, guild_id)

    return sanic.json(guild_view.model_dump(), default=str)