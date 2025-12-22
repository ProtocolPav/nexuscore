from sanic import Blueprint

from src.routes.quest_progress import progress_blueprint
from src.routes.users import user_blueprint
from src.routes.events import events_blueprint
from src.routes.quests import quest_blueprint
from src.routes.projects import project_blueprint
from src.routes.guilds import guild_blueprint
from src.routes.server import server_blueprint
from src.routes.pins import pin_blueprint
from src.routes.wrapped import wrapped_blueprint

blueprints = [
    user_blueprint,
    project_blueprint,
    pin_blueprint,
    quest_blueprint,
    progress_blueprint,
    events_blueprint,
    guild_blueprint,
    server_blueprint,
    wrapped_blueprint
]

blueprint_group = Blueprint.group(url_prefix='/', *blueprints, version=0.2, version_prefix='/api/v')
