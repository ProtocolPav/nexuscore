from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Response, Depends
from scalar_fastapi import get_scalar_api_reference, Theme
from fastapi.middleware.cors import CORSMiddleware

from src.database import db

#from src.routes import blueprint_group

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

@app.get("/docs", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        # Your OpenAPI document
        openapi_url=app.openapi_url,
        # Avoid CORS issues (optional)
        scalar_proxy_url="https://proxy.scalar.com",
        theme=Theme.ALTERNATE
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

@app.get("/healthcheck")
async def health_check():
    """
    Healthcheck

    Used by GCP to check for instance health,
    GCP will automatically restart the instance if this health check
    returns a 404 3 times in a row
    """
    return Response(status_code=200)

#app.blueprint(blueprint_group)
