from typing import Optional

from src.database import Database
from src.models.user import UserModel, ProfileModel, PlaytimeSummary

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


# Define components in the OpenAPI schema
# This can be done via a decorator, but for some reason
# the decorator stops intellisense from working
openapi.component(UserView)
