import os
from typing import Optional

from asyncpg import Pool, create_pool

DATABASE_NAME = os.environ.get('DATABASE_NAME')
DATABASE_USER = os.environ.get('DATABASE_USER')
DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD')
DATABASE_HOST = os.environ.get('DATABASE_HOST')
DATABASE_PORT = os.environ.get('DATABASE_PORT')

class Database:
    def __init__(self):
        self.pool: Optional[Pool] = None

    async def init_pool(self):
        self.pool = await create_pool(database=DATABASE_NAME,
                                     user=DATABASE_USER,
                                     password=DATABASE_PASSWORD,
                                     host=DATABASE_HOST,
                                     port=DATABASE_PORT,
                                     min_size=1,
                                     max_size=10,
                                     loop=None)

    async def close_pool(self):
        if self.pool:
            await self.pool.close()

db = Database()
