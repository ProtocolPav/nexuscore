from datetime import datetime
from typing import Literal

from pydantic import Field
from typing_extensions import Optional

from sanic_ext import openapi

from src.database import Database
from src.models.users.objectives import UserObjectiveModel, UserObjectiveUpdateModel, UserObjectivesListModel, UserObjectiveCreateModel
from src.models.quests.objective import ObjectivesListModel
from src.utils.base import BaseModel, BaseList, optional_model
from src.utils.errors import BadRequest400, NotFound404


class QuestProgressBaseModel(BaseModel):
    accept_time: datetime = Field(description="The time that the user accepted this quest",
                                  json_schema_extra={"example": '2024-05-05 05:34:21.123456'})
    start_time: Optional[datetime] = Field(description="The time the user actually started to complete the quest",
                                           json_schema_extra={"example": '2024-05-05 05:34:21.123456'})
    end_time: Optional[datetime] = Field(description="The time the user ended the quest, either by failing or completing it",
                                         json_schema_extra={"example": '2024-05-05 05:34:21.123456'})
    status: Literal['active', 'pending', 'completed', 'failed'] = Field(description="The status of the quest",
                                                                        json_schema_extra={"example": 'in_progress'})


@openapi.component()
class QuestProgressModel(QuestProgressBaseModel):
    progress_id: int = Field(description="The ID of this specific progress instance of the quest",
                             json_schema_extra={"example": 54})
    thorny_id: int = Field(description="The Thorny ID of the user who started this quest",
                           json_schema_extra={"example": 34})
    quest_id: int = Field(description="The quest ID to reference to",
                          json_schema_extra={"example": 453})
    objectives: UserObjectivesListModel = Field(description="A list of the user's objective progress")

    @classmethod
    async def fetch(cls, db: Database, thorny_id: int = None, quest_id: int = None, *args) -> "QuestProgressModel":
        if not thorny_id and not quest_id:
            raise BadRequest400(extra={'ids': ['thorny_id', 'quest_id']})

        data = await db.pool.fetchrow("""
                                          SELECT * from users.quests
                                          WHERE thorny_id = $1
                                            AND quest_id = $2
                                      """,
                                      thorny_id, quest_id)

        if data:
            objectives = await UserObjectivesListModel.fetch(db, thorny_id, quest_id)

            return cls(**data, objectives=objectives)
        else:
            raise NotFound404(extra={'resource': 'quest_progress', 'id': f'Thorny ID: {thorny_id}, Quest ID: {quest_id}'})

    @classmethod
    async def fetch_active_quest(cls, db: Database, thorny_id: int) -> "QuestProgressModel":
        if not thorny_id:
            raise BadRequest400(extra={'ids': ['thorny_id']})

        data = await db.pool.fetchrow("""
                                          SELECT * from users.quests
                                          WHERE thorny_id = $1
                                            AND status = 'in_progress'
                                          ORDER BY accepted_on
                                      """,
                                      thorny_id)

        if data:
            objectives = await UserObjectivesListModel.fetch(db, thorny_id, data['quest_id'])

            return cls(**data, objectives=objectives)
        else:
            raise NotFound404(extra={'resource': 'quest_progress', 'id': thorny_id})

    @classmethod
    async def create(cls, db: Database, model: "QuestProgressCreateModel", *args):
        async with db.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("""
                                       INSERT INTO users.quests(quest_id, thorny_id)
                                       VALUES($1, $2)
                                   """,
                                   model.quest_id, model.thorny_id)

                objectives_list = await ObjectivesListModel.fetch(db, model.quest_id)

                for objective in objectives_list:
                    create_model = UserObjectiveCreateModel(thorny_id=model.thorny_id, quest_id=model.quest_id, objective_id=objective.objective_id)
                    await UserObjectiveModel.create(db, create_model)

    async def mark_failed(self, db: Database):
        quest_update = QuestProgressUpdateModel(status='failed')
        await self.update(db, quest_update)

        for objective in self.objectives:
            if objective.status == 'in_progress':
                objective_update = UserObjectiveUpdateModel(status='failed')
                await objective.update(db, objective_update)

    async def update(self, db: Database, model: "QuestProgressUpdateModel"):
        for k, v in model.model_dump().items():
            setattr(self, k, v) if v is not None else None

        await db.pool.execute("""
                                  UPDATE users.quests
                                  SET accepted_on = $1,
                                      started_on = $2,
                                      status = $3
                                  WHERE thorny_id = $4
                                    AND quest_id = $5
                              """,
                              self.accepted_on, self.started_on,
                              self.status, self.thorny_id, self.quest_id)


class QuestProgressListModel(BaseList[QuestProgressModel]):
    @classmethod
    async def fetch(cls, db: Database, thorny_id: int = None, *args) -> "QuestProgressListModel":
        if not thorny_id:
            raise BadRequest400(extra={'ids': ['thorny_id']})

        data = await db.pool.fetch("""
                                       SELECT * from users.quests
                                       WHERE thorny_id = $1
                                   """,
                                   thorny_id)

        quests = []
        for quest in data:
            objectives = await UserObjectivesListModel.fetch(db, thorny_id, quest['quest_id'])

            quests.append(QuestProgressModel(**quest, objectives=objectives))

        return cls(root=quests)


class QuestProgressCreateModel(BaseModel):
    thorny_id: int = Field(description="The Thorny ID of the user who started this quest",
                           json_schema_extra={"example": 34})
    quest_id: int = Field(description="The quest ID to reference to",
                          json_schema_extra={"example": 453})


QuestProgressUpdateModel = optional_model('QuestProgressUpdateModel', QuestProgressBaseModel)
