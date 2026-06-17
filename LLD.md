# LLD: Email Super Agent

**Version:** 1.0  
**Status:** Draft  

---

## LangGraph State Schema

```python
# packages/agent/src/agent/state.py

class EmailMessage(TypedDict):
    gmail_id: str
    thread_id: str
    sender: str
    subject: str
    body_snippet: str
    received_at: str  # ISO 8601

class AnalyzedEmail(TypedDict):
    gmail_id: str
    category: str   # ActionRequired | Meeting | Finance | FYI | Newsletter | Spam
    summary: str    # 1-3 sentences
    is_urgent: bool

class AgentState(TypedDict):
    run_id: str
    emails: list[EmailMessage]
    analyzed: list[AnalyzedEmail]
    report_markdown: str
    errors: list[str]
```

Graph edges: `fetch_emails → analyze → report → END`

---

## Anthropic Client Pattern

```python
# packages/agent/src/agent/llm.py

import anthropic

_client: anthropic.AsyncAnthropic | None = None

def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic()  # reads ANTHROPIC_API_KEY from env
    return _client

# Usage in nodes — streaming with adaptive thinking:
async with get_client().messages.stream(
    model="claude-opus-4-8",
    max_tokens=4096,
    thinking={"type": "adaptive"},
    messages=[{"role": "user", "content": prompt}],
) as stream:
    response = await stream.get_final_message()
```

---

## Node Contracts

### `fetch_emails` node
- **Input state fields used:** `run_id`
- **Output state fields set:** `emails`, `errors`
- **Side effects:** Inserts `EmailRecord` rows (category/summary/is_urgent = NULL)
- **Gmail scopes required:** `https://www.googleapis.com/auth/gmail.readonly`
- **Config:** `GMAIL_FETCH_HOURS` (default 24), `GMAIL_MAX_RESULTS` (default 100)

### `analyze` node
- **Input state fields used:** `emails`, `run_id`
- **Output state fields set:** `analyzed`, `errors`
- **Side effects:** Updates `EmailRecord` rows with category/summary/is_urgent
- **Claude call:** One call per email (batched in groups of 10 via `asyncio.gather`)
- **Prompt template key:** classify + summarize in a single structured response

### `report` node
- **Input state fields used:** `analyzed`, `run_id`
- **Output state fields set:** `report_markdown`
- **Side effects:** Inserts `Report` row, updates `Run.status = completed`
- **Claude call:** Single streaming call over all analyzed emails

---

## Pydantic Schemas (API layer)

```python
# packages/api/src/api/routes/reports.py

class RunResponse(BaseModel):
    run_id: str
    status: str

class ReportSummary(BaseModel):
    run_id: str
    email_count: int
    created_at: datetime

class ReportDetail(BaseModel):
    run_id: str
    markdown: str
    email_count: int
    created_at: datetime
```

---

## Config (pydantic-settings)

```python
# packages/common/src/common/config.py

class Settings(BaseSettings):
    # Database
    database_url: str  # postgresql+asyncpg://...

    # Anthropic
    anthropic_api_key: str

    # Gmail
    gmail_credentials_json: str  # path to OAuth2 credentials file
    gmail_token_json: str        # path to persisted token
    gmail_fetch_hours: int = 24
    gmail_max_results: int = 100

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
```

---

## SQLAlchemy Models

```python
# Declarative base in packages/common/src/common/database.py
Base = DeclarativeBase()

# packages/common/src/common/models/run.py
class Run(Base):
    __tablename__ = "runs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    status: Mapped[str] = mapped_column(String, default="running")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

# packages/common/src/common/models/email_record.py
class EmailRecord(Base):
    __tablename__ = "email_records"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"))
    gmail_id: Mapped[str] = mapped_column(String)
    thread_id: Mapped[str] = mapped_column(String)
    sender: Mapped[str] = mapped_column(String)
    subject: Mapped[str] = mapped_column(String)
    body_snippet: Mapped[str] = mapped_column(Text)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_urgent: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())

# packages/common/src/common/models/report.py
class Report(Base):
    __tablename__ = "reports"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), unique=True)
    markdown: Mapped[str] = mapped_column(Text)
    email_count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
```

---

## Alembic Setup

- `alembic.ini` at repo root pointing to `migrations/`
- `migrations/env.py` imports `Base` from `common.database` and all models to ensure they register
- Sync engine used for migrations only (alembic doesn't support async natively)
- `DATABASE_URL` env var used; async URL (`postgresql+asyncpg://`) must be converted to sync (`postgresql+psycopg2://`) for alembic env.py

---

## Error Handling Strategy

- Node-level errors are caught and appended to `state["errors"]` (non-fatal)
- If `fetch_emails` fails entirely, graph transitions to END with `Run.status = failed`
- Individual email analysis failures skip that email and log to `errors`
- All unhandled exceptions in API routes return `500` with a `detail` field
