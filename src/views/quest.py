from typing import Self

from src.database import Database
from src.models.quest import QuestModel, RewardModel, ObjectiveModel

from pydantic import BaseModel, model_serializer


class QuestView(BaseModel):
    quest: QuestModel
    rewards: list[RewardModel]
    objectives: list[ObjectiveModel]
