# How to Run — Email Super Agent

## Prerequisites

- [UV](https://docs.astral.sh/uv/) installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) running
- An [Anthropic API key](https://console.anthropic.com/)
- A Google Cloud project with Gmail API enabled and OAuth2 credentials downloaded as `credentials.json`

---

## 1. First-Time Setup

```bash
# Clone the repo
git clone https://github.com/narendracode/email-deep-agent.git
cd email-deep-agent

# Install dependencies and create .env from template
make setup
```

Open `.env` and fill in your secrets:

```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
GMAIL_CREDENTIALS_JSON=credentials.json   # path to your Google OAuth2 file
```

Place your `credentials.json` (downloaded from Google Cloud Console) in the project root.

---

## 2. Start Services with Docker

```bash
make up
```

This will:
1. Start PostgreSQL on port 5432
2. Run Alembic migrations automatically
3. Start the FastAPI API on port 8000

Verify everything is running:
```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

---

## 3. Gmail OAuth2 Authentication (First Run)

The first time you trigger an agent run, Gmail OAuth2 will open a browser window for you to authorize access. This only happens once — the token is saved to `token.json`.

```bash
# Trigger a run (this will open your browser for Gmail auth if needed)
curl -X POST http://localhost:8000/run
# {"run_id":"...", "status":"running"}
```

---

## 4. Check Your Report

```bash
# List all reports
curl http://localhost:8000/reports

# Get a specific report (replace RUN_ID with the value from POST /run)
curl http://localhost:8000/reports/RUN_ID
```

---

## 5. Common Commands

| Command | Description |
|---------|-------------|
| `make up` | Build and start all services |
| `make down` | Stop all services |
| `make logs` | Follow Docker logs |
| `make migrate` | Run database migrations |
| `make test` | Run tests with coverage |
| `make check` | Run lint + types + tests |
| `make run-api` | Start API locally (without Docker) |
| `make run-agent` | Run agent once locally |

---

## 6. Running Tests

```bash
make test
# or
uv run pytest --cov=packages --cov-report=term-missing -v
```

---

## 7. Gmail API Setup (Google Cloud Console)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable the **Gmail API**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Application type: **Desktop app**
6. Download the JSON and save as `credentials.json` in the project root
7. Add your email address to **Test users** under OAuth consent screen

---

## 8. Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | (postgres on db:5432) | PostgreSQL connection string |
| `ANTHROPIC_API_KEY` | — | Your Anthropic API key (required) |
| `GMAIL_CREDENTIALS_JSON` | `credentials.json` | Path to OAuth2 credentials file |
| `GMAIL_TOKEN_JSON` | `token.json` | Path to persisted OAuth2 token |
| `GMAIL_FETCH_HOURS` | `24` | Hours of email history per run |
| `GMAIL_MAX_RESULTS` | `100` | Max emails per run |
| `LOG_LEVEL` | `INFO` | Logging level |
| `ENVIRONMENT` | `development` | App environment |
