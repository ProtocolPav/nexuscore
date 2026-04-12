# Nexuscore — Agent Guidelines

## Project Overview

Nexuscore is a Python async REST API backend for the "Everthorn" Minecraft guild community. It serves as the data layer for the "Thorny" Discord bot. Built with **Sanic**, **Pydantic v2**, and **asyncpg** on Python 3.12, backed by PostgreSQL.

---

## Build & Run Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (development — hot reload)
# Edit nexus.py: uncomment dev=True line, comment fast=True line
python nexus.py

# Run locally (production mode)
python nexus.py

# Docker build & run
docker build -t nexuscore .
docker run nexuscore
```

### Production Deployment
CI/CD via Google Cloud Build (`cloudbuild.yaml`). Pushing to the configured branch triggers a build that:
1. Builds the Docker image (Python 3.12 Alpine)
2. Pushes to GCP Artifact Registry (`europe-docker.pkg.dev`)
3. Publishes a Pub/Sub message to trigger `docker-compose` update

---

## Testing

**There is no test suite in this repository.** No `pytest`, `unittest`, or any testing library is in `requirements.txt`, and no `tests/` directory exists. When adding tests:
- Use `pytest` with `pytest-asyncio` for async route/model tests
- Place tests under `tests/` at the project root
- Run a single test: `pytest tests/path/to/test_file.py::test_function_name -v`
- Run all tests: `pytest`

---

## Linting & Formatting

No linter or formatter is configured (no `.flake8`, `.pylintrc`, `.ruff.toml`, `pyproject.toml`, `.black`, `mypy.ini`). Follow the observed conventions below. When adding tooling, prefer `ruff` for linting/formatting.

---

## Code Style Guidelines

### General
- **Python 3.12** — use modern Python features where appropriate
- **4-space indentation**, no tabs
- Keep lines to a reasonable length (~100 chars); no strict enforcer
- Docstrings on all route handlers (used by Sanic/OpenAPI for Swagger UI)
- Inline comments for complex SQL logic only

### Imports
- **Absolute imports only** — always use the `src.` prefix from the project root:
  ```python
  from src.dependencies.database import Database
  from src.utils.base import BaseModel, BaseList, optional_model
  from src.utils.errors import BadRequest400, NotFound404, Forbidden403
  ```
- **Import ordering** (loosely PEP 8, not enforced):
  1. Standard library (`typing`, `typing_extensions`, `asyncio`, etc.)
  2. Third-party (`sanic`, `pydantic`, `asyncpg`, `httpx`)
  3. Internal (`src.*`)
- Route files import model modules and use qualified access:
  ```python
  from src.models import guilds         # then: guilds.GuildModel
  from src.models.users import user     # then: user.UserModel
  ```
- Model files use direct name imports:
  ```python
  from src.models.quests.objective import ObjectivesListModel, ObjectiveCreateModel
  ```
- Prefer `from typing import ...` but `typing_extensions` is acceptable for backports

### Type Annotations
- **All function signatures must have full type annotations** — parameters and return types
- Use Pydantic v2 `Field()` on every model attribute with `description` and `examples`
- Use `Annotated` + `StringConstraints` for validated string types
- Use `Literal` + `Field(discriminator=...)` for discriminated union polymorphism
- Use forward references (quoted strings) for circular/self-referencing types:
  ```python
  async def fetch(cls, db: Database, quest_id: int) -> "QuestModel": ...
  ```
- `mypy` is not configured — but write type-correct code

### Naming Conventions
- **Files:** `snake_case` (e.g., `quest_progress.py`, `reward_metadata.py`)
- **Classes:** `PascalCase` with consistent suffixes:
  - `XBaseModel` — shared validated fields
  - `XModel` — full DB-fetched representation (extends `XBaseModel`, has CRUD methods)
  - `XCreateModel` — input model for creation (typically inherits from `XBaseModel`)
  - `XUpdateModel` — all-optional update model, generated via `optional_model()`
  - `XListModel` — `BaseList[XModel]` wrapping a list of models
- **Blueprints:** `snake_case` with `_blueprint` suffix (e.g., `user_blueprint`)
- **Route handlers:** `snake_case` verbs (e.g., `create_user`, `get_guild`, `fail_active_quest`)
- **Variables:** `snake_case` (e.g., `thorny_id`, `guild_id`, `quest_model`)
- **Type aliases:** `PascalCase` (e.g., `MinecraftID`, `Targets`, `Metadata`, `TargetProgress`)
- **Dict maps / constants:** `SCREAMING_SNAKE_CASE` (e.g., `TARGET_TYPE_MAP`, `CUSTOMIZATION_TYPE_MAP`)
- **DB fields:** `snake_case` matching PostgreSQL column names exactly

### Models (Pydantic v2)
- All models extend `src.utils.base.BaseModel` (which extends `pydantic.BaseModel` with `model_config = ConfigDict(populate_by_name=True)`)
- All list wrapper models extend `BaseList[T]` (a `Generic[T]` with an `items: List[T]` field)
- Generate update models with the `optional_model()` utility — do not duplicate field definitions:
  ```python
  UserUpdateModel = optional_model("UserUpdateModel", UserBaseModel)
  ```
- Decorate models with `@openapi.component()` for Swagger documentation

### Database Access (Active Record Pattern)
- DB access methods live directly on the model class — not in a separate repository layer
- `@classmethod` for `fetch`, `fetch_all`, `create`; instance method for `update`
- Always type the `db` parameter as `Database`
- Use `asyncpg` positional parameters (`$1`, `$2`, ...); never format SQL strings with user input
- Use `asyncio.gather()` for concurrent independent queries
- DB schema-qualified table names: `users.user`, `guilds.guild`, `quests_v3.quest`, etc.

### Error Handling
Use the three custom exceptions from `src/utils/errors.py`:
```python
from src.utils.errors import BadRequest400, NotFound404, Forbidden403
```

Standard pattern for all fetch operations:
```python
# 1. Validate required input
if not thorny_id:
    raise BadRequest400(extra={'ids': ['thorny_id']})

# 2. Execute query
data = await db.pool.fetchrow("SELECT ... WHERE thorny_id = $1", thorny_id)

# 3. Return or raise
if data:
    return cls(**data)
raise NotFound404(extra={'resource': 'user', 'id': thorny_id})
```

Use `@model_validator` on Pydantic models to raise `BadRequest400` for invalid business logic (e.g., empty target lists, mismatched types, out-of-range counts).

For duplicate detection:
```python
try:
    await ItemModel.fetch(db, body.item_id)
    raise BadRequest400('This item already exists')
except NotFound404:
    await ItemModel.create(db, body)
```

Errors propagate to Sanic's exception handler — do not wrap entire route handlers in try/except unless handling a specific expected case.

---

## Architecture Patterns

### Blueprint-Based Routing
Each domain has its own `Blueprint` in `src/routes/`. All blueprints aggregate in `src/routes/__init__.py` as a `blueprint_group` with prefix `/api/v0.2/`.

### Dependency Injection
`Database` is registered with Sanic-Ext DI at startup:
```python
@app.before_server_start
async def init_db(application: Sanic):
    db = await Database.init_pool()
    application.ext.dependency(db)
```
Route handlers receive `db: Database` as an injected parameter — do not instantiate `Database` inside routes.

### Configuration
Runtime config (DB credentials, Discord webhook URL) is read from `config.json` (gitignored, never committed). No environment variables or secrets manager is used. Do not hardcode credentials.

### OpenAPI Documentation
Use `@openapi.definition(...)` on route handlers and `@openapi.component()` on models. Swagger UI is served at `/api/docs`. Every route must have a `summary` in its docstring and proper `@openapi.definition` decorator.

### SQL Queries
Raw SQL with `asyncpg` — no ORM. Build dynamic queries by appending SQL fragments and parameters to lists, then joining:
```python
conditions = ["guild_id = $1"]
params = [guild_id]
if some_filter:
    params.append(some_filter)
    conditions.append(f"column = ${len(params)}")
query = f"SELECT ... WHERE {' AND '.join(conditions)}"
```
