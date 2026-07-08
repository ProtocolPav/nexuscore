import asyncpg
from src.dependencies.database import Database
from src.errors import AlreadyExists, NotFound
from src.models.users.profile import ProfileDB, ProfileUpdate

from src.models.users.user import UserDB, UserIn, UserUpdate


class UserRepository:
    def __init__(self, db: Database):
        self.db = db

    async def fetch(self, guild_id: int, thorny_id: int) -> UserDB:
        data = await self.db.pool.fetchrow("""
            SELECT * FROM users.user
            WHERE guild_id = $1
            AND thorny_id = $2
        """,guild_id, thorny_id)

        if not data:
            raise NotFound("User")

        return UserDB.model_validate(dict(data))

    async def create(self, guild_id: int, model: UserIn) -> UserDB:
        try:
            data = await self.db.pool.fetchrow("""
                WITH user_table AS (
                    INSERT INTO users.user(guild_id, user_id, username)
                    VALUES ($1, $2, $3)
                    RETURNING *
                ),
                profile_table AS (
                    INSERT INTO users.profile(thorny_id)
                    VALUES (user_table.thorny_id)
                )
                SELECT * FROM user_table
            """, guild_id, model.user_id, model.username)
        except asyncpg.UniqueViolationError:
            raise AlreadyExists("User")

        return UserDB.model_validate(dict(data))

    async def update(self, guild_id: int, thorny_id: int, model: UserUpdate) -> UserDB:
        user = await self.fetch(guild_id, thorny_id)

        updated = user.model_copy(update=model.model_dump(exclude_none=True))
        # TODO: Whitelist currently cannot be set to null.

        await self.db.pool.execute("""
           UPDATE users.user
           SET username = $1,
               birthday = $2,
               balance = $3,
               active = $4,
               role = $5,
               patron = $6,
               level = $7,
               xp = $8,
               required_xp = $9,
               last_message = $10,
               gamertag = $11,
               whitelist = $12,
               location = $13,
               dimension = $14,
               hidden = $15,
               xuid = $16
           WHERE thorny_id = $17
        """,updated.username, updated.birthday, updated.balance,
                   updated.active, updated.role, updated.patron,
                   updated.level, updated.xp, updated.required_xp,
                   updated.last_message, updated.gamertag, updated.whitelist,
                   updated.location, updated.dimension, updated.hidden,
                   updated.xuid, updated.thorny_id)

        return updated

    async def fetch_by_gamertag(self, guild_id: int, gamertag: str) -> UserDB:
        data = await self.db.pool.fetchrow("""
            SELECT * FROM users.user
            WHERE guild_id = $1
            AND gamertag = $2
        """,guild_id, gamertag)

        if not data:
            raise NotFound("User")

        return UserDB.model_validate(dict(data))

    async def fetch_by_whitelist(self, guild_id: int, whitelist: str) -> UserDB:
        data = await self.db.pool.fetchrow("""
            SELECT * FROM users.user
            WHERE guild_id = $1
            AND whitelist = $2
        """,guild_id, whitelist)

        if not data:
            raise NotFound("User")

        return UserDB.model_validate(dict(data))

    async def fetch_by_discord_id(self, guild_id: int, discord_id: int) -> UserDB:
        data = await self.db.pool.fetchrow("""
            SELECT * FROM users.user
            WHERE guild_id = $1
            AND user_id = $2
        """,guild_id, discord_id)

        if not data:
            raise NotFound("User")

        return UserDB.model_validate(dict(data))

    async def fetch_profile(self, guild_id: int, thorny_id: int) -> ProfileDB:
        data = await self.db.pool.fetchrow("""
            SELECT * FROM users.user
            INNER JOIN users.profile ON users.user.thorny_id = users.profile.thorny_id
            WHERE guild_id = $1
            AND users.user.thorny_id = $2
        """,guild_id, thorny_id)

        if not data:
            raise NotFound("Profile")

        return ProfileDB.model_validate(dict(data))

    async def update_profile(self, guild_id: int, thorny_id: int, model: ProfileUpdate) -> ProfileDB:
        profile = await self.fetch_profile(guild_id, thorny_id)

        updated = profile.model_copy(update=model.model_dump(exclude_none=True))

        await self.db.pool.execute("""
           UPDATE users.profile
           SET slogan = $1,
               aboutme = $2,
               lore = $3,
               character_name = $4,
               character_age = $5,
               character_race = $6,
               character_role = $7,
               character_origin = $8,
               character_beliefs = $9,
               agility = $10,
               valor = $11,
               strength = $12,
               charisma = $13,
               creativity = $14,
               ingenuity = $15
           WHERE thorny_id = $16
        """,updated.slogan, updated.aboutme, updated.lore, updated.character_name,
                   updated.character_age, updated.character_race, updated.character_role, updated.character_origin,
                   updated.character_beliefs, updated.agility, updated.valor, updated.strength, updated.charisma,
                   updated.creativity, updated.ingenuity, updated.thorny_id)

        return updated