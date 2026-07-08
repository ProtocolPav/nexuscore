from src.errors import BadRequest, NotFound
from src.models.users.profile import ProfileOut, ProfileUpdate
from src.models.users.user import UserDB, UserOut, UserIn, UserUpdate

from src.repositories.user import UserRepository


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def _to_out(self, user: UserDB) -> UserOut:
        profile = await self.get_profile(user.guild_id, user.thorny_id)

        return UserOut(
            **user.model_dump(),
            profile=profile
        )

    async def new(self, guild_id: int, model: UserIn) -> UserOut:
        usr_db = await self.user_repo.create(guild_id, model)
        return await self._to_out(usr_db)

    async def get(self, guild_id: int, thorny_id: int) -> UserOut:
        usr_db = await self.user_repo.fetch(guild_id, thorny_id)
        return await self._to_out(usr_db)

    async def update(self, guild_id: int, thorny_id: int, model: UserUpdate) -> UserOut:
        usr_db = await self.user_repo.update(guild_id, thorny_id, model)
        return await self._to_out(usr_db)

    async def lookup(
            self,
            guild_id: int,
            gamertag: str | None = None,
            whitelist: str | None = None,
            discord_id: int | None = None,
    ) -> UserOut:
        provided = sum(x is not None for x in [gamertag, whitelist, discord_id])
        if provided == 0:
            raise BadRequest('Must provide one of: gamertag, whitelist, discord_id')
        if provided > 1:
            raise BadRequest('Provide only one of: gamertag, whitelist, discord_id')

        if gamertag is not None:
            usr_db = await self.user_repo.fetch_by_gamertag(guild_id, gamertag)
        elif whitelist is not None:
            usr_db = await self.user_repo.fetch_by_whitelist(guild_id, whitelist)
        else:
            usr_db = await self.user_repo.fetch_by_discord_id(guild_id, discord_id)

        if usr_db is None:
            raise NotFound('User')

        return await self._to_out(usr_db)

    async def get_profile(self, guild_id: int, thorny_id: int) -> ProfileOut:
        profile_db = await self.user_repo.fetch_profile(guild_id, thorny_id)
        return ProfileOut(**profile_db.model_dump())

    async def update_profile(self, guild_id: int, thorny_id: int, model: ProfileUpdate) -> ProfileOut:
        profile_db = await self.user_repo.update_profile(guild_id, thorny_id, model)
        return ProfileOut(**profile_db.model_dump())