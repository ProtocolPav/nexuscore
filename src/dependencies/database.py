from typing import Optional

from asyncpg import Pool, create_pool
import json


class Database:
    def __init__(self):
        self.pool: Optional[Pool] = None

    async def init_pool(self):
        config = json.load(open('../config.json', 'r'))

        self.pool = await create_pool(database=config['database']['name'],
                                     user=config['database']['user'],
                                     password=config['database']['password'],
                                     host=config['database']['host'],
                                     port=5432,
                                     min_size=1,
                                     max_size=10,
                                     loop=None)

    async def close_pool(self):
        if self.pool:
            await self.pool.close()

db = Database()
