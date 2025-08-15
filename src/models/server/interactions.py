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
    async def fetch(cls,
                    db: Database,
                    coordinates: list[int] = None,
                    coordinates_end: list[int] = None,
                    thorny_ids: list[int] = None,
                    interaction_types: list[InteractionType] = None,
                    references: list[str | InteractionRef] = None,
                    dimensions: list[str] = None,
                    time_start: datetime = None,
                    time_end: datetime = None,
                    *args) -> "InteractionListModel":
        """
        Fetches a list of interactions from the database based on specified filters.

        Parameters
        ----------
        db : Database
            Database connection instance used to make the query.
        coordinates : list of int, optional
            A list of integers defining the starting coordinates to filter the query.
        coordinates_end : list of int, optional
            A list of integers defining the ending coordinates for the range filter.
        thorny_ids : list of int, optional
            A list of IDs representing thorny users to be retrieved.
        interaction_types : list of InteractionType, optional
            A list of interaction types to match in the query results.
        references : list of str or InteractionRef, optional
            A list of references or identifiers related to the interaction events.
        dimensions : list of str, optional
            A list of dimension names to filter the interactions.
        time_start : datetime, optional
            The starting time of the interaction events to filter by.
        time_end : datetime, optional
            The ending time of the interaction events to filter by.
        *args
            Additional arguments that may be passed but not utilized directly.

        Returns
        -------
        InteractionListModel
            A model containing the list of fetched interactions.
        """

        data = await db.pool.fetch("""
                                   SELECT * FROM events.interactions i
                                   WHERE i.coordinates = ARRAY[$1::smallint, $2::smallint, $3::smallint]
                                   """,
                                   coordinates[0], coordinates[1], coordinates[2])

        interactions: list[InteractionModel] = []
        for interaction in data:
            interactions.append(InteractionModel(**interaction))

        return cls(root=interactions)


class InteractionCreateModel(InteractionBaseModel):
    pass