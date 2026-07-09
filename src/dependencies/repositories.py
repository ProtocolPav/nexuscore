from fastapi import Depends

from src.dependencies.database import Database, get_db
from src.repositories.guild import GuildRepository
from src.repositories.quests.objective import ObjectiveRepository
from src.repositories.pin import PinRepository
from src.repositories.project import ProjectRepository
from src.repositories.quests.objective_progress import ObjectiveProgressRepository
from src.repositories.quests.quest import QuestRepository
from src.repositories.quests.quest_progress import QuestProgressRepository
from src.repositories.quests.reward import RewardRepository
from src.repositories.user import UserRepository
from src.repositories.wiki.content import ContentRepository
from src.repositories.wiki.page import PageRepository
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
) -> ProjectRepository:
    return ProjectRepository(database)

def get_pin_repo(
        database: Database = Depends(get_db),
) -> PinRepository:
    return PinRepository(database)

def get_quest_repo(
        database: Database = Depends(get_db),
) -> QuestRepository:
    return QuestRepository(database)

def get_objective_repo(
        database: Database = Depends(get_db),
) -> ObjectiveRepository:
    return ObjectiveRepository(database)

def get_reward_repo(
        database: Database = Depends(get_db),
) -> RewardRepository:
    return RewardRepository(database)

def get_quest_progress_repo(
        database: Database = Depends(get_db),
) -> QuestProgressRepository:
    return QuestProgressRepository(database)

def get_objective_progress_repo(
        database: Database = Depends(get_db),
) -> ObjectiveProgressRepository:
    return ObjectiveProgressRepository(database)

def get_wiki_page_repo(
        database: Database = Depends(get_db),
) -> PageRepository:
    return PageRepository(database)

def get_wiki_content_repo(
        database: Database = Depends(get_db),
) -> ContentRepository:
    return ContentRepository(database)