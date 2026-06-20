from fastapi import Depends

from src.dependencies.repositories import get_guild_repo, get_project_repo, get_user_repo, get_pin_repo, get_world_repo
from src.repositories.guild import GuildRepository
from src.repositories.project import ProjectRepository
from src.repositories.user import UserRepository
from src.repositories.pin import PinRepository
from src.repositories.world import WorldRepository
from src.services.guild import GuildService
from src.services.project import ProjectService
from src.services.pin import PinService
from src.services.user import UserService
from src.services.world import WorldService


def get_guild_service(
        guild_repo: GuildRepository = Depends(get_guild_repo),
) -> GuildService:
    return GuildService(guild_repo)

def get_project_service(
        project_repo: ProjectRepository = Depends(get_project_repo),
        user_repo: UserRepository = Depends(get_user_repo)
) -> ProjectService:
    return ProjectService(project_repo, user_repo)

def get_pin_service(
        pin_repo: PinRepository = Depends(get_pin_repo),
) -> PinService:
    return PinService(pin_repo)

def get_user_service(
        user_repo: UserRepository = Depends(get_user_repo),
) -> UserService:
    return UserService(user_repo)

def get_world_service(
        world_repo: WorldRepository = Depends(get_world_repo),
) -> WorldService:
    return WorldService(world_repo)