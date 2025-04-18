import json
from typing import Optional

from pydantic import BaseModel, Field, RootModel
from sanic_ext import openapi

from src.database import Database


@openapi.component()
class WorldModel(BaseModel):
    guild_id: int = Field(description="The guild ID that corresponds to this world",
                          examples=[123456789012345678])
    overworld_border: float = Field(description="The Overworld border size",
                                    examples=[2000])
    nether_border: float = Field(description="The Nether border size",
                                    examples=[1500])
    end_border: float = Field(description="The End border size",
                                    examples=[1034.33])

    @classmethod
    async def fetch(cls, db: Database, guild_id: int) -> Optional["WorldModel"]:
        data = await db.pool.fetchrow("""
                                       SELECT overworld_border,
                                              nether_border,
                                              end_border
                                       FROM server.world
                                       WHERE guild_id = $1
                                       """,
                                      guild_id)

        return cls(**data) if data else None

    async def update(self, db: Database):
        await db.pool.execute("""
                              UPDATE server.world
                              SET overworld_border = $1,
                                  nether_border = $2,
                                  end_border = $3
                              WHERE guild_id = $4
                              """,
                              self.overworld_border, self.nether_border, self.end_border, self.guild_id)

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


@openapi.component()
class WorldUpdateModel(BaseModel):
    overworld_border: float = Field(description="The Overworld border size",
                                    examples=[2000])
    nether_border: float = Field(description="The Nether border size",
                                    examples=[1500])
    end_border: float = Field(description="The End border size",
                                    examples=[1034.33])

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")
