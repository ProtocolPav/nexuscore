from typing import Optional

from src.database import Database
from src.models.user import UserModel, ProfileModel, PlaytimeSummary, UserQuestModel, UserObjectiveModel
from src.views.quest import QuestView

from pydantic import BaseModel

from sanic_ext import openapi


class UserView(BaseModel):
    user: UserModel
    profile: ProfileModel
    playtime: PlaytimeSummary

    @classmethod
    async def get_thorny_id(cls, db: Database, guild_id: int, user_id: int = None, gamertag: str = None):
        if gamertag and guild_id:
            data = await db.pool.fetchrow("""
                                           SELECT thorny_id FROM users.user
                                           WHERE guild_id = $1
                                           AND (whitelist = $2 OR gamertag = $2)
                                           """,
                                          guild_id, gamertag)
        elif guild_id and user_id:
            data = await db.pool.fetchrow("""
                                           SELECT thorny_id FROM users.user
                                           WHERE guild_id = $1
                                           AND user_id = $2
                                           """,
                                          guild_id, user_id)
        else:
            return -1

        return data['thorny_id'] if data else None

    @classmethod
    async def build(cls, db: Database, thorny_id: int):
        user = await UserModel.fetch(db, thorny_id)
        profile = await ProfileModel.fetch(db, thorny_id)
        playtime = await PlaytimeSummary.fetch(db, thorny_id)

        return cls(user=user, profile=profile, playtime=playtime)

    @classmethod
    def view_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")

    @classmethod
    async def new(cls, db: Database, guild_id: int, discord_id: int, username: str):
        await db.pool.execute("""
                                with user_table as (
                                    insert into users.user(user_id, guild_id, username)
                                    values($1, $2, $3)

                                    returning thorny_id
                                )
                                insert into users.profile(thorny_id)
                                select thorny_id from user_table
                               """,
                              discord_id, guild_id, username)


class UserQuestView(BaseModel):
    quest: Optional[UserQuestModel]
    objectives: Optional[list[UserObjectiveModel]]

    @classmethod
    async def build(cls, db: Database, thorny_id: int, quest_id: int):
        quest = await UserQuestModel.fetch(db, thorny_id, quest_id)
        objective_ids = await UserObjectiveModel.get_all_objectives(db, thorny_id, quest_id)

        objectives = []
        for objective in objective_ids:
            objectives.append(await UserObjectiveModel.fetch(db, thorny_id, quest_id, objective))

        return cls(quest=quest, objectives=objectives)

    @classmethod
    def view_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")

    @classmethod
    async def new(cls, db: Database, thorny_id: int, quest_id: int):
        quest_view = await QuestView.build(db, quest_id)

        async with db.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("""
                                   INSERT INTO users.quests(quest_id, thorny_id)
                                   VALUES($1, $2)
                                   """,
                                   quest_id, thorny_id)

                for objective in quest_view.objectives:
                    await conn.execute("""
                                       INSERT INTO users.objectives(quest_id, thorny_id, objective_id)
                                       VALUES($1, $2, $3)
                                       """,
                                       quest_id, thorny_id, objective.objective_id)

    @classmethod
    async def mark_failed(cls, db: Database, thorny_id: int, quest_id: int):
        quest = await cls.build(db, thorny_id, quest_id)
        quest.quest.status = 'failed'
        await quest.quest.update(db, thorny_id)

        for obj in quest.objectives:
            if obj.status == 'in_progress':
                obj.status = 'failed'
                await obj.update(db, thorny_id)


# Define components in the OpenAPI schema
# This can be done via a decorator, but for some reason
# the decorator stops intellisense from working
openapi.component(UserView)
