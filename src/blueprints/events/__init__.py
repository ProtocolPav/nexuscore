from sanic import Blueprint
from src.blueprints.events.amethyst import amethyst_blueprint

event_blueprints = [amethyst_blueprint]
event_blueprint_group = Blueprint.group(url_prefix='/events', *event_blueprints)