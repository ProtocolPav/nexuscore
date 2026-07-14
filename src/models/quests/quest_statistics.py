from datetime import date
from typing import Annotated, Optional

from pydantic import Field, BaseModel

QuestID = Annotated[int, Field(
    description="The Quest ID",
    examples=[732]
)]


class ObjectiveStatistics(BaseModel):
    objective_id: int = Field(description="The objective ID", examples=[22])
    order_index: int = Field(description="The order of the objective, used for funnel sorting", examples=[0])
    description: str = Field(description="The objective description", examples=["Kill 100 Thorns"])

    players_reached: int = Field(description="Number of players who started this objective")
    players_completed: int = Field(description="Number of players who completed this objective")
    players_failed: int = Field(description="Number of players who failed this objective")

    completion_rate: float = Field(description="players_completed / players_reached. 0 if none reached.", examples=[0.72])
    drop_rate: float = Field(description="players_failed / players_reached. 0 if none reached.", examples=[0.28])

    avg_time_seconds: Optional[int] = Field(
        description="Average time in seconds spent on this objective (start_time to end_time), across completions",
        default=None
    )
    median_time_seconds: Optional[int] = Field(
        description="Median time in seconds spent on this objective, across completions",
        default=None
    )


class QuestCompletionBucket(BaseModel):
    bucket_start_seconds: int = Field(description="Start of the time bucket in seconds", examples=[0])
    bucket_end_seconds: int = Field(description="End of the time bucket in seconds", examples=[3600])
    count: int = Field(description="Number of completions that fall within this bucket", examples=[14])


class DailyActivityEntry(BaseModel):
    date: date = Field(description="The calendar date", examples=["2026-01-01"])
    accepts: int = Field(description="Number of quest accepts on this date")
    completions: int = Field(description="Number of quest completions on this date")
    failures: int = Field(description="Number of quest failures on this date")


class QuestStatisticsOut(BaseModel):
    quest_id: QuestID
    title: str = Field(description="The quest title", examples=["Re-Quest: Aha!"])
    quest_type: str = Field(description="The quest type", examples=["side"])

    # Funnel
    total_accepts: int = Field(description="Total number of times this quest has been accepted")
    total_pending: int = Field(description="Players who accepted but never started the quest")
    total_started: int = Field(description="Players who actively began working on objectives")
    total_completed: int = Field(description="Players who completed the quest")
    total_failed: int = Field(description="Players who failed the quest")

    completion_rate: float = Field(
        description="total_completed / total_accepts. 0 if no accepts.",
        examples=[0.65]
    )
    started_rate: float = Field(
        description="total_started / total_accepts. Indicates whether players bounce before starting.",
        examples=[0.90]
    )

    # Timing (all based on start_time -> end_time for completed quests only)
    avg_completion_time_seconds: Optional[int] = Field(
        description="Average time in seconds to complete the quest",
        default=None
    )
    median_completion_time_seconds: Optional[int] = Field(
        description="Median time in seconds to complete the quest",
        default=None
    )
    fastest_completion_seconds: Optional[int] = Field(
        description="Fastest recorded completion time in seconds",
        default=None
    )
    slowest_completion_seconds: Optional[int] = Field(
        description="Slowest recorded completion time in seconds",
        default=None
    )

    # Players
    unique_players: int = Field(description="Number of distinct players who accepted the quest")
    repeat_attempt_players: int = Field(description="Number of players who accepted the quest more than once")

    # Graph data
    objectives: list[ObjectiveStatistics] = Field(
        description="Per-objective statistics, sorted by order_index, for funnel/waterfall charts"
    )
    completion_time_histogram: list[QuestCompletionBucket] = Field(
        description="Bucketed completion times for histogram display"
    )
    daily_activity: list[DailyActivityEntry] = Field(
        description="Daily accepts, completions, and failures for time-series line charts"
    )
