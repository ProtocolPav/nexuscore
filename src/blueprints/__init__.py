from sanic import Blueprint
from src.blueprints.users import user_blueprint
# from src.blueprints.events import event_blueprint_group
# from src.blueprints.cms import content_blueprint
from src.blueprints.quests import quest_blueprint
from src.blueprints.projects import project_blueprint

blueprints = [user_blueprint, project_blueprint, quest_blueprint]
blueprint_group = Blueprint.group(url_prefix='/', *blueprints, version=0.1, version_prefix='/api/v')
