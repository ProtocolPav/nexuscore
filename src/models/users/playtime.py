from datetime import datetime, date

from pydantic import Field
from sanic_ext import openapi
from typing_extensions import Optional

from src.database import Database
from src.utils.base import BaseModel, BaseList
from src.utils.errors import BadRequest400, NotFound404


@openapi.component()
class DailyPlaytime(BaseModel):
    day: date = Field(description="Total playtime in seconds",
                     json_schema_extra={"example": '2024-05-05'})
    playtime: float = Field(description="The day's playtime in seconds",
                            json_schema_extra={"example": 125.54})


@openapi.component()
class DailyPlaytimeList(BaseList[DailyPlaytime]):
    @classmethod
    async def fetch(cls, db: Database, thorny_id: int = None, *args) -> "DailyPlaytimeList":
        if not thorny_id:
            raise BadRequest400(extra={'ids': ['thorny_id']})

        data = await db.pool.fetch("""
                                    SELECT t.day, SUM(t.playtime) AS playtime
                                    FROM (
                                        SELECT COALESCE(EXTRACT(EPOCH FROM SUM(playtime)), 0) AS playtime, 
                                               DATE(connect_time) AS day
                                        FROM events.sessions_view sv 
                                        INNER JOIN users.user ON sv.thorny_id = users.user.thorny_id 
                                        WHERE sv.thorny_id = $1
                                        GROUP BY day
                                    ) AS t
                                    GROUP BY t.day
                                    ORDER BY t.day DESC
                                    LIMIT 7
                                   """, thorny_id)

        if data:
            days = []
            for day in data:
                days.append(DailyPlaytime(**day))

            return cls(root=days)
        else:
            raise NotFound404(extra={'resource': 'user_daily_playtime', 'id': thorny_id})


@openapi.component()
class MonthlyPlaytime(BaseModel):
    month: date = Field(description="Total playtime in seconds",
                        json_schema_extra={"example": '2024-05-01'})
    playtime: float = Field(description="The month's playtime in seconds",
                            json_schema_extra={"example": 332.89})


@openapi.component()
class MonthlyPlaytimeList(BaseList[MonthlyPlaytime]):
    @classmethod
    async def fetch(cls, db: Database, thorny_id: int = None, *args) -> "MonthlyPlaytimeList":
        if not thorny_id:
            raise BadRequest400(extra={'ids': ['thorny_id']})

        data = await db.pool.fetch("""
                                    SELECT t.month AS month, SUM(t.playtime) AS playtime
                                    FROM (
                                        SELECT COALESCE(EXTRACT(EPOCH FROM SUM(playtime)), 0) AS playtime,
                                               date_trunc('month', connect_time)::date as month
                                        FROM events.sessions_view sv 
                                        INNER JOIN users.user ON sv.thorny_id = users.user.thorny_id 
                                        WHERE sv.thorny_id = $1
                                        GROUP BY month
                                    ) AS t
                                    GROUP BY t.month
                                    ORDER BY t.month DESC
                                    LIMIT 12
                                   """, thorny_id)

        if data:
            months = []
            for month in data:
                months.append(MonthlyPlaytime(**month))

            return cls(root=months)
        else:
            raise NotFound404(extra={'resource': 'user_monthly_playtime', 'id': thorny_id})


class PlaytimeSummary(BaseModel):
    thorny_id: int = Field(description="The ThornyID of a user",
                           json_schema_extra={"example": 34})
    total: float = Field(description="Total playtime in seconds",
                         json_schema_extra={"example": 3600})
    session: Optional[datetime] = Field(description="The date and time when the user connected, or `null`",
                                        json_schema_extra={"example": '2024-01-01 01:00:00+00:00'})
    daily: DailyPlaytimeList = Field(description="The list of playtime in seconds each day. Up to 7 days.")
    monthly: MonthlyPlaytimeList = Field(description="The list of playtime in seconds each month. Up to 12 months.")

    @classmethod
    async def fetch(cls, db: Database, thorny_id: int, *args) -> "PlaytimeSummary":
        if not thorny_id:
            raise BadRequest400(extra={'ids': ['thorny_id']})

        data = await db.pool.fetchrow("""
                                      WITH total_playtime AS (
                                        SELECT SUM (EXTRACT (EPOCH FROM playtime)) AS total_playtime
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
                                      )
                                      SELECT (
                                        SELECT thorny_id
                                        FROM users.user
                                        WHERE thorny_id = $1
                                      ) AS thorny_id,
                                        COALESCE(
                                            (
                                                SELECT total_playtime
                                                FROM total_playtime
                                            ), 0 
                                      ) AS total,
                                        (SELECT session FROM session) AS session
                                      """,
                                      thorny_id)

        if data:
            monthly = await MonthlyPlaytimeList.fetch(db, thorny_id)
            daily = await DailyPlaytimeList.fetch(db, thorny_id)

            return cls(**data, daily=daily, monthly=monthly)
        else:
            raise NotFound404(extra={'resource': 'user_playtime', 'id': thorny_id})
