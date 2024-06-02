from asyncpg import Pool, create_pool
import json


class Database:
    def __init__(self, pool: Pool):
        self.pool = pool

    @classmethod
    async def init_pool(cls):
        config = json.load(open('./config.json', 'r+'))

        return cls(await create_pool(database=config['database']['name'],
                                     user=config['database']['user'],
                                     password=config['database']['password'],
                                     host=config['database']['host'],
                                     port=5432,
                                     min_size=1,
                                     max_size=10,
                                     loop=None))
