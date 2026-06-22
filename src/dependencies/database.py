from contextlib import asynccontextmanager
from typing import Optional

from asyncpg import Pool, create_pool

from src.settings import settings

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

    @asynccontextmanager
    async def get_transaction(self):
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                yield connection

    @asynccontextmanager
    async def get_connection(self):
        async with self.pool.acquire() as connection:
            yield connection

db = Database()

def get_db() -> Database:
    return db