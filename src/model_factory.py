from src.models.user import UserModel, ProfileModel
from asyncpg import Pool, create_pool
import json


class Factory:
    pool: Pool

    @classmethod
    async def init_pool(cls):
        config = json.load(open('./config.json', 'r+'))
        cls.pool = await create_pool(database=config['database']['name'],
                                     user=config['database']['user'],
                                     password=config['database']['password'],
                                     host=config['database']['host'],
                                     port=5432,
                                     max_inactive_connection_lifetime=1.0,
                                     max_size=3000,
                                     loop=None)


class UserFactory(Factory):
    @classmethod
    async def build_user_model(cls, thorny_id: int):
        data = await cls.pool.fetchrow("""
                                       SELECT * FROM users.user
                                       WHERE users.user.thorny_id = $1
                                       """,
                                       thorny_id)

        return dict(UserModel.parse_obj(dict(data)))

    @classmethod
    async def build_profile_model(cls, thorny_id: int):
        data = await cls.pool.fetchrow("""
                                       SELECT * FROM users.profile
                                       WHERE users.profile.thorny_id = $1
                                       """,
                                       thorny_id)

        return dict(ProfileModel.parse_obj(dict(data)))
