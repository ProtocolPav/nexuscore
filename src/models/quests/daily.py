import json
import random
from datetime import date, datetime
from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.models.quests.objective import Logic, ObjectiveType
from src.models.quests.objective_customization.customization import LocationCustomization
from src.models.quests.objective_targets.target import (
    KillTargetModel,
    MineTargetModel,
    ScriptEventTargetModel,
    VisitTargetModel,
)
from src.models.quests.quest import QuestIn, QuestOut
from src.models.quests.reward_metadata import Metadata
from src.utils.minecraft_id import MINECRAFT_REGEX_PATTERN

DAILY_QUEST_TYPE = "daily"


class RandomCount(BaseModel):
    """
    A randomizable number. Either an inclusive `min`/`max` range, or a list of `choices`.
    """
    min: Optional[int] = Field(description="The minimum value (inclusive)", examples=[5], default=None)
    max: Optional[int] = Field(description="The maximum value (inclusive)", examples=[8], default=None)
    choices: Optional[list[int]] = Field(description="A list of values to choose from", examples=[[5, 10, 20]],
                                         default=None)

    @model_validator(mode='after')
    def check_values(self) -> "RandomCount":
        if self.choices is not None:
            if self.min is not None or self.max is not None:
                raise ValueError("Use either `choices` or `min`/`max`, not both")
            if len(self.choices) == 0:
                raise ValueError("`choices` must contain at least one value")
            if any(c < 0 for c in self.choices):
                raise ValueError("`choices` cannot contain negative values")
        else:
            if self.min is None or self.max is None:
                raise ValueError("Either `choices` or both `min` and `max` must be provided")
            if self.min < 0:
                raise ValueError("`min` cannot be negative")
            if self.min > self.max:
                raise ValueError("`min` cannot be larger than `max`")

        return self

    def lowest(self) -> int:
        return min(self.choices) if self.choices is not None else self.min

    def roll(self, rng: random.Random) -> int:
        if self.choices is not None:
            return rng.choice(self.choices)

        return rng.randint(self.min, self.max)


def _single(value: int) -> RandomCount:
    return RandomCount(choices=[value])


# ---------- Target options ----------
# Same as the regular targets, except `count` is randomizable

TargetOptionCount = Annotated[RandomCount, Field(
    description="The count of this target. Randomized each time the daily quest is generated.",
    default_factory=lambda: _single(1),
)]


class KillTargetOption(KillTargetModel):
    count: TargetOptionCount


class MineTargetOption(MineTargetModel):
    count: TargetOptionCount


class ScriptEventTargetOption(ScriptEventTargetModel):
    count: TargetOptionCount


class VisitTargetOption(VisitTargetModel):
    count: TargetOptionCount


TargetOption = Annotated[
    Union[MineTargetOption, KillTargetOption, ScriptEventTargetOption, VisitTargetOption],
    Field(discriminator="target_type")
]


# ---------- Customization options ----------

Chance = Annotated[float, Field(
    description="The chance (0 to 1) of this customization being added to the generated quest",
    ge=0, le=1,
    examples=[0.25],
)]


class MainhandOption(BaseModel):
    chance: Chance
    items: list[Annotated[str, Field(pattern=MINECRAFT_REGEX_PATTERN)]] = Field(
        description="The items to choose from", examples=[["minecraft:iron_sword", "minecraft:stone_sword"]],
        min_length=1,
    )


class LocationOption(BaseModel):
    chance: Chance
    locations: list[LocationCustomization] = Field(description="The locations to choose from", min_length=1)
    show_waypoint: bool = Field(description="Also add a waypoint at the chosen location", default=True)


class TimerOption(BaseModel):
    chance: Chance
    seconds: RandomCount = Field(description="The timer length in seconds")
    fail: bool = Field(description="Fail the quest when the timer ends", default=True)


class MaximumDeathsOption(BaseModel):
    chance: Chance
    deaths: RandomCount = Field(description="The maximum deaths allowed")
    fail: bool = Field(description="Fail the quest when the death count is exceeded", default=True)


class NaturalBlockOption(BaseModel):
    chance: Chance


class CustomizationOptions(BaseModel):
    # Used in requests and responses; keep a single schema so API client generators don't see duplicates
    model_config = ConfigDict(json_schema_mode_override="validation")

    mainhand: Optional[MainhandOption] = Field(description="Possible mainhand requirement", default=None)
    location: Optional[LocationOption] = Field(description="Possible location requirement", default=None)
    timer: Optional[TimerOption] = Field(description="Possible timer", default=None)
    maximum_deaths: Optional[MaximumDeathsOption] = Field(description="Possible maximum deaths", default=None)
    natural_block: Optional[NaturalBlockOption] = Field(description="Possible natural block requirement",
                                                        default=None)


# Which objective types may use each customization
CUSTOMIZATION_ALLOWED_TYPES: dict[str, set[str]] = {
    "mainhand": {"kill", "mine"},
    "location": {"kill", "mine", "scriptevent"},
    "timer": {"kill", "mine", "scriptevent", "visit"},
    "maximum_deaths": {"kill", "mine", "scriptevent", "visit"},
    "natural_block": {"mine"},
}


# ---------- Reward options ----------

class RewardOption(BaseModel):
    balance: Optional[RandomCount] = Field(description="The randomized balance (nugs) to give", default=None)
    item: Optional[Annotated[str, Field(pattern=MINECRAFT_REGEX_PATTERN)]] = Field(
        description="The item to give", examples=["minecraft:diamond"], default=None,
    )
    count: Optional[RandomCount] = Field(description="The randomized item count", default=None)
    display_name: Optional[str] = Field(description="Text to display instead of the item name", default=None)
    item_metadata: list[Metadata] = Field(description="Extra item metadata", default_factory=list)

    @model_validator(mode='after')
    def check_reward(self) -> "RewardOption":
        if self.balance is None and self.item is None:
            raise ValueError("The reward must have either a balance or an item")

        if self.balance is not None and self.item is not None:
            raise ValueError("The reward cannot have both a balance and an item")

        if self.item is not None and self.count is None:
            raise ValueError("The reward must have a count if it has an item")

        if self.item is not None and self.count.lowest() < 1:
            raise ValueError("An item reward's count must be at least 1")

        return self


# ---------- Daily templates ----------

TemplateID = Annotated[int, Field(description="The daily template ID", examples=[12])]
GuildID = Annotated[int, Field(description="The guild this template belongs to", examples=[123456789012345678])]
Name = Annotated[str, Field(description="Internal name of the template", examples=["Sheep Hunt"])]
Enabled = Annotated[bool, Field(description="Whether this template can be chosen", examples=[True])]
Weight = Annotated[int, Field(description="Relative chance of this template being chosen", ge=1, examples=[1])]
CreatedBy = Annotated[int, Field(
    description="The Thorny ID that created this template. Generated quests are attributed to them.",
    examples=[1],
)]
Title = Annotated[str, Field(
    description="The generated quest title. Supports `{targets}` and `{count}` placeholders.",
    examples=["Daily: Shear Pressure"],
)]
Description = Annotated[str, Field(
    description="The generated quest description. Supports `{targets}` and `{count}` placeholders.",
    examples=["The farmers need wool. Kill {targets}!"],
)]
ObjectiveDescription = Annotated[str, Field(
    description="The generated objective description. Supports `{targets}` and `{count}` placeholders.",
    examples=["Kill {targets}"],
)]
ObjectiveDisplay = Annotated[str, Field(
    description="Optional objective display override. Supports `{targets}` and `{count}` placeholders.",
    examples=["Kill {count} Sheep"],
)]
TargetOptions = Annotated[list[TargetOption], Field(
    description="The possible targets. Target types must equal `objective_type`.",
)]
TargetPicks = Annotated[RandomCount, Field(
    description="How many of the target options to use. Default: all of them.",
)]
TargetCount = Annotated[RandomCount, Field(
    description="The randomized total count for `or` logic. Required when logic is `or`.",
)]
Customizations = Annotated[CustomizationOptions, Field(
    description="The customizations this template may randomly add",
)]
Rewards = Annotated[list[RewardOption], Field(description="The possible rewards")]
RewardPicks = Annotated[int, Field(description="How many of the reward options are given", ge=0, examples=[1])]


class DailyTemplateBase(BaseModel):
    name: Name
    enabled: Enabled = True
    weight: Weight = 1
    created_by: CreatedBy
    title: Title
    description: Description
    objective_description: ObjectiveDescription
    objective_display: Optional[ObjectiveDisplay] = None
    objective_type: ObjectiveType
    logic: Logic = "and"
    targets: TargetOptions
    target_picks: Optional[TargetPicks] = None
    target_count: Optional[TargetCount] = None
    customizations: Customizations = Field(default_factory=CustomizationOptions)
    rewards: Rewards = Field(default_factory=list)
    reward_picks: RewardPicks = 1

    @model_validator(mode='after')
    def check_template(self):
        if len(self.targets) == 0:
            raise ValueError("Templates must have at least one target")

        for target in self.targets:
            if target.target_type != self.objective_type:
                raise ValueError(f"All targets must be of the same type. "
                                 f"Offending target: {target.target_type} != {self.objective_type}")

            if target.count.lowest() < 1:
                raise ValueError("A target's count must be at least 1")

        if self.logic == "or" and self.target_count is None:
            raise ValueError("`target_count` is required when logic is `or`")

        if self.target_count is not None and self.target_count.lowest() < 1:
            raise ValueError("`target_count` must be at least 1")

        if self.target_picks is not None and self.target_picks.lowest() < 1:
            raise ValueError("`target_picks` must be at least 1")

        for name in CustomizationOptions.model_fields:
            if getattr(self.customizations, name) is not None \
                    and self.objective_type not in CUSTOMIZATION_ALLOWED_TYPES[name]:
                raise ValueError(f"The `{name}` customization is not allowed on `{self.objective_type}` objectives")

        return self


class DailyTemplateDB(DailyTemplateBase):
    template_id: TemplateID
    guild_id: GuildID
    created_at: datetime

    @model_validator(mode='before')
    @classmethod
    def pre_process_json(cls, data):
        for key in ("targets", "target_picks", "target_count", "customizations", "rewards"):
            if isinstance(data.get(key), str):
                data[key] = json.loads(data[key])

        return data


class DailyTemplateOut(DailyTemplateDB):
    pass


class DailyTemplateIn(DailyTemplateBase):
    pass


class DailyTemplateUpdate(BaseModel):
    name: Optional[Name] = None
    enabled: Optional[Enabled] = None
    weight: Optional[Weight] = None
    created_by: Optional[CreatedBy] = None
    title: Optional[Title] = None
    description: Optional[Description] = None
    objective_description: Optional[ObjectiveDescription] = None
    objective_display: Optional[ObjectiveDisplay] = None
    objective_type: Optional[ObjectiveType] = None
    logic: Optional[Logic] = None
    targets: Optional[TargetOptions] = None
    target_picks: Optional[TargetPicks] = None
    target_count: Optional[TargetCount] = None
    customizations: Optional[Customizations] = None
    rewards: Optional[Rewards] = None
    reward_picks: Optional[RewardPicks] = None


# ---------- Generated daily quests ----------

class DailyQuestIn(QuestIn):
    """A generated daily quest. Only the generator creates these; QuestIn does not accept `daily`."""
    quest_type: Literal["daily"] = Field(description="Always `daily`", default="daily")


class DailyQuestDB(BaseModel):
    guild_id: GuildID
    quest_date: date = Field(description="The UTC date this daily quest is for", examples=["2026-11-22"])
    quest_id: int = Field(description="The generated quest's ID", examples=[732])
    template_id: Optional[int] = Field(description="The template this quest was generated from", examples=[12])


class DailyQuestOut(BaseModel):
    quest_date: date = Field(description="The UTC date this daily quest is for", examples=["2026-11-22"])
    template_id: Optional[int] = Field(description="The template this quest was generated from. "
                                                   "`null` if the template was deleted.", examples=[12])
    quest: QuestOut = Field(description="The generated quest. `quest.last_edited_at` is set if an admin "
                                        "has customised it.")
