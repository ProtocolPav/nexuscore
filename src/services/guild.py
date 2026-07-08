import asyncio

from src.dependencies.database import db
from src.models.guilds import (
    ChannelOut,
    ConnectionIn,
    ConnectionOut,
    FeatureOut,
    GuildIn,
    GuildOut,
    GuildPlaytimeAnalysis,
    GuildUpdate,
    InteractionIn,
    InteractionOut,
    OnlineMember
)
from src.models.guilds.guild import GuildDB
from src.models.guilds.interaction import InteractionQuery
from src.models.guilds.session import SessionDB, SessionOut, SessionQuery
from src.models.users import playtime
from src.models.users.profile import ProfileOut
from src.models.users.user import UserOut

from src.repositories.guild import GuildRepository

from fastapi import HTTPException

from src.repositories.user import UserRepository


class GuildService:
    def __init__(self, guild_repo: GuildRepository, user_repo: UserRepository):
        self.guild_repo = guild_repo
        self.user_repo = user_repo

    async def _to_out(self, guild: GuildDB) -> GuildOut:
        features = await self.get_features(guild.guild_id)
        channels = await self.get_channels(guild.guild_id)

        return GuildOut(
            **guild.model_dump(),
            features=features,
            channels=channels
        )

    async def _session_to_out(self, guild_id: int, session: SessionDB) -> SessionOut:
        user = await self.user_repo.fetch(guild_id, session.thorny_id)
        profile = await self.user_repo.fetch_profile(guild_id, session.thorny_id)

        return SessionOut(
            start=session.connect_time,
            end=session.disconnect_time,
            duration=session.playtime.total_seconds() if session.playtime else None,
            user=UserOut(
                **user.model_dump(),
                profile=ProfileOut(**profile.model_dump())
            )
        )

    async def get(self, guild_id: int) -> GuildOut:
        guild_db = await self.guild_repo.fetch(guild_id)
        return await self._to_out(guild_db)

    async def new(self, model: GuildIn) -> GuildOut:
        guild_db = await self.guild_repo.create(model)
        return await self._to_out(guild_db)

    async def update(self, guild_id: int, model: GuildUpdate) -> GuildOut:
        guild_db = await self.guild_repo.update(guild_id, model)
        return await self._to_out(guild_db)

    async def get_features(self, guild_id: int) -> list[FeatureOut]:
        features_db = await self.guild_repo.fetch_features(guild_id)
        return [FeatureOut(**f.model_dump()) for f in features_db]

    async def get_channels(self, guild_id: int) -> list[ChannelOut]:
        channels_db = await self.guild_repo.fetch_channels(guild_id)
        return [ChannelOut(**c.model_dump()) for c in channels_db]

    async def get_online_members(self, guild_id: int) -> list[OnlineMember]:
        return await self.guild_repo.fetch_online_members(guild_id)

    async def get_sessions(self, guild_id: int, query: SessionQuery) -> list[SessionOut]:
        sessions_db = await self.guild_repo.fetch_sessions(guild_id, query)

        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(self._session_to_out(guild_id, s)) for s in sessions_db]

        return [t.result() for t in tasks]

    async def get_playtime_analysis(self, guild_id: int) -> GuildPlaytimeAnalysis:
        return await self.guild_repo.fetch_playtime_analysis(guild_id)

    async def new_connection(self, model: ConnectionIn) -> ConnectionOut:
        ignored = False

        try:
            user_playtime = await playtime.PlaytimeSummary.fetch(db, model.thorny_id)

            if (model.type == 'connect' and user_playtime.session) or (model.type == 'disconnect' and not user_playtime.session):
                ignored = True
        except HTTPException:
            # In case the playtime summary fetch fails, we still want to create the connection
            pass

        connection_db = await self.guild_repo.create_connection(model, ignored)

        return ConnectionOut(**connection_db.model_dump())

    async def new_interaction(self, model: InteractionIn) -> InteractionOut:
        interaction_db = await self.guild_repo.create_interaction(model)
        return InteractionOut(**interaction_db.model_dump())

    async def get_interactions(self, query: InteractionQuery) -> list[InteractionOut]:
        interactions_db = await self.guild_repo.fetch_interactions(query)
        return [InteractionOut(**i.model_dump()) for i in interactions_db]