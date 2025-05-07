import asyncio

from pydantic import Field
from typing_extensions import Optional
from sanic_ext import openapi

from src.database import Database
from src.utils.base import BaseModel, BaseList
from src.utils.errors import BadRequest400, NotFound404


@openapi.component()
class InteractionStatistic(BaseModel):
    reference: str = Field(description="The interaction reference",
                           json_schema_extra={"example": 'minecraft:zombie'})
    type: str = Field(description="The interaction type",
                      json_schema_extra={"example": 'kill'})
    count: int = Field(description="The amount of the block mined, entity killed, etc.",
                       json_schema_extra={"example": 24})


@openapi.component()
class InteractionStatisticsList(BaseList[InteractionStatistic]):
    @classmethod
    async def fetch(cls, db: Database, thorny_id: int = None, interaction_type: str = None, *args) -> "InteractionStatisticsList":
        if not thorny_id or not interaction_type:
            raise BadRequest400('No thorny ID or interaction type provided. Please provide both to fetch interaction statistics')

        data = await db.pool.fetch("""
                                    select "type", reference, count(reference) as "count" from events.interactions i 
                                    where i.thorny_id = $1
                                    and i.type = $2
                                    group by type, reference
                                    order by "count" desc
                                   """, thorny_id, interaction_type)

        if data:
            stats = []
            for stat in data:
                stats.append(InteractionStatistic(**stat))

            return cls(root=stats)
        else:
            raise NotFound404(extra={'resource': f'user_interactions_{interaction_type}', 'id': thorny_id})


@openapi.component()
class InteractionTotals(BaseModel):
    mine: int
    kill: int
    place: int
    die: int
    use: int

    @classmethod
    async def fetch(cls, db: Database, thorny_id: int, *args) -> "InteractionTotals":
        if not thorny_id:
            raise BadRequest400('No thorny ID provided. Please provide it to fetch interaction statistics')

        data = await db.pool.fetchrow("""
                                        SELECT
                                            COALESCE(SUM(CASE WHEN type = 'mine' THEN 1 ELSE 0 END), 0) as mine,
                                            COALESCE(SUM(CASE WHEN type = 'place' THEN 1 ELSE 0 END), 0) as place,
                                            COALESCE(SUM(CASE WHEN type = 'kill' THEN 1 ELSE 0 END), 0) as kill,
                                            COALESCE(SUM(CASE WHEN type = 'die' THEN 1 ELSE 0 END), 0) as die,
                                            COALESCE(SUM(CASE WHEN type = 'use' THEN 1 ELSE 0 END), 0) as use
                                        FROM events.interactions
                                        WHERE thorny_id = $1;
                                        """, thorny_id)
        if data:
            return cls(**data)
        else:
            raise NotFound404(extra={'resource': f'user_interaction_totals', 'id': thorny_id})



class InteractionSummary(BaseModel):
    blocks_mined: InteractionStatisticsList
    blocks_placed: InteractionStatisticsList
    kills: InteractionStatisticsList
    deaths: InteractionStatisticsList
    uses: InteractionStatisticsList
    totals: InteractionTotals

    @classmethod
    async def fetch(cls, db: Database, thorny_id: int) -> "InteractionSummary":
        if not thorny_id:
            raise BadRequest400('No thorny ID provided. Please provide it to fetch interaction statistics')

        totals, mine, place, kills, deaths, uses = await asyncio.gather(
            InteractionTotals.fetch(db, thorny_id),
            InteractionStatisticsList.fetch(db, thorny_id, 'mine'),
            InteractionStatisticsList.fetch(db, thorny_id, 'place'),
            InteractionStatisticsList.fetch(db, thorny_id, 'kill'),
            InteractionStatisticsList.fetch(db, thorny_id, 'die'),
            InteractionStatisticsList.fetch(db, thorny_id, 'use')
        )

        if totals:
            return cls(blocks_mined=mine, blocks_placed=place, kills=kills, deaths=deaths, uses=uses, totals=totals)
        else:
            raise NotFound404(extra={'resource': f'user_interactions', 'id': thorny_id})
