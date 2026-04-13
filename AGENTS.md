# AGENTS.md - Nexuscore Development Guide

## Project Overview

- **Project**: Nexuscore - FastAPI backend for Everthorn internal services
- **Language**: Python 3.12
- **Framework**: FastAPI with asyncpg (async PostgreSQL)
- **Database**: PostgreSQL

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
3. Local application imports (`src.dependencies`, `src.models`, `src.routes`)

Example:
```python
import secrets
from typing import Optional

from argon2 import PasswordHasher
from fastapi import APIRouter, Depends, Form

from src.dependencies.auth import get_current_client
from src.dependencies.database import db
from src.models.auth import ClientCreateRequest
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
- Keep queries in route handlers or dedicated model methods

### Configuration
- Use `pydantic_settings.BaseSettings` for configuration
- Use uppercase field names for environment variables
- Access via `settings` singleton from `src.config`

### API Routes
- Use `APIRouter` for route organization
- Use prefixes to group routes (e.g., `/auth`, `/v1`)
- Use tags for OpenAPI documentation
- Use `Security` for dependency injection with scopes

### Database
- Access pool via `db.pool` (from `src.dependencies.database`)
- Use transactions for multi-statement operations
- Use connection context managers for safe cleanup

## Testing

There is currently no testing set up for this project.

## Linting

There is currently no linting configured for this project. Consider adding `ruff` or `flake8` in the future.

## Project Structure

```
nexuscore/
├── src/
│   ├── main.py           # FastAPI app entry point
│   ├── config.py         # Settings configuration
│   ├── dependencies/    # Dependency injection (auth, database)
│   ├── models/          # Pydantic models (auth, users, guilds, etc.)
│   ├── routes/          # API route handlers
│   └── utils/           # Utility classes and functions
├── config.json          # Application configuration
├── requirements.txt     # Python dependencies
└── Dockerfile           # Docker configuration
```

## Common Patterns

### Creating a New Route
```python
from fastapi import APIRouter, Depends, Security
from src.dependencies.auth import get_current_client
from src.dependencies.database import db
from src.models.auth import TokenPayload

router = APIRouter(prefix="/endpoint", tags=["Category"])

@router.get("/items")
async def get_items(token: TokenPayload = Security(get_current_client)):
    # implementation
    return {"items": []}
```

### Adding a Model
```python
from pydantic import BaseModel
from typing import Optional

class MyModel(BaseModel):
    field1: str
    field2: Optional[int] = None
```
