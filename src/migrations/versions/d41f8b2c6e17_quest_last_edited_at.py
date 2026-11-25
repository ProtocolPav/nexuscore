"""quest-last-edited-at

Revision ID: d41f8b2c6e17
Revises: c7e2d4a91f30
Create Date: 2026-11-25 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd41f8b2c6e17'
down_revision: Union[str, Sequence[str], None] = 'c7e2d4a91f30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE quests_v3.quest
        ADD COLUMN last_edited_at timestamptz NULL;
    """)


def downgrade():
    op.execute("""
        ALTER TABLE quests_v3.quest
        DROP COLUMN last_edited_at;
    """)
