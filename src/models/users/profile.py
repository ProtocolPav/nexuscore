from datetime import datetime, date
from typing import Literal

from pydantic import StringConstraints, BaseModel, Field
from typing_extensions import Annotated, Optional

import json

from sanic_ext import openapi

from src.database import Database

ShortString = Annotated[str, StringConstraints(max_length=35)]
LongString = Annotated[str, StringConstraints(max_length=300)]


class ProfileModel(BaseModel):
    slogan: ShortString = Field(description="The slogan showed on the profile. Max. 35 characters",
                                examples=['Thorny Forever!!'])
    aboutme: LongString = Field(description="The user's aboutme section. Max. 300 characters",
                                examples=['My really cool and descriptive aboutm...'])
    lore: LongString = Field(description="Same as the aboutme, but for the user's character. Max. 300 characters.",
                             examples=['There once was a hero of this wor...'])
    character_name: ShortString = Field(description="The character's name. Max. 35 characters",
                                        examples=['Haiko'])
    character_age: int = Field(description="The character's age",
                               examples=[56])
    character_race: ShortString = Field(description="The character's race. Max. 35 characters",
                                        examples=['Human'])
    character_role: ShortString = Field(description="The character's role. Max. 35 characters",
                                        examples=['Farmer'])
    character_origin: ShortString = Field(description="The character's origin. Max. 35 characters",
                                          examples=['Japan'])
    character_beliefs: ShortString = Field(description="The character's beliefs. Max. 35 characters",
                                           examples=['Buddhism'])
    agility: int
    valor: int
    strength: int
    charisma: int
    creativity: int
    ingenuity: int

    @classmethod
    async def fetch(cls, db: Database, thorny_id: int):
        data = await db.pool.fetchrow("""
                                       SELECT * FROM users.profile
                                       WHERE thorny_id = $1
                                       """,
                                      thorny_id)

        return cls(**data)

    async def update(self, db: Database, thorny_id: int):
        await db.pool.execute("""
                               UPDATE users.profile
                               SET slogan = $1,
                                   aboutme = $2,
                                   lore = $3,
                                   character_name = $4,
                                   character_age = $5,
                                   character_race = $6,
                                   character_role = $7,
                                   character_origin = $8,
                                   character_beliefs = $9,
                                   agility = $10,
                                   valor = $11,
                                   strength = $12,
                                   charisma = $13,
                                   creativity = $14,
                                   ingenuity = $15
                               WHERE thorny_id = $16
                               """,
                              self.slogan, self.aboutme, self.lore, self.character_name,
                              self.character_age, self.character_race, self.character_role, self.character_origin,
                              self.character_beliefs, self.agility, self.valor, self.strength, self.charisma,
                              self.creativity, self.ingenuity, thorny_id)

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")


class ProfileUpdateModel(BaseModel):
    slogan: Optional[ShortString] = Field(description="The slogan showed on the profile. Max. 35 characters",
                                examples=['Thorny Forever!!'])
    aboutme: Optional[LongString] = Field(description="The user's aboutme section. Max. 300 characters",
                                examples=['My really cool and descriptive aboutm...'])
    lore: Optional[LongString] = Field(description="Same as the aboutme, but for the user's character. Max. 300 characters.",
                             examples=['There once was a hero of this wor...'])
    character_name: Optional[ShortString] = Field(description="The character's name. Max. 35 characters",
                                        examples=['Haiko'])
    character_age: Optional[int] = Field(description="The character's age",
                               examples=[56])
    character_race: Optional[ShortString] = Field(description="The character's race. Max. 35 characters",
                                        examples=['Human'])
    character_role: Optional[ShortString] = Field(description="The character's role. Max. 35 characters",
                                        examples=['Farmer'])
    character_origin: Optional[ShortString] = Field(description="The character's origin. Max. 35 characters",
                                          examples=['Japan'])
    character_beliefs: Optional[ShortString] = Field(description="The character's beliefs. Max. 35 characters",
                                           examples=['Buddhism'])
    agility: Optional[int]
    valor: Optional[int]
    strength: Optional[int]
    charisma: Optional[int]
    creativity: Optional[int]
    ingenuity: Optional[int]

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")
