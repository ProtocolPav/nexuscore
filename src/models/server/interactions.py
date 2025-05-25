from datetime import datetime
from typing import Literal

from pydantic import StringConstraints, Field
from typing_extensions import Annotated, Optional

from src.database import Database
from src.utils.base import BaseModel, BaseList
from src.utils.errors import BadRequest400, NotFound404

InteractionRef = Annotated[str, StringConstraints(pattern='^[a-z]+:[0-9a-z_*]+$')]
InteractionType = Literal["kill", "mine", "place", "use", "die", "scriptevent"]


class InteractionBaseModel(BaseModel):
    thorny_id: int = Field(description="The user who interacted",
                           json_schema_extra={"example": 323})
    type: InteractionType = Field(description="The type of interaction",
                                  json_schema_extra={"example": 'kill'})
    coordinates: list[int] = Field(description="The coordinates where it happened",
                                   json_schema_extra={"example": [-432, 74, 85]})
    reference: str | InteractionRef = Field(description="The reference of the interaction. e.g. what block was mined",
                                            json_schema_extra={"example": 'minecraft:dirt'})
    mainhand: Optional[InteractionRef] = Field(description="The item in the player's mainhand",
                                               json_schema_extra={"example": 'minecraft:diamond_sword'})
    time: datetime = Field(description="The time of this interaction",
                           json_schema_extra={"example": '2025-01-01 04:00:00.123456'})
    dimension: InteractionRef = Field(description="The dimension",
                                      json_schema_extra={"example": 'minecraft:overworld'})


class InteractionModel(InteractionBaseModel):
    interaction_id: int = Field(description="The interaction ID",
                                json_schema_extra={"example": 23321343224})

    @classmethod
    async def create(cls, db: Database, model: "InteractionCreateModel", *args):
        await db.pool.execute("""
                              INSERT INTO events.interactions(thorny_id,
                                                              type,
                                                              coordinates,
                                                              reference,
                                                              mainhand,
                                                              dimension)
                              VALUES($1, $2, $3, $4, $5, $6)
                              """,
                              model.thorny_id, model.type, model.coordinates, model.reference, model.mainhand, model.dimension)


class InteractionListModel(BaseList[InteractionModel]):
    @classmethod
    async def fetch(cls, db: Database, coordinates: list[int] = None, *args) -> "InteractionListModel":
        if not coordinates:
            raise BadRequest400(extra={'ids': ['coordinates']})

        data = await db.pool.fetch("""
                                   SELECT * FROM events.interactions i
                                   WHERE i.coordinates = ARRAY[$1::smallint, $2::smallint, $3::smallint]
                                   """,
                                   coordinates[0], coordinates[1], coordinates[2])

        if data:
            interactions: list[InteractionModel] = []
            for interaction in data:
                interactions.append(InteractionModel(**interaction))

            return cls(root=interactions)
        else:
            raise NotFound404(extra={'resource': 'interaction_list', 'id': f'coords:{coordinates[0]},{coordinates[1]},{coordinates[2]}'})


class InteractionCreateModel(InteractionBaseModel):
    pass