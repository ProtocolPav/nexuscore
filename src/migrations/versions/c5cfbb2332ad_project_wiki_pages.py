"""Project wiki pages

Revision ID: c5cfbb2332ad
Revises: 23b5838e1d36
Create Date: 2026-08-29 23:34:22.514531

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5cfbb2332ad'
down_revision: Union[str, Sequence[str], None] = '23b5838e1d36'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
