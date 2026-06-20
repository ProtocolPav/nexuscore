from fastapi import Depends

from src.dependencies.repositories import get_guild_repo, get_project_repo, get_user_repo
from src.repositories.guild import GuildRepository
from src.repositories.project import ProjectRepository
from src.repositories.user import UserRepository
from src.services.guild import GuildService
from src.services.project import ProjectService


def get_guild_service(
        guild_repo: GuildRepository = Depends(get_guild_repo),
) -> GuildService:
    return GuildService(guild_repo)

def get_project_service(
        project_repo: ProjectRepository = Depends(get_project_repo),
        user_repo: UserRepository = Depends(get_user_repo)
) -> ProjectService:
    return ProjectService(project_repo, user_repo)