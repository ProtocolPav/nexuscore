from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field
from typing_extensions import Optional

import json

from sanic_ext import openapi

from src.database import Database
from src.views.quest import QuestView


@openapi.component()
class UserObjectiveModel(BaseModel):
    quest_id: int
    objective_id: int
    start: datetime
    end: Optional[datetime]
    completion: int
    status: Literal['in_progress', 'completed', 'failed']

    @classmethod
    async def fetch(cls, db: Database, thorny_id: int, quest_id: int, objective_id: int) -> "UserObjectiveModel":
        data = await db.pool.fetchrow("""
                                      SELECT * from users.objectives
                                      WHERE thorny_id = $1
                                      AND quest_id = $2
                                      AND objective_id = $3
                                      """,
                                      thorny_id, quest_id, objective_id)

        return cls(**data)

    @classmethod
    async def fetch_all_objectives(cls, db: Database, thorny_id: int, quest_id: int) -> list["UserObjectiveModel"]:
        data = await db.pool.fetch("""
                                   SELECT * from users.objectives
                                   WHERE thorny_id = $1
                                   AND quest_id = $2
                                   """,
                                   thorny_id, quest_id)

        objectives = []
        for objective in data:
            objectives.append(cls(**objective))

        return objectives

    async def update(self, db: Database, thorny_id: int):
        await db.pool.execute("""
                               UPDATE users.objectives
                               SET "start" = $1,
                                   "end" = $2,
                                   "completion" = $3,
                                   "status" = $4
                               WHERE thorny_id = $5
                               AND quest_id = $6
                               AND objective_id = $7
                               """,
                              self.start, self.end, self.completion,
                              self.status, thorny_id, self.quest_id, self.objective_id)

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


class UserQuestModel(BaseModel):
    quest_id: int = Field(description="The quest ID", examples=[45])
    accepted_on: datetime = Field(description="The time that the user accepted this quest",
                                  examples=['2024-05-05T05:34:21.123456Z'])
    started_on: Optional[datetime] = Field(description="The time the user actually started to complete the quest",
                                           examples=['2024-03-21T12:33:45.123456Z'])
    status: Literal['in_progress', 'completed', 'failed']
    objectives: list[UserObjectiveModel]

    @classmethod
    async def fetch(cls, db: Database, thorny_id: int, quest_id: int) -> "UserQuestModel":
        data = await db.pool.fetchrow("""
                                      SELECT * from users.quests
                                      WHERE thorny_id = $1 AND quest_id = $2
                                      """,
                                      thorny_id, quest_id)

        objectives = await UserObjectiveModel.fetch_all_objectives(db, thorny_id, quest_id)

        return cls(**data, objectives=objectives)

    @classmethod
    async def get_active_quest(cls, db: Database, thorny_id: int) -> int:
        data = await db.pool.fetchrow("""
                                      SELECT quest_id from users.quests
                                      WHERE thorny_id = $1
                                      AND status = 'in_progress'
                                      """,
                                      thorny_id)

        return data['quest_id'] if data else None

    @classmethod
    async def get_all_quests(cls, db: Database, thorny_id: int) -> list[int]:
        data = await db.pool.fetchrow("""
                                      SELECT ARRAY_AGG(quest_id) AS quests from users.quests
                                      WHERE thorny_id = $1
                                      """,
                                      thorny_id)

        return data['quests'] if data else None

    async def update(self, db: Database, thorny_id: int):
        await db.pool.execute("""
                               UPDATE users.quests
                               SET accepted_on = $1,
                                   started_on = $2,
                                   objectives_completed = $3,
                                   status = $4
                               WHERE thorny_id = $5
                               AND quest_id = $6
                               """,
                              self.accepted_on, self.started_on, self.objectives_completed,
                              self.status, thorny_id, self.quest_id)

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


class UserQuestUpdateModel(BaseModel):
    accepted_on: Optional[datetime]
    started_on: Optional[datetime]
    objectives_completed: Optional[int]
    status: Optional[Literal['completed']]

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


class UserObjectiveUpdateModel(BaseModel):
    start: Optional[datetime]
    end: Optional[datetime]
    completion: Optional[int]
    status: Optional[Literal['in_progress', 'completed', 'failed']]

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


class UserQuestView(BaseModel):
    quest: Optional[UserQuestModel]
    objectives: Optional[list[UserObjectiveModel]]

    @classmethod
    async def build(cls, db: Database, thorny_id: int, quest_id: int):
        quest = await UserQuestModel.fetch(db, thorny_id, quest_id)
        objective_ids = await UserObjectiveModel.get_all_objectives(db, thorny_id, quest_id)

        objectives = []
        for objective in objective_ids:
            objectives.append(await UserObjectiveModel.fetch(db, thorny_id, quest_id, objective))

        return cls(quest=quest, objectives=objectives)

    @classmethod
    def view_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")

    @classmethod
    async def new(cls, db: Database, thorny_id: int, quest_id: int):
        quest_view = await QuestView.build(db, quest_id)

        async with db.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("""
                                   INSERT INTO users.quests(quest_id, thorny_id)
                                   VALUES($1, $2)
                                   """,
                                   quest_id, thorny_id)

                for objective in quest_view.objectives:
                    await conn.execute("""
                                       INSERT INTO users.objectives(quest_id, thorny_id, objective_id)
                                       VALUES($1, $2, $3)
                                       """,
                                       quest_id, thorny_id, objective.objective_id)

    @classmethod
    async def mark_failed(cls, db: Database, thorny_id: int, quest_id: int):
        quest = await cls.build(db, thorny_id, quest_id)
        quest.quest.status = 'failed'
        await quest.quest.update(db, thorny_id)

        for obj in quest.objectives:
            if obj.status == 'in_progress':
                obj.status = 'failed'
                await obj.update(db, thorny_id)