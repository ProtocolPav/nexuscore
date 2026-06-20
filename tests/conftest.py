import pytest
from unittest.mock import AsyncMock
from datetime import date, datetime

from src.models.users.profile import ProfileDB, ProfileOut
from src.models.users.user import UserDB, UserOut


# ---------------------------------------------------------------------------
# Shared model factories
# ---------------------------------------------------------------------------

def make_profile_db(thorny_id: int = 1) -> ProfileDB:
    return ProfileDB(
        thorny_id=thorny_id,
        slogan="Test slogan",
        aboutme="About me text",
        lore="Some lore",
        character_name="Test Character",
        character_age=25,
        character_race="Human",
        character_role="Farmer",
        character_origin="Test Origin",
        character_beliefs="Test Beliefs",
        agility=3,
        valor=3,
        strength=3,
        charisma=3,
        creativity=3,
        ingenuity=3,
    )


def make_user_db(
    thorny_id: int = 1,
    user_id: int = 111111111111111111,
    guild_id: int = 999999999999999999,
) -> UserDB:
    return UserDB(
        thorny_id=thorny_id,
        user_id=user_id,
        guild_id=guild_id,
        join_date=date(2024, 1, 1),
        username="testuser",
        birthday=None,
        balance=0,
        active=True,
        role=None,
        patron=False,
        level=1,
        xp=0,
        required_xp=100,
        last_message=None,
        gamertag="TestUser",
        whitelist="TestUser",
        xuid=None,
        location=None,
        dimension=None,
        hidden=False,
    )


def make_user_out(thorny_id: int = 1, **kwargs) -> UserOut:
    profile = ProfileOut(**make_profile_db(thorny_id).model_dump())
    user_db = make_user_db(thorny_id, **kwargs)
    return UserOut(**user_db.model_dump(), profile=profile)
