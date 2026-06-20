from typing import Annotated

from fastapi import APIRouter, Query, status, Security, Depends

from src.dependencies.auth import Scope, get_guild_client
from src.dependencies.database import db
from src.dependencies.services import get_quest_service
from src.models.auth import TokenPayload

from src.models.quests.quest import QuestIn, QuestOut, QuestQuery
from src.services.quest import QuestService

quests = APIRouter(prefix='/quests', tags=['Quests'])


# @quests.post('', status_code=status.HTTP_201_CREATED)
# async def create_quest(body: QuestIn) -> QuestOut:
#     """
#     Create New Quest
#
#     Creates a new quest based on the information provided.
#     Some fields are optional and can be `null` while others are required.
#     Check the schema for more info on that.
#     """
#     quest_id = await quest.QuestModel.create(db, body)
#     quest_model = await quest.QuestModel.fetch(db, quest_id)
#
#     return quest_model
#
#
# @quests.get('')
# async def get_all_quests(filter_query: Annotated[QuestQuery, Query()]) -> quest.QuestListModel:
#     """
#     Get All Quests
#
#     Returns all quests ordered by start date, recent first
#     """
#     quests_model = await quest.QuestListModel.fetch(
#         db,
#         filter_query.time_start.isoformat() if filter_query.time_start else None,
#         filter_query.time_end.isoformat() if filter_query.time_end else None,
#         [str(x) for x in filter_query.creator_thorny_ids] if filter_query.creator_thorny_ids else None,
#         filter_query.quest_types,
#         filter_query.active,
#         filter_query.future,
#         filter_query.past,
#     )
#
#     return quests_model


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


# @quests.get('/{quest_id}/objectives')
# async def get_objectives(quest_id: int) -> objective.ObjectivesListModel:
#     """
#     Get All Objectives
#
#     Returns a list of all the objectives a quest has
#     """
#     objectives_model = await objective.ObjectivesListModel.fetch(db, quest_id)
#
#     return objectives_model
#
#
# @quests.get('/{quest_id}/objectives/{objective_id}')
# async def get_objective(quest_id: int, objective_id: int) -> objective.ObjectiveModel:
#     """
#     Get Objective
#
#     Returns the specified objective
#     """
#     objective_model = await objective.ObjectiveModel.fetch(db, quest_id, objective_id)
#
#     return objective_model
#
#
# @quests.get('/{quest_id}/objectives/{objective_id}/rewards')
# async def get_rewards(quest_id: int, objective_id: int) -> reward.RewardsListModel:
#     """
#     Get All Rewards
#
#     Returns all the rewards of the specified objective
#     """
#     rewards_model = await reward.RewardsListModel.fetch(db, quest_id, objective_id)
#
#     return rewards_model
#
#
# @quests.patch('/{quest_id}')
# @quests.put('/{quest_id}')
# async def update_quest(quest_id: int, body: quest.QuestUpdateModel) -> quest.QuestModel:
#     """
#     Update Quest
#
#     Update a quest
#     """
#     model = await quest.QuestModel.fetch(db, quest_id)
#     await model.update(db, body)
#
#     return model
#
#
# @quests.patch('/reward/{reward_id}')
# @quests.put('/reward/{reward_id}')
# async def update_reward(reward_id: int, body: reward.RewardUpdateModel) -> reward.RewardModel:
#     """
#     Update Reward
#
#     Update an objective's reward
#     """
#     model = await reward.RewardModel.fetch(db, reward_id)
#     await model.update(db, body)
#
#     return model
#
#
# @quests.patch('/objective/{objective_id}')
# @quests.put('/objective/{objective_id}')
# async def update_objective(objective_id: int, body: objective.ObjectiveUpdateModel) -> objective.ObjectiveModel:
#     """
#     Update Objective
#
#     Update a quest's objective
#     """
#     model = await objective.ObjectiveModel.fetch(db, objective_id)
#     await model.update(db, body)
#
#     return model
