from enum import Enum
from typing import Annotated, Optional
from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import OAuth2
from fastapi.openapi.models import OAuthFlows, OAuthFlowClientCredentials
import jwt
from pydantic import ValidationError

from src.dependencies.auth.token import decode_token
from src.errors import GuildScopedTokenRequired, InvalidCredentials, MissingScope, TokenExpired
from src.models.auth import TokenPayload
from fastapi.security import SecurityScopes


class Scope(str, Enum):
    GUILDS_READ = "guilds:read"
    GUILDS_WRITE = "guilds:write"

    GUILDS_MEMBERS_READ = "guilds.members:read"
    GUILDS_MEMBERS_WRITE = "guilds.members:write"
    GUILDS_PROJECTS_READ = "guilds.projects:read"
    GUILDS_PROJECTS_WRITE = "guilds.projects:write"

    QUESTS_READ = "quests:read"
    QUESTS_WRITE = "quests:write"
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
    Scope.QUESTS_READ: "Read quests and progress",
    Scope.QUESTS_WRITE: "Create and update quests",
    Scope.EVENTS_READ: "Read server events",
    Scope.EVENTS_WRITE: "Create server events",
    Scope.SERVER_READ: "Read Minecraft server data",
    Scope.ADMIN_CLIENTS: "Register new guild clients",
    Scope.ADMIN_GUILDS: "Create new Guilds",
}


class OAuth2ClientCredentials(OAuth2):
    async def __call__(self, request: Request) -> Optional[str]:
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return None
        return authorization.removeprefix("Bearer ").strip()


oauth2_scheme = OAuth2ClientCredentials(
    flows=OAuthFlows(
        clientCredentials=OAuthFlowClientCredentials(
            tokenUrl="/auth/token",
            refreshUrl="/auth/token",
            scopes={scope.value: desc for scope, desc in SCOPE_DESCRIPTIONS.items()}
        )
    )
)


async def get_current_client(
        security_scopes: SecurityScopes,
        token: Annotated[Optional[str], Depends(oauth2_scheme)],
) -> TokenPayload:
    """
    Returns the current logged in client.

    Raises errors if there is no client or if the client does not have the required scopes.
    """
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"

    if token is None:
        raise InvalidCredentials(authenticate_value)

    try:
        payload = decode_token(token)
        client = TokenPayload(**payload)
    except jwt.ExpiredSignatureError:
        raise TokenExpired(authenticate_value)
    except (jwt.InvalidTokenError, ValidationError):
        raise InvalidCredentials(authenticate_value)

    for scope in security_scopes.scopes:
        if scope not in client.scopes:
            raise MissingScope(scope, authenticate_value)

    return client


async def get_guild_client(
        auth: Annotated[TokenPayload, Security(get_current_client)]
) -> TokenPayload:
    """
    Returns the current logged in client but also ensures that the guild_id is set.

    Used primarily for guild-scoped endpoints.
    """
    if auth.guild_id is None:
        raise GuildScopedTokenRequired()
    return auth