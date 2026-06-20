# AGENTS.md - Nexuscore Development Guide

## Project Overview

- **Project**: Nexuscore - FastAPI backend for Everthorn internal services
- **Language**: Python 3.12
- **Framework**: FastAPI with asyncpg (async PostgreSQL)
- **Database**: PostgreSQL

## Architecture

The application follows a Router -> Service -> Repository architecture:
- **Router (src/routes)**: Handles HTTP requests, validates input via Pydantic models, and calls service layer.
- **Service (src/services)**: Contains business logic, orchestrates multiple repositories, validates data, and transforms DB models to Out models.
- **Repository (src/repositories)**: Handles all database interactions using raw SQL with asyncpg, returns DB models.
- **Models (src/models)**: 
  - DB models (suffix `DB`) represent actual database tables with all fields.
  - Out models (suffix `Out`) exclude some fields and may include others for API responses.
  - Input models (suffix `In`) are used for request validation.
  - Update models (suffix `Update`) must have all fields as optional

## Running the Application

### Development
```bash
pip install -r requirements.txt
PYTHONPATH=. python -m fastapi run src/main.py --host 0.0.0.0 --port 8000
```

### Docker
```bash
docker build -t nexuscore .
docker run -e JWT_SECRET=xxx -e DATABASE_NAME=xxx -e DATABASE_USER=xxx -e DATABASE_PASSWORD=xxx -e DATABASE_HOST=xxx -e WEBHOOK_URL=xxx nexuscore
```

## Environment Variables

Required environment variables:
- `JWT_SECRET` - Secret key for JWT signing
- `DATABASE_NAME` - PostgreSQL database name
- `DATABASE_USER` - Database user
- `DATABASE_PASSWORD` - Database password
- `DATABASE_HOST` - Database host
- `DATABASE_PORT` - Database port (default: 5432)
- `WEBHOOK_URL` - Discord webhook URL

## Code Style Guidelines

### Imports
Order imports in the following groups:
1. Standard library (`secrets`, `typing`)
2. Third-party packages (`fastapi`, `asyncpg`, `pydantic`)
3. Local application imports (`src.dependencies`, `src.models`, `src.routes`, `src.services`, `src.repositories`)

Example:
```python
import secrets
from typing import Optional

from argon2 import PasswordHasher
from fastapi import APIRouter, Depends, Form

from src.dependencies.auth import get_current_client
from src.dependencies.database import db
from src.dependencies.services import get_quest_service
from src.dependencies.repositories import get_quest_repository

from src.models.auth import ClientCreateRequest
from src.models.quests.quest import QuestDB, QuestOut
from src.services.quest import QuestService
from src.repositories.quest import QuestRepository
```

### Naming Conventions
- **Classes**: PascalCase (e.g., `Database`, `BaseModel`, `TokenResponse`)
- **Functions/Variables**: snake_case (e.g., `get_token`, `db_pool`, `client_id`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `JWT_ALGORITHM`, `TOKEN_TTL_SECONDS`)
- **Files**: snake_case (e.g., `auth.py`, `database.py`, `base.py`)

### Type Hints
- Use Python's `typing` module for complex types
- Use built-in types directly where possible (e.g., `list[str]` over `List[str]`)
- Use `Optional[T]` instead of `Union[T, None]`
- Always include return types on functions

Example:
```python
from typing import Optional, List

async def get_connection(db: Database) -> PoolAcquireContext:
    ...
```

### Pydantic Models (v2)
- Use `pydantic.BaseModel` as base class
- Use `.model_json_schema()` not `.schema()` for schema generation
- Use `model_validate()` not `.parse_obj()` for validation
- Use `model_dump()` not `.dict()` for serialization

Example:
```python
class TokenResponse(BaseModel):
    access_token: str
    expires_in: int
    scope: List[str]
```

### Async/Await
- All database operations use `asyncpg` and must be async
- Use `async with` for context managers (transactions, pool acquisition)
- Use `await` for all async calls

### Error Handling
- Use `HTTPException` from FastAPI for HTTP errors
- Include meaningful error messages
- Use appropriate HTTP status codes

Example:
```python
from fastapi import HTTPException, status

if not client:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid client credentials"
    )
```

### SQL Queries
- Use parameterized queries with `$1`, `$2`, etc.
- Use raw SQL strings (not ORM)
- Keep queries in repository methods

### Configuration
- Use `pydantic_settings.BaseSettings` for configuration
- Use uppercase field names for environment variables
- Access via `settings` singleton from `src.config`

### API Routes
- Use `APIRouter` for route organization
- Use prefixes to group routes (e.g., `/auth`, `/v1`)
- Use tags for OpenAPI documentation
- Use `Security` for dependency injection with scopes
- Depend on services via `Depends(get_*_service)`

### Database
- Access pool via `db.pool` (from `src.dependencies.database`)
- Use transactions for multi-statement operations
- Use connection context managers for safe cleanup

## Project Structure

```
nexuscore/
├── src/
│   ├── main.py           # FastAPI app entry point
│   ├── config.py         # Settings configuration
│   ├── dependencies/    # Dependency injection (auth, database, services, repositories)
│   │   ├── auth/        # Authentication dependencies
│   │   ├── database.py  # Database connection
│   │   ├── services.py  # Service dependency providers
│   │   └── repositories.py # Repository dependency providers
│   ├── models/          # Pydantic models (DB, Out, In)
│   │   ├── auth/        # Authentication models
│   │   ├── quests/      # Quest-related models
│   │   ├── users/       # User-related models
│   │   ├── guilds/      # Guild-related models
│   │   ├── projects/    # Project-related models
│   │   └── worlds/      # World-related models
│   ├── repositories/    # Database interaction layer (returns DB models)
│   │   ├── auth/        # Authentication repositories
│   │   ├── quests/      # Quest-related repositories
│   │   ├── users/       # User-related repositories
│   │   ├── guilds/      # Guild-related repositories
│   │   ├── projects/    # Project-related repositories
│   │   └── worlds/      # World-related repositories
│   ├── services/        # Business logic layer (returns Out models)
│   │   ├── auth/        # Authentication services
│   │   ├── quests/      # Quest-related services
│   │   ├── users/       # User-related services
│   │   ├── guilds/      # Guild-related services
│   │   ├── projects/    # Project-related services
│   │   └── worlds/      # World-related services
│   ├── routes/          # API route handlers (Router layer)
│   │   ├── auth.py      # Authentication routes
│   │   ├── quests.py    # Quest-related routes
│   │   ├── users.py     # User-related routes
│   │   ├── guilds.py    # Guild-related routes
│   │   ├── projects.py  # Project-related routes
│   │   ├── worlds.py    # World-related routes
│   │   └── ...          # Other route files
│   ├── utils/           # Utility classes and functions
│   └── errors.py        # Custom exception classes
├── migrations/          # Database migrations (Alembic)
│   ├── env.py
│   └── versions/
├── config.json          # Application configuration
├── requirements.txt     # Python dependencies
└── Dockerfile           # Docker configuration
```

## Common Patterns

### Creating a New Route
```python
from fastapi import APIRouter, status, Security, Depends
from src.dependencies.auth import Scope, get_guild_client
from src.dependencies.services import get_quest_service
from src.models.auth import TokenPayload
from src.models.quests.quest import QuestIn, QuestOut

router = APIRouter(prefix="/quests", tags=["Quests"])

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_quest(
        body: QuestIn,
        _: TokenPayload = Security(get_guild_client, scopes=[Scope.GUILDS_WRITE]),
        service: QuestService = Depends(get_quest_service)
) -> QuestOut:
    """
    Create New Quest
    """
    return await service.create(body)
```

### Adding a Service
```python
from src.repositories.quests.quest import QuestRepository
from src.models.quests.quest import QuestIn, QuestOut, QuestDB

class QuestService:
    def __init__(self, quest_repo: QuestRepository):
        self.quest_repo = quest_repo

    async def create(self, model: QuestIn) -> QuestOut:
        quest_db = await self.quest_repo.create(model)
        return QuestOut(**quest_db.model_dump())
```

### Adding a Repository
```python
import asyncpg
from asyncpg.pool import PoolConnectionProxy
from src.dependencies.database import Database
from src.errors import AlreadyExists, NotFound
from src.models.quests.quest import QuestDB, QuestIn

class QuestRepository:
    def __init__(self, db: Database):
        self.db = db

    async def create(self, model: QuestIn) -> QuestDB:
        try:
            data = await self.db.pool.fetchrow("""
                INSERT INTO quests_v3.quests(
                    name,
                    description
                )
                VALUES($1, $2)
                RETURNING *
            """, model.name, model.description)
        except asyncpg.UniqueViolationError:
            raise AlreadyExists("Quest")
        return QuestDB.model_validate(dict(data))
```

## Testing

There is currently no testing set up for this project.

## Linting

There is currently no linting configured for this project. Consider adding `ruff` or `flake8` in the future.