import secrets

from fastapi import HTTPException, Security, status, Depends
from fastapi.security import APIKeyHeader, HTTPBasicCredentials, HTTPBasic

# These are temporary, for dev mode for now.
VALID_API_KEYS = {
    "usr_alice": "9d207bf0-10f5-4d8f-a479-22ff5aeff8d1"
}

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=True)
security = HTTPBasic()

def verify_api_key(api_key: str = Security(API_KEY_HEADER)) -> str:
    """
    Validate the API key from the X-API-Key header.

    For getting the owner of the key, add a parameter `owner: str = Security(get_api_key_owner)` to the route.
    """
    # Use secrets.compare_digest to prevent timing attacks
    for owner, valid_key in VALID_API_KEYS.items():
        if secrets.compare_digest(api_key, valid_key):
            return owner  # Return the key owner for use in the route
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    correct_username = secrets.compare_digest(credentials.username, "admin")
    correct_password = secrets.compare_digest(credentials.password, "admin")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username