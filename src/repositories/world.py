from src.dependencies.database import Database
from src.errors import AlreadyExists, NotFound
from src.models.worlds.world import WorldDB, WorldUpdate


class WorldRepository:
    def __init__(self, db: Database):
        self.db = db

    async def fetch(self, guild_id: int) -> WorldDB:
        data = await self.db.pool.fetchrow("""
            SELECT * FROM server.world
            WHERE guild_id = $1
        """,guild_id)

        if not data:
            raise NotFound("World")

        return WorldDB.model_validate(dict(data))

    async def update(self, guild_id: int, model: WorldUpdate) -> WorldDB:
        world = await self.fetch(guild_id)

        updated = world.model_copy(update=model.model_dump(exclude_none=True))
        # TODO: Whitelist currently cannot be set to null.

        await self.db.pool.execute("""
            UPDATE server.world
            SET overworld_border = $1,
                nether_border = $2,
                end_border = $3
            WHERE guild_id = $4
        """,updated.overworld_border, updated.nether_border, updated.end_border, guild_id)

        return updated