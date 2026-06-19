from fastapi import Depends

from src.dependencies.database import Database, get_db
from src.repositories.guild import GuildRepository
from src.repositories.pin import PinRepository
from src.repositories.project import ProjectRepository
# from src.repositories.quest import QuestRepository
from src.repositories.user import UserRepository
from src.repositories.world import WorldRepository


def get_guild_repo(
        database: Database = Depends(get_db),
) -> GuildRepository:
    return GuildRepository(database)

def get_user_repo(
        database: Database = Depends(get_db)
) -> UserRepository:
    return UserRepository(database)

def get_world_repo(
        database: Database = Depends(get_db),
) -> WorldRepository:
    return WorldRepository(database)

def get_project_repo(
        database: Database = Depends(get_db),
        user_repo: UserRepository = Depends(get_user_repo),
) -> ProjectRepository:
    return ProjectRepository(database, user_repo)

def get_pin_repo(
        database: Database = Depends(get_db),
) -> PinRepository:
    return PinRepository(database)

# def get_quest_repo(
#         database: Database = Depends(get_db),
#         # user_repo: UserRepository = Depends(get_user_repo),
# ) -> QuestRepository:
#     return QuestRepository(database)