import asyncpg
from src.dependencies.database import Database
from src.errors import AlreadyExists, NotFound
from src.models.quests.quest import QuestDB, QuestIn, QuestUpdate


class QuestRepository:
    def __init__(self, db: Database):
        self.db = db

    async def fetch(self, quest_id: int) -> QuestDB:
        data = await self.db.pool.fetchrow("""
            SELECT * FROM quests_v3.quest
            WHERE quest_id = $1
        """,quest_id)

        if not data:
            raise NotFound("Quest")

        return QuestDB.model_validate(dict(data))

    async def create(self, model: QuestIn) -> QuestDB:
        try:
            data = await self.db.pool.fetchrow("""
                WITH quest_table AS (
                    INSERT INTO quests_v3.quest(
                        start_time, 
                        end_time, 
                        title, 
                        description,
                        created_by,
                        tags,
                        quest_type
                    )
                    VALUES($1, $2, $3, $4, $5, $6, $7)

                    RETURNING *
                )
                SELECT * from quest_table
            """, model.start_time, model.end_time, model.title, model.description, model.created_by,
                                               model.tags, model.quest_type)
        except asyncpg.UniqueViolationError:
            raise AlreadyExists("Quest")

        return QuestDB.model_validate(dict(data))

    async def update(self, quest_id: int, model: QuestUpdate) -> QuestDB:
        quest = await self.fetch(quest_id)

        updated = quest.model_copy(update=model.model_dump(exclude_none=True))

        await self.db.pool.execute("""
            UPDATE quests_v3.quest
            SET start_time = $1,
                end_time = $2,
                title = $3,
                description = $4,
                created_by = $5,
                tags = $6,
                quest_type = $7
            WHERE quest_id = $8
        """,updated.start_time, updated.end_time, updated.title, updated.description, updated.created_by,
                                   updated.tags, updated.quest_type, updated.quest_id)

        return updated