from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, Security, status

from src.dependencies.auth import get_guild_client
from src.dependencies.services import get_daily_quest_service
from src.models.auth import Scope, TokenPayload

from src.models.quests.daily import DailyQuestIn, DailyQuestOut, DailyTemplateIn, DailyTemplateOut, DailyTemplateUpdate
from src.models.quests.quest import QuestOut
from src.services.daily_quest import DailyQuestService

daily_quests_router = APIRouter(prefix='/guilds/me/quests/daily', tags=['Daily Quests'])


QuestDateQuery = Query(
    default=None,
    description="The UTC date of the daily quest. Default: today.",
    examples=["2026-11-27"],
)


@daily_quests_router.get('')
async def get_daily_quest(
        quest_date: Optional[date] = QuestDateQuery,
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_QUESTS_READ]),
        service: DailyQuestService = Depends(get_daily_quest_service),
) -> QuestOut:
    """
    Get Daily Quest

    Returns the guild's daily quest for a UTC day, today by default.
    Daily quests reset at 00:00 UTC.
    """
    return await service.get_day(auth.guild_id, quest_date)


@daily_quests_router.get('/upcoming')
async def list_upcoming_daily_quests(
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_QUESTS_READ]),
        service: DailyQuestService = Depends(get_daily_quest_service),
) -> list[DailyQuestOut]:
    """
    List Upcoming Daily Quests

    Returns every generated daily quest from today onwards, ordered by date.
    Daily quests are generated several days in advance, so admins can customise
    an upcoming day's quest with PATCH /guilds/me/quests/{quest_id}.
    `quest.last_edited_at` shows which ones have been customised.
    """
    return await service.get_upcoming(auth.guild_id)


@daily_quests_router.post('/generate')
async def generate_daily_quest(
        quest_date: Optional[date] = QuestDateQuery,
        force: bool = Query(default=False, description="Replace the day's daily quest if it already exists, "
                                                      "including any admin edits. Players' unfinished "
                                                      "progress on the old one is abandoned."),
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_QUESTS_WRITE]),
        service: DailyQuestService = Depends(get_daily_quest_service),
) -> QuestOut:
    """
    Generate Daily Quest

    Daily quests are generated automatically, several days in advance. Use this to
    generate a day's quest immediately (today by default, or any future day), or with
    `force=true` to re-roll it.
    """
    return await service.generate(auth.guild_id, quest_date, force=force)


@daily_quests_router.get('/templates')
async def list_daily_templates(
        enabled: Optional[bool] = Query(default=None, description="Filter by enabled state"),
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_QUESTS_READ]),
        service: DailyQuestService = Depends(get_daily_quest_service),
) -> list[DailyTemplateOut]:
    """
    List Daily Templates

    Returns the guild's pool of daily quest templates.
    """
    return await service.get_templates(auth.guild_id, enabled)


@daily_quests_router.post('/templates', status_code=status.HTTP_201_CREATED)
async def create_daily_template(
        body: DailyTemplateIn,
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_QUESTS_WRITE]),
        service: DailyQuestService = Depends(get_daily_quest_service),
) -> DailyTemplateOut:
    """
    Create Daily Template

    Adds a new template to the guild's daily quest pool.
    """
    return await service.new_template(auth.guild_id, body)


@daily_quests_router.post('/templates/preview')
async def preview_daily_template(
        body: DailyTemplateIn,
        _: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_QUESTS_READ]),
        service: DailyQuestService = Depends(get_daily_quest_service),
) -> DailyQuestIn:
    """
    Preview Daily Template

    Rolls a quest from the given template without saving anything.
    Call it multiple times to see the randomization.
    """
    return service.preview_template(body)


@daily_quests_router.get('/templates/{template_id}')
async def get_daily_template(
        template_id: int,
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_QUESTS_READ]),
        service: DailyQuestService = Depends(get_daily_quest_service),
) -> DailyTemplateOut:
    """
    Get Daily Template
    """
    return await service.get_template(auth.guild_id, template_id)


@daily_quests_router.patch('/templates/{template_id}')
@daily_quests_router.put('/templates/{template_id}')
async def update_daily_template(
        template_id: int,
        body: DailyTemplateUpdate,
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_QUESTS_WRITE]),
        service: DailyQuestService = Depends(get_daily_quest_service),
) -> DailyTemplateOut:
    """
    Update Daily Template

    Changes only affect daily quests generated afterwards.
    """
    return await service.update_template(auth.guild_id, template_id, body)


@daily_quests_router.delete('/templates/{template_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_daily_template(
        template_id: int,
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_QUESTS_WRITE]),
        service: DailyQuestService = Depends(get_daily_quest_service),
):
    """
    Delete Daily Template

    Removes a template from the pool. Already generated daily quests are kept.
    """
    await service.delete_template(auth.guild_id, template_id)
