---
name: new-model
description: Use this guide whenever you need to add a completely new domain resource to Nexuscore. It covers every layer you must touch, in the correct order, grounded in the patterns already used throughout the codebase. Follow each section top-to-bottom; do not skip layers.
---

## Architecture Reminder

Nexuscore follows a strict **Router → Service → Repository** layered architecture.

| Layer | Location | Responsibility |
|---|---|---|
| **Models** | `src/models/<domain>/` | Pydantic models: `DB`, `Out`, `In`, `Update` variants |
| **Repository** | `src/repositories/<domain>.py` | All raw SQL via asyncpg; returns `DB` models only |
| **Service** | `src/services/<domain>.py` | Cross-repo orchestration, business logic; returns `Out` models |
| **Router** | `src/routes/<domain>.py` | FastAPI route handlers; delegates entirely to services |
| **DI wiring** | `src/dependencies/repositories.py` + `services.py` | Factory functions that inject repos into services |

> **No business logic in routers. No SQL outside repositories. No `Out` models inside repositories.**

---

## Step 1 — Database

### 1a. Understand the existing schema holistically

Before writing any DDL, read the existing migration(s) in `src/migrations/versions/` — especially
`a56b022de770_initial_migration.py` — to understand:

- **Existing schemas**: `guilds`, `users`, `quests_v3`, `events`, `auth`, `server`, `projects`.
  Place your new table in the appropriate existing schema, or create a new one only if truly
  warranted.
- **Foreign key targets**: use exact schema-qualified references, e.g.
  `users."user"(thorny_id)`, `guilds.guild(guild_id)`.
- **Column naming conventions**: snake_case, singular table names, PKs named `<table>_id` or
  `thorny_id` for users.
- **Index conventions**: one index per FK column and per frequently-filtered column. Name them
  `idx_<schema>_<table>_<column>`.

### 1b. Generate the Alembic revision

Always generate a new revision file. Never apply raw DDL to the database without one.

```bash
# From the project root
alembic revision -m "<short-description>"
# e.g.
alembic revision -m "add_widgets_table"
```

This creates `src/migrations/versions/<hash>_add_widgets_table.py`.

### 1c. Write `upgrade()` and `downgrade()`

Nexuscore migrations use **raw SQL via `op.execute()`** — not SQLAlchemy's `op.create_table()`.
Match this pattern exactly.

```python
# src/migrations/versions/<hash>_add_widgets_table.py
from typing import Sequence, Union
from alembic import op

revision: str = '<hash>'
down_revision: Union[str, Sequence[str], None] = '<previous_hash>'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create schema only if new
    op.execute("CREATE SCHEMA IF NOT EXISTS widgets;")

    # 2. Primary table
    op.execute("""
        CREATE TABLE widgets.widget (
            widget_id   bigserial NOT NULL,
            guild_id    int8 NOT NULL,
            name        varchar NOT NULL,
            description varchar NOT NULL,
            owner_id    int8 NOT NULL,
            created_on  timestamptz DEFAULT now() NOT NULL,
            CONSTRAINT widget_pk PRIMARY KEY (widget_id)
        );
    """)

    # 3. Foreign keys (added separately, after table creation)
    op.execute("""
        ALTER TABLE widgets.widget
        ADD CONSTRAINT widget_guild_fk
        FOREIGN KEY (guild_id) REFERENCES guilds.guild(guild_id);
    """)

    op.execute("""
        ALTER TABLE widgets.widget
        ADD CONSTRAINT widget_user_fk
        FOREIGN KEY (owner_id) REFERENCES users."user"(thorny_id);
    """)

    # 4. Indexes — one per FK column and per query-hot column
    op.execute("CREATE INDEX idx_widgets_widget_guild_id ON widgets.widget USING btree (guild_id);")
    op.execute("CREATE INDEX idx_widgets_widget_owner_id ON widgets.widget USING btree (owner_id);")

    # 5. Secondary / junction tables follow the same pattern
    op.execute("""
        CREATE TABLE widgets.tag (
            widget_id int8 NOT NULL,
            tag       varchar NOT NULL,
            CONSTRAINT tag_pk PRIMARY KEY (widget_id, tag)
        );
    """)

    op.execute("""
        ALTER TABLE widgets.tag
        ADD CONSTRAINT tag_widget_fk
        FOREIGN KEY (widget_id) REFERENCES widgets.widget(widget_id);
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS widgets.tag;")
    op.execute("DROP TABLE IF EXISTS widgets.widget;")
    op.execute("DROP SCHEMA IF EXISTS widgets;")
```

**Rules:**
- `downgrade()` must fully reverse `upgrade()` in reverse dependency order.
- Use `timestamptz DEFAULT now()` for all timestamps (timezone-aware).
- Schema-qualify every table name in every query (`schema.table`).
- Note that `users."user"` requires quoting — `user` is a reserved keyword in PostgreSQL.

---

## Step 2 — Model Layer

Models live in `src/models/<domain>/`. Create the sub-directory and `__init__.py` if new.

```
src/models/widgets/
    __init__.py         ← empty
    widget.py           ← main model file
    tag.py              ← secondary model if needed
```

### Annotated field pattern

Nexuscore uses `Annotated` type aliases for all reusable fields. This means field metadata is
defined once and reused across all model variants — not repeated per model.

```python
# src/models/widgets/widget.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from typing_extensions import Annotated

from src.models.users.user import UserOut


# --- Annotated field aliases (define once, reuse everywhere) ---

WidgetID = Annotated[int, Field(
    description="The auto-assigned widget ID",
    examples=[1]
)]
GuildID = Annotated[int, Field(
    description="The Discord guild ID this widget belongs to",
)]
WidgetName = Annotated[str, Field(
    description="The display name of the widget",
    examples=["My Widget"]
)]
WidgetDescription = Annotated[str, Field(
    description="A short description of what the widget does",
    examples=["It does something useful"]
)]
OwnerID = Annotated[int, Field(
    description="The thorny_id of the widget owner",
    examples=[42]
)]
CreatedOn = Annotated[datetime, Field(
    description="UTC timestamp of when the widget was created",
    examples=["2024-01-01T00:00:00+00:00"]
)]
Owner = Annotated[UserOut, Field(
    description="The owner of the widget as a full User object"
)]
```

### `XDB` — raw database representation

Only fields that exist as columns in the database. No nested objects.

```python
class WidgetBase(BaseModel):
    widget_id: WidgetID
    guild_id: GuildID
    name: WidgetName
    description: WidgetDescription
    created_on: CreatedOn

class WidgetDB(WidgetBase):
    owner_id: OwnerID
```

### `XOut` — API response model

Enriched with nested objects resolved by the Service layer. Omits raw FK IDs that are
replaced by the full nested model.

```python
class WidgetOut(WidgetBase):
    owner: Owner          # resolved from owner_id by the service
    # status: ...         # add other enriched fields here
```

**Eager-loading decision:** include a nested `Out` model when clients almost always need that
data. The project resource, for example, always exposes `owner: UserOut` rather than raw
`owner_id`, because every client immediately needs the user details anyway.

### `XIn` — creation input

Only the fields a client must supply. Never include PKs, auto-timestamps, or guild_id (that
comes from the auth token in most cases).

```python
class WidgetIn(BaseModel):
    name: WidgetName
    description: WidgetDescription
    owner_id: OwnerID
```

### `XUpdate` — partial update input

**All fields must be `Optional` with a default of `None`.**

```python
class WidgetUpdate(BaseModel):
    name: Optional[WidgetName] = None
    description: Optional[WidgetDescription] = None
    owner_id: Optional[OwnerID] = None
```

---

## Step 3 — Repository Layer

Repositories are **classes** with `self.db: Database`. They contain all raw SQL and only ever
return `DB` models. No business logic, no `Out` models here.

```python
# src/repositories/widget.py
import asyncpg

from src.dependencies.database import Database
from src.errors import NotFound, AlreadyExists
from src.models.widgets.widget import WidgetDB, WidgetIn, WidgetUpdate


class WidgetRepository:
    def __init__(self, db: Database):
        self.db = db

    async def fetch(self, guild_id: int, widget_id: int) -> WidgetDB:
        data = await self.db.pool.fetchrow("""
            SELECT * FROM widgets.widget
            WHERE widget_id = $1
              AND guild_id  = $2
        """, widget_id, guild_id)

        if not data:
            raise NotFound("Widget")

        return WidgetDB.model_validate(dict(data))

    async def fetch_all(self, guild_id: int) -> list[WidgetDB]:
        data = await self.db.pool.fetch("""
            SELECT * FROM widgets.widget
            WHERE guild_id = $1
        """, guild_id)

        if not data:
            raise NotFound("Widgets")

        return [WidgetDB.model_validate(dict(row)) for row in data]

    async def create(self, guild_id: int, model: WidgetIn) -> WidgetDB:
        try:
            data = await self.db.pool.fetchrow("""
                INSERT INTO widgets.widget (guild_id, name, description, owner_id)
                VALUES ($1, $2, $3, $4)
                RETURNING *
            """, guild_id, model.name, model.description, model.owner_id)
        except asyncpg.UniqueViolationError:
            raise AlreadyExists("Widget")

        return WidgetDB.model_validate(dict(data))

    async def update(self, guild_id: int, widget_id: int, model: WidgetUpdate) -> WidgetDB:
        existing = await self.fetch(guild_id, widget_id)

        updated = existing.model_copy(update=model.model_dump(exclude_none=True))

        await self.db.pool.execute("""
            UPDATE widgets.widget
            SET name        = $1,
                description = $2,
                owner_id    = $3
            WHERE widget_id = $4
        """, updated.name, updated.description, updated.owner_id, updated.widget_id)

        return updated
```

**Rules:**
- All queries use `$1`, `$2` positional params — never f-string user data into SQL.
- `fetch` / `fetch_all` raise `NotFound` (from `src.errors`) when nothing is found.
- `create` catches `asyncpg.UniqueViolationError` and raises `AlreadyExists`.
- `update` fetches the existing record first, merges with `model_copy(update=...)`, then persists.
- Always use `model_validate(dict(data))` to convert asyncpg `Record` objects to Pydantic models.
- Use `RETURNING *` on `INSERT` so you can immediately return the full `DB` model.
- All table references are schema-qualified.

---

## Step 4 — Service Layer

Services are **classes** that receive repositories via `__init__`. They orchestrate multiple
repositories, apply business logic, and always return `Out` models — never `DB` models.

```python
# src/services/widget.py
import asyncio

from src.models.widgets.widget import WidgetDB, WidgetIn, WidgetOut, WidgetUpdate
from src.models.users.user import UserOut
from src.repositories.widget import WidgetRepository
from src.repositories.user import UserRepository


class WidgetService:
    def __init__(self, widget_repo: WidgetRepository, user_repo: UserRepository):
        self.widget_repo = widget_repo
        self.user_repo = user_repo

    async def _to_out(self, widget: WidgetDB) -> WidgetOut:
        # Resolve nested models — use asyncio.gather() for independent fetches
        owner = await self.user_repo.fetch(widget.guild_id, widget.owner_id)

        return WidgetOut(
            **widget.model_dump(),
            owner=UserOut(**owner.model_dump()),
        )

    async def get(self, guild_id: int, widget_id: int) -> WidgetOut:
        widget_db = await self.widget_repo.fetch(guild_id, widget_id)
        return await self._to_out(widget_db)

    async def get_all(self, guild_id: int) -> list[WidgetOut]:
        widgets_db = await self.widget_repo.fetch_all(guild_id)

        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(self._to_out(w)) for w in widgets_db]

        return [t.result() for t in tasks]

    async def new(self, guild_id: int, model: WidgetIn) -> WidgetOut:
        widget_db = await self.widget_repo.create(guild_id, model)
        return await self._to_out(widget_db)

    async def update(self, guild_id: int, widget_id: int, model: WidgetUpdate) -> WidgetOut:
        widget_db = await self.widget_repo.update(guild_id, widget_id, model)
        return await self._to_out(widget_db)
```

**Rules:**
- Services never raise `HTTPException` or any Nexus error directly — that is the repository's job.
- Use `asyncio.gather()` for 2–3 independent async calls; use `asyncio.TaskGroup()` for
  parallelising a dynamic list of tasks (e.g. mapping `_to_out` over many DB records).
- Use `model_copy(update=...)` pattern in repositories for partial updates, not in services.
- The `_to_out` helper keeps enrichment logic in one place.

---

## Step 5 — Dependency Injection Wiring

Every repository and service must be registered as a FastAPI dependency factory.

### 5a. `src/dependencies/repositories.py`

Add a factory function for the new repository:

```python
from src.repositories.widget import WidgetRepository

def get_widget_repo(
    database: Database = Depends(get_db),
) -> WidgetRepository:
    return WidgetRepository(database)
```

### 5b. `src/dependencies/services.py`

Add a factory function for the new service, injecting its required repositories:

```python
from src.dependencies.repositories import get_widget_repo, get_user_repo
from src.repositories.widget import WidgetRepository
from src.repositories.user import UserRepository
from src.services.widget import WidgetService

def get_widget_service(
    widget_repo: WidgetRepository = Depends(get_widget_repo),
    user_repo: UserRepository = Depends(get_user_repo),
) -> WidgetService:
    return WidgetService(widget_repo, user_repo)
```

---

## Step 6 — Router

### 6a. Create `src/routes/<domain>.py`

```python
# src/routes/widget.py
from fastapi import APIRouter, Depends, Security, status

from src.dependencies.auth import Scope, get_guild_client
from src.dependencies.services import get_widget_service
from src.models.auth import TokenPayload
from src.models.widgets.widget import WidgetIn, WidgetOut, WidgetUpdate
from src.services.widget import WidgetService

widgets_router = APIRouter(prefix='/guilds/me/widgets', tags=['Widgets'])


@widgets_router.get('')
async def list_widgets(
    auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_READ]),
    service: WidgetService = Depends(get_widget_service),
) -> list[WidgetOut]:
    """
    Get a list of Widgets
    """
    return await service.get_all(auth.guild_id)


@widgets_router.post('', status_code=status.HTTP_201_CREATED)
async def create_widget(
    body: WidgetIn,
    auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_WRITE]),
    service: WidgetService = Depends(get_widget_service),
) -> WidgetOut:
    """
    Create a new Widget
    """
    return await service.new(auth.guild_id, body)


@widgets_router.get('/{widget_id}')
async def get_widget(
    widget_id: int,
    auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_READ]),
    service: WidgetService = Depends(get_widget_service),
) -> WidgetOut:
    """
    Get a specific Widget
    """
    return await service.get(auth.guild_id, widget_id)


@widgets_router.put('/{widget_id}')
@widgets_router.patch('/{widget_id}')
async def update_widget(
    widget_id: int,
    body: WidgetUpdate,
    auth: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_WRITE]),
    service: WidgetService = Depends(get_widget_service),
) -> WidgetOut:
    """
    Update a Widget. Null/omitted fields are ignored.
    """
    return await service.update(auth.guild_id, widget_id, body)
```

### 6b. Register in `src/routes/__init__.py`

```python
from src.routes.widget import widgets_router

api_router.include_router(widgets_router)
```

---

## Final Checklist

**Database**
- [ ] Read all existing migrations to understand schema, FKs, and naming before writing DDL
- [ ] Alembic revision generated with a descriptive `-m` message
- [ ] `upgrade()` uses `op.execute()` with raw SQL — not `op.create_table()`
- [ ] FK constraints added via separate `ALTER TABLE ... ADD CONSTRAINT` calls
- [ ] Indexes created for every FK column and query-hot column
- [ ] `downgrade()` fully and correctly reverses `upgrade()` in reverse dependency order
- [ ] All table names are schema-qualified (e.g. `widgets.widget`, not just `widget`)
- [ ] `users."user"` is quoted (reserved keyword in PostgreSQL)

**Models**
- [ ] Annotated type aliases defined once for each field, reused across all model variants
- [ ] `XDB` contains only raw DB columns — no nested objects
- [ ] `XOut` replaces FK id columns with the resolved nested `Out` model (where appropriate)
- [ ] `XIn` contains only what the client should supply (no PKs, no auto-timestamps)
- [ ] `XUpdate` has every field as `Optional[...] = None`
- [ ] `model_validate(dict(data))` used to parse asyncpg Records

**Repository**
- [ ] Class with `__init__(self, db: Database)`
- [ ] Returns only `DB` models — never `Out` models
- [ ] `fetch` / `fetch_all` raise `NotFound` from `src.errors`
- [ ] `create` catches `asyncpg.UniqueViolationError` and raises `AlreadyExists`
- [ ] `update` fetches existing, merges with `model_copy(update=model.model_dump(exclude_none=True))`, then persists
- [ ] All SQL uses positional `$1`, `$2` params
- [ ] All table references are schema-qualified

**Service**
- [ ] Class with `__init__(self, *_repos)`
- [ ] Returns only `Out` models — never `DB` models
- [ ] `_to_out` helper centralises DB → Out enrichment
- [ ] Independent fetches parallelised with `asyncio.gather()`
- [ ] Lists of tasks parallelised with `asyncio.TaskGroup()`
- [ ] No `HTTPException` or Nexus errors raised directly

**Dependency Injection**
- [ ] `get_<resource>_repo` factory added to `src/dependencies/repositories.py`
- [ ] `get_<resource>_service` factory added to `src/dependencies/services.py`, injecting all required repos

**Router**
- [ ] Router registered in `src/routes/__init__.py`
- [ ] Every handler has a docstring
- [ ] `status_code` set explicitly where non-200
- [ ] Both `PUT` and `PATCH` registered on the update handler
- [ ] Auth injected via `Security(get_guild_client, scopes=[...])`
- [ ] Service injected via `Depends(get_<resource>_service)`
- [ ] No business logic in route handlers — delegate entirely to the service
