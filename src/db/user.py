from src.db.pool import webserver_pool
from src.db.utils import recursive_dict_update


async def fetch_user_by_id(thorny_id: int):
    async with webserver_pool.connection() as conn:
        user_data = await conn.fetchrow("""
                                        SELECT * FROM thorny.user
                                        WHERE thorny.user.thorny_user_id = $1
                                        """,
                                        thorny_id
                                        )

        profile_data = await conn.fetchrow("""
                                           SELECT * FROM thorny.profile
                                           WHERE thorny.profile.thorny_user_id = $1
                                           """,
                                           thorny_id
                                           )

        monthly_playtime = await conn.fetch("""
                                            SELECT t.year, t.month, sum(t.playtime) as playtime
                                            FROM (SELECT sum(playtime) as playtime, 
                                                         date_part('month', connect_time) as month, 
                                                         date_part('year', connect_time) as year
                                                  FROM thorny.playtime
                                                  INNER JOIN thorny.user 
                                                    ON thorny.playtime.thorny_user_id = thorny.user.thorny_user_id 
                                                  WHERE thorny.playtime.thorny_user_id = $1
                                                  GROUP BY connect_time 
                                                  ) as t
                                            GROUP BY t.year, t.month
                                            ORDER BY t.year DESC, t.month DESC
                                            """,
                                            thorny_id
                                            )

        daily_playtime = await conn.fetch("""
                                          SELECT t.day, sum(t.playtime) as playtime 
                                          FROM (SELECT sum(playtime) as playtime, 
                                                       date(connect_time) as day
                                                FROM thorny.playtime
                                                INNER JOIN thorny.user
                                                    ON thorny.playtime.thorny_user_id = thorny.user.thorny_user_id 
                                                WHERE thorny.playtime.thorny_user_id = $1
                                                GROUP BY day 
                                                ) as t
                                          GROUP BY t.day
                                          ORDER BY t.day DESC
                                          """,
                                          thorny_id
                                          )

        total_playtime = await conn.fetchrow("""
                                             SELECT SUM(playtime) as total_playtime
                                             FROM thorny.playtime
                                             WHERE thorny_user_id = $1
                                             GROUP BY thorny_user_id
                                             """,
                                             thorny_id
                                             )

        current_session = await conn.fetchrow("""
                                              SELECT * FROM thorny.playtime
                                              WHERE thorny_user_id = $1
                                              AND disconnect_time is null
                                              ORDER BY connect_time desc
                                              LIMIT 1
                                              """,
                                              thorny_id
                                              )

        projects = await conn.fetch("""
                                    SELECT project_id, name FROM thorny.projects
                                    WHERE owner_id = $1
                                    """,
                                    thorny_id
                                    )

        levels = await conn.fetchrow("""
                                     SELECT * FROM thorny.levels
                                     WHERE thorny_user_id = $1
                                     """,
                                     thorny_id
                                     )

    user = {
        "thorny_id": user_data['thorny_user_id'],
        "discord_id": user_data['user_id'],
        "guild_id": user_data['guild_id'],
        "username": user_data['username'],
        "guild_join_date": user_data['join_date'],
        "birthday": user_data['birthday'],
        "balance": user_data['balance'],
        "is_in_guild": user_data['active'],
        "profile": {
            "slogan": profile_data['slogan'],
            "gamertag": profile_data['gamertag'],
            "whitelisted_gamertag": profile_data['whitelisted_gamertag'],
            "aboutme": profile_data['aboutme'],
            "character": {
                "lore": profile_data['lore'],
                "name": profile_data['character_name'],
                "age": profile_data['character_age'],
                "race": profile_data['character_race'],
                "role": profile_data['character_role'],
                "origin": profile_data['character_origin'],
                "beliefs": profile_data['character_beliefs'],
                "agility": profile_data['agility'],
                "valor": profile_data['valor'],
                "strength": profile_data['strength'],
                "charisma": profile_data['charisma'],
                "creativity": profile_data['creativity'],
                "ingenuity": profile_data['ingenuity']
            }
        },
        "levels": {
            "level": levels['user_level'],
            "xp": levels['xp'],
            "required_xp": levels['required_xp'],
            "last_message": levels['last_message']
        },
        "read_only": {
            "playtime": {
                "monthly": [{"year": month['year'],
                             "month": month['month'],
                             "playtime": month['playtime']
                             } for month in monthly_playtime],
                "daily": [{"day": day['day'],
                           "playtime": day['playtime']
                           } for day in daily_playtime],
                "total": total_playtime['total_playtime'],
                "current_connection": current_session
            },
            "projects": [{"id": project['project_id'],
                          "name": project['name']
                          } for project in projects]
        }
    }

    return user


async def fetch_user_by_gamertag(guild_id: int, gamertag: str):
    async with webserver_pool.connection() as conn:
        thorny_id = await conn.fetchrow("""
                                        SELECT thorny.user.thorny_user_id FROM thorny.user
                                        INNER JOIN thorny.profile
                                            ON thorny.user.thorny_user_id = thorny.profile.thorny_user_id
                                        WHERE thorny.user.guild_id = $1
                                        AND thorny.profile.whitelisted_gamertag = $2
                                        """,
                                        guild_id, gamertag
                                        )

        return await fetch_user_by_id(thorny_id[0])


async def fetch_user_by_discord_id(guild_id: int, discord_id: int):
    async with webserver_pool.connection() as conn:
        thorny_id = await conn.fetchrow("""
                                        SELECT thorny.user.thorny_user_id FROM thorny.user
                                        WHERE thorny.user.guild_id = $1
                                        AND thorny.user.user_id = $2
                                        """,
                                        guild_id, discord_id
                                        )

        return await fetch_user_by_id(thorny_id[0])


async def update_user(user: dict, updates: dict):
    recursive_dict_update(user, updates)

    async with webserver_pool.connection() as conn:
        await conn.execute("""
                           UPDATE thorny.user
                           SET username = $2, join_date = $3, birthday = $4, balance = $5, active = $6
                           WHERE thorny_user_id = $1
                           """,
                           user['thorny_id'], user['username'], user['guild_join_date'], user['birthday'],
                           user['balance'], user['is_in_guild'])

        profile = user['profile']
        character = profile['character']
        await conn.execute("""
                           UPDATE thorny.profile
                           SET slogan = $2, gamertag = $3, aboutme = $4, lore = $5, character_name = $6, character_age = $7,
                           character_race = $8, character_origin = $9, character_role = $10, character_beliefs = $11,
                           agility = $12, strength = $13, valor = $14, charisma = $15, creativity = $16, ingenuity = $17,
                           whitelisted_gamertag = $18
                           WHERE thorny_user_id = $1
                           """,
                           user['thorny_id'], profile['slogan'], profile['gamertag'], profile['aboutme'], character['lore'],
                           character['name'], character['age'], character['race'], character['origin'], character['role'],
                           character['beliefs'], character['agility'], character['strength'], character['valor'],
                           character['charisma'], character['creativity'], character['ingenuity'],
                           profile['whitelisted_gamertag'])

        levels = user['levels']
        await conn.execute("""
                           UPDATE thorny.levels
                           SET user_level = $2, xp = $3, required_xp = $4, last_message = $5
                           WHERE thorny_user_id = $1
                           """,
                           user['thorny_id'], levels['level'], levels['xp'], levels['required_xp'], levels['last_message'])

    return user

