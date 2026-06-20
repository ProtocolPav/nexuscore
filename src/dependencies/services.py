from fastapi import Depends

from src.dependencies.repositories import get_project_repo, get_user_repo
from src.repositories.project import ProjectRepository
from src.repositories.user import UserRepository
from src.services.project import ProjectService


def get_project_service(
        project_repo: ProjectRepository = Depends(get_project_repo),
        user_repo: UserRepository = Depends(get_user_repo)
) -> ProjectService:
    return ProjectService(project_repo, user_repo)