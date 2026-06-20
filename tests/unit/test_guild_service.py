import pytest
from unittest.mock import AsyncMock

from src.services.guild import GuildService
from src.models.guilds.guild import GuildDB
from src.models.guilds import FeatureOut, ChannelOut


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_guild_db(guild_id: int = 999999999999999999) -> GuildDB:
    return GuildDB(
        guild_id=guild_id,
        guild_name="Test Guild",
        active=True,
    )


@pytest.fixture
def mock_guild_repo():
    return AsyncMock()


@pytest.fixture
def service(mock_guild_repo):
    return GuildService(guild_repo=mock_guild_repo)


# ---------------------------------------------------------------------------
# GuildService.get
# ---------------------------------------------------------------------------

class TestGuildServiceGet:
    async def test_get_returns_guild_out(self, service, mock_guild_repo):
        mock_guild_repo.fetch.return_value = make_guild_db()
        mock_guild_repo.fetch_features.return_value = []
        mock_guild_repo.fetch_channels.return_value = []

        result = await service.get(guild_id=999999999999999999)

        assert result.guild_id == 999999999999999999
        mock_guild_repo.fetch.assert_called_once_with(999999999999999999)

    async def test_get_assembles_features_and_channels(self, service, mock_guild_repo):
        mock_guild_repo.fetch.return_value = make_guild_db()
        mock_guild_repo.fetch_features.return_value = []
        mock_guild_repo.fetch_channels.return_value = []

        result = await service.get(guild_id=999999999999999999)

        assert isinstance(result.features, list)
        assert isinstance(result.channels, list)


# ---------------------------------------------------------------------------
# GuildService.get_features
# ---------------------------------------------------------------------------

class TestGuildServiceGetFeatures:
    async def test_get_features_returns_feature_out_list(self, service, mock_guild_repo):
        mock_guild_repo.fetch_features.return_value = []

        result = await service.get_features(guild_id=999999999999999999)

        assert result == []
        mock_guild_repo.fetch_features.assert_called_once_with(999999999999999999)


# ---------------------------------------------------------------------------
# GuildService.get_channels
# ---------------------------------------------------------------------------

class TestGuildServiceGetChannels:
    async def test_get_channels_returns_channel_out_list(self, service, mock_guild_repo):
        mock_guild_repo.fetch_channels.return_value = []

        result = await service.get_channels(guild_id=999999999999999999)

        assert result == []
        mock_guild_repo.fetch_channels.assert_called_once_with(999999999999999999)


# ---------------------------------------------------------------------------
# GuildService.get_interactions
# ---------------------------------------------------------------------------

class TestGuildServiceGetInteractions:
    async def test_get_interactions_returns_list(self, service, mock_guild_repo):
        from src.models.guilds.interaction import InteractionQuery
        mock_guild_repo.fetch_interactions.return_value = []
        query = InteractionQuery()

        result = await service.get_interactions(query=query)

        assert result == []
        mock_guild_repo.fetch_interactions.assert_called_once_with(query)
