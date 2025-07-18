from datetime import datetime

from typing_extensions import Literal

from src.models.quests.objective import ObjectivesListModel
from src.utils.base import BaseModel, BaseList, optional_model

from pydantic import Field
from sanic_ext import openapi

from src.database import Database
from src.models.quests.objective import ObjectiveCreateModel, ObjectiveModel
from src.utils.errors import BadRequest400, NotFound404


class QuestBaseModel(BaseModel):
    start_time: datetime = Field(description="When this quest will begin to be available to be accepted",
                                 json_schema_extra={"example": "2024-03-03 04:00:00"})
    end_time: datetime = Field(description="The time that this quest will no longer be available to be accepted",
                               json_schema_extra={"example": "2024-05-03 04:00:00"})
    title: str = Field(description="The quest title",
                       json_schema_extra={"example": 'Skeleton Killer'})
    description: str = Field(description="The description of the quest",
                             json_schema_extra={"example": 'Skeletons are evil...'})
    created_by: int = Field(description="The user that created this quest",
                            json_schema_extra={"example": "13"})
    tags: list[str] = Field(description="A list of tags describing this quest",
                            json_schema_extra={"example": ['pvp', 'timed', 'challenge']})
    quest_type: Literal['story', 'side', 'minor'] = Field(description="The quest type",
                                                          json_schema_extra={"example": "side"})


@openapi.component()
class QuestModel(QuestBaseModel):
    quest_id: int = Field(description="The ID of the quest",
                          json_schema_extra={"example": 732})
    objectives: ObjectivesListModel = Field(description="A list of objectives for this quest")

    @classmethod
    async def create(cls, db: Database, model: "QuestCreateModel", *args) -> int:
        async with db.pool.acquire() as conn:
            async with conn.transaction():
                quest_id = await conn.fetchrow("""
                                                with quest_table as (
                                                    insert into quests.quest(
                                                        start_time, 
                                                        end_time, 
                                                        title, 
                                                        description,
                                                        created_by,
                                                        tags,
                                                        quest_type
                                                    )
                                                    values($1, $2, $3, $4, $5, $6, $7)

                                                    returning quest_id
                                                )
                                                select quest_id as id from quest_table
                                               """,
                                               model.start_time, model.end_time,
                                               model.title, model.description, model.created_by, model.tags,
                                               model.quest_type)

        for objective in model.objectives:
            await ObjectiveModel.create(db=db, model=objective, quest_id=quest_id['id'])

        return quest_id['id']

    @classmethod
    async def fetch(cls, db: Database, quest_id: int, *args) -> "QuestModel":
        if not quest_id:
            raise BadRequest400(extra={'ids': ['quest_id']})

        data = await db.pool.fetchrow("""
                                       SELECT * FROM quests.quest
                                       WHERE quest_id = $1
                                       """,
                                      quest_id)

        if data:
            objectives = await ObjectivesListModel.fetch(db, quest_id)

            return cls(**data, objectives=objectives)
        else:
            raise NotFound404(extra={'resource': 'quest', 'id': quest_id})

    async def update(self, db: Database, model: "QuestUpdateModel"):
        for k, v in model.model_dump().items():
            setattr(self, k, v) if v else None

        await db.pool.execute("""
                              UPDATE quests.quest
                              SET start_time = $1,
                                  end_time = $2,
                                  title = $3,
                                  description = $4
                                  created_by = $5
                                  tags = $6
                                  quest_type = $7
                              WHERE quest_id = $8
                              """,
                              self.start_time, self.end_time,
                              self.title, self.description, self.created_by,
                              self.tags, self.quest_type, self.quest_id)


class QuestListModel(BaseList[QuestModel]):
    @classmethod
    async def fetch(cls, db: Database, *args) -> "QuestListModel":
        data = await db.pool.fetch("""
                                 SELECT * FROM quests.quest
                                 WHERE NOW() BETWEEN start_time AND end_time
                                 ORDER BY start_time DESC
                                 """)

        quests: list[QuestModel] = []
        for quest in data:
            objectives = await ObjectivesListModel.fetch(db, quest['quest_id'])
            quests.append(QuestModel(**quest, objectives=objectives))

        return cls(root=quests)


QuestUpdateModel = optional_model('QuestUpdateModel', QuestBaseModel)


class QuestCreateModel(QuestBaseModel):
    objectives: list[ObjectiveCreateModel] = Field(description="A list of objectives for this quest")
