import json

from pydantic import Field, model_validator, BaseModel
from typing import Annotated, Optional

from src.models.quests.reward_metadata import Metadata
from src.utils.minecraft_id import MINECRAFT_REGEX_PATTERN

QuestID = Annotated[int, Field(
    description="The ID of the quest this reward belongs to",
)]
ObjectiveID = Annotated[int, Field(
    description="The ID of the objective this reward belongs to",
)]
RewardID = Annotated[int, Field(
    description="The ID of this reward",
)]
Balance = Annotated[int, Field(
    description="The balance this reward will add",
)]
ItemID = Annotated[str, Field(
    description="The item this reward will give",
    pattern=MINECRAFT_REGEX_PATTERN
)]
Count = Annotated[int, Field(
    description="The amount of this item this reward will give",
)]
DisplayName = Annotated[str, Field(
    description="The optional text to display instead of the reward item name",
)]
ItemMetadata = Annotated[list[Metadata], Field(
    description="The metadata for the item reward, to add extra customization",
)]

class RewardBase(BaseModel):
    reward_id: RewardID
    balance: Optional[Balance]
    item: Optional[ItemID]
    count: Optional[Count]
    display_name: Optional[DisplayName]
    item_metadata: ItemMetadata


class RewardDB(RewardBase):
    quest_id: QuestID
    objective_id: ObjectiveID

    @model_validator(mode='before')
    @classmethod
    def pre_process_json(cls, data):
        if isinstance(data.get('item_metadata'), str):
            data['item_metadata'] = json.loads(data['item_metadata'])

        return data


class RewardOut(BaseModel):
    reward_id: RewardID
    balance: Optional[Balance]
    item: Optional[ItemID]
    count: Optional[Count]
    display_name: Optional[DisplayName]
    item_metadata: ItemMetadata


class RewardIn(BaseModel):
    balance: Optional[Balance]
    item: Optional[ItemID]
    count: Optional[Count]
    display_name: Optional[DisplayName]
    item_metadata: ItemMetadata

    @model_validator(mode='after')
    def check_targets(self) -> "RewardIn":
        if self.balance is None and self.item is None:
            raise ValueError("The reward must have either a balance or an item")

        if self.balance is not None and self.item is not None:
            raise ValueError("The reward cannot have both a balance and an item")

        if self.item is not None and self.count is None:
            raise ValueError("The reward must have a count if it has an item")

        return self


class RewardUpdate(BaseModel):
    reward_id: Optional[RewardID] = None
    balance: Optional[Balance] = None
    item: Optional[ItemID] = None
    count: Optional[Count] = None
    display_name: Optional[DisplayName] = None
    item_metadata: Optional[ItemMetadata] = None
