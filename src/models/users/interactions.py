from pydantic import BaseModel, Field
from typing_extensions import Optional
from sanic_ext import openapi

import json

from src.database import Database


@openapi.component()
class InteractionStatistic(BaseModel):
    reference: str = Field(description="The block or entity in question",
                           examples=['minecraft:stone', 'minecraft:zombie'])
    type: str = Field(description="The type of interaction, kill, mine, place or use",
                      examples=['kill'])
    count: int = Field(description="The amount of the block mined, entity killed, etc.",
                       examples=[56054])


@openapi.component()
class InteractionTotals(BaseModel):
    mine: int
    kill: int
    place: int
    die: int
    use: int


class InteractionSummary(BaseModel):
    blocks_mined: Optional[list[InteractionStatistic]]
    blocks_placed: Optional[list[InteractionStatistic]]
    kills: Optional[list[InteractionStatistic]]
    deaths: Optional[list[InteractionStatistic]]
    uses: Optional[list[InteractionStatistic]]
    totals: InteractionTotals

    @classmethod
    async def fetch(cls, db: Database, thorny_id: int) -> Optional["InteractionSummary"]:
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
                                             from (select sum("count") as "sum" from blocks_mined) as m,
                                                  (select sum("count") as "sum" from blocks_placed) as p,
                                                  (select sum("count") as "sum" from kills) as k,
                                                  (select sum("count") as "sum" from deaths) as d,
                                                  (select sum("count") as "sum" from uses) as u
                                            ),
                                            '[]'::json
                                        ) as totals
                                        """,
                                      thorny_id)

        if data['thorny_id']:
            processed_dict = {'thorny_id': thorny_id,
                              'totals': json.loads(data['totals']),
                              'blocks_mined': json.loads(data['blocks_mined']),
                              'blocks_placed': json.loads(data['blocks_placed']),
                              'kills': json.loads(data['kills']),
                              'deaths': json.loads(data['deaths']),
                              'uses': json.loads(data['uses'])}
        else:
            return None

        return cls(**processed_dict)

    @classmethod
    def doc_schema(cls):
        return cls.model_json_schema(ref_template="#/components/schemas/{model}")