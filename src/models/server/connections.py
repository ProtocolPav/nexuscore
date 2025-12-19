from pydantic import Field

from src.utils.base import BaseModel, BaseList
from src.database import Database

from datetime import datetime
from typing import Literal


class ConnectionBaseModel(BaseModel):
    type: Literal["connect", "disconnect"] = Field(description="The type of connection",
                                                   json_schema_extra={"example": 'connect'})
    thorny_id: int = Field(description="The user who is connecting",
                           json_schema_extra={"example": 43})
    ignored: bool = Field(description="Ignore this connection. Ignored connections aren't included in metrics",
                          default=False,
                          json_schema_extra={"example": False})


class ConnectionModel(ConnectionBaseModel):
    connection_id: int = Field(description="The connection ID",
                               json_schema_extra={"example": 3432})
    time: datetime = Field(description="A datetime object representing the time of the connection",
                           json_schema_extra={"example": '2025-01-01 04:23:32+00:00'})

    @classmethod
    async def create(cls, db: Database, model: "ConnectionCreateModel", *args):
        await db.pool.execute("""
                              INSERT INTO events.connections(type, thorny_id, ignored)
                              VALUES($1, $2, $3)
                              """,
                              model.type, model.thorny_id, model.ignored)


class ConnectionCreateModel(ConnectionBaseModel):
    pass