from pydantic import BaseModel, Field

from typing import Optional

from src.database import Database


class GuildModel(BaseModel):
    guild_id: int = Field(description="The discord guild ID",
                          examples=[631936703190440136])
    name: str = Field(description="The name of the guild",
                      examples=['Everthorn'])
    currency_name: str = Field(description="The name of the guild's currency (plural)",
                               examples=['Nugs'])
    currency_emoji: str = Field(description="The emoji of the guild's currency",
                                examples=['<:Nug:884320353202081833>'])
    level_up_message: str = Field(description="The message that gets sent when a user levels up",
                                  examples=['Yay! You leveled up!'])
    join_message: str = Field(description="The message that gets sent when a user joins the guild",
                              examples=['Welcome to our guild!'])
    leave_message: str = Field(description="The message that gets sent when a user leaves the guild",
                               examples=['Bye bye :(('])
    xp_multiplier: float = Field(description="The xp multiplier of this guild",
                                 examples=[1.3])
    active: bool = Field(description="Whether Thorny is in this guild or not",
                         examples=[True])

    @classmethod
    async def fetch(cls, db: Database, guild_id: int) -> Optional["GuildModel"]:
        data = await db.pool.fetchrow("""
                                      SELECT * FROM guilds.guild
                                      WHERE guild_id = $1
                                      """,
                                      guild_id)

        return cls(**data) if data else None

    @classmethod
    async def new(cls, db: Database, guild_id: int, name: str):
        await db.pool.execute("""
                                with guild_table as (
                                    insert into guilds.guild(guild_id, name)
                                    values($1, $2)
                                )
                                insert into guilds.features(guild_id, feature)
                                    values ($1, 'profile'),
                                           ($1, 'levels'),
                                           ($1, 'basic')
                               """,
                              guild_id, name)

    async def update(self, db: Database):
        await db.pool.execute(f"""
                              UPDATE guilds.guild
                              SET name = $2,
                                  currency_name = $3,
                                  currency_emoji = $4,
                                  level_up_message = $5,
                                  join_message = $6,
                                  leave_message = $7,
                                  xp_multiplier = $8,
                                  active = $9
                              WHERE guild_id = $1
                              """,
                              self.guild_id, self.name, self.currency_name,
                              self.currency_emoji, self.level_up_message, self.join_message,
                              self.leave_message, self.xp_multiplier, self.active)

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


class GuildCreateModel(BaseModel):
    guild_id: int
    name: str

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")
