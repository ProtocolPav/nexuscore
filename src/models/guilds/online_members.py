from datetime import datetime
from typing import Optional

from pydantic import Field, BaseModel
from typing_extensions import Annotated

ThornyID = Annotated[int, Field(
    description="The ThornyID of the user",
    examples=[543]
)]
UserID = Annotated[int, Field(
    description="The Discord ID of the user",
    examples=[18463748938364]
)]
Session = Annotated[datetime, Field(
    description="The date and time when the session started",
    examples=['2024-05-05 13:44:33+00:00']
)]
Username = Annotated[str, Field(
    description="The username of the user",
    examples=['protocolpav']
)]
Whitelist = Annotated[str, Field(
    description="The gamertag of the user",
    examples=['ProtocolPav']
)]
Location = Annotated[tuple[int, int, int], Field(
    description="The last in-game location of the user",
    examples=[(544, 18, -432)]
)]
Dimension = Annotated[str, Field(
    description="The last in-game dimension the user was in",
)]
Hidden = Annotated[bool, Field(
    description="Whether the user should be hidden on the Live Map",
)]
XUID = Annotated[str, Field(
    description="The XUID of the user",
    examples=['127843834324332']
)]

class OnlineMemberDB(BaseModel):
    thorny_id: ThornyID
    user_id: UserID
    session: Session
    username: Username
    whitelist: Whitelist
    location: Location
    dimension: Dimension
    hidden: Hidden
    xuid: Optional[XUID]

class OnlineMemberOut(OnlineMemberDB):
    pass