from datetime import date, datetime
from typing import Literal, Optional

from src.database import Database
from src.utils.base import BaseList, BaseModel
from pydantic import Field

from sanic_ext import openapi

from src.utils.errors import BadRequest400, NotFound404

@openapi.component()
class TotalPlaytimeModel(BaseModel):
    total_seconds: float = Field(description="Total seconds played this year",
                               json_schema_extra={"example": '144332.443203'})

    @classmethod
    async def fetch(cls, db: Database, thorny_id: int = None, *args) -> "TotalPlaytimeModel":
        if not thorny_id:
            raise BadRequest400(extra={'ids': ['thorny_id']})

        data = await db.pool.fetchrow("""
                                          SELECT
                                              SUM(EXTRACT(EPOCH FROM playtime)) as total_seconds
                                          FROM events.sessions_view
                                          WHERE thorny_id = $1
                                            AND connect_time >= '2025-01-01'
                                            AND connect_time < '2025-12-13'
                                          GROUP BY thorny_id
                                      """,
                                      thorny_id)

        if data:
            return cls(**data)
        else:
            raise NotFound404(extra={'resource': 'playtime', 'id': f'{thorny_id}'})


@openapi.component()
class HighestDayModel(BaseModel):
    day: date = Field(description="The day they played on",
                      json_schema_extra={"example": '2015-04-01'})
    seconds_played: float = Field(description="The total seconds played this year",)

    @classmethod
    async def fetch(cls, db: Database, thorny_id: int = None, *args) -> "HighestDayModel":
        if not thorny_id:
            raise BadRequest400(extra={'ids': ['thorny_id']})

        data = await db.pool.fetchrow("""
                                          SELECT
                                              DATE(connect_time) as day,
                                              SUM(EXTRACT(EPOCH FROM playtime)) as seconds_played
                                          FROM events.sessions_view
                                          WHERE thorny_id = $1
                                            AND connect_time >= '2025-01-01'
                                            AND connect_time < '2025-12-13'
                                          GROUP BY DATE(connect_time)
                                          ORDER BY seconds_played DESC
                                          LIMIT 1
                                      """,
                                      thorny_id)

        if data:
            return cls(**data)
        else:
            raise NotFound404(extra={'resource': 'playtime', 'id': f'{thorny_id}'})


@openapi.component()
class MostActiveHourModel(BaseModel):
    hour_of_day: int = Field(description="The hour of the day they connected (1, 3, 23)")
    session_count: int = Field(description="How many sessions this person has had connecting at this hour")
    total_seconds: int = Field(description="Total seconds played during those sessions")

    @classmethod
    async def fetch(cls, db: Database, thorny_id: int = None, *args) -> "MostActiveHourModel":
        if not thorny_id:
            raise BadRequest400(extra={'ids': ['thorny_id']})

        data = await db.pool.fetchrow("""
                                          SELECT
                                              EXTRACT(HOUR FROM connect_time) as hour_of_day,
                                              COUNT(*) as session_count,
                                              SUM(EXTRACT(EPOCH FROM playtime)) as total_seconds
                                          FROM events.sessions_view
                                          WHERE thorny_id = $1
                                            AND connect_time >= '2025-01-01'
                                            AND connect_time < '2025-12-13'
                                          GROUP BY EXTRACT(HOUR FROM connect_time)
                                          ORDER BY total_seconds DESC
                                          LIMIT 1
                                      """,
                                      thorny_id)

        if data:
            return cls(**data)
        else:
            raise NotFound404(extra={'resource': 'playtime', 'id': f'{thorny_id}'})


@openapi.component()
class FavouritePersonModel(BaseModel):
    other_player_id: int = Field(description="Other player id")
    username: str = Field(description="Username")
    seconds_played_together: float = Field(description="Total seconds played together")


@openapi.component()
class FavouritePersonListModel(BaseList[FavouritePersonModel]):
    @classmethod
    async def fetch(cls, db: Database, thorny_id: int = None, *args) -> "FavouritePersonListModel":
        if not thorny_id:
            raise BadRequest400(extra={'ids': ['thorny_id']})

        data = await db.pool.fetch("""
                                       WITH user_sessions AS (
                                           SELECT
                                               connect_time,
                                               disconnect_time,
                                               thorny_id
                                           FROM events.sessions_view
                                           WHERE thorny_id = $1
                                             AND connect_time >= '2025-01-01'
                                             AND connect_time < '2025-12-13'
                                       ),
                                            other_sessions AS (
                                                SELECT
                                                    connect_time,
                                                    disconnect_time,
                                                    thorny_id
                                                FROM events.sessions_view
                                                WHERE thorny_id != $1
                                                  AND connect_time >= '2025-01-01'
                                                  AND connect_time < '2025-12-13'
                                            ),
                                            overlapping_time AS (
                                                SELECT
                                                    os.thorny_id as other_player_id,
                                                    SUM(
                                                            EXTRACT(EPOCH FROM (
                                                                LEAST(COALESCE(us.disconnect_time, NOW()), COALESCE(os.disconnect_time, NOW())) -
                                                                GREATEST(us.connect_time, os.connect_time)
                                                                ))
                                                    ) as seconds_together
                                                FROM user_sessions us
                                                         JOIN other_sessions os
                                                              ON us.connect_time < COALESCE(os.disconnect_time, NOW())
                                                                  AND COALESCE(us.disconnect_time, NOW()) > os.connect_time
                                                GROUP BY os.thorny_id
                                            )
                                       SELECT
                                           ot.other_player_id,
                                           u.username,
                                           ROUND(ot.seconds_together::numeric, 2) as seconds_played_together
                                       FROM overlapping_time ot
                                                JOIN users."user" u ON u.thorny_id = ot.other_player_id
                                       ORDER BY ot.seconds_together DESC
                                       LIMIT 5
                                   """, thorny_id)

        blocks: list[FavouritePersonModel] = []
        for block in data:
            blocks.append(FavouritePersonModel(**block))

        return cls(root=blocks)

@openapi.component()
class GrindDayModel(BaseModel):
    grind_date: date = Field(description="Grind date")
    sessions: int = Field(description="Number of sessions")
    hours_played: float = Field(description="Total hours played")
    first_login: datetime = Field(description="First login")
    last_logout: datetime = Field(description="Last logout")
    blocks: int = Field(description="Number of blocks")
    blocks_placed: int = Field(description="Number of blocks placed")
    blocks_mined: int = Field(description="Number of blocks mined")
    mob_kills: int = Field(description="Number of mob kills")
    interactions: int = Field(description="Number of interactions")
    quests_completed: int = Field(description="Number of quests completed")
    total_combined_actions: int = Field(description="Total combined actions")

    @classmethod
    async def fetch(cls, db: Database, thorny_id: int = None, *args) -> "GrindDayModel":
        if not thorny_id:
            raise BadRequest400(extra={'ids': ['thorny_id']})

        data = await db.pool.fetchrow("""
                                          WITH daily_sessions AS (
                                              SELECT
                                                  DATE(connect_time) as grind_date,
                                                  thorny_id,
                                                  COUNT(DISTINCT connect_event_id) as sessions,
                                                  SUM(EXTRACT(EPOCH FROM playtime) / 3600) as hours_played,
                                                  MIN(connect_time) as first_login,
                                                  MAX(COALESCE(disconnect_time, NOW())) as last_logout
                                              FROM events.sessions_view
                                              WHERE thorny_id = $1
                                                AND connect_time >= '2025-01-01'
                                                AND connect_time < '2025-12-13'
                                              GROUP BY DATE(connect_time), thorny_id
                                          ),
                                               daily_interactions AS (
                                                   SELECT
                                                       DATE(time) as grind_date,
                                                       COUNT(*) FILTER (WHERE type IN ('place', 'mine')) as blocks,
                                                       COUNT(*) FILTER (WHERE type = 'place') as blocks_placed,
                                                       COUNT(*) FILTER (WHERE type = 'mine') as blocks_mined,
                                                       COUNT(*) FILTER (WHERE type = 'kill') as mob_kills,
                                                       COUNT(*) FILTER (WHERE type = 'use') as interactions
                                                   FROM events.interactions
                                                   WHERE thorny_id = $1
                                                     AND time >= '2025-01-01'
                                                     AND time < '2025-12-13'
                                                   GROUP BY DATE(time)
                                               ),
                                               daily_quests AS (
                                                   SELECT
                                                       DATE(o."end") as grind_date,
                                                       COUNT(DISTINCT uq.quest_id) as quests_completed
                                                   FROM users.quests uq
                                                            JOIN users.objectives o ON o.quest_id = uq.quest_id AND o.thorny_id = uq.thorny_id
                                                   WHERE uq.thorny_id = $1
                                                     AND uq.status = 'completed'
                                                     AND o."end" >= '2025-01-01'
                                                     AND o."end" < '2025-12-13'
                                                   GROUP BY DATE(o."end")
                                               )
                                          SELECT
                                              ds.grind_date,
                                              ds.sessions,
                                              ROUND(ds.hours_played::numeric, 2) as hours_played,
                                              ds.first_login,
                                              ds.last_logout,
                                              COALESCE(di.blocks, 0) as blocks,
                                              COALESCE(di.blocks_placed, 0) as blocks_placed,
                                              COALESCE(di.blocks_mined, 0) as blocks_mined,
                                              COALESCE(di.mob_kills, 0) as mob_kills,
                                              COALESCE(di.interactions, 0) as interactions,
                                              COALESCE(dq.quests_completed, 0) as quests_completed,
                                              COALESCE(di.blocks, 0) + COALESCE(di.mob_kills, 0) + COALESCE(di.interactions, 0) + COALESCE(dq.quests_completed, 0) as total_combined_actions
                                          FROM daily_sessions ds
                                                   LEFT JOIN daily_interactions di ON di.grind_date = ds.grind_date
                                                   LEFT JOIN daily_quests dq ON dq.grind_date = ds.grind_date
                                          ORDER BY total_combined_actions DESC
                                          LIMIT 1
                                      """,
                                      thorny_id)

        if data:
            return cls(**data)
        else:
            raise NotFound404(extra={'resource': 'playtime', 'id': f'{thorny_id}'})