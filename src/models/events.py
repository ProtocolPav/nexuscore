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

    @classmethod
    async def new(cls, db: Database, model: "ConnectionCreateModel"):
        await db.pool.execute("""
                              INSERT INTO events.connections(type, thorny_id)
                              VALUES($1, $2)
                              """,
                              model.type, model.thorny_id)


class ConnectionCreateModel(BaseModel):
    type: Literal["connect", "disconnect"]
    thorny_id: int


# Either: minecraft:your_id_name
# Or: player:Player Gamertag Here
InteractionRef = Annotated[str, StringConstraints(pattern='^[a-z]+:[a-z_]+$')]
PlayerRef = Annotated[str, StringConstraints(pattern='player:.+')]


class InteractionModel(BaseModel):
    interaction_id: int
    thorny_id: int
    type: Literal["kill", "mine", "place", "use", "die"]
    position_x: int
    position_y: int
    position_z: int
    reference: InteractionRef | PlayerRef
    mainhand: Optional[InteractionRef]
    time: datetime
    dimension: InteractionRef


class InteractionCreateModel(BaseModel):
    thorny_id: int
    type: Literal["kill", "mine", "place", "use", "die"]
    position_x: int
    position_y: int
    position_z: int
    reference: InteractionRef | PlayerRef
    mainhand: Optional[InteractionRef]
    time: datetime
    dimension: InteractionRef
