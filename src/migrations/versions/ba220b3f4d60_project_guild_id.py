"""project-guild-id

Revision ID: ba220b3f4d60
Revises: a56b022de770
Create Date: 2026-06-19 22:14:50.350489

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ba220b3f4d60'
down_revision: Union[str, Sequence[str], None] = 'a56b022de770'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE projects.project
        ADD COLUMN guild_id int8;
    """)

    op.execute("""
        UPDATE projects.project
        SET guild_id = 611008530077712395
        WHERE guild_id IS NULL;
    """)

    op.execute("""
        ALTER TABLE projects.project
        ALTER COLUMN guild_id SET NOT NULL;
    """)

    op.execute("""
        ALTER TABLE projects.project
        ADD CONSTRAINT project_guild_fk
        FOREIGN KEY (guild_id) REFERENCES guilds.guild(guild_id);
    """)


def downgrade():
    op.execute("""
        ALTER TABLE projects.project
        DROP CONSTRAINT project_guild_fk;
    """)

    op.execute("""
        ALTER TABLE projects.project
        DROP COLUMN guild_id;
    """)
