from datetime import date, datetime
from typing import Literal, Optional

from src.database import Database
from src.utils.base import BaseModel
from pydantic import Field

from sanic_ext import openapi

from src.utils.errors import BadRequest400, NotFound404

@openapi.component()
class TotalQuests(BaseModel):
    total_accepted: int = Field(description="Total accepted quests")
    total_completed: int = Field(description="Total completed quests")
    total_failed: int = Field(description="Total failed quests")
    completion_rate: float = Field(description="Completion rate")

    @classmethod
    async def fetch(cls, db: Database, thorny_id: int = None, *args) -> "TotalQuests":
        if not thorny_id:
            raise BadRequest400(extra={'ids': ['thorny_id']})

        data = await db.pool.fetchrow("""
                                          SELECT
                                              COUNT(*) as total_accepted,
                                              COUNT(*) FILTER (WHERE status = 'completed') as total_completed,
                                              COUNT(*) FILTER (WHERE status = 'failed') as total_failed,
                                              ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'completed') / COUNT(*), 2) as completion_rate
                                          FROM users.quests
                                          WHERE thorny_id = $1
                                            AND accepted_on >= '2025-01-01'
                                            AND accepted_on < '2025-12-13'
                                      """,
                                      thorny_id)

        if data:
            return cls(**data)
        else:
            raise NotFound404(extra={'resource': 'quests', 'id': f'{thorny_id}'})


@openapi.component()
class FastestQuestDone(BaseModel):
    title: str = Field(description="Title of the quest")
    start_time: datetime = Field(description="Start time of the quest")
    completion_time: datetime = Field(description="Completion time of the quest")
    duration_seconds: float = Field(description="Duration of the quest")

    @classmethod
    async def fetch(cls, db: Database, thorny_id: int = None, *args) -> "FastestQuestDone":
        if not thorny_id:
            raise BadRequest400(extra={'ids': ['thorny_id']})

        data = await db.pool.fetchrow("""
                                          WITH quest_times AS (
                                              SELECT
                                                  uq.quest_id,
                                                  q.title,
                                                  uq.accepted_on as start_time,
                                                  MAX(o."end") as completion_time,
                                                  MAX(o."end") - uq.accepted_on as duration
                                              FROM users.quests uq
                                                       JOIN quests.quest q ON uq.quest_id = q.quest_id
                                                       JOIN users.objectives o ON o.quest_id = uq.quest_id AND o.thorny_id = uq.thorny_id
                                              WHERE uq.thorny_id = $1
                                                AND uq.status = 'completed'
                                                AND uq.accepted_on >= '2025-01-01'
                                                AND uq.accepted_on < '2025-12-13'
                                                AND o.status = 'completed'
                                                AND o."end" IS NOT NULL
                                              GROUP BY uq.quest_id, q.title, uq.accepted_on
                                          )
                                          SELECT
                                              title,
                                              start_time,
                                              completion_time,
                                              EXTRACT(EPOCH FROM duration) as duration_seconds
                                          FROM quest_times
                                          ORDER BY duration ASC
                                          LIMIT 1
                                      """,
                                      thorny_id)

        if data:
            return cls(**data)
        else:
            raise NotFound404(extra={'resource': 'quests', 'id': f'{thorny_id}'})

@openapi.component()
class TotalRewards(BaseModel):
    total_rewards: int = Field(description="Total rewards")
    total_balance_earned: int = Field(description="Total balance earned")
    total_items_earned: int = Field(description="Total items earned")
    unique_items: int = Field(description="Unique items")

    @classmethod
    async def fetch(cls, db: Database, thorny_id: int = None, *args) -> "TotalRewards":
        if not thorny_id:
            raise BadRequest400(extra={'ids': ['thorny_id']})

        data = await db.pool.fetchrow("""
                                          SELECT
                                              COUNT(*) as total_rewards,
                                              SUM(r.balance) as total_balance_earned,
                                              SUM(r.count) FILTER (WHERE r.item IS NOT NULL) as total_items_earned,
                                              COUNT(DISTINCT r.item) as unique_items
                                          FROM users.quests uq
                                                   JOIN quests.reward r ON uq.quest_id = r.quest_id
                                          WHERE uq.thorny_id = 12
                                            AND uq.status = 'completed'
                                            AND uq.accepted_on >= '2025-01-01'
                                            AND uq.accepted_on < '2025-12-13'
                                      """,
                                      thorny_id)

        if data:
            return cls(**data)
        else:
            raise NotFound404(extra={'resource': 'quests', 'id': f'{thorny_id}'})