from datetime import datetime, date
from typing import Literal

import httpx
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


class RelayModel(BaseModel):
    type: Literal["message", "start", "stop", "crash", "join", "leave", "other"]
    content: str
    embed_title: str
    embed_content: str
    name: str


    def generate_embed(self):
        if self.type == 'stop':
            return {'title': self.embed_title, 'color': 13763629, 'description': self.embed_content}
        elif self.type == 'start':
            return {'title': self.embed_title, 'color': 776785, 'description': self.embed_content}
        elif self.type == 'crash':
            return {'title': self.embed_title, 'color': 16738740, 'description': self.embed_content}
        elif self.type == 'join':
            return {'title': self.embed_title, 'color': 40544, 'description': self.embed_content}
        elif self.type == 'leave':
            return {'title': self.embed_title, 'color': 14893620, 'description': self.embed_content}
        elif self.type == 'other':
            return {'title': self.embed_title, 'color': 14679808, 'description': self.embed_content}

    async def relay(self):
        webhook_url = "https://discord.com/api/webhooks/1220073150944120852/sm-znmdkPUkhw33n_jquHb97qLcaOlCOsHdaRY-zWednGIaDU4irO6rE8iVrvwBP8-FG"
        webhook_content = {'username': self.name or 'Server',
                           'content': self.content,
                           'embeds': [] if self.type == 'message' else [self.generate_embed()],
                           'attachments': []}

        async with httpx.AsyncClient() as client:
            await client.request(method="POST", url=webhook_url, json=webhook_content)


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
                                                              dimension)
                              VALUES($1, $2, $3, $4, $5, $6, $7, $8)
                              """,
                              model.thorny_id, model.type, model.position_x, model.position_y,
                              model.position_z, model.reference, model.mainhand, model.dimension)

    @classmethod
    async def check_coordinates(cls, db: Database, coordinates: tuple[int, int, int]) -> bool:
        exists = await db.pool.fetchrow("""
                                        SELECT
                                        CASE WHEN EXISTS 
                                        (
                                            SELECT * FROM events.interactions i WHERE 
                                            i.position_x = $1
                                            and i.position_y = $2
                                            and i.position_z = $3
                                            and type = 'place'
                                        )
                                        THEN true 
                                        ELSE false
                                        END
                                        """,
                                       coordinates[0], coordinates[1], coordinates[2])

        return exists['case']


class InteractionCreateModel(BaseModel):
    thorny_id: int
    type: Literal["kill", "mine", "place", "use", "die"]
    position_x: int
    position_y: int
    position_z: int
    reference: str
    mainhand: Optional[InteractionRef]
    dimension: InteractionRef
