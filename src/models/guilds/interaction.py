from datetime import datetime
from typing import Literal, Optional

from pydantic import Field, BaseModel, StringConstraints
from typing_extensions import Annotated

MINECRAFT_REGEX_PATTERN = r'^([a-z]+:[0-9a-z_*]+|[A-Za-z0-9_ \-\.]+)$'

InteractionID = Annotated[int, Field(
    description="The ID of the interaction",
    examples=[3422]
)]
ThornyID = Annotated[int, Field(
    description="The ThornyID of the user",
    examples=[543]
)]
InteractionType = Annotated[Literal["kill", "mine", "place", "use", "die", "scriptevent"], Field(
    description="The type of interaction",
    examples=['kill']
)]
Coordinates = Annotated[tuple[int, int, int], Field(
    description="The coordinates of the interaction",
    examples=[(12, 34, 56)]
)]
Reference = Annotated[str, Field(
    description="The reference of the interaction",
    examples=['minecraft:skeleton'],
    pattern=MINECRAFT_REGEX_PATTERN
)]
Mainhand = Annotated[str, Field(
    description="The mainhand of the interaction",
    examples=['minecraft:diamond_sword'],
    pattern=MINECRAFT_REGEX_PATTERN
)]
Time = Annotated[datetime, Field(
    description="The time of the interaction",
)]
Dimension = Annotated[str, Field(
    description="The dimension of the interaction",
    examples=['minecraft:overworld'],
    pattern=MINECRAFT_REGEX_PATTERN
)]

class InteractionDB(BaseModel):
    interaction_id: InteractionID
    thorny_id: ThornyID
    type: InteractionType
    coordinates: Coordinates
    reference: Reference
    mainhand: Optional[Mainhand]
    time: Time
    dimension: Dimension

class InteractionIn(BaseModel):
    thorny_id: ThornyID
    type: InteractionType
    coordinates: Coordinates
    reference: Reference
    mainhand: Optional[Mainhand]
    dimension: Dimension

class InteractionOut(InteractionDB):
    pass

class InteractionQuery(BaseModel):
    coordinates: Optional[list[int]] = Field(description="The coordinates where it happened",
                                             examples=[[-432, 74, 85]], default=None)
    coordinates_end: Optional[list[int]] = Field(description="Optional End coordinates",
                                                 examples=[[-432, 74, 85]], default=None)
    thorny_ids: Optional[list[int]] = Field(description="The thorny IDs to filter by",
                                            examples=[1, 2021, 543], default=None)
    interaction_types: Optional[list[InteractionType]] = Field(description="The interaction types to filter by",
                                                               examples=["kill", "place"], default=None)
    references: Optional[list[str]] = Field(description="The references to filter by",
                                                             examples=["minecraft:dirt", "minecraft:diamond_sword"], default=None)
    dimensions: Optional[list[str]] = Field(description="The dimensions to filter by",
                                            examples=["minecraft:overworld", "minecraft:the_nether"], default=None)
    time_start: Optional[datetime] = Field(description="The start time of the interaction events",
                                           examples=["2025-01-01 04:00:00+00:00"], default=None)
    time_end: Optional[datetime] = Field(description="The end time of the interaction events",
                                         examples=["2025-01-01 04:00:00+00:00"], default=None)
    page: Optional[int] = Field(description="The page number of the results. Defaults to 1",
                                examples=[1], default=1)
    page_size: Optional[int] = Field(description="The number of results per page. Defaults to 100",
                                     examples=[10], default=100)