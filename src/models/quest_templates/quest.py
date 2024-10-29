from datetime import datetime, date

from pydantic import BaseModel, Field
from typing_extensions import Optional

from src.database import Database
from src.models.quest_templates.objective import ObjectiveModel


class QuestModel(BaseModel):
    quest_id: int = Field(description="The ID of the quest",
                          examples=[4])
    start_time: datetime = Field(description="When this quest will begin to be available to be accepted",
                                 examples=["2024-03-03 04:00:00"])
    end_time: datetime = Field(description="The time that this quest will no longer be available to be accepted",
                               examples=["2024-05-03 04:00:00"])
    title: str = Field(description="The quest title",
                       examples=['Adventure across Padova'])
    description: str = Field(description="The description of the quest",
                             examples=['Embark on a huge adventure...'])
    objectives: list[ObjectiveModel]

    @classmethod
    async def new(cls, db: Database, model: "QuestCreateModel") -> int:
        ...

    @classmethod
    async def fetch(cls, db: Database, quest_id: int):
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

        return cls(**data) if data else None

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

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


class QuestUpdateModel(BaseModel):
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    title: Optional[str]
    description: Optional[str]

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


class QuestCreateModel(BaseModel):
    start_time: datetime
    end_time: datetime
    title: str
    description: str

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")