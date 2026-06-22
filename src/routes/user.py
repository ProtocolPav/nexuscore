from fastapi import APIRouter, Depends, Security
from starlette import status

from src.dependencies.auth import get_guild_client
from src.dependencies.services import get_user_service
from src.dependencies.database import db

from src.models.auth import TokenPayload, Scope
from src.models.users import user, playtime, interactions
from src.models.users.profile import ProfileOut, ProfileUpdate

from src.services.user import UserService

members_router = APIRouter(prefix='/guilds/me/users', tags=['Users'])


@members_router.post('', status_code=status.HTTP_201_CREATED)
async def create_user(
        body: user.UserIn,
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_MEMBERS_WRITE]),
        service: UserService = Depends(get_user_service),
) -> user.UserOut:
    """
    Creates a new user in the guild.
    """
    return await service.new(auth.guild_id, body)


@members_router.get('/lookup')
async def lookup_user(
        gamertag: str = None,
        whitelist: str = None,
        discord_id: int = None,
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_MEMBERS_READ]),
        service: UserService = Depends(get_user_service),
) -> user.UserOut:
    """
    Looks up a guild member by gamertag, whitelisted gamertag, or Discord ID.
    Exactly one parameter must be provided.
    """
    return await service.lookup(auth.guild_id, gamertag, whitelist, discord_id)


@members_router.get('/{thorny_id}')
async def get_user(
        thorny_id: int,
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_MEMBERS_READ]),
        service: UserService = Depends(get_user_service),
) -> user.UserOut:
    """
    This returns the User object
    """
    return await service.get(auth.guild_id, thorny_id)


@members_router.put('/{thorny_id}')
@members_router.patch('/{thorny_id}')
async def partial_update_user(
        thorny_id: int,
        body: user.UserUpdate,
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_MEMBERS_WRITE]),
        service: UserService = Depends(get_user_service),
) -> user.UserOut:
    """
    This updates a user. All fields are optional, meaning you may
    set a field to `null` to not update it.

    `whitelist` does not apply to this. If you set it to null, it will become null.
    """
    return await service.update(auth.guild_id, thorny_id, body)


@members_router.get('/{thorny_id}/profile', name='Get User Profile', deprecated=True)
async def get_profile(
        thorny_id: int,
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_MEMBERS_READ]),
        service: UserService = Depends(get_user_service),
) -> ProfileOut:
    """
    This returns the user's profile.

    Will be removed in a future release. Use `/users/{thorny_id}` instead.
    """
    return await service.get_profile(auth.guild_id, thorny_id)


@members_router.put('/{thorny_id}/profile')
@members_router.patch('/{thorny_id}/profile')
async def partial_update_profile(
        thorny_id: int,
        body: ProfileUpdate,
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_MEMBERS_WRITE]),
        service: UserService = Depends(get_user_service),
) -> ProfileOut:
    """
    This updates a user's profile. Anything set to NULL will be ignored.
    """
    return await service.update_profile(auth.guild_id, thorny_id, body)


@members_router.get('/{thorny_id}/playtime', name='Get User Playtime')
async def get_playtime(thorny_id: int) -> playtime.PlaytimeSummary:
    """
    This returns the user's playtime. Note that all playtime is in seconds!
    """
    return await playtime.PlaytimeSummary.fetch(db, thorny_id)


@members_router.get('/{thorny_id}/interactions', name='Get User Interactions')
async def get_interactions(thorny_id: int) -> interactions.InteractionSummary:
    """
    This returns the user's interaction summary.
    This may take long to process, so ensure you have the proper timeouts set.
    """
    return await interactions.InteractionSummary.fetch(db, thorny_id)
