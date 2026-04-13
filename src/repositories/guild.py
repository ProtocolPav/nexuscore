import asyncpg
from src.dependencies.database import Database
from src.errors import AlreadyExists, NotFound
from src.models.guilds.features import FeatureDB
from src.models.guilds.guild import GuildDB, GuildIn, GuildUpdate


class GuildRepository:
    def __init__(self, db: Database):
        self.db = db

    async def fetch(self, guild_id: int) -> GuildDB:
        data = await self.db.pool.fetchrow("""
            SELECT * FROM guilds.guild 
            WHERE guild_id = $1
        """,guild_id)

        if not data:
            raise NotFound("Guild")

        return GuildDB.model_validate(dict(data))

    async def fetch_features(self, guild_id: int) -> list[FeatureDB]:
        data = await self.db.pool.fetch("""
            SELECT * FROM guilds.features
            WHERE guild_id = $1
        """, guild_id)

        return [FeatureDB.model_validate(dict(row)) for row in data]

    async def create(self, model: GuildIn) -> GuildDB:
        try:
            data = await self.db.pool.fetchrow("""
                WITH guild_table AS (
                    INSERT INTO guilds.guild(guild_id, name)
                    VALUES ($1, $2)
                    RETURNING *
                ),
                features_table AS (
                    INSERT INTO guilds.features(guild_id, feature)
                        VALUES ($1, 'profile'), ($1, 'levels'), ($1, 'basic')
                )
                SELECT * FROM guild_table
            """, model.guild_id, model.name)
        except asyncpg.UniqueViolationError:
            raise AlreadyExists("Guild")

        return GuildDB.model_validate(dict(data))

    async def update(self, guild_id: int, model: GuildUpdate) -> GuildDB:
        guild = await self.fetch(guild_id)

        updated = guild.model_copy(update=model.model_dump(exclude_none=True))

        await self.db.pool.execute("""
            UPDATE guilds.guild
            SET name=$2, 
                currency_name=$3, 
                currency_emoji=$4,
                level_up_message=$5, 
                join_message=$6, 
                leave_message=$7,
                xp_multiplier=$8, 
                active=$9
            WHERE guild_id = $1
        """,updated.guild_id, updated.name, updated.currency_name,
                  updated.currency_emoji, updated.level_up_message, updated.join_message,
                  updated.leave_message, updated.xp_multiplier, updated.active)

        return updated