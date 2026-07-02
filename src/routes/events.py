from fastapi import APIRouter, Depends, Security, status

from src.dependencies.auth import get_guild_client
from src.dependencies.services import get_events_service, get_pin_service

from src.models.auth import TokenPayload, Scope
from src.models.events.event import EventIn, EventOut, EventUpdate
from src.models.projects.pin import PinOut, PinIn, PinUpdate
from src.services.event import EventService

from src.services.pin import PinService

events_router = APIRouter(prefix='/guilds/me/events', tags=['Events'])

@events_router.get('')
async def list_events(
        _: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_PINS_READ]),
        service: EventService = Depends(get_events_service)
) -> list[EventOut]:
    """
    Get a list of Events
    """
    return await service.get_all()


@events_router.post('', status_code=status.HTTP_201_CREATED)
async def create_event(
        body: EventIn,
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_PINS_WRITE]),
        service: EventService = Depends(get_events_service)
) -> EventOut:
    """
    Creates a new event
    """
    return await service.new(auth.guild_id, body)


@events_router.get('/{event_id}')
async def get_event(
        event_id: int,
        _: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_PINS_READ]),
        service: EventService = Depends(get_events_service)
) -> EventOut:
    """
    Returns the event specified
    """
    return await service.get(event_id)


@events_router.patch('/{event_id}')
@events_router.put('/{event_id}')
async def partial_update_pin(
        pin_id: int,
        body: EventUpdate,
        _: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_PINS_WRITE]),
        service: EventService = Depends(get_events_service)
) -> EventOut:
    """
    Update Event
    """
    return await service.update(pin_id, body)
