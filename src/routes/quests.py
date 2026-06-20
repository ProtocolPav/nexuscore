from typing import Annotated

from fastapi import APIRouter, Query, Security, Depends, status

from src.dependencies.auth import Scope, get_guild_client
from src.dependencies.services import get_quest_service
from src.models.auth import TokenPayload

from src.models.quests.quest import QuestIn, QuestOut, QuestQuery, QuestUpdate
from src.services.quest import QuestService

quests = APIRouter(prefix='/guilds/me/quests', tags=['Quests'])


@quests.post('', status_code=status.HTTP_201_CREATED)
async def create_quest(
        body: QuestIn,
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_WRITE]),
        service: QuestService = Depends(get_quest_service),
) -> QuestOut:
    """
    Create New Quest

    Creates a new quest based on the information provided.
    Some fields are optional and can be `null` while others are required.
    Check the schema for more info on that.
    """
    return await service.new(auth.guild_id, body)


@quests.get('')
async def list_quests(
        filter_query: Annotated[QuestQuery, Query()],
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_READ]),
        service: QuestService = Depends(get_quest_service),
) -> list[QuestOut]:
    """
    Get a list of Quests
    """
    return await service.get_all(auth.guild_id, filter_query)


@quests.get('/{quest_id}')
async def get_quest(
        quest_id: int,
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_READ]),
        service: QuestService = Depends(get_quest_service)
) -> QuestOut:
    """
    Get Quest

    Returns a specific quest, objectives and rewards
    """
    return await service.get(auth.guild_id, quest_id)


@quests.patch('/{quest_id}')
@quests.put('/{quest_id}')
async def partial_update_quest(
        quest_id: int,
        body: QuestUpdate,
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_WRITE]),
        service: QuestService = Depends(get_quest_service),
) -> QuestOut:
    """
    Updates quest details and/or objectives. Objectives and rewards are additive-only:
    include an `objective_id`/`reward_id` to update an existing entry, or omit it to create a new one.
    Existing objectives and rewards not present in the payload are left untouched.
    """
    return await service.update(auth.guild_id, quest_id, body)
