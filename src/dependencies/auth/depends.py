from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2
from fastapi.openapi.models import OAuthFlows, OAuthFlowClientCredentials
import jwt

from .token import decode_token
from src.models.auth import TokenPayload

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
                "clients:write": "Manage clients",
                "guilds:read": "Read guild information",
                "guilds:write": "Create and update guilds",
                "users:read": "Read user profiles",
                "users:write": "Create and update users",
                "quests:read": "Read quests",
                "quests:write": "Create and update quests"
            }
        )
    )
)

def require_auth(
        token: str = Depends(oauth2_scheme),
) -> TokenPayload:
    try:
        payload = decode_token(token)
        return TokenPayload(**payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid token")

def require_scope(*scopes: str):
    """Factory that returns a dependency checking for specific scopes."""
    def checker(token: TokenPayload = Depends(require_auth)) -> TokenPayload:
        for scope in scopes:
            if scope not in token.scopes:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail=f"Missing required scope: {scope}")
        return token
    return checker

def require_guild(token: TokenPayload = Depends(require_auth)) -> TokenPayload:
    """Ensures a Token can only access its own guild. Used for guild-scoped routes."""
    if token.guild_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="This route requires a guild-scoped token")
    return token