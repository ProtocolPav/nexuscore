from typing import Annotated

from fastapi import APIRouter, HTTPException, Response, Query

from src.dependencies.database import db
from src.models.users import playtime
from src.models.server import relay

events = APIRouter(prefix='/events', tags=['Events'])


@events.post('/relay', name="Server Relay", status_code=201)
async def server_relay_event(body: relay.RelayModel) -> Response:
    """
    Relays a message to the discord server via a webhook.
    Essentially acts as a wrapper, instead of calling a HTTP to the
    webhook, just send a POST to here.
    """
    await body.relay()

    return Response(status_code=201)