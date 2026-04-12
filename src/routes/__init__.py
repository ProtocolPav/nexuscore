from src.routes.events import events
from src.routes.guilds import guild
from src.routes.pins import pins
from src.routes.projects import projects
from src.routes.users import users
from src.routes.quests import quests
from src.routes.quest_progress import quest_progress_router
from src.routes.server import server
from src.routes.wrapped import wrapped

from fastapi import APIRouter

api_router = APIRouter(
    prefix='/v0.2',
)

api_router.include_router(users)
api_router.include_router(events)
api_router.include_router(guild)
api_router.include_router(pins)
api_router.include_router(projects)
api_router.include_router(quests)
api_router.include_router(quest_progress_router)
api_router.include_router(server)
api_router.include_router(wrapped)