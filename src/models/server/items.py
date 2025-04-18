import json
from typing import Annotated, Optional

from pydantic import BaseModel, Field, RootModel, StringConstraints
from sanic_ext import openapi

from src.database import Database

ItemID = Annotated[str, StringConstraints(pattern='^[a-z]+:[a-z_0-9]+$')]

@openapi.component()
class ItemModel(BaseModel):
    item_id: ItemID = Field(description="The minecraft ID of the item",
                            examples=["minecraft:diamond_sword"])
    value: float = Field(description="The initial block value of one of this item",
                         examples=[0.3])
    max_uses: int = Field(description="The maximum uses this item will have before it's value goes to 0",
                          examples=[1043])
    depreciation: float = Field(description="The depreciation % of this item",
                                examples=[0.1])
    current_uses: int = Field(description="The current uses of this item",
                          examples=[40])

    @classmethod
    async def new(cls, db: Database, model: "ItemCreateModel"):
        await db.pool.execute("""
                              insert into server.items(item_id, value, max_uses, depreciation, current_uses)
                              values($1, $2, $3, $4, 0)
                              """,
                              model.item_id, model.value, model.max_uses, model.depreciation)

    @classmethod
    async def fetch(cls, db: Database, item_id: ItemID) -> Optional["ItemModel"]:
        data = await db.pool.fetchrow("""
                                       SELECT * FROM server.items
                                       WHERE item_id = $1
                                       """,
                                      item_id)

        return cls(**data) if data else None

    async def update(self, db: Database):
        await db.pool.execute("""
                               UPDATE server.items
                               SET value = $1,
                                   max_uses = $2,
                                   depreciation = $3,
                                   current_uses = $4
                               WHERE item_id = $5
                               """,
                              self.value, self.max_uses, self.depreciation, self.current_uses, self.item_id)

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


class ItemListModel(RootModel):
    root: list[ItemModel]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    @staticmethod
    async def fetch(db: Database) -> "ItemListModel":
        item_ids = await db.pool.fetchrow("""
                                          SELECT COALESCE(array_agg(item_id), ARRAY[]::character varying[]) as ids
                                          FROM server.items
                                          """)

        items = []
        for item_id in item_ids.get('ids', []):
            items.append(await ItemModel.fetch(db, item_id))

        items.sort(key= lambda x: x.item_id, reverse=True)
        return ItemListModel(root=items)

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


@openapi.component()
class ItemCreateModel(BaseModel):
    item_id: ItemID = Field(description="The minecraft ID of the item",
                            examples=["minecraft:diamond_sword"])
    value: float = Field(description="The initial block value of one of this item",
                         examples=[0.3])
    max_uses: int = Field(description="The maximum uses this item will have before it's value goes to 0",
                          examples=[1043])
    depreciation: float = Field(description="The depreciation % of this item",
                                examples=[0.1])

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")
