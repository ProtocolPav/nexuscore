from src.models.events.event import EventDB, EventIn, EventOut, EventUpdate
from src.repositories.event import EventRepository


class EventService:
    def __init__(self, event_repo: EventRepository):
        self.event_repo = event_repo

    async def _to_out(self, event: EventDB) -> EventOut:
        return EventOut(**event.model_dump())

    async def get(self, pin_id: int) -> EventOut:
        event_db = await self.event_repo.fetch(pin_id)
        return await self._to_out(event_db)

    async def get_all(self) -> list[EventOut]:
        events_db = await self.event_repo.fetch_all()
        return [await self._to_out(p) for p in events_db]

    async def new(self, guild_id: int, model: EventIn) -> EventOut:
        event_db = await self.event_repo.create(guild_id, model)
        return await self._to_out(event_db)

    async def update(self, pin_id: int, model: EventUpdate) -> EventOut:
        event_db = await self.event_repo.update(pin_id, model)
        return await self._to_out(event_db)