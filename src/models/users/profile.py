from pydantic import Field, BaseModel
from typing_extensions import Annotated


ThornyID = Annotated[int, Field(
    description="The ThornyID of the profile",
    examples=[34]
)]
Slogan = Annotated[str, Field(
    description="The slogan of the profile",
    examples=["I HEART THORNY"],
    max_length=35
)]
AboutMe = Annotated[str, Field(
    description="The aboutme of the profile",
    examples=["Really cool about me..."],
    max_length=300
)]
Lore = Annotated[str, Field(
    description="The lore of the profile",
    examples=["Very long lore..."],
    max_length=300
)]
CharacterName = Annotated[str, Field(
    description="The character name of the profile",
    examples=["Captain Easton"],
    max_length=35
)]
CharacterAge = Annotated[int, Field(
    description="The character age of the profile",
    examples=[43]
)]
CharacterRace = Annotated[str, Field(
    description="The character race of the profile",
    examples=["Human"],
    max_length=35
)]
CharacterRole = Annotated[str, Field(
    description="The character role of the profile",
    examples=["Farmer"],
    max_length=35
)]
CharacterOrigin = Annotated[str, Field(
    description="The character origin of the profile",
    examples=["Yutakana Province"],
    max_length=35
)]
CharacterBeliefs = Annotated[str, Field(
    description="The character beliefs of the profile",
    examples=["Thornyism"],
    max_length=35
)]
Agility = Annotated[int, Field(
    description="The character agility of the profile",
    le=6,
    ge=0
)]
Valor = Annotated[int, Field(
    description="The character valor of the profile",
    le=6,
    ge=0
)]
Strength = Annotated[int, Field(
    description="The character strength of the profile",
    le=6,
    ge=0
)]
Charisma = Annotated[int, Field(
    description="The character charisma of the profile",
    le=6,
    ge=0
)]
Creativity = Annotated[int, Field(
    description="The character creativity of the profile",
    le=6,
    ge=0
)]
Ingenuity = Annotated[int, Field(
    description="The character ingeniu of the profile",
    le=6,
    ge=0
)]

class ProfileDB(BaseModel):
    thorny_id: ThornyID
    slogan: Slogan
    aboutme: AboutMe
    lore: Lore
    character_name: CharacterName
    character_age: CharacterAge
    character_race: CharacterRace
    character_role: CharacterRole
    character_origin: CharacterOrigin
    character_beliefs: CharacterBeliefs
    agility: Agility
    valor: Valor
    strength: Strength
    charisma: Charisma
    creativity: Creativity
    ingenuity: Ingenuity

class ProfileOut(ProfileDB):
    thorny_id: ThornyID = Field(exclude=True)

class ProfileUpdate(BaseModel):
    slogan: Slogan = None
    aboutme: AboutMe = None
    lore: Lore = None
    character_name: CharacterName = None
    character_age: CharacterAge = None
    character_race: CharacterRace = None
    character_role: CharacterRole = None
    character_origin: CharacterOrigin = None
    character_beliefs: CharacterBeliefs = None
    agility: Agility = None
    valor: Valor = None
    strength: Strength = None
    charisma: Charisma = None
    creativity: Creativity = None
    ingenuity: Ingenuity = None