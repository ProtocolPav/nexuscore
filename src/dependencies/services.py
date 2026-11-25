from botocore.client import BaseClient
from fastapi import Depends

from src.dependencies.database import Database
from src.dependencies.r2_client import get_r2_client
from src.dependencies.repositories import (
    get_daily_quest_repo, get_daily_template_repo,
    get_guild_repo,
    get_objective_progress_repo, get_objective_repo,
    get_project_repo,
    get_quest_progress_repo, get_quest_repo,
    get_quest_statistics_repo,
    get_user_repo,
    get_pin_repo,
    get_wiki_content_repo, get_wiki_page_repo, get_world_repo,
    get_reward_repo
)
from src.repositories.guild import GuildRepository
from src.repositories.quests.daily_quest import DailyQuestRepository
from src.repositories.quests.daily_template import DailyTemplateRepository
from src.repositories.quests.objective import ObjectiveRepository
from src.repositories.project import ProjectRepository
from src.repositories.quests.objective_progress import ObjectiveProgressRepository
from src.repositories.quests.quest import QuestRepository
from src.repositories.quests.quest_progress import QuestProgressRepository
from src.repositories.quests.quest_statistics import QuestStatisticsRepository
from src.repositories.quests.reward import RewardRepository
from src.repositories.user import UserRepository
from src.repositories.pin import PinRepository
from src.repositories.wiki.content import ContentRepository
from src.repositories.wiki.page import PageRepository
from src.repositories.world import WorldRepository
from src.services.daily_quest import DailyQuestService
from src.services.guild import GuildService
from src.services.image import ImageService
from src.services.project import ProjectService
from src.services.pin import PinService
from src.services.quest import QuestService
from src.services.quest_progress import QuestProgressService
from src.services.user import UserService
from src.services.wiki import WikiService
from src.services.world import WorldService


def get_guild_service(
        guild_repo: GuildRepository = Depends(get_guild_repo),
        user_repo: UserRepository = Depends(get_user_repo),
) -> GuildService:
    return GuildService(guild_repo, user_repo)

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

def get_quest_service(
        quest_repo: QuestRepository = Depends(get_quest_repo),
        objective_repo: ObjectiveRepository = Depends(get_objective_repo),
        reward_repo: RewardRepository = Depends(get_reward_repo),
        user_repo: UserRepository = Depends(get_user_repo),
        statistics_repo: QuestStatisticsRepository = Depends(get_quest_statistics_repo),
) -> QuestService:
    return QuestService(quest_repo, objective_repo, reward_repo, user_repo, statistics_repo)

def get_quest_progress_service(
        quest_repo: QuestRepository = Depends(get_quest_repo),
        objective_repo: ObjectiveRepository = Depends(get_objective_repo),
        quest_progress_repo: QuestProgressRepository = Depends(get_quest_progress_repo),
        objective_progress_repo: ObjectiveProgressRepository = Depends(get_objective_progress_repo),
) -> QuestProgressService:
    return QuestProgressService(quest_repo, objective_repo, quest_progress_repo, objective_progress_repo)

def get_daily_quest_service(
        template_repo: DailyTemplateRepository = Depends(get_daily_template_repo),
        daily_repo: DailyQuestRepository = Depends(get_daily_quest_repo),
        quest_service: QuestService = Depends(get_quest_service),
        quest_progress_service: QuestProgressService = Depends(get_quest_progress_service),
        user_repo: UserRepository = Depends(get_user_repo),
) -> DailyQuestService:
    return DailyQuestService(template_repo, daily_repo, quest_service, quest_progress_service, user_repo)


# Builders for use outside of a request, e.g. background tasks

def build_quest_service(database: Database) -> QuestService:
    return QuestService(
        QuestRepository(database), ObjectiveRepository(database), RewardRepository(database),
        UserRepository(database), QuestStatisticsRepository(database),
    )

def build_quest_progress_service(database: Database) -> QuestProgressService:
    return QuestProgressService(
        QuestRepository(database), ObjectiveRepository(database),
        QuestProgressRepository(database), ObjectiveProgressRepository(database),
    )

def build_daily_quest_service(database: Database) -> DailyQuestService:
    return DailyQuestService(
        DailyTemplateRepository(database), DailyQuestRepository(database),
        build_quest_service(database), build_quest_progress_service(database),
        UserRepository(database),
    )

def get_wiki_service(
        page_repo: PageRepository = Depends(get_wiki_page_repo),
        content_repo: ContentRepository = Depends(get_wiki_content_repo),
        project_repo: ProjectRepository = Depends(get_project_repo),
        user_repo: UserRepository = Depends(get_user_repo),
) -> WikiService:
    return WikiService(page_repo, content_repo, project_repo, user_repo)

def get_image_service(
        r2_client: BaseClient = Depends(get_r2_client)
) -> ImageService:
    return ImageService(r2_client)