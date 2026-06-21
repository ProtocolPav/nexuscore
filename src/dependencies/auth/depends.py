from enum import Enum
from typing import Annotated, Optional
from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import OAuth2
from fastapi.openapi.models import OAuthFlows, OAuthFlowClientCredentials
import jwt
from pydantic import ValidationError

from src.dependencies.auth.token import decode_token
from src.errors import GuildScopedTokenRequired, InvalidCredentials, MissingScope, TokenExpired
from src.models.auth import SCOPE_DESCRIPTIONS, TokenPayload
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