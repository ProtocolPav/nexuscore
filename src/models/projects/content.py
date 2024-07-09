from datetime import date, datetime

from pydantic import BaseModel, Field
from typing_extensions import Optional, Literal

from src.database import Database
from src.models import users


class ContentModel(BaseModel):
    content: str
    since: datetime
    edited_by: users.UserModel

    @classmethod
    async def fetch(cls, db: Database, project_id: str) -> Optional["ContentModel"]:
        data = await db.pool.fetchrow("""
                                       SELECT content, since, user_id
                                       FROM projects.content
                                       WHERE project_id = $1
                                       ORDER BY since DESC
                                       """,
                                      project_id)

        if data:
            edited_by = await users.UserModel.fetch(db, data['user_id'])

            return cls(**data, edited_by=edited_by)
        else:
            return None

    @staticmethod
    async def insert_content(db: Database, project_id: str, content: str, edited_by_user: int = None):
        await db.pool.execute("""
                               INSERT INTO projects.content(project_id, content, since, user_id)
                               VALUES($1, $2, NOW(), $3)
                               """,
                              project_id, content, edited_by_user)

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


class ContentCreateModel(BaseModel):
    content: str
    edited_by: int

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")
