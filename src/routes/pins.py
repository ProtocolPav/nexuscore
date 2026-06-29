from fastapi import APIRouter, Depends, Security, status

from src.dependencies.auth import get_guild_client
from src.dependencies.services import get_pin_service

from src.models.auth import TokenPayload, Scope
from src.models.projects.pin import PinOut, PinIn, PinUpdate

from src.services.pin import PinService

pins_router = APIRouter(prefix='/pins', tags=['Pins'])

@pins_router.get('')
async def list_pins(
        _: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_PINS_READ]),
        service: PinService = Depends(get_pin_service)
) -> list[PinOut]:
    """
    Get a list of Pins
    """
    return await service.get_all()


@pins_router.post('', status_code=status.HTTP_201_CREATED)
async def create_pin(
        body: PinIn,
        _: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_PINS_WRITE]),
        service: PinService = Depends(get_pin_service)
) -> PinOut:
    """
    Creates a new pin
    """
    return await service.new(body)


@pins_router.get('/{pin_id}')
async def get_pin(
        pin_id: int,
        _: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_PINS_READ]),
        service: PinService = Depends(get_pin_service)
) -> PinOut:
    """
    Returns the pin specified
    """
    return await service.get(pin_id)


@pins_router.patch('/{pin_id}')
@pins_router.put('/{pin_id}')
async def partial_update_pin(
        pin_id: int,
        body: PinUpdate,
        _: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_PINS_WRITE]),
        service: PinService = Depends(get_pin_service)
) -> PinOut:
    """
    Update Pin

    Update the pin. Anything that you do not want to update can be left as `null`
    """
    return await service.update(pin_id, body)
