from pydantic import BaseModel
from asyncpg import Pool, create_pool
import json


class Base(BaseModel):
    ...
