from datetime import datetime
from src.utils.base import BaseModel, BaseList, optional_model

from pydantic import Field
from sanic_ext import openapi

from src.database import Database
from src.models.quests.objective import ObjectiveCreateModel
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

    @classmethod
    async def create(cls, db: Database, model: "QuestCreateModel" = None, *args) -> int:
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
                    objective_id = await conn.fetchrow("""
                                                        with objective_table as (
                                                            insert into quests.objective(quest_id,
                                                                                         objective,
                                                                                         objective_count,
                                                                                         objective_type,
                                                                                         objective_timer,
                                                                                         required_mainhand,
                                                                                         required_location,
                                                                                         location_radius,
                                                                                         "order",
                                                                                         description,
                                                                                         natural_block,
                                                                                         display)
                                                            values($1, 
                                                                   $2, 
                                                                   $3, 
                                                                   $4, 
                                                                   CASE WHEN $5::double precision IS NULL THEN NULL
                                                                   ELSE make_interval(secs => $5::double precision)
                                                                   END, 
                                                                   $6, 
                                                                   $7, 
                                                                   $8, 
                                                                   $9,
                                                                   $10,
                                                                   $11,
                                                                   $12)

                                                            returning objective_id
                                                        )
                                                        select objective_id as id from objective_table
                                                       """,
                                                       quest_id['id'], objective.objective, objective.objective_count,
                                                       objective.objective_type, objective.objective_timer,
                                                       objective.required_mainhand, objective.required_location,
                                                       objective.location_radius, objective.order, objective.description,
                                                       objective.natural_block, objective.display)

                    if objective.rewards:
                        for reward in objective.rewards:
                            await conn.execute("""
                                               INSERT INTO quests.reward(quest_id, 
                                                                         objective_id,
                                                                         balance,
                                                                         item,
                                                                         count,
                                                                         display_name)
                                               VALUES($1, $2, $3, $4, $5, $6)
                                               """,
                                               quest_id['id'], objective_id['id'], reward.balance, reward.item, reward.count,
                                               reward.display_name)

                return quest_id['id']

    @classmethod
    async def fetch(cls, db: Database, quest_id: int = None, *args):
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

        if data:
            return cls(**data)
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
        quest_ids = await db.pool.fetchrow("""
                                           SELECT COALESCE(array_agg(quest_id), ARRAY[]::integer[]) as ids
                                           FROM quests.quest
                                           WHERE NOW() BETWEEN start_time AND end_time
                                           """)

        quests: list[QuestModel] = []
        for quest_id in quest_ids.get('ids', []):
            quests.append(await QuestModel.fetch(db, quest_id))

        quests.sort(key= lambda x: x.start_time, reverse=True)
        return cls(root=quests)


QuestUpdateModel = optional_model('QuestUpdateModel', QuestBaseModel)


class QuestCreateModel(QuestBaseModel):
    objectives: list[ObjectiveCreateModel] = Field(description="A list of objectives for this quest")
