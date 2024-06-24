from datetime import datetime, date

from pydantic import BaseModel, Field
from typing_extensions import Optional

from src.database import Database


class UserModel(BaseModel):
    thorny_id: int = Field(description="The ThornyID of a user. This is a unique number.",
                           examples=[345])
    user_id: int = Field(description="The Discord user ID. Multiple users can have Thorny accounts on "
                                     "different servers.",
                         examples=[123456789012345678])
    guild_id: int = Field(description="The Discord guild ID this user is registered in.",
                          examples=[123456789012345678])
    username: Optional[str] = Field(description="The discord username this user has. Same format as discord usernames",
                                    examples=['protocolpav', 'thatoreocookie'])
    join_date: date = Field(description="The date the ThornyID was created. Usually when a user joins the guild",
                            examples=['2024-05-14'])
    birthday: Optional[date] = Field(description="The user's birthday. This is optional.",
                                     examples=['2003-05-14'])
    balance: int = Field(description="The user's balance on the guild.")
    active: bool = Field(description="If the user is in the guild or not.")
    role: str = Field(description="The role of the user",
                      examples=['Owner', 'Community Manager', 'Dweller'])
    patron: bool = Field(description="Whether the user is a patron or not")
    level: int = Field(description="The user's level")
    xp: int = Field(description="The user's xp")
    required_xp: int = Field(description="The xp required to reach the next level")
    last_message: datetime = Field(description="The last time the user gained XP",
                                   examples=['2024-05-24 23:34:04.123456'])
    gamertag: Optional[str] = Field(description="The user's gamertag")
    whitelist: Optional[str] = Field(description="The gamertag that this user is whitelisted under")

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

    @classmethod
    async def fetch(cls, db: Database, thorny_id: int) -> Optional["UserModel"]:
        data = await db.pool.fetchrow("""
                                       SELECT * FROM users.user
                                       WHERE thorny_id = $1
                                       """,
                                      thorny_id)

        return cls(**data) if data else None

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

    async def update(self, db: Database):
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
                                   whitelist = $12
                               WHERE thorny_id = $13
                               """,
                              self.username, self.birthday, self.balance, self.active,
                              self.role, self.patron, self.level, self.xp, self.required_xp,
                              self.last_message, self.gamertag, self.whitelist, self.thorny_id)

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


class UserUpdateModel(BaseModel):
    username: Optional[str] = Field(description="The user's discord username")
    birthday: Optional[date] = Field(description="The birthday in the format: YYYY-MM-DD",
                                     examples=['1996-04-15'])
    balance: Optional[int] = Field(description="The user's new balance")
    active: Optional[bool] = Field(description="Whether the user is a member of the guild or not")
    role: Optional[str] = Field(description="The user's topmost role")
    patron: Optional[bool] = Field(description="Whether the user is a patron or not")
    level: Optional[int] = Field(description="The user's level")
    xp: Optional[int] = Field(description="The user's xp")
    required_xp: Optional[int] = Field(description="The required xp to reach the next level")
    last_message: Optional[datetime] = Field(description="The last time the user gained XP",
                                             examples=['2022-03-03T15:23:45.123456Z'])
    gamertag: Optional[str] = Field(description="The user's gamertag")
    whitelist: Optional[str] = Field(description="The gamertag that this user is whitelisted under")

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


class UserCreateModel(BaseModel):
    guild_id: int
    discord_id: int
    username: str

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")
