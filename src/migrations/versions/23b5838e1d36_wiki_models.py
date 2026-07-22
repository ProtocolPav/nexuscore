"""Wiki Models

Revision ID: 23b5838e1d36
Revises: 05bf89b8a612
Create Date: 2026-07-09 23:46:43.376167

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '23b5838e1d36'
down_revision: Union[str, Sequence[str], None] = '05bf89b8a612'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS wiki;")

    op.execute("""
        CREATE TABLE wiki.page (
            page_id      BIGSERIAL PRIMARY KEY,
            author_id    INTEGER NOT NULL,
            guild_id     BIGINT NOT NULL,
            project_id   VARCHAR,
            slug         VARCHAR NOT NULL,
            title        VARCHAR NOT NULL,
            summary      VARCHAR,
            category     VARCHAR,
            tags         TEXT[] NOT NULL DEFAULT '{}',
            cover_image  VARCHAR,
            published    BOOLEAN NOT NULL DEFAULT FALSE,
            locked       BOOLEAN NOT NULL DEFAULT FALSE,
            view_count   INTEGER NOT NULL DEFAULT 0,
            created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_wiki_pages_guild_slug UNIQUE (guild_id, slug)
        )
    """)

    op.execute("""
        ALTER TABLE wiki.page
        ADD CONSTRAINT wiki_page_project_fk 
        FOREIGN KEY (project_id) REFERENCES projects.project(project_id);
    """)

    op.execute("""
        CREATE INDEX idx_wiki_pages_guild_id ON wiki.page (guild_id)
    """)

    op.execute("""
        CREATE INDEX idx_wiki_pages_project_id ON wiki.page (project_id)
    """)

    op.execute("""
        CREATE INDEX idx_wiki_pages_author_id ON wiki.page (author_id)
    """)

    op.execute("""
        CREATE TABLE wiki.content (
            content_id   BIGSERIAL PRIMARY KEY,
            page_id      INTEGER NOT NULL REFERENCES wiki.page (page_id) ON DELETE CASCADE,
            version      INTEGER NOT NULL,
            edited_by    INTEGER NOT NULL,
            editor_type  VARCHAR NOT NULL,
            change_note  VARCHAR NOT NULL DEFAULT '',
            content      JSONB NOT NULL,
            created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_wiki_content_page_version UNIQUE (page_id, version)
        )
    """)

    op.execute("""
        CREATE INDEX idx_wiki_content_page_id ON wiki.content (page_id)
    """)

    op.execute("""
        CREATE INDEX idx_wiki_content_edited_by ON wiki.content (edited_by)
    """)


def downgrade() -> None:
    """Downgrade schema."""
    pass
