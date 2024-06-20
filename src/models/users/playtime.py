from datetime import datetime, date

from pydantic import BaseModel, Field
from sanic_ext import openapi
from typing_extensions import Optional

import json

from src.database import Database


@openapi.component
class DailyPlaytime(BaseModel):
    day: date
    playtime: float


@openapi.component
class MonthlyPlaytime(BaseModel):
    month: date
    playtime: float


class PlaytimeSummary(BaseModel):
    total: float = Field(description="Total playtime in seconds",
                         examples=[3600])
    session: Optional[datetime] = Field(description="The date and time when the user connected, or `null`",
                                        examples=['2024-05-34'])
    daily: list[DailyPlaytime] = Field(description="The list of playtime in seconds each day. Up to 7 days.")
    monthly: list[MonthlyPlaytime] = Field(description="The list of playtime in seconds each month. Up to 12 months.")

    @classmethod
    async def fetch(cls, db: Database, thorny_id: int) -> Optional["PlaytimeSummary"]:
        data = await db.pool.fetchrow("""
                WITH daily_playtime AS (
                    SELECT t.day, SUM(t.playtime) AS playtime
                    FROM (
                        SELECT SUM(playtime) AS playtime, 
                               DATE(connect_time) AS day
                        FROM events.sessions_view sv 
                        INNER JOIN users.user ON sv.thorny_id = users.user.thorny_id 
                        WHERE sv.thorny_id = $1
                        GROUP BY day
                    ) AS t
                    GROUP BY t.day
                    ORDER BY t.day DESC
                    LIMIT 7
                ),
                total_playtime AS (
                    SELECT SUM(EXTRACT(EPOCH FROM playtime)) AS total_playtime
                    FROM events.sessions_view sv 
                    WHERE thorny_id = $1
                    GROUP BY thorny_id
                ),
                session AS (
                    SELECT connect_time as session
                    FROM events.sessions_view sv 
                    WHERE thorny_id = $1
                    AND disconnect_time IS NULL
                    GROUP BY thorny_id, connect_time
                    order by connect_time DESC
                    limit 1
                ),
                monthly_playtime AS (
                    SELECT t.month AS month, SUM(t.playtime) AS playtime
                    FROM (
                        SELECT SUM(playtime) AS playtime,
                               date_trunc('month', connect_time)::date as month
                        FROM events.sessions_view sv 
                        INNER JOIN users.user ON sv.thorny_id = users.user.thorny_id 
                        WHERE sv.thorny_id = $1
                        GROUP BY month
                    ) AS t
                    GROUP BY t.month
                    ORDER BY t.month DESC
                    LIMIT 12
                )
                SELECT 
                    (
                        SELECT thorny_id FROM users.user
                        WHERE thorny_id = $1
                    ) AS thorny_id,
                    COALESCE(
                        (
                         SELECT JSON_AGG(JSON_BUILD_OBJECT('day', wp.day,
                                                           'playtime', COALESCE(EXTRACT(EPOCH FROM wp.playtime), 0)))
                         FROM daily_playtime wp
                         ),
                         '[]'::json
                    ) AS daily,
                    COALESCE(
                        (
                         SELECT total_playtime
                         FROM total_playtime
                         ),
                         0
                    ) AS total,
                    (SELECT session
                        FROM session) AS session,
                    COALESCE(
                        (
                         SELECT JSON_AGG(JSON_BUILD_OBJECT('month', mp.month,
                                                           'playtime', COALESCE(EXTRACT(EPOCH FROM mp.playtime), 0)))
                         FROM monthly_playtime mp
                         ),
                         '[]'::json
                    ) AS monthly;
                                      """,
                                      thorny_id)

        if data['thorny_id']:
            processed_dict = {'thorny_id': thorny_id,
                              'total': data['total'],
                              'daily': json.loads(data['daily']),
                              'monthly': json.loads(data['monthly']),
                              'session': data['session']}
        else:
            return None

        return cls(**processed_dict)

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")
