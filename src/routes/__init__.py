from src.routes.events import events
from src.routes.guilds import guild
from src.routes.pins import pins
from src.routes.projects import projects
from src.routes.users import users

from fastapi import APIRouter

api_router = APIRouter(
    prefix='/v1',
)

api_router.include_router(users)
api_router.include_router(events)
api_router.include_router(guild)
api_router.include_router(pins)
api_router.include_router(projects)
