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
        ADD CONSTRAINT auth_clients_guild_fk 
        FOREIGN KEY (guild_id) REFERENCES guilds.guild(guild_id);
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

    # User Tables
    op.execute("""
        CREATE TABLE users."user" (
            thorny_id bigserial NOT NULL,
            user_id int8 NOT NULL,
            guild_id int8 NOT NULL,
            username varchar NULL,
            join_date date DEFAULT now() NOT NULL,
            birthday date NULL,
            balance int4 DEFAULT 0 NOT NULL,
            active bool DEFAULT true NOT NULL,
            "role" varchar DEFAULT 'Dweller'::character varying NOT NULL,
            patron bool DEFAULT false NOT NULL,
            "level" int4 DEFAULT 0 NOT NULL,
            xp int4 DEFAULT 0 NOT NULL,
            required_xp int4 DEFAULT 100 NOT NULL,
            last_message timestamptz DEFAULT now() NOT NULL,
            gamertag varchar NULL,
            whitelist varchar NULL,
            "location" _int2 NULL,
            dimension varchar NULL,
            hidden bool DEFAULT false NOT NULL,
            xuid varchar NULL,
            CONSTRAINT user_pkey PRIMARY KEY (thorny_id)
        );
    """)

    op.execute("""
        ALTER TABLE users."user"
        ADD CONSTRAINT user_guild_fk 
        FOREIGN KEY (guild_id) REFERENCES guilds.guild(guild_id);
    """)

    op.execute("""
        CREATE TABLE users.profile (
            thorny_id int8 NOT NULL,
            slogan varchar(35) DEFAULT 'My Cool Slogan'::character varying NOT NULL,
            aboutme varchar(300) DEFAULT 'I am a really amazing person and I should definitely write more about myself!'::character varying NOT NULL,
            lore varchar(300) DEFAULT 'This character has a super interesting backstory. I should write about it.'::character varying NOT NULL,
            character_name varchar(35) DEFAULT 'My Character'::character varying NOT NULL,
            character_age int4 DEFAULT 0 NOT NULL,
            character_race varchar(35) DEFAULT 'Human'::character varying NOT NULL,
            character_role varchar(35) DEFAULT 'Adventurer'::character varying NOT NULL,
            character_origin varchar(35) DEFAULT 'Earth-like Realm'::character varying NOT NULL,
            character_beliefs varchar(35) DEFAULT 'Thorny Religion'::character varying NOT NULL,
            agility int4 DEFAULT 1 NOT NULL,
            valor int4 DEFAULT 1 NOT NULL,
            strength int4 DEFAULT 1 NOT NULL,
            charisma int4 DEFAULT 1 NOT NULL,
            creativity int4 DEFAULT 1 NOT NULL,
            ingenuity int4 DEFAULT 1 NOT NULL,
            CONSTRAINT profile_pkey PRIMARY KEY (thorny_id)
        );
    """)

    op.execute("""
        ALTER TABLE users.profile 
        ADD CONSTRAINT profile_user_fk 
        FOREIGN KEY (thorny_id) REFERENCES users."user"(thorny_id);
    """)

    # Connections
    op.execute("""
        CREATE TABLE events.connections (
            connection_id bigserial NOT NULL,
            "time" timestamptz DEFAULT now() NOT NULL,
            "type" varchar NOT NULL,
            thorny_id int8 NOT NULL,
            ignored bool DEFAULT false NOT NULL,
            CONSTRAINT connections_pk PRIMARY KEY (connection_id)
        );
    """)

    op.execute("""
        CREATE INDEX idx_connections_ignored ON events.connections USING btree (ignored);
        CREATE INDEX idx_connections_thorny_id ON events.connections USING btree (thorny_id);
        CREATE INDEX idx_connections_time ON events.connections USING btree ("time");
        CREATE INDEX idx_connections_type ON events.connections USING btree (type);
    """)

    op.execute("""
        ALTER TABLE events.connections 
        ADD CONSTRAINT connections_user_fk 
        FOREIGN KEY (thorny_id) REFERENCES users."user"(thorny_id);
    """)



def downgrade() -> None:
    """Downgrade schema."""
    pass
