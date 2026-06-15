"""initial-migration

Revision ID: a56b022de770
Revises: 
Create Date: 2026-06-15 01:58:54.208036

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a56b022de770'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Auth Table
    op.execute("""
        CREATE TABLE IF NOT EXISTS auth.clients (
            client_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            client_name     TEXT NOT NULL,
            hashed_key      TEXT NOT NULL,
            tier            TEXT NOT NULL DEFAULT 'guild',
            guild_id        BIGINT,
            scopes          TEXT[] NOT NULL DEFAULT '{}',
            is_active       BOOLEAN NOT NULL DEFAULT TRUE,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
            last_used_at    TIMESTAMPTZ
        );
    """)

    op.execute("""
        ALTER TABLE auth.clients
        ADD CONSTRAINT chk_guild_id
        CHECK (
            (tier = 'guild' AND guild_id IS NOT NULL) OR
            (tier = 'master' AND guild_id IS NULL)
        );
    """)

    op.execute("""
        CREATE INDEX idx_clients_guild_id ON auth.clients (guild_id)
            WHERE guild_id IS NOT NULL;
    """)

    # Guild Tables
    op.execute("""
        CREATE TABLE IF NOT EXISTS guilds.guild (
            guild_id         int8 NOT NULL,
            "name"           varchar NOT NULL,
            currency_name    varchar DEFAULT 'nugs'::character varying NULL,
            currency_emoji   varchar DEFAULT '<:Nug:884320353202081833>'::character varying NULL,
            level_up_message varchar DEFAULT 'Keep chatting and maybe, just maybe you will beat the #1!'::character varying NULL,
            join_message     varchar DEFAULT 'Have fun, and remember to follow the rules!'::character varying NULL,
            leave_message    varchar DEFAULT 'Always sad to see someone go :pensive:'::character varying NULL,
            xp_multiplier    int4 DEFAULT 1 NOT NULL,
            active           bool DEFAULT true NOT NULL,
            created_on       timestamptz DEFAULT now() NOT NULL,
            CONSTRAINT guildv2_pk PRIMARY KEY (guild_id)
        );
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS guilds.features (
            guild_id int8 NOT NULL,
            feature varchar NOT NULL,
            configured bool DEFAULT false NOT NULL,
            CONSTRAINT features_pk PRIMARY KEY (guild_id, feature)
        );
    """)

    op.execute("""
        ALTER TABLE guilds.features 
        ADD CONSTRAINT features_guild_fk 
        FOREIGN KEY (guild_id) REFERENCES guilds.guild(guild_id);
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS guilds.channels (
            guild_id int8 NOT NULL,
            channel_type varchar NOT NULL,
            channel_id int8 NOT NULL,
            CONSTRAINT channels_pk PRIMARY KEY (guild_id, channel_type)
        );
    """)

    op.execute("""
        ALTER TABLE guilds.channels 
        ADD CONSTRAINT channels_guild_fk 
        FOREIGN KEY (guild_id) REFERENCES guilds.guild(guild_id);
    """)

    #


def downgrade() -> None:
    """Downgrade schema."""
    pass
