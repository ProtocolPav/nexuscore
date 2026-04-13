import asyncpg
from src.dependencies.database import Database
from src.errors import AlreadyExists, NotFound

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
                )
                SELECT * FROM user_table
            """, guild_id, model.user_id, model.username)
        except asyncpg.UniqueViolationError:
            raise AlreadyExists("User")

        return UserDB.model_validate(dict(data))

    async def update(self, guild_id: int, thorny_id: int, model: UserUpdate) -> UserDB:
        user = await self.fetch(guild_id, thorny_id)

        updated = user.model_copy(update=model.model_dump(exclude_none=True))

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