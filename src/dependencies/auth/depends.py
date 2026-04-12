from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from .token import decode_token
from src.models.auth import TokenPayload

bearer_scheme = HTTPBearer()

def require_auth(
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> TokenPayload:
    try:
        payload = decode_token(credentials.credentials)
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