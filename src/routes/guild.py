from fastapi import APIRouter, HTTPException, Security
from starlette import status

from src.dependencies.auth import get_current_client, get_guild_client
from src.dependencies.database import db
from src.models import guilds
from src.models.auth import TokenPayload
from src.models.guilds import ConnectionOut
from src.models.users import playtime
from src.repositories.guild import GuildRepository

guilds_router = APIRouter(prefix='/guilds', tags=['Guilds'])
repo = GuildRepository(db)


@guilds_router.post('', status_code=status.HTTP_201_CREATED)
async def create_guild(
        body: guilds.GuildIn,
        auth: TokenPayload = Security(get_current_client, scopes=['admin:guilds'])
) -> guilds.GuildOut:
    """
    Creates a new guild. If a guild with this ID already exists, it returns a 400.
    """
    guild = await repo.create(body)
    features = await repo.fetch_features(auth.guild_id)
    channels = await repo.fetch_channels(auth.guild_id)

    return guilds.GuildOut(
        **guild.model_dump(),
        features=[guilds.FeatureOut(**f.model_dump()) for f in features ],
        channels=[guilds.ChannelOut(**c.model_dump()) for c in channels],
    )


@guilds_router.get('/me')
async def get_guild(
        auth: TokenPayload = Security(get_guild_client, scopes=['guilds:read'])
) -> guilds.GuildOut:
    """
    Fetch your guild information
    """
    guild = await repo.fetch(auth.guild_id)
    features = await repo.fetch_features(auth.guild_id)
    channels = await repo.fetch_channels(auth.guild_id)

    return guilds.GuildOut(
        **guild.model_dump(),
        features=[guilds.FeatureOut(**f.model_dump()) for f in features ],
        channels=[guilds.ChannelOut(**c.model_dump()) for c in channels],
    )


@guilds_router.patch('/me')
@guilds_router.put('/me')
async def partial_update_guild(
        body: guilds.GuildUpdate,
        auth: TokenPayload = Security(get_guild_client, scopes=['guilds:write']),
) -> guilds.GuildOut:
    """
    Partially updates guild information. Both `PATCH` and `PUT` work the same way.
    """
    guild = await repo.update(auth.guild_id, body)
    features = await repo.fetch_features(auth.guild_id)
    channels = await repo.fetch_channels(auth.guild_id)

    return guilds.GuildOut(
        **guild.model_dump(),
        features=[guilds.FeatureOut(**f.model_dump()) for f in features ],
        channels=[guilds.ChannelOut(**c.model_dump()) for c in channels],
    )


@guilds_router.get('/me/features', deprecated=True)
async def get_features(
        auth: TokenPayload = Security(get_guild_client, scopes=['guilds:read']),
) -> list[guilds.FeatureOut]:
    """Returns a list of features enabled for the authenticated guild."""
    features = await repo.fetch_features(auth.guild_id)

    return [guilds.FeatureOut(**f.model_dump()) for f in features]


@guilds_router.get('/me/channels', deprecated=True)
async def get_channels(
        auth: TokenPayload = Security(get_guild_client, scopes=['guilds:read']),
) -> list[guilds.ChannelOut]:
    """
    This returns a list of the guild's channels
    """
    channels = await repo.fetch_channels(auth.guild_id)

    return [guilds.ChannelOut(**c.model_dump()) for c in channels]


@guilds_router.get('/me/playtime')
async def get_guild_playtime(
        auth: TokenPayload = Security(get_guild_client, scopes=['guilds:read']),
) -> guilds.GuildPlaytimeAnalysis:
    """
    This returns the guild's playtime summary. Playtime is in seconds.

    > [!warning]
    > The playtime analysis is currently a work in progress, and may not have all data.
    > Data shape might change in the future.
    """
    guild_analysis = await repo.fetch_playtime_analysis(auth.guild_id)

    return guild_analysis


@guilds_router.get('/me/online')
async def get_online_members(
        auth: TokenPayload = Security(get_guild_client, scopes=['guilds:read']),
) -> list[guilds.OnlineMember]:
    """
    Returns a list of all players currently connected to Geode.
    """
    players = await repo.fetch_online_members(auth.guild_id)

    return [guilds.OnlineMember(**p.model_dump()) for p in players]


@guilds_router.post('/me/connection', status_code=status.HTTP_201_CREATED)
async def create_connection(
        body: guilds.ConnectionIn,
        auth: TokenPayload = Security(get_guild_client, scopes=['guilds:write', 'guilds.members:write']),
) -> guilds.ConnectionOut:
    """
    Creates a connection event.
    """
    try:
        user_playtime = await playtime.PlaytimeSummary.fetch(db, body.thorny_id)

        if (body.type == 'connect' and user_playtime.session) or (body.type == 'disconnect' and not user_playtime.session):
            body.ignored = True
    except HTTPException:
        # In case the playtime summary fetch fails, we still want to create the connection
        pass

    conn = await repo.create_connection(body)

    return ConnectionOut(**conn.model_dump())
