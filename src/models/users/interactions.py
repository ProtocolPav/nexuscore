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

        data = await db.pool.fetchrow("""
                                    with blocks_mined as (
                                        select "type", reference, count(reference) as "count" from events.interactions i 
                                        where i.thorny_id = $1
                                        and i.type = 'mine'
                                        group by type, reference
                                        order by "count" desc
                                    ),
                                    blocks_placed as (
                                        select "type", reference, count(reference) as "count" from events.interactions i 
                                        where i.thorny_id = $1
                                        and i.type = 'place'
                                        group by type, reference
                                        order by "count" desc
                                    ),
                                    kills as (
                                        select "type", reference, count(reference) as "count" from events.interactions i 
                                        where i.thorny_id = $1
                                        and i.type = 'kill'
                                        group by type, reference
                                        order by "count" desc
                                    ),
                                    deaths as (
                                        select "type", reference, count(reference) as "count" from events.interactions i 
                                        where i.thorny_id = $1
                                        and i.type = 'die'
                                        group by type, reference
                                        order by "count" desc
                                    ),
                                    uses as (
                                        select "type", reference, count(reference) as "count" from events.interactions i 
                                        where i.thorny_id = $1
                                        and i.type = 'use'
                                        group by type, reference
                                        order by "count" desc
                                    )

                                    select 
                                        (
                                            SELECT thorny_id FROM users.user
                                            WHERE thorny_id = $1
                                        ) AS thorny_id,
                                        coalesce(
                                            (select json_agg(json_build_object('reference', t.reference,
                                                                               'type', t."type",
                                                                               'count', t."count"))
                                             from blocks_mined as t
                                            ),
                                            '[]'::json
                                        ) as blocks_mined,
                                        coalesce(
                                            (select json_agg(json_build_object('reference', t.reference,
                                                                               'type', t."type",
                                                                               'count', t."count"))
                                             from blocks_placed as t
                                            ),
                                            '[]'::json
                                        ) as blocks_placed,
                                        coalesce(
                                            (select json_agg(json_build_object('reference', t.reference,
                                                                               'type', t."type",
                                                                               'count', t."count"))
                                             from kills as t
                                            ),
                                            '[]'::json
                                        ) as kills,
                                        coalesce(
                                            (select json_agg(json_build_object('reference', t.reference,
                                                                               'type', t."type",
                                                                               'count', t."count"))
                                             from deaths as t
                                            ),
                                            '[]'::json
                                        ) as deaths,
                                        coalesce(
                                            (select json_agg(json_build_object('reference', t.reference,
                                                                               'type', t."type",
                                                                               'count', t."count"))
                                             from uses as t
                                            ),
                                            '[]'::json
                                        ) as uses,
                                        coalesce(
                                            (select json_build_object('mine', m."sum",
                                                                      'place', p."sum",
                                                                      'kill', k."sum",
                                                                      'die', d."sum",
                                                                      'use', u."sum")
                                             from (select coalesce(sum("count"), 0) as "sum" from blocks_mined) as m,
                                                  (select coalesce(sum("count"), 0) as "sum" from blocks_placed) as p,
                                                  (select coalesce(sum("count"), 0) as "sum" from kills) as k,
                                                  (select coalesce(sum("count"), 0) as "sum" from deaths) as d,
                                                  (select coalesce(sum("count"), 0) as "sum" from uses) as u
                                            ),
                                            '[]'::json
                                        ) as totals
                                        """,
                                      thorny_id)

        if data:
            return cls(**data)
        else:
            raise NotFound404(extra={'resource': f'user_interactions', 'id': thorny_id})
