from fastapi import APIRouter

from src.dependencies.database import db

from src.models.wrapped.wrapped import EverthornWrapped2025

wrapped = APIRouter(prefix='/wrapped', tags=['Wrapped'])


@wrapped.get('/{thorny_id}')
async def get_wrapped(thorny_id: int) -> EverthornWrapped2025:
    """
    Get Everthorn Wrapped 2025

    Returns the wrapped statistics for a user for the year 2025.
    Includes playtime, quests, rewards, interactions, projects, and grind day metrics.
    """
    wrapped_data = await EverthornWrapped2025.fetch(db, thorny_id)

    return wrapped_data