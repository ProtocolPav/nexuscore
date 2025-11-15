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
            setattr(self, k, v) if v is not None else None

        await db.pool.execute("""
                              UPDATE quests.quest
                              SET start_time = $1,
                                  end_time = $2,
                                  title = $3,
                                  description = $4,
                                  created_by = $5,
                                  tags = $6,
                                  quest_type = $7
                              WHERE quest_id = $8
                              """,
                              self.start_time, self.end_time,
                              self.title, self.description, self.created_by,
                              self.tags, self.quest_type, self.quest_id)


class QuestListModel(BaseList[QuestModel]):
    @classmethod
    async def fetch(cls,
                    db: Database,
                    time_start: str = None,
                    time_end: str = None,
                    creator_thorny_ids: list[str] = None,
                    quest_types: list[str] = None,
                    active: bool = None,
                    future: bool = None,
                    past: bool = None,
                    *args) -> "QuestListModel":
        # Build the query dynamically
        query_parts = ["SELECT * FROM quests.quest q"]
        conditions = []
        params = []

        # Handle thorny_ids (OR condition using ANY)
        if creator_thorny_ids is not None and len(creator_thorny_ids) > 0:
            param_idx = len(params)
            conditions.append(f"q.created_by = ANY(${param_idx + 1}::int[])")

            thorny_ids_int = [int(x) for x in creator_thorny_ids]
            params.append(thorny_ids_int)

        # Handle interaction_types (OR condition using ANY)
        if quest_types is not None and len(quest_types) > 0:
            param_idx = len(params)
            conditions.append(f"q.quest_type = ANY(${param_idx + 1})")

            params.append(quest_types)

        # Handle time filtering
        if time_start is not None and time_end is not None:
            # Both start and end provided - filter between range
            param_idx = len(params)
            conditions.append(f"q.start_time >= ${param_idx + 1}::timestamp AND q.end_time <= ${param_idx + 2}::timestamp")
            params.extend([
                datetime.strptime(time_start, '%Y-%m-%d %H:%M:%S.%f'),
                datetime.strptime(time_end, '%Y-%m-%d %H:%M:%S.%f')
            ])

        elif time_start is not None:
            # Only start time provided - filter after this time
            param_idx = len(params)
            conditions.append(f"q.start_time >= ${param_idx + 1}::timestamp")
            params.append(datetime.strptime(time_start, '%Y-%m-%d %H:%M:%S.%f'))

        elif time_end is not None:
            # Only end time provided - filter before this time
            param_idx = len(params)
            conditions.append(f"q.end_time <= ${param_idx + 1}::timestamp")
            params.append(datetime.strptime(time_end, '%Y-%m-%d %H:%M:%S.%f'))

        # Handle "active", "future" and "past" quests
        if active:
            conditions.append(f"NOW() BETWEEN q.start_time AND q.end_time")

        if future:
            conditions.append(f"q.start_time > NOW()")

        if past:
            conditions.append(f"q.end_time < NOW()")

        # Add WHERE clause if we have conditions
        if conditions:
            query_parts.append("WHERE")
            query_parts.append(" AND ".join(conditions))

        # Add ORDER BY clause
        query_parts.append("ORDER BY q.quest_id DESC")

        query = " ".join(query_parts)

        # Execute the query
        data = await db.pool.fetch(query, *params)

        quests: list[QuestModel] = []
        for quest in data:
            objectives = await ObjectivesListModel.fetch(db, quest['quest_id'])
            quests.append(QuestModel(**quest, objectives=objectives))

        return cls(root=quests)


QuestUpdateModel = optional_model('QuestUpdateModel', QuestBaseModel)


class QuestCreateModel(QuestBaseModel):
    objectives: list[ObjectiveCreateModel] = Field(description="A list of objectives for this quest")
