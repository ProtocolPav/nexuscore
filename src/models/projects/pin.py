from pydantic import BaseModel, Field, RootModel
from typing_extensions import Optional

from src.database import Database

from sanic_ext import openapi


@openapi.component()
class PinModel(BaseModel):
    id: int = Field(description="Pin id",
                    examples=[1])
    name: str = Field(description="Pin name",
                      examples=['Bloomin Flower Shop'])
    description: str = Field(description="A short description of the pin, such as what the shop sells, etc.",
                             examples=['Sells Flowers'])
    coordinates: tuple[int, int, int] = Field(description="The coordinates of the pin",
                                              examples=[[333, 55, -65]])
    pin_type: str = Field(description="The type of pin this is",
                          examples=["shop", "farm"])

    @classmethod
    async def new(cls, db: Database, model: "PinCreateModel") -> int:
        pin = await db.pool.fetchrow("""
                                    with pins_table as (
                                        insert into projects.pins(name,
                                                                  description,
                                                                  coordinates,
                                                                  pin_type
                                                                 )
                                        values($1, $2, $3, $4)
                                        
                                        returning id
                                    )
                                    
                                    select id from pins_table
                                   """,
                                  model.name, model.description, model.coordinates, model.pin_type)

        return pin['id']

    @classmethod
    async def fetch(cls, db: Database, pin_id: int) -> Optional["PinModel"]:
        data = await db.pool.fetchrow("""
                                       SELECT * FROM projects.pins p
                                       WHERE p.id = $1
                                       """,
                                      pin_id)

        if data:
            return cls(**data)
        else:
            return None

    async def update(self, db: Database):
        await db.pool.execute("""
                               UPDATE projects.pins
                               SET name = $1,
                                   pin_type = $2,
                                   coordinates = $3,
                                   description = $4,
                               WHERE id = $5
                               """,
                              self.name, self.pin_type, self.coordinates,
                              self.description, self.id)

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


class PinsListModel(RootModel):
    root: list[PinModel]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    @staticmethod
    async def fetch(db: Database) -> "PinsListModel":
        pin_ids = await db.pool.fetchrow("""
                                         SELECT COALESCE(array_agg(id), ARRAY[]::integer[]) as ids
                                         FROM projects.pins
                                         """)

        pins = []
        for pin_id in pin_ids.get('ids', []):
            pins.append(await PinModel.fetch(db, pin_id))

        return PinsListModel(root=pins)

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


class PinCreateModel(BaseModel):
    name: str = Field(description="Pin name",
                      examples=['Bloomin Flower Shop'])
    description: str = Field(description="A short description of the pin, such as what the shop sells, etc.",
                             examples=['Sells Flowers'])
    coordinates: tuple[int, int, int] = Field(description="The coordinates of the pin",
                                              examples=[[333, 55, -65]])
    pin_type: str = Field(description="The type of pin this is",
                          examples=["shop", "farm"])

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


class PinUpdateModel(BaseModel):
    name: str = Field(description="Pin name",
                      examples=['Bloomin Flower Shop'])
    description: str = Field(description="A short description of the pin, such as what the shop sells, etc.",
                             examples=['Sells Flowers'])
    coordinates: tuple[int, int, int] = Field(description="The coordinates of the pin",
                                              examples=[[333, 55, -65]])
    pin_type: str = Field(description="The type of pin this is",
                          examples=["shop", "farm"])

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")