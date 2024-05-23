import json
from typing import Any, Optional, Self

from src.database import Database
from src.models.user import UserModel, ProfileModel, PlaytimeSummary

from sanic_ext import openapi

from pydantic import BaseModel, model_serializer


@openapi.component
class UserView(BaseModel):
    user: UserModel
    profile: Optional[ProfileModel]
    playtime: Optional[PlaytimeSummary]

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

        return data['thorny_id']

    @classmethod
    async def build(cls, db: Database, thorny_id: int) -> Self:
        user = await UserModel.fetch(db, thorny_id)
        profile = await ProfileModel.fetch(db, thorny_id)
        playtime = await PlaytimeSummary.fetch(db, thorny_id)

        return cls(user=user, profile=profile, playtime=playtime)

    @model_serializer
    def serialize_for_output(self):
        user = self.user.model_dump()
        profile = {'profile': self.profile.model_dump()}
        playtime = {'playtime': self.playtime.model_dump()}
        return user | profile | playtime

    @classmethod
    def view_schema(cls):
        class Schema(UserModel):
            profile: Optional[ProfileModel]
            playtime: Optional[PlaytimeSummary]

        return Schema.model_json_schema(ref_template="#/components/schemas/{model}")
