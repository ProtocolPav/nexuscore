-- Wiki schema and tables

CREATE SCHEMA IF NOT EXISTS wiki;

-- wiki.page
CREATE TABLE IF NOT EXISTS wiki.page (
    page_id       TEXT PRIMARY KEY,
    title         TEXT        NOT NULL,
    summary       TEXT,
    category      TEXT,
    tags          TEXT[]      DEFAULT '{}',
    cover_image   TEXT,
    author_id     INT         NOT NULL REFERENCES users.user(thorny_id),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    published     BOOLEAN     NOT NULL DEFAULT FALSE,
    locked        BOOLEAN     NOT NULL DEFAULT FALSE,
    view_count    INT         NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_page_category  ON wiki.page(category);
CREATE INDEX IF NOT EXISTS idx_page_published ON wiki.page(published);

-- wiki.page_content
CREATE TABLE IF NOT EXISTS wiki.page_content (
    content_id  SERIAL PRIMARY KEY,
    page_id     TEXT        NOT NULL REFERENCES wiki.page(page_id) ON DELETE CASCADE,
    content     JSONB       NOT NULL,
    editor_type TEXT        NOT NULL DEFAULT 'blocknote',
    version     INT         NOT NULL DEFAULT 1,
    edited_by   INT         NOT NULL REFERENCES users.user(thorny_id),
    edited_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    change_note TEXT
);

CREATE INDEX IF NOT EXISTS idx_page_content_page_version ON wiki.page_content(page_id, version DESC);
CREATE INDEX IF NOT EXISTS idx_page_content_gin          ON wiki.page_content USING GIN(content);
