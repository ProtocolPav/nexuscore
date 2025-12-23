from pydantic import Field, StringConstraints
from typing import Annotated, Literal, Optional, Union

from src.utils.base import BaseModel, BaseList, optional_model

from sanic_ext import openapi

MinecraftID = Annotated[str, StringConstraints(pattern='^[a-z]+:[a-z_0-9]+$')]


@openapi.component()
class MetadataBaseModel(BaseModel):
    metadata_type: str = Field(description="The metadata type",
                               json_schema_extra={"example": "enchantment"})


@openapi.component()
class EnchantmentModel(MetadataBaseModel):
    metadata_type: Literal['enchantment'] = Field(description="The metadata type",
                                                  json_schema_extra={"example": "enchantment"})
    enchantment_id: str = Field(description="The enchantment ID",
                                json_schema_extra={"example": "minecraft:sharpness"})
    enchantment_level: int = Field(description="The enchantment level",
                                   json_schema_extra={"example": 4})


@openapi.component()
class RandomEnchantmentModel(MetadataBaseModel):
    metadata_type: Literal['enchantment_random'] = Field(description="The metadata type",
                                                         json_schema_extra={"example": "enchantment_random"})
    level_min: int = Field(description="The minimum XP Level to use for the random enchantments",
                           json_schema_extra={"example": 4})
    level_max: int = Field(description="The maximum XP Level to use for the random enchantments",
                           json_schema_extra={"example": 10})
    treasure: bool = Field(description="Whether treasure enchantments are allowed to be added",
                           json_schema_extra={"example": True})


@openapi.component()
class PotionModel(MetadataBaseModel):
    metadata_type: Literal['potion'] = Field(description="The metadata type",
                                             json_schema_extra={"example": "potion"})
    potion_effect: str = Field(description="The potion effect type",
                               json_schema_extra={"example": "minecraft:long_speed"})
    potion_delivery: str = Field(description="The potion delivery type",
                                 json_schema_extra={"example": "Consume"})


@openapi.component()
class NameModel(MetadataBaseModel):
    metadata_type: Literal['name'] = Field(description="The metadata type",
                                           json_schema_extra={"example": "name"})
    item_name: str = Field(description="The item name",
                           json_schema_extra={"example": "Super Secret Note"})


@openapi.component()
class LoreModel(MetadataBaseModel):
    metadata_type: Literal['lore'] = Field(description="The metadata type",
                                           json_schema_extra={"example": "lore"})
    item_lore: str = Field(description="The item lore",
                           json_schema_extra={"example": "This item gives +3 knockback"})


@openapi.component()
class DamageModel(MetadataBaseModel):
    metadata_type: Literal['damage'] = Field(description="The metadata type",
                                             json_schema_extra={"example": "damage"})
    damage_percentage: float = Field(description="The percentage of durability the item should lose",
                                     json_schema_extra={"example": 0.43})


Metadata = Annotated[
    Union[
        EnchantmentModel,
        RandomEnchantmentModel,
        PotionModel,
        NameModel,
        LoreModel,
        DamageModel
    ],
    Field(discriminator="metadata_type")
]