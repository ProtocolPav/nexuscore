from sanic import Blueprint, Request
import sanic

from src.database import Database

from sanic_ext import openapi

from src.models import events, users

events_blueprint = Blueprint('events', '/events')


@events_blueprint.route('/connection', methods=['POST'])
@openapi.body(content={'application/json': events.ConnectionCreateModel.model_json_schema()})
@openapi.response(status=201, description='Success')
async def connect_event(request: Request, db: Database):
    """
    Insert Connection

    Inserts a connection event. Either `connect` or `disconnect`.
    """
    model = events.ConnectionCreateModel(**request.json)
    user_playtime = await users.PlaytimeSummary.fetch(db, model.thorny_id)

    if model.type == 'connect' and user_playtime.session is None:
        await events.ConnectionModel.new(db, model)
    elif model.type == 'disconnect' and user_playtime.session:
        await events.ConnectionModel.new(db, model)
    else:
        await events.ConnectionModel.new(db, model, ignore=True)
        return sanic.HTTPResponse(status=400)

    return sanic.HTTPResponse(status=201)


@events_blueprint.route('/interaction', methods=['POST'])
@openapi.body(content={'application/json': events.InteractionCreateModel.model_json_schema()})
@openapi.response(status=201, description='Success')
async def interaction_event(request: Request, db: Database):
    """
    Insert Interaction

    Inserts an interaction event.
    """
    model = events.InteractionCreateModel(**request.json)

    await events.InteractionModel.new(db, model)

    return sanic.HTTPResponse(status=201)


@events_blueprint.route('/relay', methods=['POST'])
@openapi.body(content={'application/json': events.RelayModel.model_json_schema()})
@openapi.response(status=201, description='Success')
async def server_relay_event(request: Request, db: Database):
    """
    Webhook Relay

    Relays a message to the discord server via a webhook.
    Essentially acts as a wrapper, instead of calling a HTTP to the
    webhook, just send a POST to here.
    """
    model = events.RelayModel(**request.json)

    await model.relay()

    return sanic.HTTPResponse(status=201)