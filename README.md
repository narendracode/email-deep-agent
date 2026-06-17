# Email Super Agent

AI-powered email analysis and reporting using LangGraph, LangChain, and Claude Opus 4.8.

## Quick Start

```bash
make setup   # copy .env, install deps
# fill in ANTHROPIC_API_KEY and Gmail credentials in .env
make up      # start PostgreSQL + API via Docker
```

See [how_to_run.md](how_to_run.md) for full setup instructions including Gmail OAuth2 setup.

## Documentation

- [PRD.md](PRD.md) — Product requirements
- [system_design.md](system_design.md) — Architecture and data flow
- [LLD.md](LLD.md) — Low-level implementation details
- [how_to_run.md](how_to_run.md) — Setup and running guide
