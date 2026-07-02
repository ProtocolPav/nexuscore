from pydantic import Field, BaseModel
from typing import Annotated, Literal, Union


class EventBlockBase(BaseModel):
    block_id: int = Field(description="The block id")
    position: float = Field(description="The fractional ordering index of this block on the page",
                            examples=[1.0])
    created_at: str = Field(description="ISO 8601 datetime the block was created",
                            examples=["2024-05-01T18:00:00Z"])
    updated_at: str = Field(description="ISO 8601 datetime the block was last updated",
                            examples=["2024-05-01T18:00:00Z"])


class HeroBlock(EventBlockBase):
    type: Literal["hero"] = Field(description="The type of the block", examples=["hero"])
    image: str = Field(description="The hero/banner image path or URL",
                       examples=["/events/summer-games/hero.png"])
    eyebrow: str | None = Field(description="Small label shown above the title",
                                examples=["SEASONAL EVENT"],
                                default=None)
    tagline: str | None = Field(description="Short line shown under the title",
                                examples=["Compete for glory and loot"],
                                default=None)


class CountdownBlock(EventBlockBase):
    type: Literal["countdown"] = Field(description="The type of the block", examples=["countdown"])
    label: str | None = Field(description="Label shown above the countdown",
                              examples=["Registration closes in"],
                              default=None)
    target_time: str = Field(description="ISO 8601 datetime the countdown counts to",
                             examples=["2026-08-01T18:00:00Z"])


class StatItem(BaseModel):
    icon: str = Field(description="Phosphor icon component name", examples=["TrophyIcon"])
    label: str = Field(description="The stat label", examples=["Prize Pool"])
    value: str = Field(description="The stat value", examples=["$500"])
    color: str | None = Field(description="Optional Tailwind color class for the icon",
                              examples=["text-amber-500"],
                              default=None)


class StatRowBlock(EventBlockBase):
    type: Literal["stat_row"] = Field(description="The type of the block", examples=["stat_row"])
    items: list[StatItem] = Field(description="The stats to display side by side")


class NarrativeBlock(EventBlockBase):
    type: Literal["narrative"] = Field(description="The type of the block", examples=["narrative"])
    heading: str | None = Field(description="Optional section heading",
                                examples=["About This Event"],
                                default=None)
    markdown: str = Field(description="Freeform markdown content",
                          examples=["This event brings the whole server together..."])


class HighlightItem(BaseModel):
    icon: str = Field(description="Phosphor icon component name", examples=["SwordIcon"])
    title: str = Field(description="The highlight title", examples=["Boss Fight"])
    subtitle: str | None = Field(description="Optional subtitle",
                                 examples=["Day 3, 8 PM UTC"],
                                 default=None)
    description: str = Field(description="Short description of this highlight",
                             examples=["Team up to take down the Ender Dragon"])
    color: str | None = Field(description="Optional Tailwind color class for the icon", default=None)


class HighlightGridBlock(EventBlockBase):
    type: Literal["highlight_grid"] = Field(description="The type of the block", examples=["highlight_grid"])
    heading: str | None = Field(description="Optional section heading", default=None)
    items: list[HighlightItem] = Field(description="The parallel features/activities to display")


class PrizeTier(BaseModel):
    rank_label: str = Field(description="The tier label", examples=["1st Place"])
    icon: str | None = Field(description="Phosphor icon component name", default=None)
    color: str | None = Field(description="Optional Tailwind color class", default=None)
    items: list[str] = Field(description="The reward items for this tier",
                             examples=[["Diamond Armor Set", "500 Coins"]])


class PrizeTiersBlock(EventBlockBase):
    type: Literal["prize_tiers"] = Field(description="The type of the block", examples=["prize_tiers"])
    heading: str | None = Field(description="Optional section heading",
                                examples=["Rewards & Prizes"],
                                default=None)
    tiers: list[PrizeTier] = Field(description="The ranked reward tiers")


class RulesColumnsBlock(EventBlockBase):
    type: Literal["rules_columns"] = Field(description="The type of the block", examples=["rules_columns"])
    allowed: list[str] = Field(description="Allowed actions/behaviours during the event",
                               examples=[["PvP in the arena", "Trading items"]])
    disallowed: list[str] = Field(description="Disallowed actions/behaviours during the event",
                                  examples=[["Griefing", "Using hacked clients"]])


class FaqItem(BaseModel):
    question: str = Field(description="The FAQ question", examples=["Can I join late?"])
    answer: str = Field(description="The FAQ answer",
                        examples=["Yes, you can join at any point before the final day."])


class FaqBlock(EventBlockBase):
    type: Literal["faq"] = Field(description="The type of the block", examples=["faq"])
    heading: str | None = Field(description="Optional section heading",
                                examples=["Frequently Asked Questions"],
                                default=None)
    items: list[FaqItem] = Field(description="The FAQ entries")


class MediaItem(BaseModel):
    src: str = Field(description="The image path or URL",
                     examples=["/events/summer-games/gallery/1.png"])
    alt: str = Field(description="Alt text for the image",
                     examples=["Contestants building their bases"])
    caption: str | None = Field(description="Optional caption shown under the image", default=None)


class MediaGalleryBlock(EventBlockBase):
    type: Literal["media_gallery"] = Field(description="The type of the block", examples=["media_gallery"])
    heading: str | None = Field(description="Optional section heading", examples=["Gallery"], default=None)
    items: list[MediaItem] = Field(description="The gallery images")


class CtaButton(BaseModel):
    label: str = Field(description="The button label", examples=["Join the Discord"])
    url: str = Field(description="The button destination URL",
                     examples=["https://discord.gg/everthorn"])
    icon: str | None = Field(description="Phosphor icon component name", default=None)
    variant: Literal["primary", "secondary"] | None = Field(description="The button's visual weight", default=None)


class CtaBannerBlock(EventBlockBase):
    type: Literal["cta_banner"] = Field(description="The type of the block", examples=["cta_banner"])
    heading: str = Field(description="The banner heading", examples=["Ready to compete?"])
    description: str | None = Field(description="Optional supporting text", default=None)
    buttons: list[CtaButton] = Field(description="The call-to-action buttons, max 2", max_length=2)


class DividerBlock(EventBlockBase):
    type: Literal["divider"] = Field(description="The type of the block", examples=["divider"])


Blocks = Annotated[
    Union[
        HeroBlock,
        CountdownBlock,
        StatRowBlock,
        NarrativeBlock,
        HighlightGridBlock,
        PrizeTiersBlock,
        RulesColumnsBlock,
        FaqBlock,
        MediaGalleryBlock,
        CtaBannerBlock,
        DividerBlock,
    ],
    Field(discriminator="type")
]