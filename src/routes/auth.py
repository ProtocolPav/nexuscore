import base64
import secrets
from typing import Optional

from argon2 import PasswordHasher
from fastapi import APIRouter, Form, Header, Security, status

from src.dependencies.auth import get_current_client
from src.dependencies.auth.keys import verify_api_key
from src.dependencies.auth.token import create_token
from src.dependencies.database import db
from src.errors import InvalidCredentials
from src.models.auth import ClientCreateRequest, ClientCreateResponse, TokenPayload, TokenResponse, Scope

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
ph = PasswordHasher()

@auth_router.post("/token")
async def get_token(
        grant_type: str = Form(description="The grant type, always `client_credentials`",
                               default="client_credentials"),
        scope: str = Form(description="The scopes to request. Leave empty for all available scopes.",
                          default=""),
        guild_id: Optional[int] = Form(description="The guild ID to request a token for.\n"
                                                   "> [!warning]\n"
                                                   "> Used only for master clients looking to perform guild-scoped actions.",
                                       default=None),
        client_id: Optional[str] = Form(description="The client ID",
                                        default=None),
        client_secret: Optional[str] = Form(description="The raw client secret",
                                            default=None),
        authorization: Optional[str] = Header(alias="Authorization",
                                              description="Basic Auth credentials as `Basic base64(client_id:client_secret)`. Takes priority over body if both are provided.",
                                              default=None),
) -> TokenResponse:
    basic_id, basic_secret = None, None
    if authorization and authorization.startswith("Basic "):
        try:
            decoded = base64.b64decode(authorization[6:]).decode("utf-8")
            basic_id, basic_secret = decoded.split(":", 1)
        except Exception:
            raise InvalidCredentials()

    # Basic Auth takes priority over body
    resolved_id = basic_id or client_id
    resolved_secret = basic_secret or client_secret

    if not resolved_id or not resolved_secret:
        raise InvalidCredentials()

    client = await verify_api_key(str(resolved_id), resolved_secret)
    if not client:
        raise InvalidCredentials()

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
        _: TokenPayload = Security(get_current_client, scopes=[Scope.ADMIN_CLIENTS])
) -> ClientCreateResponse:
    """Master-tier clients only. Creates a guild-scoped API key."""
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