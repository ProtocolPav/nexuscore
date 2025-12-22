from datetime import datetime
from typing import Literal

from pydantic import Field
from typing_extensions import Optional

from sanic_ext import openapi

from src.database import Database
from src.models.quests.objective_progress import ObjectiveProgressCreateModel, ObjectiveProgressListModel, ObjectiveProgressModel, \
    ObjectiveProgressUpdateModel
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
    objectives: ObjectiveProgressListModel = Field(description="A list of the user's objective progress")

    @classmethod
    async def fetch(cls, db: Database, progress_id: int = None, *args) -> "QuestProgressModel":
        if not progress_id:
            raise BadRequest400(extra={'ids': ['progress_id']})

        data = await db.pool.fetchrow("""
                                          SELECT * from quests_v3.quest_progress
                                          WHERE progress_id = $1
                                      """,
                                      progress_id)

        if data:
            objectives = await ObjectiveProgressListModel.fetch(db, progress_id)

            return cls(**data, objectives=objectives)
        else:
            raise NotFound404(extra={'resource': 'quest_progress', 'id': f'{progress_id}'})

    @classmethod
    async def fetch_active_quest(cls, db: Database, thorny_id: int) -> "QuestProgressModel":
        if not thorny_id:
            raise BadRequest400(extra={'ids': ['thorny_id']})

        data = await db.pool.fetchrow("""
                                          SELECT * from quests_v3.quest_progress
                                          WHERE thorny_id = $1
                                            AND status = 'active'
                                          ORDER BY accept_time
                                      """,
                                      thorny_id)

        if data:
            objectives = await ObjectiveProgressListModel.fetch(db, data['progress_id'])

            return cls(**data, objectives=objectives)
        else:
            raise NotFound404(extra={'resource': 'quest_progress', 'id': thorny_id})

    @classmethod
    async def create(cls, db: Database, model: "QuestProgressCreateModel", *args) -> int:
        async with db.pool.acquire() as conn:
            async with conn.transaction():
                progress_id = await conn.fetchrow("""
                                                  with quest_table as (
                                                      insert into quests_v3.quest_progress(quest_id, thorny_id)
                                                          VALUES($1, $2)

                                                          returning progress_id
                                                  )
                                                  select progress_id as id from quest_table
                                                  """,
                                                  model.quest_id, model.thorny_id)

                objectives_list = await ObjectivesListModel.fetch(db, model.quest_id)

                for objective in objectives_list:
                    create_model = ObjectiveProgressCreateModel(
                        progress_id=progress_id['id'],
                        objective_id=objective.objective_id,
                        target_progress=ObjectiveProgressCreateModel.generate_target_progress(objective.targets),
                        customization_progress=ObjectiveProgressCreateModel.generate_customization_progress(objective.customizations)
                    )
                    await ObjectiveProgressModel.create(db, create_model)

                return progress_id['id']

    async def mark_failed(self, db: Database):
        quest_update = QuestProgressUpdateModel()
        quest_update.status = 'failed'
        await self.update(db, quest_update)

        for objective in self.objectives:
            if objective.status in ['active', 'pending']:
                objective_update = ObjectiveProgressUpdateModel()
                objective_update.status = 'failed'
                await objective.update(db, objective_update)

    async def update(self, db: Database, model: "QuestProgressUpdateModel"):
        for k, v in model.model_dump().items():
            setattr(self, k, v) if v is not None else None

        await db.pool.execute("""
                                  UPDATE quests_v3.quest_progress
                                  SET start_time = $1,
                                      end_time = $2,
                                      status = $3
                                  WHERE progress_id = $4
                              """,
                              self.start_time, self.end_time, self.status, self.progress_id)


class QuestProgressListModel(BaseList[QuestProgressModel]):
    @classmethod
    async def fetch(cls, db: Database, thorny_id: int = None, *args) -> "QuestProgressListModel":
        if not thorny_id:
            raise BadRequest400(extra={'ids': ['thorny_id']})

        data = await db.pool.fetch("""
                                   SELECT * from quests_v3.quest_progress
                                   WHERE thorny_id = $1
                                   """,
                                   thorny_id)

        quests = []
        for quest in data:
            objectives = await ObjectiveProgressListModel.fetch(db, quest['progress_id'])

            quests.append(QuestProgressModel(**quest, objectives=objectives))

        return cls(root=quests)


class QuestProgressCreateModel(BaseModel):
    thorny_id: int = Field(description="The Thorny ID of the user who started this quest",
                           json_schema_extra={"example": 34})
    quest_id: int = Field(description="The quest ID to reference to",
                          json_schema_extra={"example": 453})


QuestProgressUpdateModel = optional_model('QuestProgressUpdateModel', QuestProgressBaseModel)
