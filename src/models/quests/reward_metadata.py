from pydantic import Field, BaseModel
from typing import Annotated, Literal, Union

from src.utils.minecraft_id import MINECRAFT_REGEX_PATTERN


class MetadataBaseModel(BaseModel):
    metadata_type: str = Field(description="The metadata type",
                               json_schema_extra={"example": "enchantment"})


class EnchantmentModel(MetadataBaseModel):
    metadata_type: Literal['enchantment'] = Field(description="The metadata type",
                                                  json_schema_extra={"example": "enchantment"})
    enchantment_id: str = Field(description="The enchantment ID",
                                json_schema_extra={"example": "minecraft:sharpness"},
                                pattern=MINECRAFT_REGEX_PATTERN)
    enchantment_level: int = Field(description="The enchantment level",
                                   json_schema_extra={"example": 4})


class RandomEnchantmentModel(MetadataBaseModel):
    metadata_type: Literal['enchantment_random'] = Field(description="The metadata type",
                                                         json_schema_extra={"example": "enchantment_random"})
    level_min: int = Field(description="The minimum XP Level to use for the random enchantments",
                           json_schema_extra={"example": 4})
    level_max: int = Field(description="The maximum XP Level to use for the random enchantments",
                           json_schema_extra={"example": 10})
    treasure: bool = Field(description="Whether treasure enchantments are allowed to be added",
                           json_schema_extra={"example": True})


class PotionModel(MetadataBaseModel):
    metadata_type: Literal['potion'] = Field(description="The metadata type",
                                             json_schema_extra={"example": "potion"})
    potion_effect: str = Field(description="The potion effect type",
                               json_schema_extra={"example": "minecraft:long_speed"},
                               pattern=MINECRAFT_REGEX_PATTERN)
    potion_delivery: str = Field(description="The potion delivery type",
                                 json_schema_extra={"example": "Consume"})


class NameModel(MetadataBaseModel):
    metadata_type: Literal['name'] = Field(description="The metadata type",
                                           json_schema_extra={"example": "name"})
    item_name: str = Field(description="The item name",
                           json_schema_extra={"example": "Super Secret Note"})


class LoreModel(MetadataBaseModel):
    metadata_type: Literal['lore'] = Field(description="The metadata type",
                                           json_schema_extra={"example": "lore"})
    item_lore: list[str] = Field(description="The item lore",
                                 json_schema_extra={"example": ["This item gives +3 knockback", "+4 Damage"]})


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