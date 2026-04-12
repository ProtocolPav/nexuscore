from pydantic import BaseModel, Field, UUID4
from typing import Literal, Optional


class TokenRequest(BaseModel):
    grant_type: Literal["client_credentials"] = Field(description="The grant type, always `client_credentials`")
    client_id: UUID4 = Field(description="The client ID",
                             examples=["123e4567-e89b-12d3-a456-426655440000"])
    client_secret: str = Field(description="The raw API key or 'secret', sent once to get a JWT")
    scope: list[str] = Field(description="The scopes to request. Leave empty for all available scopes.",
                             examples=[["guilds:write", "guilds:read"]],
                             default=[])
    guild_id: Optional[int] = Field(description="The guild ID to request a token for.\n"
                                                "> [!warning]\n"
                                                "> Used only for master clients looking to perform guild-scoped actions.",
                                    examples=[123456789012345678],
                                    default=None)

class TokenResponse(BaseModel):
    access_token: str = Field(description="The JWT token")
    token_type: Literal["bearer"] = Field(description="The token type, always `bearer`",
                                          examples=["bearer"],
                                          default="bearer")
    expires_in: int = Field(description="The number of seconds until the token expires. Typical lifetime is 60 minutes",
                            examples=[3600])
    scope: list[str] = Field(description="The scopes granted by the token, could be a subset of requested scopes",
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
    scopes: list[str] = Field(description="The scopes granted by the token, could be a subset of requested scopes",
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
    scopes: list[str] = Field(description="The requested scopes of the client",
                             examples=[["guilds:write", "guilds:read"]])

class ClientCreateResponse(BaseModel):
    client_id: UUID4 = Field(description="The client ID of the created client",
                             examples=["123e4567-e89b-12d3-a456-426655440000"])
    client_secret: str = Field(description="The **raw** client secret. This will be shown once and never stored in a raw form")
    scopes: list[str] = Field(description="The full available scopes granted by the client",
                             examples=[["guilds:write", "guilds:read"]])