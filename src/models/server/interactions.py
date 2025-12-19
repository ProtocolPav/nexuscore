from datetime import datetime
from typing import Literal

from pydantic import StringConstraints, Field
from sanic_ext.extensions.openapi import openapi
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
                           json_schema_extra={"example": '2025-01-01 04:00:00+00:00'})
    dimension: InteractionRef = Field(description="The dimension",
                                      json_schema_extra={"example": 'minecraft:overworld'})


@openapi.component()
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
                    coordinates: list[str] = None,
                    coordinates_end: list[str] = None,
                    thorny_ids: list[str] = None,
                    interaction_types: list[InteractionType] = None,
                    references: list[str | InteractionRef] = None,
                    dimensions: list[str] = None,
                    time_start: str = None,
                    time_end: str = None,
                    page: int = None,
                    page_size: int = None,
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
        time_start : str, optional
            The starting time of the interaction events to filter by.
        time_end : str, optional
            The ending time of the interaction events to filter by.
        page : int, optional
            The page of data to return
        page_size : int, optional
            The page size of the data to return
        *args
            Additional arguments that may be passed but not utilized directly.

        Returns
        -------
        InteractionListModel
            A model containing the list of fetched interactions.

        Raises
        ------
        NotFound404
            If no interactions match the specified query parameters.
        """

        # Build the query dynamically
        query_parts = ["SELECT * FROM events.interactions i"]
        conditions = []
        params = []

        # Handle coordinates
        if coordinates is not None:
            coordinates_int = [int(x) for x in coordinates]

            if coordinates_end is not None:
                # Area query - between coordinates and coordinates_end
                param_idx = len(params)
                conditions.append(
                    f"i.coordinates[1] BETWEEN ${param_idx + 1}::smallint AND ${param_idx + 4}::smallint AND "
                    f"i.coordinates[2] BETWEEN ${param_idx + 2}::smallint AND ${param_idx + 5}::smallint AND "
                    f"i.coordinates[3] BETWEEN ${param_idx + 3}::smallint AND ${param_idx + 6}::smallint"
                )

                coordinates_end_int = [int(x) for x in coordinates_end]
                params.extend([coordinates_int[0], coordinates_int[1], coordinates_int[2],
                               coordinates_end_int[0], coordinates_end_int[1], coordinates_end_int[2]])
            else:
                # Exact coordinates match
                param_idx = len(params)
                conditions.append(
                    f"i.coordinates = ARRAY[${param_idx + 1}::smallint, ${param_idx + 2}::smallint, ${param_idx + 3}::smallint]")
                params.extend([coordinates_int[0], coordinates_int[1], coordinates_int[2]])

        # Handle thorny_ids (OR condition using ANY)
        if thorny_ids is not None and len(thorny_ids) > 0:
            param_idx = len(params)
            conditions.append(f"i.thorny_id = ANY(${param_idx + 1}::int[])")

            thorny_ids_int = [int(x) for x in thorny_ids]
            params.append(thorny_ids_int)

        # Handle interaction_types (OR condition using ANY)
        if interaction_types is not None and len(interaction_types) > 0:
            # Convert enum types to their values if needed
            type_values = [t.value if hasattr(t, 'value') else t for t in interaction_types]
            param_idx = len(params)
            conditions.append(f"i.type = ANY(${param_idx + 1}::text[])")
            params.append(type_values)

        # Handle references (OR condition using ANY)
        if references is not None and len(references) > 0:
            # Convert InteractionRef to string if needed
            ref_values = [str(r) for r in references]
            ref_conditions = []
            for ref in ref_values:
                param_idx = len(params)
                ref_conditions.append(f"i.reference ILIKE ${param_idx + 1}::text")
                params.append(ref)
            conditions.append(f"({' OR '.join(ref_conditions)})")

        # Handle dimensions (OR condition using ANY)
        if dimensions is not None and len(dimensions) > 0:
            param_idx = len(params)
            conditions.append(f"i.dimension = ANY(${param_idx + 1}::text[])")
            params.append(dimensions)

        # Handle time filtering
        if time_start is not None and time_end is not None:
            # Both start and end provided - use BETWEEN
            param_idx = len(params)
            conditions.append(f"i.time BETWEEN ${param_idx + 1}::timestamptz AND ${param_idx + 2}::timestamptz")
            params.extend([
                datetime.fromisoformat(time_start),
                datetime.fromisoformat(time_end)
            ])
        elif time_start is not None:
            # Only start provided - everything after
            param_idx = len(params)
            conditions.append(f"i.time >= ${param_idx + 1}::timestamptz")
            params.append(datetime.fromisoformat(time_start))
        elif time_end is not None:
            # Only end provided - everything before
            param_idx = len(params)
            conditions.append(f"i.time <= ${param_idx + 1}::timestamptz")
            params.append(datetime.fromisoformat(time_end))

        # Add WHERE clause if we have conditions
        if conditions:
            query_parts.append("WHERE")
            query_parts.append(" AND ".join(conditions))

        # Add ORDER BY clause
        query_parts.append("ORDER BY i.interaction_id DESC")

        # Handle pagination with OFFSET and LIMIT
        if page is not None and page_size is not None:
            # Calculate offset: (page - 1) * page_size
            offset = (page - 1) * page_size
            param_idx = len(params)

            query_parts.append(f"LIMIT ${param_idx + 1}::int OFFSET ${param_idx + 2}::int")
            params.extend([page_size, offset])

        query = " ".join(query_parts)

        # Execute the query
        data = await db.pool.fetch(query, *params)

        # Convert to InteractionModel objects
        interactions: list[InteractionModel] = []
        for interaction in data:
            interactions.append(InteractionModel(**interaction))

        return cls(root=interactions)


class InteractionCreateModel(InteractionBaseModel):
    pass