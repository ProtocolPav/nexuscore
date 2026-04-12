from typing import Annotated, Optional
from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import OAuth2
from fastapi.openapi.models import OAuthFlows, OAuthFlowClientCredentials
import jwt
from pydantic import ValidationError

from src.dependencies.auth.token import decode_token
from src.models.auth import TokenPayload
from fastapi.security import SecurityScopes


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
            scopes={
                "users:read": "Read user profiles",
                "users:write": "Create and update users",
                "guilds:read": "Read guild configuration",
                "guilds:write": "Update guild settings",
                "quests:read": "Read quests and progress",
                "quests:write": "Create and update quests",
                "events:read": "Read server events",
                "events:write": "Create server events",
                "projects:read": "Read community projects",
                "projects:write": "Create and update projects",
                "server:read": "Read Minecraft server data",
                "admin:clients": "Register new guild clients",
            }
        )
    )
)


async def get_current_client(
        security_scopes: SecurityScopes,
        token: Annotated[Optional[str], Depends(oauth2_scheme)],
) -> TokenPayload:
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )

    if token is None:
        raise credentials_exception

    try:
        payload = decode_token(token)
        client = TokenPayload(**payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": authenticate_value},
        )
    except (jwt.InvalidTokenError, ValidationError):
        raise credentials_exception

    for scope in security_scopes.scopes:
        if scope not in client.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required scope: {scope}",
                headers={"WWW-Authenticate": authenticate_value},
            )

    return client


async def get_guild_client(
        auth: Annotated[TokenPayload, Security(get_current_client)]
) -> TokenPayload:
    if auth.guild_id is None:
        raise HTTPException(status_code=403, detail="Requires guild-scoped token")
    return auth