FROM python:3.12.0-alpine

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_LINK_MODE=copy

# Install dependencies first (layer caching)
COPY pyproject.toml uv.lock /nexuscore/
RUN uv sync --frozen --no-dev --project /nexuscore

# Copy source
COPY . /nexuscore/

ENV PYTHONPATH="${PYTHONPATH}:/nexuscore/"

WORKDIR /nexuscore/src

CMD ["uv", "run", "--project", "/nexuscore", "fastapi", "run", "--host", "0.0.0.0"]