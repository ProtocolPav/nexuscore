from datetime import date, datetime

from pydantic import Field
from typing_extensions import Optional, Literal

from src.database import Database
from src.models.users import user
from src.utils.base import BaseList


class MembersListModel(BaseList[user.UserModel]):
    @classmethod
    async def fetch(cls, db: Database, project_id: str = None, *args) -> "MembersListModel":
        data = await db.pool.fetch("""
                                   SELECT user_id FROM projects.members
                                   WHERE project_id = $1
                                   """,
                                   project_id)

        members: list[user.UserModel] = []
        for member in data:
            members.append(await user.UserModel.fetch(db, member['user_id']))

        return cls(root=members)

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
