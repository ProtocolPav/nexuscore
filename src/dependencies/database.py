from typing import Optional

from asyncpg import Pool, create_pool
from src.config import settings

class Database:
    def __init__(self):
        self.pool: Optional[Pool] = None

    async def init_pool(self):
        self.pool = await create_pool(database=settings.DATABASE_NAME,
                                     user=settings.DATABASE_USER,
                                     password=settings.DATABASE_PASSWORD,
                                     host=settings.DATABASE_HOST,
                                     port=settings.DATABASE_PORT,
                                     min_size=1,
                                     max_size=10,
                                     loop=None)

    async def close_pool(self):
        if self.pool:
            await self.pool.close()

db = Database()
