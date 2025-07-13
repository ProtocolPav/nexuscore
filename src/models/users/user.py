from datetime import datetime, date

from pydantic import Field
from typing_extensions import Optional

from src.database import Database
from src.models.users.profile import ProfileCreateModel, ProfileModel
from src.utils.base import BaseModel, BaseList, optional_model

from sanic_ext import openapi

from src.utils.errors import BadRequest400, NotFound404


class UserBaseModel(BaseModel):
    username: Optional[str] = Field(description="The discord username this user has. Same format as discord usernames",
                                    json_schema_extra={"example": "protocolpav"})
    birthday: Optional[date] = Field(description="The user's birthday. This is optional.",
                                     json_schema_extra={"example": "2005-03-03"})
    balance: int = Field(description="The user's balance on the guild.",
                         json_schema_extra={"example": 2})
    active: bool = Field(description="If the user is in the guild or not.",
                         json_schema_extra={"example": True})
    role: str = Field(description="The role of the user",
                      json_schema_extra={"example": "Owner"})
    patron: bool = Field(description="Whether the user is a patron or not",
                         json_schema_extra={"example": True})
    level: int = Field(description="The user's level",
                       json_schema_extra={"example": 32})
    xp: int = Field(description="The user's xp",
                    json_schema_extra={"example": 1023})
    required_xp: int = Field(description="The xp required to reach the next level",
                             json_schema_extra={"example": 3044})
    last_message: datetime = Field(description="The last time the user gained XP",
                                   json_schema_extra={"example": "2024-03-03 04:00:00"})
    gamertag: Optional[str] = Field(description="The user's gamertag",
                                    json_schema_extra={"example": "ProtocolPav"})
    whitelist: Optional[str] = Field(description="The gamertag that this user is whitelisted under",
                                     json_schema_extra={"example": "ProtocolPav"})
    location: Optional[tuple[int, int, int]] = Field(description="The last in-game location of the user",
                                           json_schema_extra={"example": (544, 18, -432)})
    dimension: Optional[str] = Field(description="The last in-game dimension the user was in",
                           json_schema_extra={"example": 'minecraft:overworld'})


@openapi.component()
class UserModel(UserBaseModel):
    thorny_id: int = Field(description="The ThornyID of a user. This is a unique number",
                           json_schema_extra={"example": 34})
    user_id: int = Field(description="The user's Discord User ID",
                         json_schema_extra={"example": 123456789012345678})
    guild_id: int = Field(description="The Discord guild ID this user is registered in",
                          json_schema_extra={"example": 123456789012345678})
    join_date: date = Field(description="The date the ThornyID was created. Usually when a user joins the guild",
                            json_schema_extra={"example": "2024-03-03"})
    profile: ProfileModel = Field(description="The user's profile")

    @classmethod
    async def create(cls, db: Database, model: "UserCreateModel", *args) -> int:
        thorny_id = await db.pool.fetchrow("""
                                            with user_table as (
                                                insert into users.user(user_id, guild_id, username)
                                                values($1, $2, $3)
            
                                                returning thorny_id
                                            )
                                            select thorny_id as id from user_table
                                           """,
                                          model.user_id, model.guild_id, model.username)

        await ProfileModel.create(db, ProfileCreateModel(thorny_id=thorny_id['id']))

        return thorny_id['id']

    @classmethod
    async def fetch(cls, db: Database, thorny_id: int, *args) -> "UserModel":
        if not thorny_id:
            raise BadRequest400(extra={'ids': ['thorny_id']})

        data = await db.pool.fetchrow("""
                                       SELECT * FROM users.user
                                       WHERE thorny_id = $1
                                       """,
                                      thorny_id)

        if data:
            profile = await ProfileModel.fetch(db=db, thorny_id=thorny_id)

            return cls(**data, profile=profile)
        else:
            raise NotFound404(extra={'resource': 'user', 'id': thorny_id})

    @classmethod
    async def get_thorny_id(cls, db: Database, guild_id: int, user_id: int = None, gamertag: str = None) -> Optional[int]:
        """
        Returns the thorny ID based on what is provided.
        Either guild ID and user ID, or guild ID and gamertag.

        Returns None otherwise.

        :param db:
        :param guild_id:
        :param user_id:
        :param gamertag:
        :return:
        """
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
            return None

        return data['thorny_id'] if data else None

    async def update(self, db: Database, model: "UserUpdateModel"):
        for k, v in model.model_dump().items():
            setattr(self, k, v) if v or k == 'whitelist' else None

        await db.pool.execute("""
                               UPDATE users.user
                               SET username = $1,
                                   birthday = $2,
                                   balance = $3,
                                   active = $4,
                                   role = $5,
                                   patron = $6,
                                   level = $7,
                                   xp = $8,
                                   required_xp = $9,
                                   last_message = $10,
                                   gamertag = $11,
                                   whitelist = $12,
                                   location = $13,
                                   dimension = $14
                               WHERE thorny_id = $15
                               """,
                              self.username, self.birthday, self.balance, self.active,
                              self.role, self.patron, self.level, self.xp, self.required_xp,
                              self.last_message, self.gamertag, self.whitelist, self.location,
                              self.dimension, self.thorny_id)


UserUpdateModel = optional_model("UserUpdateModel", UserBaseModel)


class UserCreateModel(BaseModel):
    user_id: int = Field(description="The Discord user ID. Multiple users can have Thorny accounts on "
                                     "different servers.",
                         json_schema_extra={"example": 123456789012345678})
    guild_id: int = Field(description="The Discord guild ID this user is registered in.",
                          json_schema_extra={"example": 123456789012345678})
    username: Optional[str] = Field(description="The discord username this user has. Same format as discord usernames",
                                    json_schema_extra={"example": "protocolpav"})
