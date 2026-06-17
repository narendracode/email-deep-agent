FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy workspace definition, lockfile, and package manifests (layer cache)
COPY pyproject.toml uv.lock ./
COPY packages/common/pyproject.toml packages/common/
COPY packages/agent/pyproject.toml packages/agent/
COPY packages/api/pyproject.toml packages/api/

# Install all dependencies (no dev deps), respecting the lockfile
RUN uv sync --no-dev --frozen

# Copy source and migration files
COPY packages/common/src packages/common/src
COPY packages/agent/src packages/agent/src
COPY packages/api/src packages/api/src
COPY alembic.ini ./
COPY migrations/ migrations/

# Make src-layout packages importable without editable-install path resolution
ENV PYTHONPATH=/app/packages/common/src:/app/packages/agent/src:/app/packages/api/src

EXPOSE 8000

CMD ["/app/.venv/bin/uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
