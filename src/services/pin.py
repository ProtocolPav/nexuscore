from src.models.projects.pin import PinDB, PinIn, PinOut, PinUpdate

from src.repositories.pin import PinRepository
from src.utils.tracing import traced

from opentelemetry import trace


class PinService:
    def __init__(self, pin_repo: PinRepository):
        self.pin_repo = pin_repo

    async def _to_out(self, pin: PinDB) -> PinOut:
        return PinOut(**pin.model_dump())

    @traced
    async def get(self, pin_id: int) -> PinOut:
        span = trace.get_current_span()
        span.set_attribute("pin.id", pin_id)

        pin_db = await self.pin_repo.fetch(pin_id)
        return await self._to_out(pin_db)

    @traced
    async def get_all(self) -> list[PinOut]:
        pins_db = await self.pin_repo.fetch_all()
        return [await self._to_out(p) for p in pins_db]

    @traced
    async def new(self, model: PinIn) -> PinOut:
        pin_db = await self.pin_repo.create(model)
        return await self._to_out(pin_db)

    @traced
    async def update(self, pin_id: int, model: PinUpdate) -> PinOut:
        span = trace.get_current_span()
        span.set_attribute("pin.id", pin_id)

        pin_db = await self.pin_repo.update(pin_id, model)
        return await self._to_out(pin_db)