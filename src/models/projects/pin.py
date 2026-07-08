from typing import Annotated, Optional

from pydantic import Field, BaseModel

from fastapi import HTTPException

from src.dependencies.database import Database

PinID = Annotated[int, Field(
    description="The pin's ID"
)]
PinName = Annotated[str, Field(
    description="The name of the pin",
    examples=['Bloomin Flower Shop']
)]
PinDescription = Annotated[str, Field(
    description="A short description of the pin, such as what the shop sells, etc.",
    examples=['Sells Flowers']
)]
PinCoordinates = Annotated[list[int], Field(
    description="The coordinates of the pin",
    examples=[[333, 55, -65]]
)]
PinDimension = Annotated[str, Field(
    description="The dimension of the pin",
    examples=['minecraft:overworld']
)]
PinType = Annotated[str, Field(
    description="The type of pin this is",
    examples=["shop", "farm"]
)]


class PinDB(BaseModel):
    id: PinID
    name: PinName
    description: PinDescription
    coordinates: PinCoordinates
    dimension: PinDimension
    pin_type: PinType

class PinIn(BaseModel):
    name: PinName
    description: PinDescription
    coordinates: PinCoordinates
    dimension: PinDimension
    pin_type: PinType

class PinOut(PinDB):
    pass

class PinUpdate(BaseModel):
    name: Optional[PinName] = None
    description: Optional[PinDescription] = None
    coordinates: Optional[PinCoordinates] = None
    dimension: Optional[PinDimension] = None
    pin_type: Optional[PinType] = None
