from typing import Annotated

from fastapi import APIRouter, HTTPException, Response, Query

from src.dependencies.database import db
from src.models.server.interactions import InteractionQuery
from src.models.users import playtime
from src.models.server import interactions, connections, relay

events = APIRouter(prefix='/events', tags=['Events'])


@events.post('/interaction', status_code=201)
async def create_interaction(body: interactions.InteractionCreateModel) -> Response:
    """
    Creates an interaction event.
    """
    await interactions.InteractionModel.create(db, body)

    return Response(status_code=201)


@events.get('/interaction', name="Interaction Check", deprecated=True)
async def interaction_check(x: int, y: int, z: int) -> interactions.InteractionListModel:
    """
    Finds all interactions at a given coordinate.
    > [!caution]
    > This endpoint is deprecated and will be removed in a future release. Use `/interactions` instead.
    """
    interaction_list = await interactions.InteractionListModel.fetch(db, [x, y, z])

    return interaction_list


@events.get('/interactions', name="Get Interactions")
async def get_all_interactions(filter_query: Annotated[InteractionQuery, Query()]) -> interactions.InteractionListModel:
    """
    Filter interactions by various criteria.
    """
    interactions_model = await interactions.InteractionListModel.fetch(db,
                                                                       filter_query.coordinates,
                                                                       filter_query.coordinates_end,
                                                                       filter_query.thorny_ids,
                                                                       filter_query.interaction_types,
                                                                       filter_query.references,
                                                                       filter_query.dimensions,
                                                                       filter_query.time_start,
                                                                       filter_query.time_end,
                                                                       filter_query.page,
                                                                       filter_query.page_size)

    return interactions_model


@events.post('/relay', name="Server Relay", status_code=201)
async def server_relay_event(body: relay.RelayModel) -> Response:
    """
    Relays a message to the discord server via a webhook.
    Essentially acts as a wrapper, instead of calling a HTTP to the
    webhook, just send a POST to here.
    """
    await body.relay()

    return Response(status_code=201)