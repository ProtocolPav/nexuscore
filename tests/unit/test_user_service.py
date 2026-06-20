import pytest
from unittest.mock import AsyncMock

from src.services.user import UserService
from src.errors import BadRequest, NotFound
from tests.conftest import make_user_db, make_profile_db, make_user_out


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_user_repo():
    return AsyncMock()


@pytest.fixture
def service(mock_user_repo):
    return UserService(user_repo=mock_user_repo)


# ---------------------------------------------------------------------------
# UserService.get
# ---------------------------------------------------------------------------

class TestUserServiceGet:
    async def test_get_returns_user_out(self, service, mock_user_repo):
        """Fetching a user assembles UserOut with profile."""
        mock_user_repo.fetch.return_value = make_user_db()
        mock_user_repo.fetch_profile.return_value = make_profile_db()

        result = await service.get(guild_id=999999999999999999, thorny_id=1)

        assert result.thorny_id == 1
        assert result.profile is not None

    async def test_get_calls_correct_repo_methods(self, service, mock_user_repo):
        mock_user_repo.fetch.return_value = make_user_db()
        mock_user_repo.fetch_profile.return_value = make_profile_db()

        await service.get(guild_id=999999999999999999, thorny_id=1)

        mock_user_repo.fetch.assert_called_once_with(999999999999999999, 1)


# ---------------------------------------------------------------------------
# UserService.new
# ---------------------------------------------------------------------------

class TestUserServiceNew:
    async def test_new_returns_user_out(self, service, mock_user_repo):
        from src.models.users.user import UserIn
        user_in = UserIn(user_id=111111111111111111, username="newuser")
        mock_user_repo.create.return_value = make_user_db()
        mock_user_repo.fetch_profile.return_value = make_profile_db()

        result = await service.new(guild_id=999999999999999999, model=user_in)

        assert result.thorny_id == 1
        mock_user_repo.create.assert_called_once()


# ---------------------------------------------------------------------------
# UserService.update
# ---------------------------------------------------------------------------

class TestUserServiceUpdate:
    async def test_update_returns_updated_user_out(self, service, mock_user_repo):
        from src.models.users.user import UserUpdate
        update = UserUpdate(username="updated_name")
        updated_db = make_user_db()
        updated_db.username = "updated_name"
        mock_user_repo.update.return_value = updated_db
        mock_user_repo.fetch_profile.return_value = make_profile_db()

        result = await service.update(guild_id=999999999999999999, thorny_id=1, model=update)

        assert result.username == "updated_name"
        mock_user_repo.update.assert_called_once_with(999999999999999999, 1, update)


# ---------------------------------------------------------------------------
# UserService.lookup
# ---------------------------------------------------------------------------

class TestUserServiceLookup:
    async def test_lookup_raises_bad_request_when_no_params(self, service):
        """Providing no lookup param must raise BadRequest."""
        with pytest.raises(BadRequest):
            await service.lookup(guild_id=999999999999999999)

    async def test_lookup_raises_bad_request_when_multiple_params(self, service):
        """Providing more than one lookup param must raise BadRequest."""
        with pytest.raises(BadRequest):
            await service.lookup(
                guild_id=999999999999999999,
                gamertag="steve",
                discord_id=111111111111111111
            )

    async def test_lookup_raises_not_found_when_repo_returns_none(self, service, mock_user_repo):
        """Repo returning None must result in NotFound."""
        mock_user_repo.fetch_by_gamertag.return_value = None

        with pytest.raises(NotFound):
            await service.lookup(guild_id=999999999999999999, gamertag="ghost")

    async def test_lookup_by_gamertag_calls_correct_method(self, service, mock_user_repo):
        mock_user_repo.fetch_by_gamertag.return_value = make_user_db()
        mock_user_repo.fetch_profile.return_value = make_profile_db()

        await service.lookup(guild_id=999999999999999999, gamertag="TestUser")

        mock_user_repo.fetch_by_gamertag.assert_called_once_with(999999999999999999, "TestUser")
        mock_user_repo.fetch_by_whitelist.assert_not_called()
        mock_user_repo.fetch_by_discord_id.assert_not_called()

    async def test_lookup_by_whitelist_calls_correct_method(self, service, mock_user_repo):
        mock_user_repo.fetch_by_whitelist.return_value = make_user_db()
        mock_user_repo.fetch_profile.return_value = make_profile_db()

        await service.lookup(guild_id=999999999999999999, whitelist="TestUser")

        mock_user_repo.fetch_by_whitelist.assert_called_once_with(999999999999999999, "TestUser")
        mock_user_repo.fetch_by_gamertag.assert_not_called()
        mock_user_repo.fetch_by_discord_id.assert_not_called()

    async def test_lookup_by_discord_id_calls_correct_method(self, service, mock_user_repo):
        mock_user_repo.fetch_by_discord_id.return_value = make_user_db()
        mock_user_repo.fetch_profile.return_value = make_profile_db()

        await service.lookup(guild_id=999999999999999999, discord_id=111111111111111111)

        mock_user_repo.fetch_by_discord_id.assert_called_once_with(999999999999999999, 111111111111111111)


# ---------------------------------------------------------------------------
# UserService.get_profile
# ---------------------------------------------------------------------------

class TestUserServiceGetProfile:
    async def test_get_profile_returns_profile_out(self, service, mock_user_repo):
        mock_user_repo.fetch_profile.return_value = make_profile_db()

        result = await service.get_profile(guild_id=999999999999999999, thorny_id=1)

        assert result.slogan == "Test slogan"
        assert result.character_name == "Test Character"

    async def test_get_profile_calls_repo_with_correct_args(self, service, mock_user_repo):
        mock_user_repo.fetch_profile.return_value = make_profile_db()

        await service.get_profile(guild_id=999999999999999999, thorny_id=1)

        mock_user_repo.fetch_profile.assert_called_once_with(999999999999999999, 1)


# ---------------------------------------------------------------------------
# UserService.update_profile
# ---------------------------------------------------------------------------

class TestUserServiceUpdateProfile:
    async def test_update_profile_returns_profile_out(self, service, mock_user_repo):
        from src.models.users.profile import ProfileUpdate
        update = ProfileUpdate(slogan="New slogan")
        updated_profile = make_profile_db()
        updated_profile.slogan = "New slogan"
        mock_user_repo.update_profile.return_value = updated_profile

        result = await service.update_profile(guild_id=999999999999999999, thorny_id=1, model=update)

        assert result.slogan == "New slogan"
        mock_user_repo.update_profile.assert_called_once_with(999999999999999999, 1, update)
