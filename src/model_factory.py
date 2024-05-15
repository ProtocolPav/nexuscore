from src.models.user import UserModel, ProfileModel, PlaytimeReport
from src.models.project import ProjectModel, MembersModel, ContentModel, StatusModel
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
                                       WHERE thorny_id = $1
                                       """,
                                       thorny_id)

        return dict(UserModel.parse_obj(dict(data)))

    @classmethod
    async def build_profile_model(cls, thorny_id: int):
        data = await cls.pool.fetchrow("""
                                       SELECT * FROM users.profile
                                       WHERE thorny_id = $1
                                       """,
                                       thorny_id)

        return dict(ProfileModel.parse_obj(dict(data)))

    @classmethod
    async def build_playtime_report(cls, thorny_id: int):
        data = await cls.pool.fetchrow("""
    WITH daily_playtime AS (
        SELECT t.day, SUM(t.playtime) AS playtime
        FROM (
            SELECT SUM(playtime) AS playtime, 
                   DATE(connect_time) AS day
            FROM thorny.playtime
            INNER JOIN thorny.user ON thorny.playtime.thorny_user_id = thorny.user.thorny_user_id 
            WHERE thorny.playtime.thorny_user_id = $1
            GROUP BY day
        ) AS t
        GROUP BY t.day
        ORDER BY t.day DESC
        LIMIT 7
    ),
    total_playtime AS (
        SELECT SUM(EXTRACT(EPOCH FROM playtime)) AS total_playtime
        FROM thorny.playtime
        WHERE thorny_user_id = $1
        GROUP BY thorny_user_id
    ),
    session AS (
        SELECT connect_time as session
        FROM thorny.playtime
        WHERE thorny_user_id = $1
        GROUP BY thorny_user_id, connect_time
        order by connect_time DESC
        limit 1
    ),
    monthly_playtime AS (
        SELECT t.year || '-' || t.month AS month, SUM(t.playtime) AS playtime
        FROM (
            SELECT SUM(playtime) AS playtime, 
                   DATE_PART('month', connect_time) AS month, 
                   DATE_PART('year', connect_time) AS year
            FROM thorny.playtime
            INNER JOIN thorny.user ON thorny.playtime.thorny_user_id = thorny.user.thorny_user_id 
            WHERE thorny.playtime.thorny_user_id = $1
            GROUP BY year, month
        ) AS t
        GROUP BY t.year, t.month
        ORDER BY t.year DESC, t.month DESC
        LIMIT 12
    )
    SELECT 
        $1 AS thorny_id,
        (SELECT JSON_AGG(JSON_BUILD_OBJECT('day', wp.day, 'playtime', EXTRACT(EPOCH FROM wp.playtime)))
            FROM daily_playtime wp) AS daily,
        (SELECT total_playtime
            FROM total_playtime) AS total,
        (SELECT session
            FROM session) AS session,
        (SELECT JSON_AGG(JSON_BUILD_OBJECT('month', mp.month, 'playtime', EXTRACT(EPOCH FROM mp.playtime)))
            FROM monthly_playtime mp) AS monthly;
                                       """,
                                       thorny_id)

        processed_dict = {'thorny_id': thorny_id,
                          'total': data['total'],
                          'daily': json.loads(data['daily']),
                          'monthly': json.loads(data['monthly']),
                          'session': data['session']}

        return dict(PlaytimeReport.parse_obj(processed_dict))

    @classmethod
    async def update_user_model(cls, thorny_id: int, model: UserModel):
        await cls.pool.execute("""
                               UPDATE users.user
                               SET username = $1,
                                   birthday = $2,
                                   balance = $3,
                                   active = $4,
                                   role = $5,
                                   patron = $6,
                                   level = $7,
                                   xp = $8,
                                   required_xp = $9,
                                   last_message = $10,
                                   gamertag = $11,
                                   whitelist = $12
                               WHERE thorny_id = $13
                               """,
                               model.username, model.birthday, model.balance, model.active,
                               model.role, model.patron, model.level, model.xp, model.required_xp,
                               model.last_message, model.gamertag, model.whitelist, thorny_id)


class ProjectFactory(Factory):
    @classmethod
    async def build_project_model(cls, project_id: str):
        data = await cls.pool.fetchrow("""
                                       SELECT * FROM projects.project
                                       WHERE project_id = $1
                                       """,
                                       project_id)

        return dict(ProjectModel.parse_obj(dict(data)))

    @classmethod
    async def build_members_model(cls, project_id: str):
        data = await cls.pool.fetchrow("""
                                       SELECT ARRAY_AGG(user_id) as members FROM projects.members
                                       WHERE project_id = $1
                                       """,
                                       project_id)

        if not data['members']:
            return dict(MembersModel.parse_obj({'members': []}))
        return dict(MembersModel.parse_obj(dict(data)))

    @classmethod
    async def build_content_model(cls, project_id: str):
        data = await cls.pool.fetchrow("""
                                       SELECT content, since AS content_since, user_id AS content_edited_by
                                       FROM projects.content
                                       WHERE project_id = $1
                                       """,
                                       project_id)

        return dict(ContentModel.parse_obj(dict(data)))

    @classmethod
    async def build_status_model(cls, project_id: str):
        data = await cls.pool.fetchrow("""
                                       SELECT status, since AS status_since
                                       FROM projects.status
                                       WHERE project_id = $1
                                       """,
                                       project_id)

        return dict(StatusModel.parse_obj(dict(data)))
