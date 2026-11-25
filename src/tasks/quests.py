import asyncio
import logging
from collections.abc import Awaitable, Callable

from src.dependencies.database import db
from src.dependencies.services import build_daily_quest_service, build_quest_progress_service
from src.settings import settings

logger = logging.getLogger(__name__)


async def _run_step(name: str, step: Callable[[], Awaitable]) -> None:
    try:
        await step()
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("Quest task '%s' failed", name)


async def quest_maintenance_loop() -> None:
    """
    Background loop for time-based quest upkeep. Every `QUEST_TASKS_INTERVAL_SECONDS` it:

    1. Abandons unfinished progress on quests that have ended (any quest type)
    2. Generates today's daily quest for every guild that has enabled templates

    Running on an interval (instead of sleeping until midnight) means missed resets,
    e.g. after a restart, are caught up on the next tick. Each step is idempotent, and
    one step failing does not stop the other.
    """
    quest_progress_service = build_quest_progress_service(db)
    daily_quest_service = build_daily_quest_service(db)

    while True:
        await _run_step("abandon expired progress", quest_progress_service.abandon_expired)
        await _run_step("ensure daily quests", daily_quest_service.ensure_todays_quests)

        await asyncio.sleep(settings.QUEST_TASKS_INTERVAL_SECONDS)
