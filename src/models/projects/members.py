from datetime import date, datetime

from pydantic import BaseModel, Field
from typing_extensions import Optional, Literal

from src.database import Database
from src.models import users


class MembersModel(BaseModel):
    members: list[users.UserModel]

    @classmethod
    async def fetch(cls, db: Database, project_id: str) -> Optional["MembersModel"]:
        data = await db.pool.fetchrow("""
                                       SELECT ARRAY_AGG(user_id) as members FROM projects.members
                                       WHERE project_id = $1
                                       """,
                                      project_id)

        all_members = []
        for member in data.get('members', []):
            all_members.append(await users.UserModel.fetch(db, member))

        return cls(**{'members': all_members}) if data else None

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

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")
