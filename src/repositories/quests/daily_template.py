import json
from typing import Optional

from src.dependencies.database import Database
from src.errors import NotFound
from src.models.quests.daily import DailyTemplateDB, DailyTemplateIn


class DailyTemplateRepository:
    def __init__(self, db: Database):
        self.db = db

    @staticmethod
    def _json_args(model: DailyTemplateIn) -> tuple:
        def dump(value) -> Optional[str]:
            return json.dumps(value) if value is not None else None

        data = model.model_dump(mode='json')
        for target in data['targets']:
            target.pop('target_uuid', None)

        return (
            model.name, model.enabled, model.weight, model.created_by,
            model.title, model.description, model.objective_description, model.objective_display,
            model.objective_type, model.logic,
            dump(data['targets']),
            dump(data['target_picks']),
            dump(data['target_count']),
            dump(data['customizations']),
            dump(data['rewards']),
            model.reward_picks,
        )

    async def fetch(self, template_id: int, guild_id: int) -> DailyTemplateDB:
        data = await self.db.fetchrow("""
            SELECT * FROM quests_v3.daily_template
            WHERE template_id = $1
            AND guild_id = $2
        """, template_id, guild_id)

        if not data:
            raise NotFound("Daily Template")

        return DailyTemplateDB.model_validate(dict(data))

    async def fetch_all(self, guild_id: int, enabled: Optional[bool] = None) -> list[DailyTemplateDB]:
        data = await self.db.fetch("""
            SELECT * FROM quests_v3.daily_template
            WHERE guild_id = $1
            AND ($2::bool IS NULL OR enabled = $2::bool)
            ORDER BY template_id
        """, guild_id, enabled)

        return [DailyTemplateDB.model_validate(dict(t)) for t in data]

    async def fetch_guilds_with_enabled_templates(self) -> list[int]:
        data = await self.db.fetch("""
            SELECT DISTINCT guild_id FROM quests_v3.daily_template
            WHERE enabled = true
        """)

        return [row['guild_id'] for row in data]

    async def create(self, guild_id: int, model: DailyTemplateIn) -> DailyTemplateDB:
        data = await self.db.fetchrow("""
            INSERT INTO quests_v3.daily_template(
                name, enabled, weight, created_by,
                title, description, objective_description, objective_display,
                objective_type, logic,
                targets, target_picks, target_count, customizations, rewards, reward_picks,
                guild_id
            )
            VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                   $11::jsonb, $12::jsonb, $13::jsonb, $14::jsonb, $15::jsonb, $16, $17)
            RETURNING *
        """, *self._json_args(model), guild_id)

        return DailyTemplateDB.model_validate(dict(data))

    async def update(self, template_id: int, guild_id: int, model: DailyTemplateIn) -> DailyTemplateDB:
        data = await self.db.fetchrow("""
            UPDATE quests_v3.daily_template
            SET name = $1,
                enabled = $2,
                weight = $3,
                created_by = $4,
                title = $5,
                description = $6,
                objective_description = $7,
                objective_display = $8,
                objective_type = $9,
                logic = $10,
                targets = $11::jsonb,
                target_picks = $12::jsonb,
                target_count = $13::jsonb,
                customizations = $14::jsonb,
                rewards = $15::jsonb,
                reward_picks = $16
            WHERE template_id = $17
            AND guild_id = $18
            RETURNING *
        """, *self._json_args(model), template_id, guild_id)

        if not data:
            raise NotFound("Daily Template")

        return DailyTemplateDB.model_validate(dict(data))

    async def delete(self, template_id: int, guild_id: int) -> None:
        result = await self.db.execute("""
            DELETE FROM quests_v3.daily_template
            WHERE template_id = $1
            AND guild_id = $2
        """, template_id, guild_id)

        if result.endswith(" 0"):
            raise NotFound("Daily Template")
