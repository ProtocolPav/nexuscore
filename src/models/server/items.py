from typing import Annotated, Optional

from pydantic import Field, StringConstraints
from sanic_ext import openapi

from src.database import Database
from src.utils.base import BaseModel, BaseList
from src.utils.errors import BadRequest400, NotFound404

ItemID = Annotated[str, StringConstraints(pattern='^[a-z]+:[a-z_0-9]+$')]


class ItemBaseModel(BaseModel):
    item_id: ItemID = Field(description="The minecraft ID of the item",
                            json_schema_extra={"example": 'minecraft:diamond_sword'})
    value: float = Field(description="The initial block value of one of this item",
                         json_schema_extra={"example": 24.5})
    max_uses: int = Field(description="The maximum uses this item will have before it's value starts going into the negatives",
                          json_schema_extra={"example": 128})
    depreciation: float = Field(description="The depreciation of this item",
                                json_schema_extra={"example": 0.32})

@openapi.component()
class ItemModel(ItemBaseModel):
    current_uses: int = Field(description="The current uses of this item",
                              json_schema_extra={"example": 32})

    @classmethod
    async def create(cls, db: Database, model: "ItemCreateModel", *args):
        await db.pool.execute("""
                              insert into server.items(item_id, value, max_uses, depreciation, current_uses)
                              values($1, $2, $3, $4, 0)
                              """,
                              model.item_id, model.value, model.max_uses, model.depreciation)

    @classmethod
    async def fetch(cls, db: Database, item_id: ItemID, *args) -> "ItemModel":
        if not item_id:
            raise BadRequest400(extra={'ids': ['item_id']})

        data = await db.pool.fetchrow("""
                                       SELECT * FROM server.items
                                       WHERE item_id = $1
                                       """,
                                      item_id)

        if data:
            return cls(**data)
        else:
            raise NotFound404(extra={'resource': 'item', 'id': item_id})

    async def update(self, db: Database, model: "ItemUpdateModel"):
        for k, v in model.model_dump().items():
            setattr(self, k, v) if v is not None else None

        await db.pool.execute("""
                               UPDATE server.items
                               SET value = $1,
                                   max_uses = $2,
                                   depreciation = $3,
                                   current_uses = $4
                               WHERE item_id = $5
                               """,
                              self.value, self.max_uses, self.depreciation, self.current_uses, self.item_id)


class ItemListModel(BaseList[ItemModel]):
    @classmethod
    async def fetch(cls, db: Database, *args) -> "ItemListModel":
        data = await db.pool.fetch("""
                                    SELECT * FROM server.items
                                    ORDER BY item_id 
                                   """)

        items: list[ItemModel] = []
        for item in data:
            items.append(ItemModel(**item))

        return cls(root=items)


@openapi.component()
class ItemCreateModel(ItemBaseModel):
    pass


@openapi.component()
class ItemUpdateModel(BaseModel):
    current_uses: Optional[int] = Field(description="The current uses of this item",
                                        json_schema_extra={"example": 32})
