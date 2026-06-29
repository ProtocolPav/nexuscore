from src.models.projects.pin import PinDB, PinIn, PinOut, PinUpdate

from src.repositories.pin import PinRepository


class PinService:
    def __init__(self, pin_repo: PinRepository):
        self.pin_repo = pin_repo

    async def _to_out(self, pin: PinDB) -> PinOut:
        return PinOut(**pin.model_dump())

    async def get(self, pin_id: int) -> PinOut:
        pin_db = await self.pin_repo.fetch(pin_id)
        return await self._to_out(pin_db)

    async def get_all(self) -> list[PinOut]:
        pins_db = await self.pin_repo.fetch_all()
        return [await self._to_out(p) for p in pins_db]

    async def new(self, model: PinIn) -> PinOut:
        pin_db = await self.pin_repo.create(model)
        return await self._to_out(pin_db)

    async def update(self, pin_id: int, model: PinUpdate) -> PinOut:
        pin_db = await self.pin_repo.update(pin_id, model)
        return await self._to_out(pin_db)