from sanic import Blueprint
from src.blueprints.users import user_blueprint
from src.blueprints.events import events_blueprint
from src.blueprints.quests import quest_blueprint
from src.blueprints.projects import project_blueprint
from src.blueprints.guilds import guild_blueprint

blueprints = [user_blueprint, project_blueprint, quest_blueprint, events_blueprint, guild_blueprint]
blueprint_group = Blueprint.group(url_prefix='/', *blueprints, version=0.1, version_prefix='/api/v')
