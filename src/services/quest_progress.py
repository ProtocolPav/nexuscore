import asyncio
from datetime import datetime

from src.models.quests.objective import ObjectiveDB, ObjectiveOut
from src.models.quests.objective_customization.progress import CUSTOMIZATION_TYPE_MAP, CustomizationProgress
from src.models.quests.objective_progress import ObjectiveProgressIn, ObjectiveProgressOut
from src.models.quests.objective_targets.progress import TARGET_TYPE_MAP
from src.models.quests.quest import QuestDB, QuestIn, QuestOut, QuestQuery, QuestUpdate
from src.models.quests.quest_progress import QuestProgressDB, QuestProgressIn, QuestProgressOut, QuestProgressUpdate
from src.models.quests.reward import RewardOut
from src.models.users.profile import ProfileOut
from src.models.users.user import UserOut
from src.repositories.quests.objective import ObjectiveRepository
from src.repositories.quests.objective_progress import ObjectiveProgressRepository
from src.repositories.quests.quest import QuestRepository
from src.repositories.quests.quest_progress import QuestProgressRepository
from src.repositories.quests.reward import RewardRepository
from src.repositories.user import UserRepository


class QuestProgressService:
    def __init__(
            self,
            quest_repo: QuestRepository,
            objective_repo: ObjectiveRepository,
            quest_progress_repo: QuestProgressRepository,
            objective_progress_repo: ObjectiveProgressRepository,
    ):
        self.quest_repo = quest_repo
        self.objective_repo = objective_repo
        self.quest_progress_repo = quest_progress_repo
        self.objective_progress_repo = objective_progress_repo

    async def _to_out(self, quest: QuestProgressDB) -> QuestProgressOut:
        objectives_db = await self.objective_progress_repo.fetch_all(quest.progress_id)

        return QuestProgressOut(
            **quest.model_dump(),
            objectives=[ObjectiveProgressOut(**o.model_dump()) for o in objectives_db]
        )

    @staticmethod
    async def _generate_target_progress(objective: ObjectiveDB):
        target_progress = []
        for target in objective.targets:
            target_model = TARGET_TYPE_MAP.get(target.target_type, None)

            if target_model:
                target_progress.append(target_model(target_uuid=target.target_uuid, target_type=target.target_type))

        return target_progress

    @staticmethod
    async def _generate_customization_progress(objective: ObjectiveDB):
        customization_progress = {}
        for customization in objective.customizations.model_dump().keys():
            customization_model = CUSTOMIZATION_TYPE_MAP.get(customization, None)

            if objective.customizations.model_dump()[customization] is not None and customization_model:
                customization_progress[customization] = customization_model()

        return CustomizationProgress(**customization_progress)

    async def get(self, progress_id: int) -> QuestProgressOut:
        quest_db = await self.quest_progress_repo.fetch(progress_id)
        return await self._to_out(quest_db)

    async def get_active(self, thorny_id: int) -> QuestProgressOut:
        quest_db = await self.quest_progress_repo.fetch_active(thorny_id)
        return await self._to_out(quest_db)

    async def get_all_users_progress(self, thorny_id: int) -> list[QuestProgressOut]:
        quests_db = await self.quest_progress_repo.fetch_all_users_progress(thorny_id)

        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(self._to_out(q)) for q in quests_db]

        return [t.result() for t in tasks]

    async def get_all_quests_progress(self, quest_id: int) -> list[QuestProgressOut]:
        quests_db = await self.quest_progress_repo.fetch_all_quests_progress(quest_id)

        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(self._to_out(q)) for q in quests_db]

        return [t.result() for t in tasks]

    async def mark_failed(self, thorny_id: int) -> QuestProgressOut:
        quest_progress = await self.get_active(thorny_id)

        quest_update = QuestProgressUpdate(**{
            "status": "failed",
            "end_time": datetime.now(),
            "objectives": [
                {
                    "objective_id": o.objective_id,
                    "status": "failed",
                    "end_time": datetime.now()
                } for o in quest_progress.objectives if o.status in ['active', 'pending']
            ]
        })

        return await self.update(quest_progress.progress_id, quest_update)

    async def new(self, model: QuestProgressIn) -> QuestProgressOut:
        objectives_db = await self.objective_repo.fetch_all(model.quest_id)

        async with self.quest_repo.db.get_transaction() as conn:
            quest_progress_db = await self.quest_progress_repo.create(model, conn)

            for o in objectives_db:
                await self.objective_progress_repo.create(
                    quest_progress_db.progress_id,
                    o.objective_id,
                    ObjectiveProgressIn(
                        target_progress=await self._generate_target_progress(o),
                        customization_progress=await self._generate_customization_progress(o)
                    ),
                    conn
                )

        quest_update = QuestProgressUpdate(**{
            "objectives": [
                {
                    "objective_id": objectives_db[0].objective_id,
                    "status": "active",
                    "start_time": datetime.now()
                }
            ]
        })

        await self.update(quest_progress_db.progress_id, quest_update)

        return await self._to_out(quest_progress_db)

    async def update(self, progress_id: int, model: QuestProgressUpdate) -> QuestProgressOut:
        async with self.quest_repo.db.get_transaction() as conn:
            quest_progress_db = await self.quest_progress_repo.update(progress_id, model, conn)

            for o in model.objectives:
                if o.objective_id:
                    await self.objective_progress_repo.update(
                        quest_progress_db.progress_id,
                        o.objective_id,
                        o,
                        conn
                    )
                else:
                    await self.objective_repo.create(quest_progress_db.quest_id, o, conn)

        return await self._to_out(quest_progress_db)