from fastapi import APIRouter, Security, status

from src.dependencies.auth import Scope, get_guild_client
from src.dependencies.database import db
from src.models.auth import TokenPayload
from src.models.projects.pin import PinOut, PinIn, PinUpdate
from src.repositories.pin import PinRepository

pins_router = APIRouter(prefix='/pins', tags=['Pins'])
repo = PinRepository(db)

@pins_router.get('')
async def list_pins(
        _: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_PINS_READ])
) -> list[PinOut]:
    """
    Get a list of Pins
    """
    pins = await repo.fetch_all()

    return [PinOut(**p.model_dump()) for p in pins]


@pins_router.post('', status_code=status.HTTP_201_CREATED)
async def create_pin(
        body: PinIn,
        _: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_PINS_WRITE])
) -> PinOut:
    """
    Creates a new pin
    """
    new_pin = await repo.create(body)

    return PinOut(**new_pin.model_dump())


@pins_router.get('/{pin_id}')
async def get_pin(
        pin_id: int,
        _: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_PINS_READ])
) -> PinOut:
    """
    Returns the pin specified
    """
    pin = await repo.fetch(pin_id)

    return PinOut(**pin.model_dump())


@pins_router.patch('/{pin_id}')
@pins_router.put('/{pin_id}')
async def update_pin(
        pin_id: int,
        body: PinUpdate,
        _: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_PINS_WRITE])
) -> PinOut:
    """
    Update Pin

    Update the pin. Anything that you do not want to update can be left as `null`
    """
    pin = await repo.update(pin_id, body)

    return PinOut(**pin.model_dump())
