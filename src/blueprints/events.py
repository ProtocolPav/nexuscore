from sanic import Blueprint, Request
from sanic import json as sanicjson

from src.db.event import *
from src.blueprints.amethyst import amethyst_blueprint

events_blueprint = Blueprint('events', '/')
