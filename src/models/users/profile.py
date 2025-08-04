from pydantic import StringConstraints, Field
from typing_extensions import Annotated, Optional

from sanic_ext import openapi

from src.database import Database
from src.utils.base import BaseModel, optional_model
from src.utils.errors import BadRequest400, NotFound404

ShortString = Annotated[str, StringConstraints(max_length=35)]
LongString = Annotated[str, StringConstraints(max_length=300)]


class ProfileBaseModel(BaseModel):
    slogan: ShortString = Field(description="The slogan showed on the profile. Max. 35 characters",
                                json_schema_extra={"example": "I HEART THORNY"})
    aboutme: LongString = Field(description="The user's aboutme section. Max. 300 characters",
                                json_schema_extra={"example": "Really cool about me..."})
    lore: LongString = Field(description="Same as the aboutme, but for the user's character. Max. 300 characters.",
                             json_schema_extra={"example": "Very long lore..."})
    character_name: ShortString = Field(description="The character's name. Max. 35 characters",
                                        json_schema_extra={"example": "Captain Easton"})
    character_age: int = Field(description="The character's age",
                               json_schema_extra={"example": 43})
    character_race: ShortString = Field(description="The character's race. Max. 35 characters",
                                        json_schema_extra={"example": "Human"})
    character_role: ShortString = Field(description="The character's role. Max. 35 characters",
                                        json_schema_extra={"example": "Farmer"})
    character_origin: ShortString = Field(description="The character's origin. Max. 35 characters",
                                          json_schema_extra={"example": "Yutakana Province"})
    character_beliefs: ShortString = Field(description="The character's beliefs. Max. 35 characters",
                                           json_schema_extra={"example": "Thornyism"})
    agility: int = Field(description="The character's agility",
                         json_schema_extra={"example": 3})
    valor: int = Field(description="The character's valor",
                       json_schema_extra={"example": 6})
    strength: int = Field(description="The character's strength",
                          json_schema_extra={"example": 1})
    charisma: int = Field(description="The character's charisma",
                          json_schema_extra={"example": 5})
    creativity: int = Field(description="The character's creativity",
                            json_schema_extra={"example": 3})
    ingenuity: int = Field(description="The character's ingenuity",
                           json_schema_extra={"example": 2})


@openapi.component()
class ProfileModel(ProfileBaseModel):
    thorny_id: int = Field(description="The ThornyID of a user. This is a unique number.",
                           json_schema_extra={"example": 34})

    @classmethod
    async def create(cls, db: Database, model: "ProfileCreateModel", *args):
        await db.pool.execute("""
                              insert into users.profile(thorny_id)
                              values($1)
                              """,
                              model.thorny_id)

    @classmethod
    async def fetch(cls, db: Database, thorny_id: int, *args) -> "ProfileModel":
        if not thorny_id:
            raise BadRequest400(extra={'ids': ['thorny_id']})

        data = await db.pool.fetchrow("""
                                       SELECT * FROM users.profile
                                       WHERE thorny_id = $1
                                       """,
                                      thorny_id)

        if data:
            return cls(**data)
        else:
            raise NotFound404(extra={'resource': 'profile', 'id': thorny_id})

    async def update(self, db: Database, model: "ProfileUpdateModel"):
        for k, v in model.model_dump().items():
            setattr(self, k, v) if v is not None else None

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
                              self.creativity, self.ingenuity, self.thorny_id)


class ProfileCreateModel(BaseModel):
    thorny_id: int = Field(description="The ThornyID of a user. This is a unique number.",
                           json_schema_extra={"example": 34})


ProfileUpdateModel = optional_model("ProfileUpdateModel", ProfileBaseModel)