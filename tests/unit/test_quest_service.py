import pytest
from unittest.mock import AsyncMock, patch
from datetime import date

from src.services.quest import QuestService
from src.models.quests.quest import QuestDB, QuestIn, QuestUpdate, QuestQuery
from src.models.quests.objective import ObjectiveDB, ObjectiveOut
from src.models.quests.reward import RewardDB, RewardOut
from tests.conftest import make_user_db, make_profile_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_quest_db(quest_id: int = 1, guild_id: int = 999999999999999999) -> QuestDB:
    return QuestDB(
        quest_id=quest_id,
        guild_id=guild_id,
        created_by=1,
        title="Test Quest",
        description="A quest for testing",
        start_time=None,
        end_time=None,
        active=True,
    )


@pytest.fixture
def mock_quest_repo():
    return AsyncMock()


@pytest.fixture
def mock_objective_repo():
    return AsyncMock()


@pytest.fixture
def mock_reward_repo():
    return AsyncMock()


@pytest.fixture
def mock_user_repo():
    return AsyncMock()


@pytest.fixture
def service(mock_quest_repo, mock_objective_repo, mock_reward_repo, mock_user_repo):
    return QuestService(
        quest_repo=mock_quest_repo,
        objective_repo=mock_objective_repo,
        reward_repo=mock_reward_repo,
        user_repo=mock_user_repo,
    )


def _setup_to_out_mocks(mock_quest_repo, mock_objective_repo, mock_reward_repo, mock_user_repo):
    """Helper: wire all repos needed by QuestService._to_out."""
    mock_user_repo.fetch.return_value = make_user_db()
    mock_user_repo.fetch_profile.return_value = make_profile_db()
    mock_objective_repo.fetch_all.return_value = []
    mock_reward_repo.fetch_all.return_value = []


# ---------------------------------------------------------------------------
# QuestService.get
# ---------------------------------------------------------------------------

class TestQuestServiceGet:
    async def test_get_returns_quest_out(
        self, service, mock_quest_repo, mock_objective_repo, mock_reward_repo, mock_user_repo
    ):
        mock_quest_repo.fetch.return_value = make_quest_db()
        _setup_to_out_mocks(mock_quest_repo, mock_objective_repo, mock_reward_repo, mock_user_repo)

        result = await service.get(guild_id=999999999999999999, quest_id=1)

        assert result.quest_id == 1
        assert result.title == "Test Quest"
        mock_quest_repo.fetch.assert_called_once_with(1, 999999999999999999)

    async def test_get_assembles_creator_with_profile(
        self, service, mock_quest_repo, mock_objective_repo, mock_reward_repo, mock_user_repo
    ):
        mock_quest_repo.fetch.return_value = make_quest_db()
        _setup_to_out_mocks(mock_quest_repo, mock_objective_repo, mock_reward_repo, mock_user_repo)

        result = await service.get(guild_id=999999999999999999, quest_id=1)

        assert result.created_by.profile is not None


# ---------------------------------------------------------------------------
# QuestService.get_all
# ---------------------------------------------------------------------------

class TestQuestServiceGetAll:
    async def test_get_all_returns_empty_list_when_no_quests(
        self, service, mock_quest_repo, mock_objective_repo, mock_reward_repo, mock_user_repo
    ):
        mock_quest_repo.fetch_all.return_value = []
        query = QuestQuery()

        result = await service.get_all(guild_id=999999999999999999, query=query)

        assert result == []

    async def test_get_all_returns_multiple_quests(
        self, service, mock_quest_repo, mock_objective_repo, mock_reward_repo, mock_user_repo
    ):
        mock_quest_repo.fetch_all.return_value = [
            make_quest_db(quest_id=1),
            make_quest_db(quest_id=2),
        ]
        _setup_to_out_mocks(mock_quest_repo, mock_objective_repo, mock_reward_repo, mock_user_repo)
        query = QuestQuery()

        result = await service.get_all(guild_id=999999999999999999, query=query)

        assert len(result) == 2
