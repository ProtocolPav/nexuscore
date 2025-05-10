from typing import Optional

from pydantic import Field
from sanic_ext import openapi

from src.database import Database
from src.utils.base import BaseModel
from src.utils.errors import BadRequest400, NotFound404


class WorldBaseModel(BaseModel):
    overworld_border: float = Field(description="The Overworld border size",
                                    json_schema_extra={"example": 4000})
    nether_border: float = Field(description="The Nether border size",
                                 json_schema_extra={"example": 1500})
    end_border: float = Field(description="The End border size",
                              json_schema_extra={"example": 134.54})


@openapi.component()
class WorldModel(BaseModel):
    guild_id: int = Field(description="The guild ID that corresponds to this world",
                          json_schema_extra={"example": 123456789012345678})

    @classmethod
    async def fetch(cls, db: Database, guild_id: int, *args) -> "WorldModel":
        if not guild_id:
            raise BadRequest400(extra={'ids': ['guild_id']})

        data = await db.pool.fetchrow("""
                                       SELECT guild_id,
                                              overworld_border,
                                              nether_border,
                                              end_border
                                       FROM server.world
                                       WHERE guild_id = $1
                                       """,
                                      guild_id)

        if data:
            return cls(**data)
        else:
            raise NotFound404(extra={'resource': 'world', 'id': guild_id})

    async def update(self, db: Database, model: "WorldUpdateModel"):
        for k, v in model.model_dump().items():
            setattr(self, k, v) if v else None

        await db.pool.execute("""
                              UPDATE server.world
                              SET overworld_border = $1,
                                  nether_border = $2,
                                  end_border = $3
                              WHERE guild_id = $4
                              """,
                              self.overworld_border, self.nether_border, self.end_border, self.guild_id)


@openapi.component()
class WorldUpdateModel(WorldBaseModel):
    pass
