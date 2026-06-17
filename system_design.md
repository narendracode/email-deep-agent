# System Design: Email Super Agent

**Version:** 1.0  
**Status:** Draft  

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                        Client / Cron                         │
└─────────────────────────┬────────────────────────────────────┘
                          │ POST /run
                          ▼
┌──────────────────────────────────────────────────────────────┐
│                      packages/api (FastAPI)                  │
│  POST /run  ──► triggers AgentGraph.run()                    │
│  GET  /reports/{id}  ◄── reads from DB                       │
└─────────────────────────┬────────────────────────────────────┘
                          │ invoke
                          ▼
┌──────────────────────────────────────────────────────────────┐
│                   packages/agent (LangGraph)                  │
│                                                              │
│   ┌──────────────┐   ┌──────────────┐   ┌───────────────┐   │
│   │ fetch_emails │──►│   analyze    │──►│    report     │   │
│   │  (Gmail API) │   │  (Claude x N)│   │  (Claude x 1) │   │
│   └──────────────┘   └──────────────┘   └───────┬───────┘   │
│                                                  │ persist   │
└──────────────────────────────────────────────────┼───────────┘
                                                   │
                          ┌────────────────────────┘
                          ▼
┌──────────────────────────────────────────────────────────────┐
│                   packages/common                             │
│   ┌─────────────────────────────────────────────────────┐    │
│   │              PostgreSQL 16                          │    │
│   │   email_records  │  email_analyses  │  reports      │    │
│   └─────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┘
          ▼
┌──────────────────────────────────┐
│    External Services             │
│  • Gmail API (OAuth2)            │
│  • Anthropic API (Claude Opus)   │
└──────────────────────────────────┘
```

---

## Services (Docker-Compose)

| Service | Image / Build         | Port  | Role                              |
|---------|-----------------------|-------|-----------------------------------|
| `db`    | `postgres:16-alpine`  | 5432  | Primary data store                |
| `api`   | `docker/api.Dockerfile` | 8000 | REST API, triggers agent runs     |
| `agent` | `docker/agent.Dockerfile` | —  | Background worker / one-shot runs |

All services share a single Docker network (`deep-agent-net`). The `api` service communicates with `agent` package code in-process (imported directly). For future scale, `agent` can be extracted to a separate Celery/RQ worker.

---

## Data Flow

### Run Lifecycle

```
1. POST /run
   └─► Create Run record (status=running)
   └─► Invoke LangGraph with run_id in state

2. Node: fetch_emails
   └─► OAuth2 token from env/secret
   └─► Gmail API: list messages (last 24h)
   └─► Persist raw EmailRecord rows (run_id FK)

3. Node: analyze (per email, batched)
   └─► Build prompt: subject + body snippet
   └─► Claude Opus 4.8 (adaptive thinking, streaming)
   └─► Parse: category + summary + urgency flag
   └─► Update EmailRecord with analysis fields

4. Node: report
   └─► Aggregate all analyses into prompt
   └─► Claude Opus 4.8 → Markdown report
   └─► Persist Report row (run_id FK, markdown)
   └─► Update Run record (status=completed)

5. GET /reports/{run_id}
   └─► Read Report row → return JSON { markdown, metadata }
```

---

## Package Boundaries

### `packages/common`
- Owns: SQLAlchemy models, Alembic migrations, DB session factory, pydantic-settings config
- Imported by: `agent`, `api`
- No business logic

### `packages/agent`
- Owns: LangGraph graph definition, all nodes, Anthropic LLM client, Gmail tool
- Depends on: `common` (models, DB session, config)
- No HTTP concerns

### `packages/api`
- Owns: FastAPI app, route handlers, request/response Pydantic schemas
- Depends on: `common` (DB session, config), `agent` (graph invocation)
- No DB model definitions

---

## Database Schema

```
email_records
  id            UUID PK
  run_id        UUID FK → runs.id
  gmail_id      TEXT
  thread_id     TEXT
  sender        TEXT
  subject       TEXT
  body_snippet  TEXT
  received_at   TIMESTAMP
  category      TEXT        -- filled by analyze node
  summary       TEXT        -- filled by analyze node
  is_urgent     BOOLEAN     -- filled by analyze node
  created_at    TIMESTAMP DEFAULT NOW()

reports
  id            UUID PK
  run_id        UUID FK → runs.id  UNIQUE
  markdown      TEXT
  email_count   INT
  created_at    TIMESTAMP DEFAULT NOW()

runs
  id            UUID PK
  status        TEXT  -- running | completed | failed
  started_at    TIMESTAMP
  completed_at  TIMESTAMP
  error         TEXT
```

---

## Security Considerations

- Gmail OAuth2 tokens stored in environment variables (never in DB or logs)
- Anthropic API key from environment only
- PostgreSQL password from environment only
- No secrets committed to git (`.env` is gitignored)
- API has no auth in v1 (localhost/internal only); add bearer token in v2

---

## Scalability Notes (Future)

- Analyze node is O(N emails) — can parallelize with `asyncio.gather` per batch
- Agent can be extracted to Celery worker with Redis broker for async job queue
- Gmail webhook (Pub/Sub push) can replace polling for real-time processing
- Report storage can be extended with S3 for large attachments
