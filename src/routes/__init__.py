from sanic import Blueprint
from src.routes.users import user_blueprint
from src.routes.events import events_blueprint
from src.routes.quests import quest_blueprint
from src.routes.projects import project_blueprint
from src.routes.guilds import guild_blueprint
from src.routes.server import server_blueprint

blueprints = [user_blueprint, project_blueprint, quest_blueprint, events_blueprint, guild_blueprint, server_blueprint]
blueprint_group = Blueprint.group(url_prefix='/', *blueprints, version=0.1, version_prefix='/api/v')
