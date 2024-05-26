from datetime import datetime

from pydantic import NaiveDatetime, StringConstraints, BaseModel
from typing_extensions import Annotated, Optional, TypedDict

from sanic_ext import openapi


class GuildModel(BaseModel):
    guild_id: int
    name: str
    currency_name: str
    currency_emoji: str
    level_up_message: str
    join_message: str
    leave_message: str
    xp_multiplier: float
    active: bool


class FeatureModel(BaseModel):
    feature: str
    display_name: str
    description: str
    configured: bool


class ChannelModel(BaseModel):
    channel_type: str
    channel_id: int
