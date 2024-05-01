from sanic import Blueprint
from .users import user_blueprint
from .amethyst import amethyst_blueprint
from .events import events_blueprint

event_blueprints = [amethyst_blueprint, events_blueprint]
event_blueprint_group = Blueprint.group(url_prefix='/events', *event_blueprints)

blueprints = [user_blueprint, event_blueprint_group]
blueprint_group = Blueprint.group(url_prefix='/api', *blueprints, version=1)
