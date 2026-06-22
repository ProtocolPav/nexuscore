from fastapi import APIRouter, Response

from src.models import relay

relay_router = APIRouter(prefix='/relay', tags=['Webhook Relay'])


@relay_router.post('', name="Server Relay", status_code=201)
async def server_relay_event(body: relay.RelayModel) -> Response:
    """
    Relays a message to the discord server via a webhook.
    Essentially acts as a wrapper, instead of calling a HTTP to the
    webhook, just send a POST to here.
    """
    await body.relay()

    return Response(status_code=201)