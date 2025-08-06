from datetime import datetime

from pydantic import Field
from sanic_ext import openapi
from src.database import Database

from src.utils.base import BaseModel, BaseList, T, optional_model
from src.utils.errors import BadRequest400, NotFound404

@openapi.component()
class ConcurrentUsersBaseModel(BaseModel):
    concurrent_users: int = Field(description="The number of concurrent users",
                                  json_schema_extra={"example": 5})
    time: datetime = Field(description="The timestamp of the concurrent users",
                           json_schema_extra={"example": '2021-05-05 05:34:21.123456'})

    @classmethod
    async def fetch(cls, db: Database, guild_id: int, *args, **kwargs) -> "ConcurrentUsersBaseModel":
        if not guild_id:
            raise BadRequest400(extra={'ids': ['guild_id']})

        data = await db.pool.fetchrow("""
                                        SELECT
                                            max(cv.concurrent_users) as concurrent_users,
                                            cv.time
                                        FROM JOIN events.concurrent_view cv
                                        WHERE
                                            cv.time >= '2022-07-29'
                                      """,
                                      guild_id)

        if data:
            return cls(**data)
        else:
            raise NotFound404(extra={'resource': 'concurrent_users', 'id': guild_id})


class TotalAnalyticsModel(BaseModel):
    guild_id: int = Field(description="The discord guild ID",
                          json_schema_extra={"example": 631936703190440136})
    total_playtime: float = Field(description="This guild's total playtime in seconds",
                                  json_schema_extra={"example": 5004233.43})
    total_sessions: int = Field(description="This guild's total session number",
                                json_schema_extra={"example": 43210})
    total_users: int = Field(description="The total number of users that have ever connected",
                             json_schema_extra={"example": 124})
    average_session_length: float = Field(description="The average session duration in seconds",
                                          json_schema_extra={"example": 7954})
    peak_concurrent_users: ConcurrentUsersBaseModel = Field(description="The peak concurrent users on the server")

    @classmethod
    async def fetch(cls, db: Database, guild_id: int, *args, **kwargs) -> "TotalAnalyticsModel":
        if not guild_id:
            raise BadRequest400(extra={'ids': ['guild_id']})

        data = await db.pool.fetchrow("""
                                        SELECT
                                            sum(sv.playtime) as total_playtime,
                                            count(distinct sv.thorny_id) as total_users,
                                            count(sv.thorny_id) as total_sessions,
                                            sum(sv.playtime) / count(sv.thorny_id) as average_session_length
                                        FROM events.sessions_view sv 
                                        INNER JOIN users."user" ON users."user".thorny_id = sv.thorny_id
                                        WHERE
                                            users."user".guild_id = $1
                                            and sv.connect_time >= '2022-07-29'
                                      """,
                                      guild_id)

        if data:
            return cls(**data)
        else:
            raise NotFound404(extra={'resource': 'total_analytics', 'id': guild_id})