from datetime import date, datetime
from typing import Literal, Optional

from src.database import Database
from src.utils.base import BaseList, BaseModel
from pydantic import Field

from sanic_ext import openapi

from src.utils.errors import BadRequest400, NotFound404

@openapi.component()
class KillCountModel(BaseModel):
    mob_type: str = Field(description="The mob that was killed")
    kill_count: int = Field(description="The kill count")


@openapi.component()
class KillCountListModel(BaseList[KillCountModel]):
    @classmethod
    async def fetch(cls, db: Database, thorny_id: int = None, *args) -> "KillCountListModel":
        if not thorny_id:
            raise BadRequest400(extra={'ids': ['thorny_id']})

        data = await db.pool.fetch("""
                                       SELECT
                                           reference as mob_type,
                                           COUNT(*) as kill_count
                                       FROM events.interactions
                                       WHERE thorny_id = $1
                                         AND type = 'kill'
                                         AND time >= '2025-01-01'
                                         AND time < '2025-12-13'
                                       GROUP BY reference
                                       ORDER BY kill_count DESC
                                   """, thorny_id)

        kills: list[KillCountModel] = []
        for kill in data:
            kills.append(KillCountModel(**kill))

        return cls(root=kills)


@openapi.component()
class NemesisModel(BaseModel):
    arch_nemesis: str = Field(description="The arch nemesis")
    death_count: int = Field(description="The death count")

    @classmethod
    async def fetch(cls, db: Database, thorny_id: int = None, *args) -> "NemesisModel":
        if not thorny_id:
            raise BadRequest400(extra={'ids': ['thorny_id']})

        data = await db.pool.fetchrow("""
                                          SELECT
                                              reference as arch_nemesis,
                                              COUNT(*) as death_count
                                          FROM events.interactions
                                          WHERE thorny_id = $1
                                            AND type = 'die'
                                            AND time >= '2025-01-01'
                                            AND time < '2025-12-13'
                                          GROUP BY reference
                                          ORDER BY death_count DESC
                                          LIMIT 1
                                      """,
                                      thorny_id)

        if data:
            return cls(**data)
        else:
            raise NotFound404(extra={'resource': 'playtime', 'id': f'{thorny_id}'})


@openapi.component()
class BuildMineModel(BaseModel):
    blocks_placed: int = Field(description="The blocks placed")
    blocks_mined: int = Field(description="The blocks mined")
    net_difference: int = Field(description="The net difference")
    player_type: str = Field(description="The player type, either Creator, Destroyer or Balanced Builder")

    @classmethod
    async def fetch(cls, db: Database, thorny_id: int = None, *args) -> "BuildMineModel":
        if not thorny_id:
            raise BadRequest400(extra={'ids': ['thorny_id']})

        data = await db.pool.fetchrow("""
                                          SELECT
                                              COUNT(*) FILTER (WHERE type = 'place') as blocks_placed,
                                              COUNT(*) FILTER (WHERE type = 'mine') as blocks_mined,
                                              COUNT(*) FILTER (WHERE type = 'place') - COUNT(*) FILTER (WHERE type = 'mine') as net_difference,
                                              CASE
                                                  WHEN COUNT(*) FILTER (WHERE type = 'place') > COUNT(*) FILTER (WHERE type = 'mine') * 0.65 THEN 'Creator'
                                                  WHEN COUNT(*) FILTER (WHERE type = 'mine') > COUNT(*) FILTER (WHERE type = 'place') * 3 THEN 'Destroyer'
                                                  ELSE 'Balanced Builder'
                                                  END as player_type
                                          FROM events.interactions
                                          WHERE thorny_id = $1
                                            AND type IN ('place', 'mine')
                                            AND time >= '2025-01-01'
                                            AND time < '2025-12-13'
                                      """,
                                      thorny_id)

        if data:
            return cls(**data)
        else:
            raise NotFound404(extra={'resource': 'playtime', 'id': f'{thorny_id}'})


@openapi.component()
class FavouriteBlockModel(BaseModel):
    category: str = Field(description="The category of the favourite block, placed or mined")
    month_name: str = Field(description="The month name")
    month_number: int = Field(description="The month number")
    favorite_block: str = Field(description="The favourite block")
    count: int = Field(description="The count of the favourite block")


@openapi.component()
class FavouriteBlockListModel(BaseList[FavouriteBlockModel]):
    @classmethod
    async def fetch(cls, db: Database, thorny_id: int = None, *args) -> "FavouriteBlockListModel":
        if not thorny_id:
            raise BadRequest400(extra={'ids': ['thorny_id']})

        data = await db.pool.fetch("""
                                       WITH monthly_placed AS (
                                           SELECT
                                               DATE_TRUNC('month', time) as month,
                                               reference,
                                               COUNT(*) as times_placed,
                                               ROW_NUMBER() OVER (PARTITION BY DATE_TRUNC('month', time) ORDER BY COUNT(*) DESC) as rank
                                           FROM events.interactions
                                           WHERE thorny_id = $1
                                             AND type = 'place'
                                             AND time >= '2025-01-01'
                                             AND time < '2025-12-13'
                                           GROUP BY DATE_TRUNC('month', time), reference
                                       ),
                                            monthly_mined AS (
                                                SELECT
                                                    DATE_TRUNC('month', time) as month,
                                                    reference,
                                                    COUNT(*) as times_mined,
                                                    ROW_NUMBER() OVER (PARTITION BY DATE_TRUNC('month', time) ORDER BY COUNT(*) DESC) as rank
                                                FROM events.interactions
                                                WHERE thorny_id = $1
                                                  AND type = 'mine'
                                                  AND time >= '2025-01-01'
                                                  AND time < '2025-12-13'
                                                GROUP BY DATE_TRUNC('month', time), reference
                                            )
                                       SELECT
                                           'placed' as category,
                                           TO_CHAR(month, 'Month') as month_name,
                                           EXTRACT(MONTH FROM month) as month_number,
                                           reference as favorite_block,
                                           times_placed as count
                                       FROM monthly_placed
                                       WHERE rank = 1

                                       UNION ALL

                                       SELECT
                                           'mined' as category,
                                           TO_CHAR(month, 'Month') as month_name,
                                           EXTRACT(MONTH FROM month) as month_number,
                                           reference as favorite_block,
                                           times_mined as count
                                       FROM monthly_mined
                                       WHERE rank = 1

                                       ORDER BY month_number, category DESC
                                   """, thorny_id)

        blocks: list[FavouriteBlockModel] = []
        for block in data:
            blocks.append(FavouriteBlockModel(**block))

        return cls(root=blocks)


@openapi.component()
class FavouriteProjectModel(BaseModel):
    project_id: str = Field(description="The project id")
    name: str = Field(description="The name of the project")
    blocks_placed: int = Field(description="The number of blocks placed")

    @classmethod
    async def fetch(cls, db: Database, thorny_id: int = None, *args) -> "FavouriteProjectModel":
        if not thorny_id:
            raise BadRequest400(extra={'ids': ['thorny_id']})

        data = await db.pool.fetchrow("""
                                          SELECT
                                              p.project_id,
                                              p.name,
                                              COUNT(*) as blocks_placed
                                          FROM events.interactions i
                                                   JOIN projects.project p ON p.owner_id = i.thorny_id
                                          WHERE i.thorny_id = $1
                                            AND i.type = 'place'
                                            AND i.time >= '2025-01-01'
                                            AND i.time < '2025-12-13'
                                            AND i.dimension = p.dimension
                                            AND sqrt(
                                                        power(i.coordinates[1] - p.coordinates[1], 2) +
                                                        power(i.coordinates[2] - p.coordinates[2], 2) +
                                                        power(i.coordinates[3] - p.coordinates[3], 2)
                                                ) <= 120
                                          GROUP BY p.project_id, p.name
                                          ORDER BY blocks_placed DESC
                                          LIMIT 1
                                      """,
                                      thorny_id)

        if data:
            return cls(**data)
        else:
            raise NotFound404(extra={'resource': 'playtime', 'id': f'{thorny_id}'})


@openapi.component()
class MostActiveProjectModel(BaseModel):
    project_id: str = Field(description="The project id")
    name: str = Field(description="The name of the project")
    blocks_placed: int = Field(description="The number of blocks placed")
    blocks_mined: int = Field(description="The number of blocks mined")
    interactions: int = Field(description="The number of interactions")
    total_activity: int = Field(description="The total activity")

    @classmethod
    async def fetch(cls, db: Database, thorny_id: int = None, *args) -> "MostActiveProjectModel":
        if not thorny_id:
            raise BadRequest400(extra={'ids': ['thorny_id']})

        data = await db.pool.fetchrow("""
                                          SELECT
                                              p.project_id,
                                              p.name,
                                              COUNT(*) FILTER (WHERE i.type = 'place') as blocks_placed,
                                              COUNT(*) FILTER (WHERE i.type = 'mine') as blocks_mined,
                                              COUNT(*) FILTER (WHERE i.type = 'use') as interactions,
                                              COUNT(*) as total_activity
                                          FROM events.interactions i
                                                   JOIN projects.project p ON p.owner_id = i.thorny_id
                                          WHERE i.thorny_id = $1
                                            AND i.time >= '2025-01-01'
                                            AND i.time < '2025-12-13'
                                            AND i.dimension = p.dimension
                                            AND sqrt(
                                                        power(i.coordinates[1] - p.coordinates[1], 2) +
                                                        power(i.coordinates[2] - p.coordinates[2], 2) +
                                                        power(i.coordinates[3] - p.coordinates[3], 2)
                                                ) <= 120
                                          GROUP BY p.project_id, p.name
                                          ORDER BY total_activity DESC
                                          LIMIT 1;
                                      """,
                                      thorny_id)

        if data:
            return cls(**data)
        else:
            raise NotFound404(extra={'resource': 'playtime', 'id': f'{thorny_id}'})
