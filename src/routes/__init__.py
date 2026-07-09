from src.routes.relay import relay_router
from src.routes.guild import guilds_router
from src.routes.leaderboard import leaderboard_router
from src.routes.pins import pins_router
from src.routes.project import projects_router
from src.routes.user import members_router
from src.routes.quests import quests_router
from src.routes.quest_progress import quest_progress_router
from src.routes.wiki import wiki_router
from src.routes.world import world_router

from fastapi import APIRouter

api_router = APIRouter()

api_router.include_router(guilds_router)
api_router.include_router(leaderboard_router)
api_router.include_router(members_router)
api_router.include_router(relay_router)
api_router.include_router(pins_router)
api_router.include_router(projects_router)
api_router.include_router(quests_router)
api_router.include_router(quest_progress_router)
api_router.include_router(world_router)
api_router.include_router(wiki_router)