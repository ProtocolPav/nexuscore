import asyncio

from src.models.quests.objective import ObjectiveOut
from src.models.quests.quest import QuestDB, QuestIn, QuestOut, QuestQuery
from src.models.users.profile import ProfileOut
from src.models.users.user import UserOut
from src.repositories.objective import ObjectiveRepository
from src.repositories.quest import QuestRepository
from src.repositories.user import UserRepository


class QuestService:
    def __init__(self, quest_repo: QuestRepository, objective_repo: ObjectiveRepository, user_repo: UserRepository):
        self.quest_repo = quest_repo
        self.objective_repo = objective_repo
        self.user_repo = user_repo

    async def _to_out(self, quest: QuestDB) -> QuestOut:
        creator_db, profile_db, objectives_db = await asyncio.gather(
            self.user_repo.fetch(quest.guild_id, quest.created_by),
            self.user_repo.fetch_profile(quest.guild_id, quest.created_by),
            self.objective_repo.fetch_all(quest.quest_id)
        )

        return QuestOut(
            **quest.model_dump(exclude={"created_by"}),
            created_by=UserOut(
                **creator_db.model_dump(),
                profile=ProfileOut(**profile_db.model_dump())
            ),
            objectives=[ObjectiveOut(**o.model_dump()) for o in objectives_db]
        )

    async def get(self, guild_id: int, quest_id: int) -> QuestOut:
        quest_db = await self.quest_repo.fetch(quest_id, guild_id)
        return await self._to_out(quest_db)

    async def get_all(self, guild_id: int, query: QuestQuery) -> list[QuestOut]:
        quests_db = await self.quest_repo.fetch_all(guild_id, query)

        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(self._to_out(q)) for q in quests_db]

        return [t.result() for t in tasks]

    async def new(self, guild_id: int, model: QuestIn) -> QuestOut:
        async with self.quest_repo.db.get_transaction() as conn:
            quest_db = await self.quest_repo.create(guild_id, model, conn)
            [await self.objective_repo.create(quest_db.quest_id, o, conn) for o in model.objectives]
            return await self._to_out(quest_db)