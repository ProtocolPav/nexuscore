from fastapi import APIRouter, HTTPException, status

from src.dependencies.database import db

from src.models.quests import quest_progress, objective_progress

quest_progress_router = APIRouter(prefix='/quests/progress', tags=['Quest Progress'])


@quest_progress_router.post('', status_code=status.HTTP_201_CREATED)
async def create_quest_progress(body: quest_progress.QuestProgressCreateModel) -> quest_progress.QuestProgressModel:
    """
    Create New Quest Progress

    Adds a new quest to a user, tracking their progress.
    Automatically sets the quest progress to "active".
    """
    quest_id = await quest_progress.QuestProgressModel.create(db, body)
    quest_model = await quest_progress.QuestProgressModel.fetch(db, quest_id)
    await quest_model.update(db, quest_progress.QuestProgressUpdateModel(status='active'))
    await quest_model.objectives[0].update(db, quest_progress.ObjectiveProgressUpdateModel(status='active'))

    return quest_model


@quest_progress_router.get('/user/{thorny_id}')
async def get_all_quests(thorny_id: int) -> quest_progress.QuestProgressListModel:
    """
    Get All User's Quest Progress

    Returns all quest progress belonging to a user
    """
    quests_list = await quest_progress.QuestProgressListModel.fetch(db, thorny_id)

    return quests_list


@quest_progress_router.get('/user/{thorny_id}/active')
async def get_active_quest(thorny_id: int) -> quest_progress.QuestProgressModel:
    """
    Get User's Active Quest

    Returns the user's currently active quest.
    """
    quest = await quest_progress.QuestProgressModel.fetch_active_quest(db, thorny_id)

    return quest


@quest_progress_router.delete('/user/{thorny_id}/active', status_code=status.HTTP_204_NO_CONTENT)
async def fail_active_quest(thorny_id: int):
    """
    Fail User's Active Quest

    This marks the active quest and all of its objectives as "failed".
    """
    quest = await quest_progress.QuestProgressModel.fetch_active_quest(db, thorny_id)
    await quest.mark_failed(db)

    return None


@quest_progress_router.put('/{progress_id}')
async def update_quest(progress_id: int, body: quest_progress.QuestProgressUpdateModel) -> quest_progress.QuestProgressModel:
    """
    Update Specific User's Quest

    Updates a user's quest. Note this does not update objectives.
    """
    model = await quest_progress.QuestProgressModel.fetch(db, progress_id)
    await model.update(db, body)

    return model


@quest_progress_router.put('/{progress_id}/{objective_id}')
async def update_objective(
    progress_id: int, objective_id: int, body: objective_progress.ObjectiveProgressUpdateModel
) -> objective_progress.ObjectiveProgressModel:
    """
    Update Specific User's Quest Objective

    Updates a user's quest objective.
    """
    model = await objective_progress.ObjectiveProgressModel.fetch(db, progress_id, objective_id)
    await model.update(db, body)

    return model