# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project : Email Super Agent
This project goes through my emails and creates a report.
Python 3.12+

> Project must always start with `plan` mode and then after approval goes into the development stage.

## Project Development
- Maintain a PRD.md(Project Requirement Doc). It should be updated before building a new feature. This document is for Product Manager and used by engineering for building the feature.
- Maintain a file system_design.md for updated system design. It should be updated before the development. System Design is created to support new features in PRD.
- Maintain a LLD.md to keep a record of critical low level implementation details. Only essential information goes here.


## Setup
- Use UV package and project manager https://docs.astral.sh/uv/
- Use Monorepo to keep the projects clean and organized https://monorepo.tools
    - Common things should go in common package eg; database models
    - API can have its own package
    - AI related things can be abstracted in separate package
    - dependent package can be imported in other packages as per need
- Use Docker-Compose to run all the projects together
    - It should start it one command without manual additional setup
- Always have a how_to_run.md file updated so that user can read and run the project
- Environment variables: copy `.env.example` to `.env` for local development
    - If new docker starts then it should update the .env automatically so that project doesn't fail to start
- Keep a Makefile updated for shortcut
- alembic for data migrations and seeding

## Commands

- `pytest` — run all tests
- `pytest tests/test_items.py::test_create_item -v` — run a single test
- `pytest --cov=src --cov-report=term-missing` — run tests with coverage
- `ruff check .` — lint
- `ruff format .` — format code
- `mypy src/` — type checking

Run `ruff check . && mypy src/` before committing.

## Coding Conventions

- Type hints on all function signatures — parameters and return types
- Use `from __future__ import annotations` at the top of every module
- Pydantic models for all API input/output — never pass raw dicts across boundaries
- Use `pathlib.Path` instead of `os.path`
- f-strings for string formatting (no .format() or % formatting)
- Docstrings on public functions using Google style

```python
def get_item(item_id: int, db: Session) -> Item:
    """Fetch a single item by ID.

    Args:
        item_id: The item's primary key.
        db: Database session.

    Returns:
        The matching Item.

    Raises:
        NotFoundError: If no item matches the ID.
    """
```


## Testing

- Use pytest with fixtures defined in `conftest.py`
- Test database: use an in-memory SQLite or test-specific PostgreSQL database — never touch the dev database
- Factory fixtures for creating test data
- Aim for >80% coverage on business logic 

## Git

- Conventional commits: feat:, fix:, chore:
- Run the full check before committing: `ruff check . && ruff format --check . && mypy src/ && pytest`

## Do NOT

- Do not use `import *`
- Do not use `objects.raw()` or raw SQL — use the repository layer
- Do not use `print()` — use the configured `logging` module
- Do not use `*` imports
