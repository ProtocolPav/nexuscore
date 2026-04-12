from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, Depends
from scalar_fastapi import get_scalar_api_reference, Theme, AgentScalarConfig
from fastapi.middleware.cors import CORSMiddleware

from src.dependencies.database import db
from src.dependencies.auth import get_current_username, verify_api_key

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

@app.get("/docs", include_in_schema=False, dependencies=[Depends(get_current_username)])
async def scalar_html():
    return get_scalar_api_reference(
        # Your OpenAPI document
        openapi_url=app.openapi_url,
        scalar_proxy_url="https://proxy.scalar.com",
        theme=Theme.ALTERNATE,
        agent=AgentScalarConfig(disabled=True),
        servers=[{"url": "http://localhost:8000/api"}, {"url": "https://api.everthorn.net"}],
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

app.include_router(
    api_router,
    # dependencies=[Depends(verify_api_key)]
)

@app.get("/healthcheck", include_in_schema=False)
async def health_check():
    """
    Used by GCP to check for instance health,
    GCP will automatically restart the instance if this health check
    returns a 404 3 times in a row
    """
    return Response(status_code=200)
