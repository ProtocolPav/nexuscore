import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from src.services.project import ProjectService
from src.models.projects.project import ProjectDB, ProjectIn, ProjectUpdate
from src.models.projects.status import StatusDB, StatusIn
from tests.conftest import make_user_db, make_profile_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_project_db(project_id: str = "test-project", guild_id: int = 999999999999999999) -> ProjectDB:
    return ProjectDB(
        project_id=project_id,
        guild_id=guild_id,
        owner_id=1,
        name="Test Project",
        description="A test project",
        created_at=datetime(2024, 1, 1),
    )


def make_status_db(project_id: str = "test-project") -> StatusDB:
    return StatusDB(
        project_id=project_id,
        status="active",
        since=datetime(2024, 1, 1),
    )


@pytest.fixture
def mock_project_repo():
    return AsyncMock()


@pytest.fixture
def mock_user_repo():
    return AsyncMock()


@pytest.fixture
def service(mock_project_repo, mock_user_repo):
    return ProjectService(project_repo=mock_project_repo, user_repo=mock_user_repo)


# ---------------------------------------------------------------------------
# ProjectService.get
# ---------------------------------------------------------------------------

class TestProjectServiceGet:
    async def test_get_returns_project_out(self, service, mock_project_repo, mock_user_repo):
        mock_project_repo.fetch.return_value = make_project_db()
        mock_project_repo.fetch_status.return_value = make_status_db()
        mock_user_repo.fetch.return_value = make_user_db()
        mock_user_repo.fetch_profile.return_value = make_profile_db()

        result = await service.get(guild_id=999999999999999999, project_id="test-project")

        assert result.project_id == "test-project"
        assert result.owner is not None
        mock_project_repo.fetch.assert_called_once_with(999999999999999999, "test-project")

    async def test_get_includes_owner_with_profile(self, service, mock_project_repo, mock_user_repo):
        mock_project_repo.fetch.return_value = make_project_db()
        mock_project_repo.fetch_status.return_value = make_status_db()
        mock_user_repo.fetch.return_value = make_user_db()
        mock_user_repo.fetch_profile.return_value = make_profile_db()

        result = await service.get(guild_id=999999999999999999, project_id="test-project")

        assert result.owner.profile is not None


# ---------------------------------------------------------------------------
# ProjectService.new
# ---------------------------------------------------------------------------

class TestProjectServiceNew:
    async def test_new_calls_create_and_returns_project_out(self, service, mock_project_repo, mock_user_repo):
        model = ProjectIn(name="New Project", description="Desc", owner_id=1)
        mock_project_repo.create.return_value = make_project_db(project_id="new-project")
        mock_project_repo.fetch_status.return_value = make_status_db(project_id="new-project")
        mock_user_repo.fetch.return_value = make_user_db()
        mock_user_repo.fetch_profile.return_value = make_profile_db()

        result = await service.new(guild_id=999999999999999999, model=model)

        assert result.project_id == "new-project"
        mock_project_repo.create.assert_called_once()


# ---------------------------------------------------------------------------
# ProjectService.get_status / new_status
# ---------------------------------------------------------------------------

class TestProjectServiceStatus:
    async def test_get_status_returns_status_out(self, service, mock_project_repo):
        mock_project_repo.fetch_status.return_value = make_status_db()

        result = await service.get_status(project_id="test-project")

        assert result.status == "active"
        mock_project_repo.fetch_status.assert_called_once_with("test-project")

    async def test_new_status_calls_create_status(self, service, mock_project_repo):
        model = StatusIn(status="completed")
        mock_project_repo.create_status.return_value = make_status_db()

        result = await service.new_status(project_id="test-project", model=model)

        assert result.status == "active"  # from make_status_db
        mock_project_repo.create_status.assert_called_once_with("test-project", model)
