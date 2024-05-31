from datetime import datetime, date
from typing import Literal

from pydantic import StringConstraints, BaseModel
from typing_extensions import Annotated, Optional

import json

from sanic_ext import openapi

from src.database import Database


class ConnectionModel(BaseModel):
    connection_id: int
    time: datetime
    type: Literal["connect", "disconnect"]
    thorny_id: int
    ignored: bool

    @classmethod
    async def new(cls, db: Database, model: "ConnectionCreateModel", ignore: bool = False):
        await db.pool.execute("""
                              INSERT INTO events.connections(type, thorny_id, ignored)
                              VALUES($1, $2, $3)
                              """,
                              model.type, model.thorny_id, ignore)


class ConnectionCreateModel(BaseModel):
    type: Literal["connect", "disconnect"]
    thorny_id: int


# Either: minecraft:your_id_name
InteractionRef = Annotated[str, StringConstraints(pattern='^[a-z]+:[a-z_]+$')]


class InteractionModel(BaseModel):
    interaction_id: int
    thorny_id: int
    type: Literal["kill", "mine", "place", "use", "die"]
    position_x: int
    position_y: int
    position_z: int
    reference: str
    mainhand: Optional[InteractionRef]
    time: datetime
    dimension: InteractionRef

    @classmethod
    async def new(cls, db: Database, model: "InteractionCreateModel"):
        await db.pool.execute("""
                              INSERT INTO events.interactions(thorny_id,
                                                              type,
                                                              position_x, 
                                                              position_y,
                                                              position_z,
                                                              reference,
                                                              mainhand,
                                                              time,
                                                              dimension)
                              VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9)
                              """,
                              model.thorny_id, model.type, model.position_x, model.position_y,
                              model.position_z, model.reference, model.mainhand, model.time, model.dimension)


class InteractionCreateModel(BaseModel):
    thorny_id: int
    type: Literal["kill", "mine", "place", "use", "die"]
    position_x: int
    position_y: int
    position_z: int
    reference: str
    mainhand: Optional[InteractionRef]
    time: datetime
    dimension: InteractionRef
