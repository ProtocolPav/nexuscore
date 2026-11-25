import random
from datetime import date, datetime, time, timedelta, timezone
from typing import Optional

from src.models.quests.daily import DAILY_QUEST_TYPE, DailyTemplateBase
from src.models.quests.objective import ObjectiveIn
from src.models.quests.objective_customization.customization import (
    Customizations,
    LocationCustomization,
    MainhandCustomization,
    MaximumDeathsCustomization,
    NaturalBlockCustomization,
    TimerCustomization,
    Waypoint,
    WaypointCustomization,
)
from src.models.quests.objective_targets.target import (
    KillTargetModel,
    MineTargetModel,
    ScriptEventTargetModel,
    VisitTargetModel,
)
from src.models.quests.quest import QuestIn
from src.models.quests.reward import RewardIn

TARGET_MODELS = {
    "kill": KillTargetModel,
    "mine": MineTargetModel,
    "scriptevent": ScriptEventTargetModel,
    "visit": VisitTargetModel,
}


def daily_window(quest_date: date) -> tuple[datetime, datetime]:
    """The start and end of a daily quest: UTC midnight to the next UTC midnight."""
    start = datetime.combine(quest_date, time.min, tzinfo=timezone.utc)
    return start, start + timedelta(days=1)


def utc_today() -> date:
    return datetime.now(timezone.utc).date()


def _pretty_id(minecraft_id: str) -> str:
    """minecraft:diamond_ore -> Diamond Ore"""
    return minecraft_id.split(":")[-1].replace("_", " ").title()


def _target_name(target) -> str:
    match target.target_type:
        case "kill":
            return _pretty_id(target.entity)
        case "mine":
            return _pretty_id(target.block)
        case "scriptevent":
            return _pretty_id(target.script_id)
        case "visit":
            return target.helper_text
    return target.target_type


def _describe_targets(targets: list, logic: str, target_count: Optional[int]) -> tuple[str, int]:
    """Returns a readable target list (e.g. '12 Sheep and 4 Cows') and the total count."""
    if logic == "or":
        names = " or ".join(_target_name(t) for t in targets)
        return f"{target_count} {names}", target_count

    parts = [f"{t.count} {_target_name(t)}" for t in targets]
    if len(parts) > 1:
        text = ", ".join(parts[:-1]) + " and " + parts[-1]
    else:
        text = parts[0]

    return text, sum(t.count for t in targets)


def _format(template: Optional[str], **values) -> Optional[str]:
    if template is None:
        return None

    class _Safe(dict):
        def __missing__(self, key):
            return "{" + key + "}"

    return template.format_map(_Safe(**values))


def _roll_customizations(template: DailyTemplateBase, rng: random.Random) -> Customizations:
    options = template.customizations
    result: dict = {}

    def hit(option) -> bool:
        return option is not None and rng.random() < option.chance

    if hit(options.mainhand):
        result["mainhand"] = MainhandCustomization(item=rng.choice(options.mainhand.items))

    if hit(options.location):
        location: LocationCustomization = rng.choice(options.location.locations)
        result["location"] = location.model_copy()

        if options.location.show_waypoint:
            result["waypoint"] = WaypointCustomization(
                waypoints=[Waypoint(coordinates=location.coordinates, waypoint_type="star")]
            )

    if hit(options.timer):
        result["timer"] = TimerCustomization(seconds=options.timer.seconds.roll(rng), fail=options.timer.fail)

    if hit(options.maximum_deaths):
        result["maximum_deaths"] = MaximumDeathsCustomization(
            deaths=options.maximum_deaths.deaths.roll(rng),
            fail=options.maximum_deaths.fail,
        )

    if hit(options.natural_block):
        result["natural_block"] = NaturalBlockCustomization()

    return Customizations(**result)


def _roll_rewards(template: DailyTemplateBase, rng: random.Random) -> list[RewardIn]:
    picks = min(template.reward_picks, len(template.rewards))
    chosen = rng.sample(template.rewards, picks)

    rewards = []
    for option in chosen:
        rewards.append(RewardIn(
            balance=option.balance.roll(rng) if option.balance is not None else None,
            item=option.item,
            count=option.count.roll(rng) if option.count is not None else None,
            display_name=option.display_name,
            item_metadata=option.item_metadata,
        ))

    return rewards


def generate_daily_quest(
        template: DailyTemplateBase,
        quest_date: date,
        rng: Optional[random.Random] = None,
) -> QuestIn:
    """
    Rolls a concrete, single-objective daily quest from a template.
    Pure function: does not touch the database.
    """
    rng = rng or random.Random()

    # Targets
    options = list(template.targets)
    if template.target_picks is not None:
        picks = min(template.target_picks.roll(rng), len(options))
        options = rng.sample(options, picks)

    targets = []
    for option in options:
        model = TARGET_MODELS[option.target_type]
        targets.append(model(**option.model_dump(exclude={"count", "target_uuid"}), count=option.count.roll(rng)))

    target_count = template.target_count.roll(rng) if template.target_count is not None else None
    targets_text, total = _describe_targets(targets, template.logic, target_count)
    placeholders = {"targets": targets_text, "count": total}

    objective = ObjectiveIn(
        description=_format(template.objective_description, **placeholders),
        display=_format(template.objective_display, **placeholders),
        order_index=0,
        objective_type=template.objective_type,
        logic=template.logic,
        target_count=target_count,
        targets=targets,
        rewards=_roll_rewards(template, rng),
        customizations=_roll_customizations(template, rng),
    )

    start, end = daily_window(quest_date)

    return QuestIn(
        start_time=start,
        end_time=end,
        title=_format(template.title, **placeholders),
        description=_format(template.description, **placeholders),
        tags=["daily"],
        quest_type=DAILY_QUEST_TYPE,
        created_by=template.created_by,
        objectives=[objective],
    )
