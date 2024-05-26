import sanic
from pydantic import BaseModel
from typing import Optional, Literal, Union

from datetime import date, datetime

from sanic_ext import openapi

from src.database import Database
from src.views.user import UserView


@openapi.component
class ProjectModel(BaseModel):
    project_id: str
    name: str
    description: str
    coordinates_x: int
    coordinates_y: int
    coordinates_z: int
    thread_id: Optional[int]
    started_on: Optional[date]
    completed_on: Optional[date]
    owner_id: Union[int, UserView]

    @classmethod
    async def fetch(cls, db: Database, project_id: str):
        data = await db.pool.fetchrow("""
                                       SELECT * FROM projects.project
                                       WHERE project_id = $1
                                       """,
                                      project_id)

        return cls(**data)

    async def update(self, db: Database):
        await db.pool.execute("""
                               UPDATE projects.project
                               SET name = $1,
                                   thread_id = $2,
                                   coordinates_x = $3,
                                   coordinates_y = $4,
                                   coordinates_z = $5,
                                   description = $6,
                                   completed_on = $7,
                                   owner_id = $8
                               WHERE project_id = $9
                               """,
                              self.name, self.thread_id, self.coordinates_x, self.coordinates_y, self.coordinates_z,
                              self.description, self.completed_on, self.owner_id, self.project_id)


class ProjectUpdateModel(BaseModel):
    name: str = None
    description: str = None
    coordinates_x: int = None
    coordinates_y: int = None
    coordinates_z: int = None
    thread_id: Optional[int] = None
    completed_on: Optional[date] = None
    owner_id: int = None


@openapi.component
class MembersModel(BaseModel):
    members: list[Optional[Union[int, UserView]]]

    @classmethod
    async def fetch(cls, db: Database, project_id: str):
        data = await db.pool.fetchrow("""
                                       SELECT ARRAY_AGG(user_id) as members FROM projects.members
                                       WHERE project_id = $1
                                       """,
                                      project_id)

        return cls(**data)

    @staticmethod
    async def insert_members(db: Database, project_id: str, members: list[int]):
        async with db.pool.acquire() as conn:
            async with conn.transaction():
                for member in members:
                    await conn.execute("""
                                       INSERT INTO projects.members(project_id, user_id)
                                       VALUES($1, $2)
                                       """,
                                       project_id, member)

    @staticmethod
    async def remove_members(db: Database, project_id: str, members: list[int]):
        async with db.pool.acquire() as conn:
            async with conn.transaction():
                for member in members:
                    await conn.execute("""
                                       DELETE FROM projects.members
                                       WHERE project_id = $1 AND user_id = $2
                                       """,
                                       project_id, member)


@openapi.component
class ContentModel(BaseModel):
    content: Optional[str]
    content_since: Optional[datetime]
    content_edited_by: Optional[Union[int, UserView]]

    @classmethod
    async def fetch(cls, db: Database, project_id: str):
        data = await db.pool.fetchrow("""
                                       SELECT content, since AS content_since, user_id AS content_edited_by
                                       FROM projects.content
                                       WHERE project_id = $1
                                       ORDER BY content_since DESC
                                       """,
                                      project_id)

        return cls(**data)

    @staticmethod
    async def insert_content(db: Database, project_id: str, content: str, edited_by_user: int = None):
        await db.pool.execute("""
                               INSERT INTO projects.content(project_id, content, since, user_id)
                               VALUES($1, $2, NOW(), $3)
                               """,
                              project_id, content, edited_by_user)


@openapi.component
class StatusModel(BaseModel):
    status: Literal["pending", "ongoing", "abandoned", "completed"]
    status_since: datetime

    @classmethod
    async def fetch(cls, db: Database, project_id: str):
        data = await db.pool.fetchrow("""
                                       SELECT status, since AS status_since
                                       FROM projects.status
                                       WHERE project_id = $1
                                       ORDER BY status_since DESC
                                       """,
                                      project_id)

        return cls(**data)

    @staticmethod
    async def insert_status(db: Database, project_id: str, status: Literal["pending", "ongoing", "abandoned", "completed"]):
        if status in ['pending', 'ongoing', 'abandoned', 'completed']:
            await db.pool.execute("""
                                   INSERT INTO projects.status(project_id, status, since)
                                   VALUES($1, $2, NOW())
                                   """,
                                  project_id, status)
        else:
            raise sanic.BadRequest("Status should be one of: pending, ongoing, abandoned, completed")
