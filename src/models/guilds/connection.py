from datetime import datetime
from typing import Literal

from pydantic import Field, BaseModel
from typing_extensions import Annotated

ConnectionId = Annotated[int, Field(
    description="The ID of the connection",
    examples=[3422]
)]
ConnectionType = Annotated[Literal['connect', 'disconnect'], Field(
    description="The type of connection",
    examples=['connect']
)]
ThornyID = Annotated[int, Field(
    description="The ThornyID of the user",
    examples=[543]
)]
Ignored = Annotated[bool, Field(
    description="Whether the connection is ignored in metrics",
    examples=[True],
    default=False
)]
ConnectionTime = Annotated[datetime, Field(
    description="The time of the connection",
)]

class ConnectionDB(BaseModel):
    connection_id: ConnectionId
    type: ConnectionType
    thorny_id: ThornyID
    ignored: Ignored
    time: ConnectionTime

class ConnectionIn(BaseModel):
    thorny_id: ThornyID
    type: ConnectionType

class ConnectionOut(ConnectionDB):
    pass
