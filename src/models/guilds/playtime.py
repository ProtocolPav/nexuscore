import json
from datetime import date
from typing import Optional

from pydantic import Field, BaseModel


class GuildDailyPlaytime(BaseModel):
    day: date = Field(description="The day this data is about",
                      examples=['2024-05-05'])
    total: Optional[float] = Field(description="The total playtime that day in seconds",
                         examples=[44544.4322])
    unique_players: int = Field(description="How many unique players played that day",
                                examples=[43])
    total_sessions: int = Field(description="The total amount of sessions that day. "
                                            "(A session is when a user connects and disconnects)",
                                examples=[443])
    average_playtime_per_session: Optional[float] = Field(description="The average playtime per session today in seconds",
                                                examples=[405.325])


class GuildWeeklyPlaytime(BaseModel):
    week: int = Field(description="The week of the year this data is about",
                      examples=[23])
    total: Optional[float] = Field(description="The total playtime that week in seconds",
                         examples=[44544.4322])
    unique_players: int = Field(description="How many unique players played that week",
                                examples=[43])
    total_sessions: int = Field(description="The total amount of sessions that week. "
                                            "(A session is when a user connects and disconnects)",
                                examples=[443])
    average_playtime_per_session: Optional[float] = Field(description="The average playtime per session this week in seconds",
                                                examples=[405.325])


class GuildMonthlyPlaytime(BaseModel):
    month: date = Field(description="The month this data is about. Always the first day of that month",
                        examples=['2024-05-01'])
    total: Optional[float] = Field(description="The total playtime that month in seconds",
                         examples=[4554544.4322])
    unique_players: int = Field(description="How many unique players played that month",
                                examples=[432])


class GuildPlaytimeAnalysis(BaseModel):
    total_playtime: float = Field(description="The total playtime of this guild in seconds",
                                  examples=[1999432544.55433])
    total_unique_players: int = Field(description="The total unique players that have played on this guild",
                                      examples=[4433])
    daily_playtime: list[GuildDailyPlaytime] = Field(description="Data about the last 7 days of playtime")
    weekly_playtime: list[GuildWeeklyPlaytime] = Field(description="Data about the last 8 weeks of playtime")
    monthly_playtime: list[GuildMonthlyPlaytime] = Field(description="Data about the last 12 months of playtime")
    peak_playtime_periods: None = None
    peak_active_periods: None = None
    daily_playtime_distribution: None = None
    anomalies: None = None
    predictive_insights: None = None
