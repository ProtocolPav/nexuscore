from fastapi import APIRouter, HTTPException

from src.dependencies.database import Database, db
from src.models.projects import pin

pins = APIRouter(prefix='/pins', tags=['Pins'])

@pins.get('')
async def get_all_pins() -> pin.PinsListModel:
    """
    Get a list of Pins
    """
    pins_model = await pin.PinsListModel.fetch(db)

    return pins_model


@pins.post('', status_code=201)
async def create_pin(body: pin.PinCreateModel) -> pin.PinModel:
    """
    Creates a new pin, inserts a status and content.
    """
    pin_id = await pin.PinModel.create(db, body)
    pin_model = await pin.PinModel.fetch(db, pin_id)

    return pin_model


@pins.get('/{pin_id}')
async def get_pin(pin_id: int) -> pin.PinModel:
    """
    Returns the pin specified
    """
    pin_model = await pin.PinModel.fetch(db, pin_id)

    return pin_model


@pins.patch('/{pin_id}')
@pins.put('/{pin_id}')
async def update_pin(pin_id: int, body: pin.PinUpdateModel) -> pin.PinModel:
    """
    Update Pin

    Update the pin. Anything that you do not want to update can be left as `null`
    """
    model = await pin.PinModel.fetch(db, pin_id)
    await model.update(db, body)

    return model
