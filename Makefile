.DEFAULT_GOAL := help
.PHONY: help setup sync up down migrate logs test lint format typecheck check clean

# ── Setup ─────────────────────────────────────────────────────────────────────

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

setup: ## First-time setup: copy .env and install dependencies
	@if [ ! -f .env ]; then cp .env.example .env && echo "Created .env from .env.example — fill in your secrets"; fi
	@if [ ! -f token.json ]; then echo '{}' > token.json && echo "Created empty token.json (will be populated on first Gmail auth)"; fi
	uv sync

sync: ## Install / update all dependencies
	uv sync

# ── Docker ────────────────────────────────────────────────────────────────────

up: setup ## Build and start all services (db + api)
	docker compose up --build -d
	@echo "API available at http://localhost:8000"
	@echo "Run 'make logs' to follow logs"

down: ## Stop all services
	docker compose down

logs: ## Follow service logs
	docker compose logs -f

migrate: ## Run Alembic migrations (requires db to be running)
	uv run alembic upgrade head

# ── Development ───────────────────────────────────────────────────────────────

auth-gmail: ## Authenticate Gmail OAuth2 locally (run once to generate token.json)
	uv run python -c "from agent.tools.gmail import _get_credentials; _get_credentials(); print('token.json saved — ready for Docker')"

run-agent: ## Run the email agent once locally (requires .env with valid credentials)
	uv run python -c "import asyncio; from agent.email_agent.graph import run_agent; asyncio.run(run_agent())"

run-api: ## Start the API locally (requires local db)
	uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# ── Quality ───────────────────────────────────────────────────────────────────

lint: ## Run ruff linter
	uv run ruff check .

format: ## Format code with ruff
	uv run ruff format .

typecheck: ## Run mypy type checker
	uv run mypy packages/

test: ## Run tests with coverage
	uv run pytest --cov=packages --cov-report=term-missing -v

check: lint typecheck test ## Run all quality checks (lint + types + tests)

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
