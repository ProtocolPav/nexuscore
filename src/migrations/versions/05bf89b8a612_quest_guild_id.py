"""quest-guild-id

Revision ID: 05bf89b8a612
Revises: ba220b3f4d60
Create Date: 2026-06-20 14:24:03.930047

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05bf89b8a612'
down_revision: Union[str, Sequence[str], None] = 'ba220b3f4d60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE quests_v3.quest
        ADD COLUMN guild_id int8;
    """)

    op.execute("""
        UPDATE quests_v3.quest
        SET guild_id = 611008530077712395
        WHERE guild_id IS NULL;
    """)

    op.execute("""
        ALTER TABLE quests_v3.quest
        ALTER COLUMN guild_id SET NOT NULL;
    """)

    op.execute("""
        ALTER TABLE quests_v3.quest
        ADD CONSTRAINT quest_guild_fk
        FOREIGN KEY (guild_id) REFERENCES guilds.guild(guild_id);
    """)


def downgrade():
    op.execute("""
        ALTER TABLE quests_v3.quest
        DROP CONSTRAINT quest_guild_fk;
    """)

    op.execute("""
        ALTER TABLE quests_v3.quest
        DROP COLUMN guild_id;
    """)
