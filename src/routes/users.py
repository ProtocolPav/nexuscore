from fastapi import APIRouter, HTTPException

from src.dependencies.database import db
from src.models.users import user, profile, playtime, interactions

users = APIRouter(prefix='/users', tags=['Users'])


@users.post('/', status_code=201)
async def create_user(body: user.UserCreateModel) -> user.UserModel:
    """
    Creates a user based on the discord UserID and GuildID provided.
    If a user with these ID's already exists, it returns a 400.
    """
    if await user.UserModel.get_thorny_id(db, body.guild_id, body.user_id):
        raise HTTPException(status_code=400, detail='This user already exists')
    else:
        thorny_id = await user.UserModel.create(db, body)
        user_model = await user.UserModel.fetch(db, thorny_id)

    return user_model


@users.get('/{thorny_id}')
async def get_user(thorny_id: int) -> user.UserModel:
    """
    This returns the User object
    """
    return await user.UserModel.fetch(db, thorny_id)


@users.put('/{thorny_id}', name='Update User')
@users.patch('/{thorny_id}', name='Update User')
async def update_user(thorny_id: int, body: user.UserUpdateModel) -> user.UserModel:
    """
    This updates a user. All fields are optional, meaning you may
    set a field to `null` to not update it.

    `whitelist` does not apply to this. If you set it to null, it will become null.
    """
    model = await user.UserModel.fetch(db, thorny_id)
    await model.update(db, body)

    return model


@users.get('/{thorny_id}/profile', name='Get User Profile', deprecated=True)
async def get_profile(thorny_id: int) -> profile.ProfileModel:
    """
    This returns the user's profile.

    Will be removed in a future release. Use `/users/{thorny_id}` instead.
    """
    return await profile.ProfileModel.fetch(db, thorny_id)


@users.put('/{thorny_id}/profile')
@users.patch('/{thorny_id}/profile')
async def update_profile(thorny_id: int, body: profile.ProfileUpdateModel) -> profile.ProfileModel:
    """
    This updates a user's profile. Anything set to NULL will be ignored.
    """
    model = await profile.ProfileModel.fetch(db, thorny_id)
    await model.update(db, body)

    return model


@users.get('/{thorny_id}/playtime', name='Get User Playtime')
async def get_playtime(thorny_id: int) -> playtime.PlaytimeSummary:
    """
    This returns the user's playtime. Note that all playtime is in seconds!
    """
    return await playtime.PlaytimeSummary.fetch(db, thorny_id)


@users.get('/{thorny_id}/interactions', name='Get User Interactions')
async def get_interactions(thorny_id: int) -> interactions.InteractionSummary:
    """
    This returns the user's interaction summary.
    This may take long to process, so ensure you have the proper timeouts set.
    """
    return await interactions.InteractionSummary.fetch(db, thorny_id)


@users.get('/guild/{guild_id}/{id}', name='Get User by Gamertag or Discord ID')
async def user_by_id(guild_id: int, id: str) -> user.UserModel:
    """
    This acts the same as `Get by ThornyID`.
    This will check either the whitelisted gamertag or the user-entered gamertag.
    If the ID is numerical, it will check the user's Discord ID.
    """
    try:
        thorny_id = await user.UserModel.get_thorny_id(db, guild_id, user_id=int(id))
    except TypeError:
        thorny_id = await user.UserModel.get_thorny_id(db, guild_id, gamertag=id.replace('%20', ' '))

    user_view = await user.UserModel.fetch(db, thorny_id)

    return user_view
