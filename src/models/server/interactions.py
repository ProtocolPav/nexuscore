from datetime import datetime
from typing import Literal

from pydantic import StringConstraints, Field
from typing_extensions import Annotated, Optional

from src.database import Database
from src.utils.base import BaseModel, BaseList


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

    @classmethod
    async def check_coordinates(cls, db: Database, coordinates: list[int]) -> bool:
        exists = await db.pool.fetchrow("""
                                        SELECT
                                            CASE WHEN EXISTS (
                                                SELECT 1
                                                FROM events.interactions i
                                                WHERE i.coordinates = ARRAY[$1::smallint, $2::smallint, $3::smallint]
                                            )
                                            THEN true
                                            ELSE false
                                        END;
                                        """,
                                       coordinates[0], coordinates[1], coordinates[2])

        return exists['case']


class InteractionCreateModel(InteractionBaseModel):
    pass