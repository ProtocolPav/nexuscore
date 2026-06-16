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
    op.execute("CREATE SCHEMA IF NOT EXISTS guilds;")
    op.execute("CREATE SCHEMA IF NOT EXISTS users;")
    op.execute("CREATE SCHEMA IF NOT EXISTS quests_v3;")
    op.execute("CREATE SCHEMA IF NOT EXISTS events;")
    op.execute("CREATE SCHEMA IF NOT EXISTS auth;")
    op.execute("CREATE SCHEMA IF NOT EXISTS \"server\";")
    op.execute("CREATE SCHEMA IF NOT EXISTS projects;")

    # Guild
    op.execute("""
        CREATE TABLE guilds.guild (
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
            CONSTRAINT guild_pk PRIMARY KEY (guild_id)
        );
    """)

    # Guild Features
    op.execute("""
        CREATE TABLE guilds.features (
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

    # Guild Channels
    op.execute("""
        CREATE TABLE guilds.channels (
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
        CREATE TABLE auth.clients (
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

    # User
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
            CONSTRAINT user_pk PRIMARY KEY (thorny_id)
        );
    """)

    op.execute("""
        ALTER TABLE users."user"
        ADD CONSTRAINT user_guild_fk 
        FOREIGN KEY (guild_id) REFERENCES guilds.guild(guild_id);
    """)

    # User Profile
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
            CONSTRAINT profile_pk PRIMARY KEY (thorny_id)
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
            CONSTRAINT connection_pk PRIMARY KEY (connection_id)
        );
    """)

    op.execute("CREATE INDEX idx_connections_ignored ON events.connections USING btree (ignored);")
    op.execute("CREATE INDEX idx_connections_thorny_id ON events.connections USING btree (thorny_id);")
    op.execute("CREATE INDEX idx_connections_time ON events.connections USING btree (\"time\");")
    op.execute("CREATE INDEX idx_connections_type ON events.connections USING btree (type);")

    op.execute("""
        ALTER TABLE events.connections 
        ADD CONSTRAINT connections_user_fk 
        FOREIGN KEY (thorny_id) REFERENCES users."user"(thorny_id);
    """)

    # Sessions View
    op.execute("""
        CREATE OR REPLACE VIEW events.sessions_view
        AS SELECT connect.connection_id AS connect_event_id,
            connect."time" AS connect_time,
            disconnect.connection_id AS disconnect_event_id,
            disconnect."time" AS disconnect_time,
            disconnect."time" - connect."time" AS playtime,
            connect.thorny_id
           FROM events.connections connect
             LEFT JOIN events.connections disconnect ON connect.thorny_id = disconnect.thorny_id AND disconnect.type::text = 'disconnect'::text AND disconnect.ignored = false AND disconnect."time" = (( SELECT min(d."time") AS min
                   FROM events.connections d
                  WHERE d.type::text = 'disconnect'::text AND d.ignored = false AND d.thorny_id = connect.thorny_id AND d."time" > connect."time"))
          WHERE connect.type::text = 'connect'::text AND connect.ignored = false
          ORDER BY connect."time";
    """)

    # Interactions
    op.execute("""
        CREATE TABLE events.interactions (
            interaction_id bigserial NOT NULL,
            thorny_id int8 NOT NULL,
            "type" varchar NOT NULL,
            "time" timestamptz DEFAULT now() NOT NULL,
            dimension varchar DEFAULT 'minecraft:overworld'::character varying NOT NULL,
            reference varchar NOT NULL,
            mainhand varchar NULL,
            coordinates _int2 NULL,
            CONSTRAINT interaction_pk PRIMARY KEY (interaction_id)
        );
    """)

    op.execute("CREATE INDEX interactions_coordinates_gin_idx ON events.interactions USING gin (coordinates);")
    op.execute("CREATE INDEX interactions_reference_idx ON events.interactions USING btree (reference);")
    op.execute("CREATE INDEX interactions_thorny_id_idx ON events.interactions USING btree (thorny_id, type, reference);")
    op.execute("CREATE INDEX interactions_time_idx ON events.interactions USING btree (\"time\", reference, coordinates);")

    op.execute("""
        ALTER TABLE events.interactions 
        ADD CONSTRAINT interactions_user_fk 
        FOREIGN KEY (thorny_id) REFERENCES users."user"(thorny_id);
    """)

    # Pins
    op.execute("""
        CREATE TABLE projects.pins (
            id bigserial NOT NULL,
            pin_type varchar NOT NULL,
            "name" varchar NOT NULL,
            coordinates _int4 NOT NULL,
            description varchar NOT NULL,
            dimension varchar DEFAULT 'minecraft:overworld'::character varying NOT NULL,
            CONSTRAINT pins_pk PRIMARY KEY (id)
        );
    """)

    # Projects
    op.execute("""
        CREATE TABLE projects.project (
            project_id varchar NOT NULL,
            "name" varchar NOT NULL,
            thread_id int8 NULL,
            description varchar NOT NULL,
            started_on date DEFAULT now() NOT NULL,
            completed_on date NULL,
            owner_id int8 NOT NULL,
            coordinates _int4 NULL,
            dimension varchar DEFAULT 'minecraft:overworld'::character varying NOT NULL,
            pin_id int2 NULL,
            CONSTRAINT project_pk PRIMARY KEY (project_id)
        );
    """)

    op.execute("""
        ALTER TABLE projects.project 
        ADD CONSTRAINT project_pins_fk 
        FOREIGN KEY (pin_id) REFERENCES projects.pins(id);
    """)

    op.execute("""
        ALTER TABLE projects.project 
        ADD CONSTRAINT project_user_fk 
        FOREIGN KEY (owner_id) REFERENCES users."user"(thorny_id);
    """)

    # Project Status
    op.execute("""
        CREATE TABLE projects.status (
            project_id varchar NULL,
            status varchar NULL,
            since timestamptz DEFAULT now() NOT NULL
        );
    """)

    op.execute("""
        ALTER TABLE projects.status 
        ADD CONSTRAINT status_project_fk 
        FOREIGN KEY (project_id) REFERENCES projects.project(project_id);
    """)

    # Project Members
    op.execute("""
        CREATE TABLE projects.members (
            project_id varchar NULL,
            user_id int8 NULL
        );
    """)

    op.execute("""
        ALTER TABLE projects.members 
        ADD CONSTRAINT members_project_fk 
        FOREIGN KEY (project_id) REFERENCES projects.project(project_id);
    """)

    op.execute("""
        ALTER TABLE projects.members 
        ADD CONSTRAINT members_user_fk 
        FOREIGN KEY (user_id) REFERENCES users."user"(thorny_id);
    """)

    # World
    op.execute("""
        CREATE TABLE "server".world (
            guild_id int8 NOT NULL,
            overworld_border float4 NULL,
            nether_border float4 NULL,
            end_border float4 NULL,
            CONSTRAINT world_pk PRIMARY KEY (guild_id)
        );
    """)

    op.execute("""
        ALTER TABLE "server".world  
        ADD CONSTRAINT world_guild_fk 
        FOREIGN KEY (guild_id) REFERENCES guilds.guild(guild_id);
    """)

    # Altar Items
    op.execute("""
        CREATE TABLE "server".items (
            item_id varchar NOT NULL,
            value float4 NOT NULL,
            max_uses int4 NOT NULL,
            depreciation float4 NOT NULL,
            current_uses int4 DEFAULT 0 NOT NULL,
            CONSTRAINT items_pk PRIMARY KEY (item_id)
        );
    """)

    # Quest Table
    op.execute("""
        CREATE TABLE quests_v3.quest (
            quest_id bigserial NOT NULL,
            start_time timestamptz NOT NULL,
            end_time timestamptz NOT NULL,
            title varchar NOT NULL,
            description varchar NOT NULL,
            created_by int8 DEFAULT 15 NOT NULL,
            tags _varchar DEFAULT '{}'::character varying[] NOT NULL,
            quest_type varchar DEFAULT 'side'::character varying NOT NULL,
            CONSTRAINT quest_pk PRIMARY KEY (quest_id)
        );
    """)

    op.execute("""
        ALTER TABLE quests_v3.quest
        ADD CONSTRAINT quest_user_fk 
        FOREIGN KEY (created_by) REFERENCES users."user"(thorny_id);
    """)

    # Objectives
    op.execute("""
        CREATE TABLE quests_v3.objective (
            objective_id bigserial NOT NULL,
            quest_id int8 NOT NULL,
            objective_type varchar DEFAULT 'kill'::character varying NOT NULL,
            order_index int4 DEFAULT 0 NOT NULL,
            description varchar DEFAULT 'No objective description'::character varying NOT NULL,
            display varchar NULL,
            logic varchar DEFAULT 'and'::character varying NOT NULL,
            target_count int4 NULL,
            targets jsonb DEFAULT '[]'::jsonb NOT NULL,
            customizations jsonb DEFAULT '[]'::jsonb NOT NULL,
            CONSTRAINT objective_pk PRIMARY KEY (objective_id)
        );
    """)

    op.execute("""
        ALTER TABLE quests_v3.objective 
        ADD CONSTRAINT objective_quest_fk 
        FOREIGN KEY (quest_id) REFERENCES quests_v3.quest(quest_id);
    """)

    # Rewards
    op.execute("""
        CREATE TABLE quests_v3.reward (
            reward_id bigserial NOT NULL,
            quest_id int8 NOT NULL,
            objective_id int8 NOT NULL,
            balance int4 NULL,
            item varchar NULL,
            count int4 NULL,
            display_name varchar NULL,
            item_metadata jsonb DEFAULT '[]'::jsonb NOT NULL,
            CONSTRAINT reward_pk PRIMARY KEY (reward_id)
        );
    """)

    op.execute("""
        ALTER TABLE quests_v3.reward 
        ADD CONSTRAINT reward_objective_fk 
        FOREIGN KEY (objective_id) REFERENCES quests_v3.objective(objective_id);
    """)

    op.execute("""
        ALTER TABLE quests_v3.reward 
        ADD CONSTRAINT reward_quest_fk 
        FOREIGN KEY (quest_id) REFERENCES quests_v3.quest(quest_id);
    """)

    # Quest Progress
    op.execute("""
        CREATE TABLE quests_v3.quest_progress (
            progress_id bigserial NOT NULL,
            thorny_id int8 NOT NULL,
            quest_id int8 NOT NULL,
            accept_time timestamptz DEFAULT now() NOT NULL,
            start_time timestamptz NULL,
            end_time timestamptz NULL,
            status varchar DEFAULT 'pending'::character varying NOT NULL,
            CONSTRAINT quest_progress_pk PRIMARY KEY (progress_id)
        );
    """)

    op.execute("""
        ALTER TABLE quests_v3.quest_progress 
        ADD CONSTRAINT quest_progress_quest_fk 
        FOREIGN KEY (quest_id) REFERENCES quests_v3.quest(quest_id);
    """)

    op.execute("""
        ALTER TABLE quests_v3.quest_progress 
        ADD CONSTRAINT quest_progress_user_fk 
        FOREIGN KEY (thorny_id) REFERENCES users."user"(thorny_id);
    """)

    # Objective Progress
    op.execute("""
        CREATE TABLE quests_v3.objective_progress (
            progress_id int8 NOT NULL,
            objective_id int8 NOT NULL,
            start_time timestamptz NULL,
            end_time timestamptz NULL,
            status varchar DEFAULT 'pending'::character varying NOT NULL,
            target_progress jsonb DEFAULT '[]'::jsonb NOT NULL,
            customization_progress jsonb DEFAULT '{}'::jsonb NOT NULL,
            CONSTRAINT objective_progress_pk PRIMARY KEY (progress_id, objective_id)
        );
    """)

    op.execute("""
        ALTER TABLE quests_v3.objective_progress 
        ADD CONSTRAINT objective_progress_objective_fk 
        FOREIGN KEY (objective_id) REFERENCES quests_v3.objective(objective_id);
    """)

    op.execute("""
        ALTER TABLE quests_v3.objective_progress 
        ADD CONSTRAINT objective_progress_quest_progress_fk 
        FOREIGN KEY (progress_id) REFERENCES quests_v3.quest_progress(progress_id);
    """)

def downgrade() -> None:
    """Downgrade schema."""
    pass
