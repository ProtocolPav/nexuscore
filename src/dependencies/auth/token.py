from typing import Optional

import jwt
from datetime import datetime, timedelta, timezone
from src.config import settings

def create_token(
        client_id: str,
        tier: str,
        guild_id: Optional[int],
        scopes: list[str]
) -> tuple[str, int]:
    now = datetime.now(timezone.utc)
    expires = now + timedelta(seconds=settings.TOKEN_TTL_SECONDS)
    payload = {
        "sub": client_id,
        "tier": tier,
        "guild_id": guild_id,
        "scopes": scopes,
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, settings.TOKEN_TTL_SECONDS

def decode_token(token: str) -> dict:
    # Raises jwt.ExpiredSignatureError or jwt.InvalidTokenError on failure
    return jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["exp", "iat", "sub", "scopes"]}
    )