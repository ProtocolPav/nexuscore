import json

from pydantic import BaseModel, Field, RootModel
from sanic_ext import openapi

from src.database import Database

@openapi.component()
class PlayerModel(BaseModel):
    gamertag: str
    location: tuple[int, int, int]
    hidden: bool
    reload: int = 10

    @classmethod
    async def new(cls, db: Database, model: "PlayerCreateModel") -> "PlayerModel":
        return PlayerModel(gamertag=model.gamertag, location=model.location, hidden=model.hidden)

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


class PlayerListModel(RootModel):
    root: list[PlayerModel]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    @staticmethod
    async def fetch(db: Database):
        data = await db.pool.fetchrow("""
                                      SELECT COALESCE(location_data, '{}'::json) as locations
                                      FROM events.locations
                                      """)
        players = []

        if data:
            for location in json.loads(data['locations']):
                players.append(PlayerModel(**location))

        return PlayerListModel(root=players)

    @staticmethod
    async def update(db: Database, model: "PlayerListCreateModel"):
        async with db.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("""
                                   UPDATE events.locations
                                   SET location_data = $1::json
                                   """, json.dumps(model.model_dump()))

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


@openapi.component()
class PlayerCreateModel(BaseModel):
    gamertag: str
    location: tuple[int, int, int]
    hidden: bool

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


class PlayerListCreateModel(RootModel):
    root: list[PlayerCreateModel]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")