from fastapi import APIRouter, Depends, Security
from starlette import status

from src.errors import BadRequest

from src.dependencies.auth import Scope, get_guild_client
from src.dependencies.repositories import get_user_repo
from src.dependencies.database import db

from src.models.auth import TokenPayload
from src.models.users import user, playtime, interactions
from src.models.users.profile import ProfileOut, ProfileUpdate

from src.repositories.user import UserRepository

members_router = APIRouter(prefix='/guilds/me/users', tags=['Users'])


@members_router.post('', status_code=status.HTTP_201_CREATED)
async def create_user(
        body: user.UserIn,
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_MEMBERS_WRITE]),
        repo: UserRepository = Depends(get_user_repo),
) -> user.UserOut:
    """
    Creates a new user in the guild.
    """
    usr = await repo.create(auth.guild_id, body)
    profile = await repo.fetch_profile(auth.guild_id, usr.thorny_id)

    return user.UserOut(**usr.model_dump(), profile=ProfileOut(**profile.model_dump()))


@members_router.get('/lookup')
async def lookup_user(
        gamertag: str = None,
        whitelist: str = None,
        discord_id: int = None,
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_MEMBERS_READ]),
        repo: UserRepository = Depends(get_user_repo),
) -> user.UserOut:
    """
    Looks up a guild member by gamertag, whitelisted gamertag, or Discord ID.
    Exactly one parameter must be provided.
    """
    if gamertag:
        usr = await repo.fetch_by_gamertag(auth.guild_id, gamertag)
    elif whitelist:
        usr = await repo.fetch_by_whitelist(auth.guild_id, whitelist)
    elif discord_id:
        usr = await repo.fetch_by_discord_id(auth.guild_id, discord_id)
    else:
        raise BadRequest('Must provide one of: gamertag, whitelist, discord_id')

    profile = await repo.fetch_profile(auth.guild_id, usr.thorny_id)

    return user.UserOut(**usr.model_dump(), profile=ProfileOut(**profile.model_dump()))


@members_router.get('/{thorny_id}')
async def get_user(
        thorny_id: int,
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_MEMBERS_READ]),
        repo: UserRepository = Depends(get_user_repo),
) -> user.UserOut:
    """
    This returns the User object
    """
    usr = await repo.fetch(auth.guild_id, thorny_id)
    profile = await repo.fetch_profile(auth.guild_id, thorny_id)

    return user.UserOut(**usr.model_dump(), profile=ProfileOut(**profile.model_dump()))


@members_router.put('/{thorny_id}')
@members_router.patch('/{thorny_id}')
async def partial_update_user(
        thorny_id: int,
        body: user.UserUpdate,
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_MEMBERS_WRITE]),
        repo: UserRepository = Depends(get_user_repo),
) -> user.UserOut:
    """
    This updates a user. All fields are optional, meaning you may
    set a field to `null` to not update it.

    `whitelist` does not apply to this. If you set it to null, it will become null.
    """
    usr = await repo.update(auth.guild_id, thorny_id, body)
    profile = await repo.fetch_profile(auth.guild_id, thorny_id)

    return user.UserOut(**usr.model_dump(), profile=ProfileOut(**profile.model_dump()))


@members_router.get('/{thorny_id}/profile', name='Get User Profile', deprecated=True)
async def get_profile(
        thorny_id: int,
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_MEMBERS_READ]),
        repo: UserRepository = Depends(get_user_repo),
) -> ProfileOut:
    """
    This returns the user's profile.

    Will be removed in a future release. Use `/users/{thorny_id}` instead.
    """
    profile = await repo.fetch_profile(auth.guild_id, thorny_id)

    return ProfileOut(**profile.model_dump())


@members_router.put('/{thorny_id}/profile')
@members_router.patch('/{thorny_id}/profile')
async def update_profile(
        thorny_id: int,
        body: ProfileUpdate,
        auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_MEMBERS_WRITE]),
        repo: UserRepository = Depends(get_user_repo),
) -> ProfileOut:
    """
    This updates a user's profile. Anything set to NULL will be ignored.
    """
    profile = await repo.update_profile(auth.guild_id, thorny_id, body)

    return ProfileOut(**profile.model_dump())


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
