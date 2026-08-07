from contextlib import asynccontextmanager
from typing import Optional

from asyncpg import Pool, create_pool
from opentelemetry import trace

from src.settings import settings

tracer = trace.get_tracer("nexuscore.database")


class TracedConnection:
    """Wraps a raw asyncpg Connection — used inside transactions."""
    def __init__(self, conn):
        self._conn = conn

    async def fetch(self, query: str, *args):
        with tracer.start_as_current_span("db.fetch") as span:
            span.set_attribute("db.system", "postgresql")
            span.set_attribute("db.statement", query.strip())
            return await self._conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        with tracer.start_as_current_span("db.fetchrow") as span:
            span.set_attribute("db.system", "postgresql")
            span.set_attribute("db.statement", query.strip())
            return await self._conn.fetchrow(query, *args)

    async def execute(self, query: str, *args):
        with tracer.start_as_current_span("db.execute") as span:
            span.set_attribute("db.system", "postgresql")
            span.set_attribute("db.statement", query.strip())
            return await self._conn.execute(query, *args)


class Database:
    def __init__(self):
        self.__pool: Pool = None

    async def init_pool(self):
        self.__pool = await create_pool(database=settings.DATABASE_NAME,
                                      user=settings.DATABASE_USER,
                                      password=settings.DATABASE_PASSWORD,
                                      host=settings.DATABASE_HOST,
                                      port=settings.DATABASE_PORT,
                                      min_size=1,
                                      max_size=10,
                                      loop=None)

    async def close_pool(self):
        if self.__pool:
            await self.__pool.close()

    async def fetch(self, query: str, *args):
        with tracer.start_as_current_span("db.fetch") as span:
            span.set_attribute("db.system", "postgresql")
            span.set_attribute("db.statement", query.strip())
            return await self.__pool.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        with tracer.start_as_current_span("db.fetchrow") as span:
            span.set_attribute("db.system", "postgresql")
            span.set_attribute("db.statement", query.strip())
            return await self.__pool.fetchrow(query, *args)

    async def fetchval(self, query: str, *args):
        with tracer.start_as_current_span("db.fetchval") as span:
            span.set_attribute("db.system", "postgresql")
            span.set_attribute("db.statement", query.strip())
            return await self.__pool.fetchval(query, *args)

    async def execute(self, query: str, *args):
        with tracer.start_as_current_span("db.execute") as span:
            span.set_attribute("db.system", "postgresql")
            span.set_attribute("db.statement", query.strip())
            return await self.__pool.execute(query, *args)

    @asynccontextmanager
    async def get_transaction(self):
        with tracer.start_as_current_span("db.transaction") as tx_span:
            tx_span.set_attribute("db.system", "postgresql")
            async with self.__pool.acquire() as connection:
                async with connection.transaction():
                    yield TracedConnection(connection)

    @asynccontextmanager
    async def get_connection(self):
        async with self.__pool.acquire() as connection:
            yield TracedConnection(connection)


db = Database()

def get_db() -> Database:
    return db