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
from opentelemetry import trace

from src.repositories.user import UserRepository
from src.utils.tracing import traced


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

    @traced
    async def get(self, guild_id: int) -> GuildOut:
        span = trace.get_current_span()
        span.set_attribute("guild.id", guild_id)

        guild_db = await self.guild_repo.fetch(guild_id)
        return await self._to_out(guild_db)

    @traced
    async def new(self, model: GuildIn) -> GuildOut:
        span = trace.get_current_span()
        span.set_attribute("guild.id", model.guild_id)

        guild_db = await self.guild_repo.create(model)
        return await self._to_out(guild_db)

    @traced
    async def update(self, guild_id: int, model: GuildUpdate) -> GuildOut:
        span = trace.get_current_span()
        span.set_attribute("guild.id", guild_id)

        guild_db = await self.guild_repo.update(guild_id, model)
        return await self._to_out(guild_db)

    @traced
    async def get_features(self, guild_id: int) -> list[FeatureOut]:
        span = trace.get_current_span()
        span.set_attribute("guild.id", guild_id)

        features_db = await self.guild_repo.fetch_features(guild_id)
        return [FeatureOut(**f.model_dump()) for f in features_db]

    @traced
    async def get_channels(self, guild_id: int) -> list[ChannelOut]:
        span = trace.get_current_span()
        span.set_attribute("guild.id", guild_id)

        channels_db = await self.guild_repo.fetch_channels(guild_id)
        return [ChannelOut(**c.model_dump()) for c in channels_db]

    @traced
    async def get_online_members(self, guild_id: int) -> list[OnlineMember]:
        span = trace.get_current_span()
        span.set_attribute("guild.id", guild_id)

        return await self.guild_repo.fetch_online_members(guild_id)

    @traced
    async def get_sessions(self, guild_id: int, query: SessionQuery) -> list[SessionOut]:
        span = trace.get_current_span()
        span.set_attribute("guild.id", guild_id)

        sessions_db = await self.guild_repo.fetch_sessions(guild_id, query)
        span.set_attribute("sessions.count", len(sessions_db))

        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(self._session_to_out(guild_id, s)) for s in sessions_db]

        return [t.result() for t in tasks]

    @traced
    async def get_playtime_analysis(self, guild_id: int) -> GuildPlaytimeAnalysis:
        span = trace.get_current_span()
        span.set_attribute("guild.id", guild_id)

        return await self.guild_repo.fetch_playtime_analysis(guild_id)

    @traced
    async def new_connection(self, model: ConnectionIn) -> ConnectionOut:
        span = trace.get_current_span()
        span.set_attribute("connection.thorny_id", model.thorny_id)
        span.set_attribute("connection.type", model.type)

        ignored = False

        try:
            user_playtime = await playtime.PlaytimeSummary.fetch(db, model.thorny_id)

            if (model.type == 'connect' and user_playtime.session) or (model.type == 'disconnect' and not user_playtime.session):
                ignored = True
        except HTTPException:
            # In case the playtime summary fetch fails, we still want to create the connection
            pass

        span.set_attribute("connection.ignored", ignored)

        connection_db = await self.guild_repo.create_connection(model, ignored)

        return ConnectionOut(**connection_db.model_dump())

    @traced
    async def new_interaction(self, model: InteractionIn) -> InteractionOut:
        interaction_db = await self.guild_repo.create_interaction(model)
        return InteractionOut(**interaction_db.model_dump())

    @traced
    async def get_interactions(self, query: InteractionQuery) -> list[InteractionOut]:
        interactions_db = await self.guild_repo.fetch_interactions(query)
        return [InteractionOut(**i.model_dump()) for i in interactions_db]