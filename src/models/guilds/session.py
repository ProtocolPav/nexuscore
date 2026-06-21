from datetime import datetime, timedelta

from pydantic import Field, BaseModel
from typing_extensions import Annotated

from src.models.users.user import UserOut

ConnectEventID = Annotated[int, Field(
    description="The ID of the connect event",
    examples=[3422]
)]
DisconnectEventID = Annotated[int, Field(
    description="The ID of the disconnect event",
    examples=[3422]
)]
ConnectTime = Annotated[datetime, Field(
    description="The time the user connected",
    examples=['2024-05-05 05:34:21.123456']
)]
DisconnectTime = Annotated[datetime, Field(
    description="The time the user disconnected",
    examples=['2024-05-05 06:24:21.123456']
)]
Playtime = Annotated[timedelta, Field(
    description="The playtime timedelta object",
    examples=[123456]
)]
SessionDuration = Annotated[float, Field(
    description="The duration of the session in seconds",
    examples=[123456]
)]
ThornyID = Annotated[int, Field(
    description="The ThornyID of the user",
    examples=[543]
)]

class SessionDB(BaseModel):
    connect_event_id: ConnectEventID
    disconnect_event_id: DisconnectEventID
    connect_time: ConnectTime
    disconnect_time: DisconnectTime
    playtime: Playtime
    thorny_id: ThornyID

class SessionOut(BaseModel):
    start: ConnectTime
    end: DisconnectTime
    duration: SessionDuration
    user: UserOut
