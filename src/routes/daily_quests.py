from typing import Optional

from fastapi import APIRouter, Depends, Query, Security, status

from src.dependencies.auth import get_guild_client
from src.dependencies.services import get_daily_quest_service
from src.models.auth import Scope, TokenPayload

from src.models.quests.daily import DailyQuestIn, DailyTemplateIn, DailyTemplateOut, DailyTemplateUpdate
from src.models.quests.quest import QuestOut
from src.services.daily_quest import DailyQuestService

daily_quests_router = APIRouter(prefix='/guilds/me/quests/daily', tags=['Daily Quests'])


@daily_quests_router.get('')
async def get_daily_quest(
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_QUESTS_READ]),
        service: DailyQuestService = Depends(get_daily_quest_service),
) -> QuestOut:
    """
    Get Today's Daily Quest

    Returns the guild's daily quest for the current UTC day.
    Daily quests reset at 00:00 UTC.
    """
    return await service.get_today(auth.guild_id)


@daily_quests_router.post('/generate')
async def generate_daily_quest(
        force: bool = Query(default=False, description="Replace today's daily quest if it already exists. "
                                                      "Players' unfinished progress on the old one is abandoned."),
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_QUESTS_WRITE]),
        service: DailyQuestService = Depends(get_daily_quest_service),
) -> QuestOut:
    """
    Generate Today's Daily Quest

    Daily quests are generated automatically. Use this to generate one immediately,
    or with `force=true` to re-roll today's daily quest.
    """
    return await service.generate(auth.guild_id, force=force)


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
