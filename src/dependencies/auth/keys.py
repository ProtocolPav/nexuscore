from typing import Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from src.dependencies.database import db

ph = PasswordHasher()

async def verify_api_key(client_id: str, raw_key: str) -> Optional[dict]:
    row = await db.fetchrow(
        "SELECT * FROM auth.clients WHERE client_id = $1 AND is_active = TRUE",
        client_id
    )

    if not row:
        return None

    try:
        ph.verify(raw_key, row["hashed_key"])
    except VerifyMismatchError:
        return None

    await db.execute(
        "UPDATE auth.clients SET last_used_at = now() WHERE client_id = $1",
        client_id
    )

    return dict(row)