from sanic import Blueprint, Request, HTTPResponse
import sanic
from sanic_ext import openapi, validate
from sanic_ext.extensions.openapi.definitions import RequestBody, Response

from src.database import Database
from src.models.projects import pin
from src.utils.errors import BadRequest400, NotFound404

pin_blueprint = Blueprint("pins", url_prefix='/pins')

@pin_blueprint.route('/', methods=['GET'])
@openapi.definition(response=[
    Response(pin.PinsListModel.doc_schema(), 200)
])
async def get_all_pins(request: Request, db: Database):
    """
    Get All Pins

    Get a list of Pins
    """
    pins_model = await pin.PinsListModel.fetch(db)

    return sanic.json(pins_model.model_dump(), default=str)


@pin_blueprint.route('/', methods=['POST'])
@openapi.definition(body=RequestBody(pin.PinCreateModel.doc_schema()),
                    response=[
                        Response(pin.PinModel.doc_schema(), 201),
                        Response(BadRequest400, 400)
                    ])
@validate(json=pin.PinCreateModel)
async def create_pin(request: Request, db: Database, body: pin.PinCreateModel):
    """
    Create Pin

    Creates a new pin, inserts a status and content.
    """
    pin_id = await pin.PinModel.create(db, body)
    pin_model = await pin.PinModel.fetch(db, pin_id)

    return sanic.json(status=201, body=pin_model.model_dump(), default=str)


@pin_blueprint.route('/<pin_id:str>', methods=['GET'])
@openapi.definition(response=[
    Response(pin.PinModel.doc_schema(), 200),
    Response(NotFound404, 404)
])
async def get_pin(request: Request, db: Database, pin_id: str):
    """
    Get Pin

    Returns the pin specified
    """
    pin_model = await pin.PinModel.fetch(db, pin_id)

    return sanic.json(pin_model.model_dump(), default=str)


@pin_blueprint.route('/<pin_id:str>', methods=['PATCH', 'PUT'])
@openapi.definition(body=RequestBody(pin.PinUpdateModel.doc_schema()),
                    response=[
                        Response(pin.PinModel.doc_schema(), 200),
                        Response(BadRequest400, 400),
                        Response(NotFound404, 404)
                    ])
@validate(json=pin.PinUpdateModel)
async def update_pin(request: Request, db: Database, pin_id: str, body: pin.PinUpdateModel):
    """
    Update Pin

    Update the pin. Anything that you do not want to update can be left as `null`
    """
    model = await pin.PinModel.fetch(db, pin_id)
    await model.update(db, body)

    return sanic.json(model.model_dump(), default=str)
