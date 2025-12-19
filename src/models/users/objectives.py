from datetime import datetime
from typing import Literal

from pydantic import Field
from typing_extensions import Optional

from sanic_ext import openapi

from src.database import Database
from src.utils.base import BaseModel, BaseList, optional_model
from src.utils.errors import BadRequest400, NotFound404


class UserObjectiveBaseModel(BaseModel):
    start: datetime = Field(description="The time this objective was started on",
                            json_schema_extra={"example": '2024-05-05 05:34:21+00:00'})
    end: Optional[datetime] = Field(description="The time that this objective was completed",
                                    json_schema_extra={"example": '2024-05-05 05:34:21+00:00'})
    completion: int = Field(description="The completion of this objective",
                            json_schema_extra={"example": 5})
    status: Literal['in_progress', 'completed', 'failed'] = Field(description="The status of this objective",
                                                                  json_schema_extra={"example": 'in_progress'})


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
            raise BadRequest400(extra={'ids': ['thorny_id', 'objective_id']})

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
            setattr(self, k, v) if v is not None else None

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


@openapi.component()
class UserObjectivesListModel(BaseList[UserObjectiveModel]):
    @classmethod
    async def fetch(cls, db: Database, thorny_id: int = None, quest_id: int = None, *args) -> "UserObjectivesListModel":
        if not thorny_id and not quest_id:
            raise BadRequest400(extra={'ids': ['thorny_id', 'quest_id']})

        data = await db.pool.fetch("""
                                   SELECT * from users.objectives
                                   WHERE thorny_id = $1
                                     AND quest_id = $2
                                   """,
                                   thorny_id, quest_id)

        objectives = []
        for objective in data:
            objectives.append(UserObjectiveModel(**objective))

        return cls(root=objectives)


class UserObjectiveCreateModel(BaseModel):
    thorny_id: int = Field(description="The ThornyID of a user. This is a unique number.",
                           json_schema_extra={"example": 34})
    quest_id: int = Field(description="The quest ID",
                          json_schema_extra={"example": 453})
    objective_id: int = Field(description="The objective ID",
                              json_schema_extra={"example": 22})


UserObjectiveUpdateModel = optional_model('UserObjectiveUpdateModel', UserObjectiveBaseModel)
