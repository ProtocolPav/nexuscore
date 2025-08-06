from pydantic import Field

from src.database import Database

from sanic_ext import openapi
from src.utils.base import BaseModel, BaseList, optional_model
from src.utils.errors import BadRequest400, NotFound404


class PinBaseModel(BaseModel):
    name: str = Field(description="The pin's Name",
                      examples=['Bloomin Flower Shop'])
    description: str = Field(description="A short description of the pin, such as what the shop sells, etc.",
                             examples=['Sells Flowers'])
    coordinates: tuple[int, int, int] = Field(description="The coordinates of the pin",
                                              examples=[[333, 55, -65]])
    dimension: str = Field(description="The dimension of the pin",
                           examples=['minecraft:overworld'])
    pin_type: str = Field(description="The type of pin this is",
                          examples=["shop", "farm"])


@openapi.component()
class PinModel(PinBaseModel):
    id: int = Field(description="The pin's ID",
                    examples=[1])

    @classmethod
    async def create(cls, db: Database, model: "PinCreateModel", *args) -> int:
        pin = await db.pool.fetchrow("""
                                    with pins_table as (
                                        insert into projects.pins(name,
                                                                  description,
                                                                  coordinates,
                                                                  dimension,
                                                                  pin_type
                                                                 )
                                        values($1, $2, $3, $4, $5)

                                        returning id
                                    )

                                    select id from pins_table
                                   """,
                                     model.name, model.description, model.coordinates, model.dimension, model.pin_type)

        return pin['id']

    @classmethod
    async def fetch(cls, db: Database, pin_id: str, *args) -> "PinModel":
        if not pin_id:
            raise BadRequest400(extra={'ids': ['pin_id']})

        data = await db.pool.fetchrow("""
                                       SELECT * FROM projects.pins p
                                       WHERE p.id = $1
                                       """,
                                      pin_id)

        if data:
            return cls(**data)
        else:
            raise NotFound404(extra={'resource': 'pin', 'id': pin_id})

    async def update(self, db: Database, model: "PinUpdateModel", *args):
        for k, v in model.model_dump().items():
            setattr(self, k, v) if v is not None else None

        await db.pool.execute("""
                               UPDATE projects.pins
                               SET name = $1,
                                   pin_type = $2,
                                   coordinates = $3,
                                   description = $4,
                                   dimension = $5
                               WHERE id = $6
                               """,
                              self.name, self.pin_type, self.coordinates,
                              self.description, self.dimension, self.id)


class PinsListModel(BaseList[PinModel]):
    @classmethod
    async def fetch(cls, db: Database, *args) -> "PinsListModel":
        data = await db.pool.fetch("""
                                   SELECT * FROM projects.pins
                                   """)

        pins: list[PinModel] = []
        for pin in data:
            pins.append(PinModel(**pin))

        return cls(root=pins)


class PinCreateModel(PinBaseModel):
    pass


PinUpdateModel = optional_model('PinUpdateModel', PinBaseModel)