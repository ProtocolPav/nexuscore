import json
from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator
from typing_extensions import Optional

from sanic_ext import openapi

from src.database import Database
from src.models.quests.objective_customization.customization import Customizations
from src.models.quests.objective_customization.progress import CustomizationProgress
from src.models.quests.objective_targets.progress import TargetProgress
from src.models.quests.objective_targets.target import Targets
from src.utils.base import BaseModel, BaseList, optional_model
from src.utils.errors import BadRequest400, NotFound404


class ObjectiveProgressBaseModel(BaseModel):
    start_time: Optional[datetime] = Field(description="The time this objective was started on",
                                           json_schema_extra={"example": '2024-05-05T05:34:21Z'})
    end_time: Optional[datetime] = Field(description="The time that this objective was completed",
                                         json_schema_extra={"example": '2024-05-05T05:34:21Z'})
    status: Literal['active', 'pending', 'completed', 'failed'] = Field(description="The status of this objective",
                                                                        json_schema_extra={"example": 'active'})
    target_progress: list[TargetProgress] = Field(description="List of each objective target's progress")
    customization_progress: CustomizationProgress = Field(description="Specific customization info to track")

    @model_validator(mode='before')
    @classmethod
    def pre_process_json(cls, data):
        if isinstance(data.get('target_progress'), str):
            data['target_progress'] = json.loads(data['target_progress'])

        if isinstance(data.get('customization_progress'), str):
            data['customization_progress'] = json.loads(data['customization_progress'])

        return data


@openapi.component()
class ObjectiveProgressModel(ObjectiveProgressBaseModel):
    progress_id: int = Field(description="The quest progress ID",
                             json_schema_extra={"example": 453})
    objective_id: int = Field(description="The objective ID",
                              json_schema_extra={"example": 22})

    @classmethod
    async def fetch(cls, db: Database, progress_id: int = None, objective_id: int = None, *args) -> "ObjectiveProgressModel":
        if not progress_id or not objective_id:
            raise BadRequest400(extra={'ids': ['progress_id', 'objective_id']})

        data = await db.pool.fetchrow("""
                                      SELECT * from quests_v3.objective_progress
                                      WHERE progress_id = $1
                                        AND objective_id = $2
                                      """,
                                      progress_id, objective_id)

        if data:
            return cls(**data)
        else:
            raise NotFound404(extra={'resource': 'objective_progress', 'id': f'Progress ID: {progress_id}, Objective ID:{objective_id}'})

    @classmethod
    async def create(cls, db: Database, model: "ObjectiveProgressCreateModel", *args):
        async with db.pool.acquire() as conn:
            async with conn.transaction():
                targets = list(map(lambda x: x.model_dump(), model.target_progress))

                await conn.execute("""
                                   INSERT INTO quests_v3.objective_progress(
                                       progress_id,
                                       objective_id,
                                       target_progress,
                                       customization_progress
                                   )
                                   VALUES($1, $2, $3, $4)
                                   """,
                                   model.progress_id, model.objective_id,
                                   json.dumps(targets, default=str), model.customization_progress.model_dump_json())

    async def update(self, db: Database, model: "ObjectiveProgressUpdateModel"):
        for k, v in model.model_dump().items():
            setattr(self, k, v) if v is not None else None

        await db.pool.execute("""
                               UPDATE quests_v3.objective_progress
                               SET start_time = $1,
                                   end_time = $2,
                                   target_progress = $3,
                                   customization_progress = $4,
                                   status = $5
                               WHERE progress_id = $6
                               AND objective_id = $7
                               """,
                              self.start_time, self.end_time, self.target_progress, self.customization_progress,
                              self.status, self.progress_id, self.objective_id)


@openapi.component()
class ObjectiveProgressListModel(BaseList[ObjectiveProgressModel]):
    @classmethod
    async def fetch(cls, db: Database, progress_id: int = None, *args) -> "ObjectiveProgressListModel":
        if not progress_id:
            raise BadRequest400(extra={'ids': ['progress_id']})

        data = await db.pool.fetch("""
                                   SELECT * from quests_v3.objective_progress
                                   WHERE progress_id = $1
                                   """,
                                   progress_id)

        objectives = []
        for objective in data:
            objectives.append(ObjectiveProgressModel(**objective))

        return cls(root=objectives)


class ObjectiveProgressCreateModel(BaseModel):
    progress_id: int = Field(description="The quest progress ID",
                             json_schema_extra={"example": 453})
    objective_id: int = Field(description="The objective ID",
                              json_schema_extra={"example": 22})
    target_progress: list[TargetProgress] = Field(description="List of each objective target's progress")
    customization_progress: CustomizationProgress = Field(description="Specific customization info to track")

    @classmethod
    def generate_target_progress(cls, targets: list[Targets]):
        ...

    @classmethod
    def generate_customization_progress(cls, customization: Customizations):
        ...


ObjectiveProgressUpdateModel = optional_model('ObjectiveProgressUpdateModel', ObjectiveProgressBaseModel)
