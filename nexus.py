import secrets
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Response, Depends, Security, HTTPException, status
from fastapi.security import APIKeyHeader, HTTPBasicCredentials, HTTPBasic
from scalar_fastapi import get_scalar_api_reference, Theme, AgentScalarConfig
from fastapi.middleware.cors import CORSMiddleware

from src.database import db

from src.routes import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_pool()
    yield
    await db.close_pool()

app = FastAPI(
    title="Nexuscore",
    description="The backend for all Everthorn internal services",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    root_path="/api",
    lifespan=lifespan,
)

security = HTTPBasic()

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

@app.get("/docs", include_in_schema=False, dependencies=[Depends(get_current_username)])
async def scalar_html():
    return get_scalar_api_reference(
        # Your OpenAPI document
        openapi_url=app.openapi_url,
        scalar_proxy_url="https://proxy.scalar.com",
        theme=Theme.ALTERNATE,
        agent=AgentScalarConfig(disabled=True),
        authentication={
            'preferredSecurityScheme': 'APIKeyHeader',
            'securitySchemes': {
                'APIKeyHeader': {
                    'name': 'X-API-KEY',
                    'in': 'header',
                    'value': '9d207bf0-10f5-4d8f-a479-22ff5aeff8d1'
                },
            }
        }
    )

origins = [
    "http://localhost:3000",
    "https://localhost:3000",
    "https://api.everthorn.net",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VALID_API_KEYS = {
    "usr_alice": "9d207bf0-10f5-4d8f-a479-22ff5aeff8d1"
}

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=True)


def verify_api_key(api_key: str = Security(API_KEY_HEADER)) -> str:
    """Validate the API key from the X-API-Key header."""
    # Use secrets.compare_digest to prevent timing attacks
    for owner, valid_key in VALID_API_KEYS.items():
        if secrets.compare_digest(api_key, valid_key):
            return owner  # Return the key owner for use in the route
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )

app.include_router(api_router, dependencies=[Depends(verify_api_key)])

@app.get("/healthcheck", include_in_schema=False)
async def health_check():
    """
    Used by GCP to check for instance health,
    GCP will automatically restart the instance if this health check
    returns a 404 3 times in a row
    """
    return Response(status_code=200)
