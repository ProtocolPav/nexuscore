from datetime import datetime
from typing import Literal

from pydantic import Field
from typing_extensions import Optional, deprecated

from sanic_ext import openapi

from src.database import Database
from src.models.quests.objective import ObjectiveModel, ObjectivesListModel
from src.utils.base import BaseModel, BaseList, optional_model
from src.utils.errors import BadRequest400, NotFound404


class UserQuestBaseModel(BaseModel):
    accepted_on: datetime = Field(description="The time that the user accepted this quest",
                                  json_schema_extra={"example": '2024-05-05 05:34:21.123456'})
    started_on: Optional[datetime] = Field(description="The time the user actually started to complete the quest",
                                           json_schema_extra={"example": '2024-05-05 05:34:21.123456'})
    status: Literal['in_progress', 'completed', 'failed'] = Field(description="The status of the quest",
                                                                  json_schema_extra={"example": 'in_progress'})


class UserObjectiveBaseModel(BaseModel):
    start: datetime = Field(description="The time this objective was started on",
                            json_schema_extra={"example": '2024-05-05 05:34:21.123456'})
    end: Optional[datetime] = Field(description="The time that this objective was completed",
                                    json_schema_extra={"example": '2024-05-05 05:34:21.123456'})
    completion: int = Field(description="The completion of this objective",
                            json_schema_extra={"example": 5})
    status: Literal['in_progress', 'completed', 'failed'] = Field(description="The status of this objective",
                                                                  json_schema_extra={"example": 'in_progress'})


class UserQuestModel(UserQuestBaseModel):
    thorny_id: int = Field(description="The ThornyID of a user. This is a unique number.",
                           json_schema_extra={"example": 34})
    quest_id: int = Field(description="The quest ID",
                          json_schema_extra={"example": 453})
    objectives: "UserObjectivesListModel" = Field(description="A list of all the objectives of this quest")

    @classmethod
    async def fetch(cls, db: Database, thorny_id: int = None, quest_id: int = None, *args) -> "UserQuestModel":
        if not thorny_id and not quest_id:
            raise BadRequest400('No IDs provided. Please provide a thorny and quest ID to fetch a quest by')

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
            raise NotFound404(extra={'resource': 'user_quest', 'id': f'{thorny_id}:{quest_id}'})

    @classmethod
    async def fetch_active_quest(cls, db: Database, thorny_id: int) -> "UserQuestModel":
        if not thorny_id:
            raise BadRequest400('No ID provided. Please provide a thorny ID to fetch a quest by')

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
            raise NotFound404(extra={'resource': 'user_quest', 'id': thorny_id})

    @classmethod
    async def get_all_quest_ids(cls, db: Database, thorny_id: int) -> Optional[list[int]]:
        data = await db.pool.fetchrow("""
                                      SELECT ARRAY_AGG(quest_id) AS quests from users.quests
                                      WHERE thorny_id = $1
                                      """,
                                      thorny_id)

        return data['quests'] if data else None

    @classmethod
    async def create(cls, db: Database, model: "UserQuestCreateModel", *args):
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
        quest_update = UserQuestUpdateModel(status='failed')
        await self.update(db, quest_update)

        for objective in self.objectives:
            if objective.status == 'in_progress':
                objective_update = UserObjectiveUpdateModel(status='failed')
                await objective.update(db, objective_update)

    async def update(self, db: Database, model: "UserQuestUpdateModel"):
        for k, v in model.model_dump().items():
            setattr(self, k, v) if v else None

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


@openapi.component()
class UserObjectiveModel(UserObjectiveBaseModel):
    thorny_id: int = Field(description="The ThornyID of a user. This is a unique number.",
                           json_schema_extra={"example": 34})
    quest_id: int = Field(description="The quest ID",
                          json_schema_extra={"example": 453})
    objective_id: int = Field(description="The objective ID",
                              json_schema_extra={"example": 22})

    @classmethod
    async def fetch(cls, db: Database, thorny_id: int = None, objective_id: int = None, *args) -> "UserObjectiveModel":
        if not thorny_id and not objective_id:
            raise BadRequest400('No IDs provided. Please provide a thorny and objective ID to fetch a objective by')

        data = await db.pool.fetchrow("""
                                      SELECT * from users.objectives
                                      WHERE thorny_id = $1
                                        AND objective_id = $2
                                      """,
                                      thorny_id, objective_id)

        if data:
            return cls(**data)
        else:
            raise NotFound404(extra={'resource': 'user_objective', 'id': f'{thorny_id}:{objective_id}'})

    @classmethod
    async def create(cls, db: Database, model: "UserObjectiveCreateModel", *args):
        async with db.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("""
                                   INSERT INTO users.objectives(quest_id, thorny_id, objective_id)
                                   VALUES($1, $2, $3)
                                   """,
                                   model.quest_id, model.thorny_id, model.objective_id)

    async def update(self, db: Database, model: "UserObjectiveUpdateModel"):
        for k, v in model.model_dump().items():
            setattr(self, k, v) if v else None

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
                              self.status, self.thorny_id, self.quest_id, self.objective_id)


class UserObjectivesListModel(BaseList[UserObjectiveModel]):
    @classmethod
    async def fetch(cls, db: Database, thorny_id: int = None, quest_id: int = None, *args) -> "UserObjectivesListModel":
        if not thorny_id and not quest_id:
            raise BadRequest400('No IDs provided. Please provide a thorny and quest ID to fetch a objectives by')

        data = await db.pool.fetch("""
                                   SELECT * from users.objectives
                                   WHERE thorny_id = $1
                                     AND quest_id = $2
                                   """,
                                   thorny_id, quest_id)

        if data:
            objectives = []
            for objective in data:
                objectives.append(UserObjectiveModel(**objective))

            return cls(root=objectives)
        else:
            raise NotFound404(extra={'resource': 'user_objective_list', 'id': f'{thorny_id}:{quest_id}'})


class UserQuestsListModel(BaseList[UserQuestModel]):
    @classmethod
    async def fetch(cls, db: Database, thorny_id: int = None, *args) -> "UserQuestsListModel":
        if not thorny_id:
            raise BadRequest400('No IDs provided. Please provide a thorny and quest ID to fetch a objectives by')

        data = await db.pool.fetch("""
                                   SELECT * from users.quests
                                   WHERE thorny_id = $1
                                   """,
                                   thorny_id)

        if data:
            quests = []
            for quest in data:
                objectives = await UserObjectivesListModel.fetch(db, thorny_id, quest['quest_id'])

                quests.append(UserQuestModel(**quest, objectives=objectives))

            return cls(root=quests)
        else:
            raise NotFound404(extra={'resource': 'user_quest_list', 'id': thorny_id})


class UserQuestCreateModel(BaseModel):
    thorny_id: int = Field(description="The ThornyID of a user. This is a unique number.",
                           json_schema_extra={"example": 34})
    quest_id: int = Field(description="The quest ID",
                          json_schema_extra={"example": 453})


class UserObjectiveCreateModel(BaseModel):
    thorny_id: int = Field(description="The ThornyID of a user. This is a unique number.",
                           json_schema_extra={"example": 34})
    quest_id: int = Field(description="The quest ID",
                          json_schema_extra={"example": 453})
    objective_id: int = Field(description="The objective ID",
                              json_schema_extra={"example": 22})


UserQuestUpdateModel = optional_model('UserQuestUpdateModel', UserQuestBaseModel)

UserObjectiveUpdateModel = optional_model('UserObjectiveUpdateModel', UserObjectiveBaseModel)
