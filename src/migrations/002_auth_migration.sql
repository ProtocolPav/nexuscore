CREATE TABLE auth.clients (
    client_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_name     TEXT NOT NULL,
    hashed_key      TEXT NOT NULL,           -- bcrypt hash of the raw API key
    tier            TEXT NOT NULL DEFAULT 'guild',  -- 'master' | 'guild'
    guild_id        BIGINT,                  -- NULL for master-tier clients
    scopes          TEXT[] NOT NULL DEFAULT '{}',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_used_at    TIMESTAMPTZ
);

-- Guild clients must have a guild_id; master clients must not
ALTER TABLE auth.clients
    ADD CONSTRAINT chk_guild_id
    CHECK (
        (tier = 'guild' AND guild_id IS NOT NULL) OR
        (tier = 'master' AND guild_id IS NULL)
    );

CREATE INDEX idx_clients_guild_id ON auth.clients (guild_id)
    WHERE guild_id IS NOT NULL;