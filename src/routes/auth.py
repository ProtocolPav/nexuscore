import secrets
from typing import Optional

from argon2 import PasswordHasher
from fastapi import APIRouter, Depends, Form, HTTPException, status

from src.dependencies.auth import require_scope
from src.dependencies.auth.keys import verify_api_key
from src.dependencies.auth.token import create_token
from src.dependencies.database import db
from src.models.auth import ClientCreateRequest, ClientCreateResponse, TokenPayload, TokenResponse

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
ph = PasswordHasher()

@auth_router.post("/token")
async def get_token(
        grant_type: str = Form(description="The grant type, always `client_credentials`",
                               default="client_credentials"),
        client_id: str = Form(description="The client ID"),
        client_secret: str = Form(description="The raw client secret"),
        scope: str = Form(description="The scopes to request. Leave empty for all available scopes.",
                          default=""),
        guild_id: Optional[int] = Form(description="The guild ID to request a token for.\n"
                                                   "> [!warning]\n"
                                                   "> Used only for master clients looking to perform guild-scoped actions.",
                                       default=None),
) -> TokenResponse:
    client = await verify_api_key(str(client_id), client_secret)
    if not client:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid client credentials")

    # Intersect requested scopes with granted scopes
    granted = set(client["scopes"])
    requested = set(scope.split()) if scope else granted
    final_scopes = sorted(granted & requested)

    requested_guild_id = guild_id if guild_id and client["tier"] == 'master' else client["guild_id"]

    token, ttl = create_token(
        client_id=str(client["client_id"]),
        tier=client["tier"],
        guild_id=requested_guild_id,
        scopes=final_scopes
    )
    return TokenResponse(access_token=token, expires_in=ttl,
                         scope=final_scopes)


@auth_router.post("/clients", status_code=status.HTTP_201_CREATED)
async def register_client(
        body: ClientCreateRequest,
        token: TokenPayload = Depends(require_scope("clients:write"))
) -> ClientCreateResponse:
    """Master-tier clients only. Creates a guild-scoped API key."""
    if token.tier != "master":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only master-tier clients can register new clients")

    raw_key = secrets.token_urlsafe(48)
    hashed = ph.hash(raw_key)
    client_id = await db.pool.fetchval(
        """
        INSERT INTO auth.clients (client_name, hashed_key, tier, guild_id, scopes)
        VALUES ($1, $2, 'guild', $3, $4)
        RETURNING client_id
        """,
        body.client_name, hashed, body.guild_id, body.scopes
    )
    return ClientCreateResponse(client_id=client_id,
                                client_secret=raw_key,
                                scopes=body.scopes)