from opentelemetry import trace

from src.models.worlds.world import WorldDB, WorldOut, WorldUpdate

from src.repositories.world import WorldRepository
from src.utils.tracing import traced


class WorldService:
    def __init__(self, world_repo: WorldRepository):
        self.world_repo = world_repo

    async def _to_out(self, world: WorldDB) -> WorldOut:
        return WorldOut(**world.model_dump())

    @traced
    async def get(self, guild_id: int) -> WorldOut:
        span = trace.get_current_span()
        span.set_attribute("guild.id", guild_id)

        world_db = await self.world_repo.fetch(guild_id)
        return await self._to_out(world_db)

    @traced
    async def update(self, guild_id: int, model: WorldUpdate) -> WorldOut:
        span = trace.get_current_span()
        span.set_attribute("guild.id", guild_id)

        world_db = await self.world_repo.update(guild_id, model)
        return await self._to_out(world_db)