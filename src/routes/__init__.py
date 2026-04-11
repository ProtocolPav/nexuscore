# from src.routes.quest_progress import progress_blueprint
from src.routes.events import events
from src.routes.guilds import guild
from src.routes.users import users
# from src.routes.events import events_blueprint
# from src.routes.quests import quest_blueprint
# from src.routes.projects import project_blueprint
# from src.routes.guilds import guild_blueprint
# from src.routes.server import server_blueprint
# from src.routes.pins import pin_blueprint
# from src.routes.wrapped import wrapped_blueprint

from fastapi import APIRouter

api_router = APIRouter(
    prefix='/v1',
)

api_router.include_router(users)
api_router.include_router(events)
api_router.include_router(guild)
