from enum import Enum

from pydantic import BaseModel, Field, UUID4
from typing import Literal, Optional


class Scope(str, Enum):
    GUILDS_READ = "guilds:read"
    GUILDS_WRITE = "guilds:write"

    GUILDS_MEMBERS_READ = "guilds.members:read"
    GUILDS_MEMBERS_WRITE = "guilds.members:write"
    GUILDS_PROJECTS_READ = "guilds.projects:read"
    GUILDS_PROJECTS_WRITE = "guilds.projects:write"
    GUILDS_PINS_READ = "guilds.pins:read"
    GUILDS_PINS_WRITE = "guilds.pins:write"

    GUILDS_QUESTS_READ = "guilds.quests:read"
    GUILDS_QUESTS_WRITE = "guilds.quests:write"
    EVENTS_READ = "events:read"
    EVENTS_WRITE = "events:write"
    SERVER_READ = "server:read"

    ADMIN_CLIENTS = "admin:clients"
    ADMIN_GUILDS = "admin:guilds"


SCOPE_DESCRIPTIONS: dict[Scope, str] = {
    Scope.GUILDS_READ: "Read guild configuration",
    Scope.GUILDS_WRITE: "Update guild settings",
    Scope.GUILDS_MEMBERS_READ: "Read user profiles",
    Scope.GUILDS_MEMBERS_WRITE: "Create and update users",
    Scope.GUILDS_PROJECTS_READ: "Read project data",
    Scope.GUILDS_PROJECTS_WRITE: "Create and update projects",
    Scope.GUILDS_PINS_READ: "Read map pin data",
    Scope.GUILDS_PINS_WRITE: "Create and update map pins",
    Scope.GUILDS_QUESTS_READ: "Read quests_router and progress",
    Scope.GUILDS_QUESTS_WRITE: "Create and update quests_router",
    Scope.EVENTS_READ: "Read server events",
    Scope.EVENTS_WRITE: "Create server events",
    Scope.SERVER_READ: "Read Minecraft server data",
    Scope.ADMIN_CLIENTS: "Register new guild clients",
    Scope.ADMIN_GUILDS: "Create new Guilds",
}


class TokenResponse(BaseModel):
    access_token: str = Field(description="The JWT token")
    token_type: Literal["bearer"] = Field(description="The token type, always `bearer`",
                                          examples=["bearer"],
                                          default="bearer")
    expires_in: int = Field(description="The number of seconds until the token expires. Typical lifetime is 60 minutes",
                            examples=[3600])
    scope: list[Scope] = Field(description="The scopes granted by the token, could be a subset of requested scopes",
                             examples=[["guilds:write", "guilds:read"]])

class TokenPayload(BaseModel):
    sub: UUID4 = Field(description="The client ID of the client that requested the token",
                       examples=["123e4567-e89b-12d3-a456-426655440000"])
    tier: Literal["master", "guild"] = Field(description="The tier of the client",
                                            examples=["master", "guild"])
    guild_id: Optional[int] = Field(description="The guild ID of the client.\n"
                                                "> [!tip]\n"
                                                "> Master clients looking for guild-scoped actions must request a token with guild_id",
                                    examples=[123456789012345678],
                                    default=None)
    scopes: list[Scope] = Field(description="The scopes granted by the token, could be a subset of requested scopes",
                             examples=[["guilds:write", "guilds:read"]])
    exp: int = Field(description="The expiration time of the token, in seconds since the Unix epoch",
                    examples=[1677516800])
    iat: int = Field(description="The time the token was issued, in seconds since the Unix epoch",
                    examples=[1677516800])

class ClientCreateRequest(BaseModel):
    client_name: str = Field(description="The name of the client",
                            examples=["My cool client"])
    guild_id: int = Field(description="The guild ID of the client",
                         examples=[123456789012345678])
    scopes: list[Scope] = Field(description="The requested scopes of the client",
                             examples=[["guilds:write", "guilds:read"]])

class ClientCreateResponse(BaseModel):
    client_id: UUID4 = Field(description="The client ID of the created client",
                             examples=["123e4567-e89b-12d3-a456-426655440000"])
    client_secret: str = Field(description="The **raw** client secret. This will be shown once and never stored in a raw form")
    scopes: list[Scope] = Field(description="The full available scopes granted by the client",
                             examples=[["guilds:write", "guilds:read"]])