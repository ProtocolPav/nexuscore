"""Events Models

Revision ID: 32dd5688b699
Revises: 05bf89b8a612
Create Date: 2026-07-02 18:06:22.826013

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '32dd5688b699'
down_revision: Union[str, Sequence[str], None] = '05bf89b8a612'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS events;")

    op.execute("""
        CREATE TABLE events.event (
            event_id     SERIAL PRIMARY KEY,
            guild_id     BIGINT NOT NULL,
            slug         TEXT NOT NULL UNIQUE,
            title        TEXT NOT NULL,
            description  TEXT NOT NULL,
            image_url    TEXT,
            start_time   TIMESTAMP NOT NULL,
            end_time     TIMESTAMP NOT NULL,
            status       TEXT NOT NULL DEFAULT 'draft',
            blocks       JSONB NOT NULL DEFAULT '[]'::jsonb,
            created_at   TIMESTAMP NOT NULL DEFAULT now(),
            updated_at   TIMESTAMP NOT NULL DEFAULT now()
        );
    """)

    op.execute("""CREATE INDEX idx_events_guild_id ON events.event (guild_id);""")
    op.execute("""CREATE INDEX idx_events_status ON events.event (status);""")
    op.execute("""CREATE INDEX idx_events_blocks ON events.event USING GIN (blocks);""")


def downgrade() -> None:
    op.execute("""DROP INDEX IF EXISTS idx_events_blocks;""")
    op.execute("""DROP INDEX IF EXISTS idx_events_status;""")
    op.execute("""DROP INDEX IF EXISTS idx_events_guild_id;""")
    op.execute("""DROP TABLE IF EXISTS events.event;""")
    op.execute("DROP SCHEMA IF EXISTS events;")
