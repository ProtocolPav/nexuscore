from datetime import datetime

from sanic import Blueprint, Request
import sanic
from sanic_ext.extensions.openapi.definitions import Response, RequestBody, Parameter

from src.database import Database

from sanic_ext import openapi, validate

from src.models.users import playtime
from src.models.server import interactions, connections, relay
from src.utils.errors import NotFound404, BadRequest400

events_blueprint = Blueprint('events', '/events')


@events_blueprint.route('/connection', methods=['POST'])
@openapi.definition(body=RequestBody(connections.ConnectionCreateModel.doc_schema()),
                    response=[
                        Response(status=201),
                        Response(BadRequest400, 400)
                    ])
@validate(json=connections.ConnectionCreateModel)
async def connect_event(request: Request, db: Database, body: connections.ConnectionCreateModel):
    """
    Insert Connection

    Inserts a connection event. Either `connect` or `disconnect`.
    """
    try:
        user_playtime = await playtime.PlaytimeSummary.fetch(db, body.thorny_id)

        if (body.type == 'connect' and not user_playtime.session) or (body.type == 'disconnect' and user_playtime.session):
            await connections.ConnectionModel.create(db, body)
        else:
            body.ignored = True
            await connections.ConnectionModel.create(db, body)
            raise BadRequest400('Connection was created but ignored because the user does not have a session')
    except NotFound404:
        await connections.ConnectionModel.create(db, body)

    return sanic.empty(status=201)


@events_blueprint.route('/interaction', methods=['POST'])
@openapi.definition(body=RequestBody(interactions.InteractionCreateModel.doc_schema()),
                    response=[
                        Response(status=201),
                        Response(BadRequest400, 400)
                    ])
@validate(json=interactions.InteractionCreateModel)
async def interaction_event(request: Request, db: Database, body: interactions.InteractionCreateModel):
    """
    Insert Interaction

    Inserts an interaction event.
    """
    await interactions.InteractionModel.create(db, body)

    return sanic.empty(status=201)


@events_blueprint.route('/interaction', methods=['GET'])
@openapi.definition(response=[
                        Response({'application/json': interactions.InteractionListModel.doc_schema()}, 200),
                        Response(BadRequest400, 400),
                        Response(NotFound404, 404)
                    ],
                    parameter=[
                        Parameter('x', int),
                        Parameter('y', int),
                        Parameter('z', int)
                    ]
)
async def interaction_check(request: Request, db: Database):
    """
    Check Interaction Coordinates

    Finds all interactions at a given coordinate.
    args: x, y, z
    """
    coordinates = [int(request.args['x'][0]), int(request.args['y'][0]), int(request.args['z'][0])]
    interaction_list = await interactions.InteractionListModel.fetch(db, coordinates)

    return sanic.json(interaction_list.model_dump(), default=str)


@events_blueprint.route('/interactions', methods=['GET'])
@openapi.definition(response=[
    Response(interactions.InteractionListModel.doc_schema(), 200)
],
    parameter=[
        Parameter('coordinates', list[int], description="The coordinates or start coordinates"),
        Parameter('coordinates_end', list[int], description="The end coordinates. You must also have `coordinates` set"),
        Parameter('thorny_ids', list[int], description="The thorny IDs to filter by"),
        Parameter('interaction_types', list[str], description="The interaction types to filter by"),
        Parameter('references', list[str], description="The references to filter by. You can use % as wildcards"),
        Parameter('dimensions', list[str], description="The dimensions to filter by"),
        Parameter('time_start', datetime, description="The start time to filter by"),
        Parameter('time_end', datetime, description="The end time to filter by"),
        Parameter('page', int, description="The page to return. Default: 1"),
        Parameter('page_size', int, description="The size of each page in items. Default: 100")
    ])
async def get_all_interactions(request: Request, db: Database):
    """
    Get All Interactions

    This returns a list of all Interactions based on filters
    """
    coordinates = request.args.getlist('coordinates')
    coordinates_end = request.args.getlist('coordinates_end')
    thorny_ids = request.args.getlist('thorny_ids')
    interaction_types = request.args.getlist('interaction_types')
    references = request.args.getlist('references')
    dimensions = request.args.getlist('dimensions')
    time_start = request.args.get('time_start')
    time_end = request.args.get('time_end')

    page = request.args.get('page')
    page_size = request.args.get('page_size')

    interactions_model = await interactions.InteractionListModel.fetch(db,
                                                                       coordinates,
                                                                       coordinates_end,
                                                                       thorny_ids,
                                                                       interaction_types,
                                                                       references,
                                                                       dimensions,
                                                                       time_start,
                                                                       time_end,
                                                                       int(page) if page else 1,
                                                                       int(page_size) if page_size else 100)

    return sanic.json(interactions_model.model_dump(), default=str)


@events_blueprint.route('/relay', methods=['POST'])
@openapi.definition(body=RequestBody(relay.RelayModel.doc_schema()),
                    response=[
                        Response(status=201)
                    ])
@validate(json=relay.RelayModel)
async def server_relay_event(request: Request, db: Database, body: relay.RelayModel):
    """
    Webhook Relay

    Relays a message to the discord server via a webhook.
    Essentially acts as a wrapper, instead of calling a HTTP to the
    webhook, just send a POST to here.
    """
    await body.relay()

    return sanic.empty(status=201)