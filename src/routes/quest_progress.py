from fastapi import APIRouter, status, Security, Depends

from src.dependencies.auth import Scope, get_guild_client
from src.dependencies.services import get_quest_progress_service
from src.models.auth import TokenPayload

from src.models.quests.quest_progress import QuestProgressIn, QuestProgressOut, QuestProgressUpdate
from src.services.quest_progress import QuestProgressService

quest_progress_router = APIRouter(prefix='/guilds/me/quests_router/progress', tags=['Quests'])


@quest_progress_router.post('', status_code=status.HTTP_201_CREATED)
async def create_quest_progress(
        body: QuestProgressIn,
        _: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_WRITE]),
        service: QuestProgressService = Depends(get_quest_progress_service)
) -> QuestProgressOut:
    """
    Create New Quest Progress

    Adds a new quest to a user, tracking their progress.
    Automatically sets the quest progress to "active".
    """
    return await service.new(body)


@quest_progress_router.get('/user/{thorny_id}')
async def list_quest_progress(
        thorny_id: int,
        _: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_READ]),
        service: QuestProgressService = Depends(get_quest_progress_service)
) -> list[QuestProgressOut]:
    """
    Get All User's Quest Progress

    Returns all quest progress belonging to a user
    """
    return await service.get_all_users_progress(thorny_id)


@quest_progress_router.get('/user/{thorny_id}/active')
async def get_active_quest_progress(
        thorny_id: int,
        _: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_READ]),
        service: QuestProgressService = Depends(get_quest_progress_service)
) -> QuestProgressOut:
    """
    Get User's Active Quest

    Returns the user's currently active quest.
    """
    return await service.get_active(thorny_id)


@quest_progress_router.delete('/user/{thorny_id}/active', status_code=status.HTTP_204_NO_CONTENT)
async def fail_active_quest_progress(
        thorny_id: int,
        _: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_WRITE]),
        service: QuestProgressService = Depends(get_quest_progress_service)
):
    """
    Fail User's Active Quest

    This marks the active quest and all of its objectives as "failed".
    """
    await service.mark_failed(thorny_id)


@quest_progress_router.put('/{progress_id}')
@quest_progress_router.patch('/{progress_id}')
async def partial_update_quest_progress(
        progress_id: int,
        body: QuestProgressUpdate,
        _: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_WRITE]),
        service: QuestProgressService = Depends(get_quest_progress_service)
) -> QuestProgressOut:
    """
    Update Specific User's Quest

    Updates a user's quest.
    """
    return await service.update(progress_id, body)
