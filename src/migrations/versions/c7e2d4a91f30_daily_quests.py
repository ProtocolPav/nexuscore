"""daily-quests

Revision ID: c7e2d4a91f30
Revises: 23b5838e1d36
Create Date: 2026-11-22 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7e2d4a91f30'
down_revision: Union[str, Sequence[str], None] = '23b5838e1d36'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The pool of objective templates a guild's daily quest is rolled from
    op.execute("""
        CREATE TABLE quests_v3.daily_template (
            template_id bigserial NOT NULL,
            guild_id int8 NOT NULL,
            name varchar NOT NULL,
            enabled bool DEFAULT true NOT NULL,
            weight int4 DEFAULT 1 NOT NULL,
            created_by int8 NOT NULL,
            created_at timestamptz DEFAULT now() NOT NULL,
            title varchar NOT NULL,
            description varchar NOT NULL,
            objective_description varchar NOT NULL,
            objective_display varchar NULL,
            objective_type varchar NOT NULL,
            logic varchar DEFAULT 'and'::character varying NOT NULL,
            targets jsonb DEFAULT '[]'::jsonb NOT NULL,
            target_picks jsonb NULL,
            target_count jsonb NULL,
            customizations jsonb DEFAULT '{}'::jsonb NOT NULL,
            rewards jsonb DEFAULT '[]'::jsonb NOT NULL,
            reward_picks int4 DEFAULT 1 NOT NULL,
            CONSTRAINT daily_template_pk PRIMARY KEY (template_id),
            CONSTRAINT daily_template_guild_fk FOREIGN KEY (guild_id) REFERENCES guilds.guild(guild_id),
            CONSTRAINT daily_template_user_fk FOREIGN KEY (created_by) REFERENCES users."user"(thorny_id)
        );
    """)

    # One generated daily quest per guild per (UTC) day
    op.execute("""
        CREATE TABLE quests_v3.daily_quest (
            guild_id int8 NOT NULL,
            quest_date date NOT NULL,
            quest_id int8 NOT NULL,
            template_id int8 NULL,
            CONSTRAINT daily_quest_pk PRIMARY KEY (guild_id, quest_date),
            CONSTRAINT daily_quest_guild_fk FOREIGN KEY (guild_id) REFERENCES guilds.guild(guild_id),
            CONSTRAINT daily_quest_quest_fk FOREIGN KEY (quest_id) REFERENCES quests_v3.quest(quest_id),
            CONSTRAINT daily_quest_template_fk FOREIGN KEY (template_id)
                REFERENCES quests_v3.daily_template(template_id) ON DELETE SET NULL
        );
    """)

    # Speeds up the "active quest" lookups which now filter by quest type
    op.execute("""
        CREATE INDEX IF NOT EXISTS quest_progress_thorny_status_idx
        ON quests_v3.quest_progress (thorny_id, status);
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS quests_v3.quest_progress_thorny_status_idx;")
    op.execute("DROP TABLE quests_v3.daily_quest;")
    op.execute("DROP TABLE quests_v3.daily_template;")
