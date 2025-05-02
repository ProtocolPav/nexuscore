from datetime import datetime

from src.models.quests import ObjectivesListModel
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


@openapi.component()
class QuestModel(QuestBaseModel):
    quest_id: int = Field(description="The ID of the quest",
                          json_schema_extra={"example": 732})
    objectives: BaseList[ObjectiveModel] = Field(description="A list of objectives for this quest")

    @classmethod
    async def create(cls, db: Database, model: "QuestCreateModel", *args) -> int:
        async with db.pool.acquire() as conn:
            async with conn.transaction():
                quest_id = await conn.fetchrow("""
                                                with quest_table as (
                                                    insert into quests.quest(start_time, end_time, title, description)
                                                    values($1, $2, $3, $4)

                                                    returning quest_id
                                                )
                                                select quest_id as id from quest_table
                                               """,
                                               model.start_time, model.end_time,
                                               model.title, model.description)

        for objective in model.objectives:
            await ObjectiveModel.create(db=db, model=objective, quest_id=quest_id['id'])

        return quest_id['id']

    @classmethod
    async def fetch(cls, db: Database, quest_id: int, *args):
        if not quest_id:
            raise BadRequest400('No quest ID provided. Please provide a quest ID to fetch a quest by')

        data = await db.pool.fetchrow("""
                                       SELECT quest_id,
                                              start_time,
                                              end_time,
                                              title,
                                              description
                                       FROM quests.quest
                                       WHERE quest_id = $1
                                       """,
                                      quest_id)

        objectives = await ObjectivesListModel.fetch(db, quest_id)

        if data:
            return cls(**data, objectives=objectives)
        else:
            raise NotFound404(extra={'resource': 'quest', 'id': quest_id})

    async def update(self, db: Database):
        await db.pool.execute("""
                              UPDATE quests.quest
                              SET start_time = $1,
                                  end_time = $2,
                                  title = $3,
                                  description = $4
                              WHERE quest_id = $5
                              """,
                              self.start_time, self.end_time,
                              self.title, self.description, self.quest_id)


class QuestListModel(BaseList[QuestModel]):
    @classmethod
    async def fetch(cls, db: Database, *args):
        quest_data = await db.pool.fetch("""
                                         SELECT * FROM quests.quest
                                         WHERE NOW() BETWEEN start_time AND end_time
                                         ORDER BY start_time DESC
                                         """)

        quests: list[QuestModel] = []
        for quest in quest_data:
            objectives = await ObjectivesListModel.fetch(db, quest['quest_id'])
            quests.append(QuestModel(**quest, objectives=objectives))

        return cls(root=quests)


QuestUpdateModel = optional_model('QuestUpdateModel', QuestBaseModel)


class QuestCreateModel(QuestBaseModel):
    objectives: list[ObjectiveCreateModel] = Field(description="A list of objectives for this quest")
