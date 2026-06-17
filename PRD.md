# PRD: Email Super Agent

**Version:** 1.0  
**Status:** Draft  
**Owner:** Product  

---

## Overview

Email Super Agent is an AI-powered system that autonomously reads a user's Gmail inbox, classifies and summarizes emails, and produces a structured daily/on-demand report. The agent is orchestrated by LangGraph, reasoned by Claude Opus 4.8, and surfaced via a REST API.

---

## Problem Statement

Users receive dozens to hundreds of emails daily. Manually triaging them is time-consuming and error-prone. An intelligent agent that reads, categorizes, and summarizes emails into a concise report saves significant cognitive load and ensures nothing important is missed.

---

## Goals

1. Fetch unread/recent emails from Gmail automatically.
2. Classify each email by category (Action Required, FYI, Newsletter, Spam, Meeting, Finance, etc.).
3. Summarize email content using Claude with adaptive thinking.
4. Generate a structured Markdown report grouped by category, with priority highlights.
5. Persist raw emails and reports in PostgreSQL for history and re-querying.
6. Expose a REST API to trigger runs and retrieve reports.

---

## Non-Goals (v1)

- Multi-provider email support (Outlook, Yahoo) — Gmail only
- Real-time push notifications (webhook-triggered)
- UI / frontend dashboard
- Sending or replying to emails on behalf of the user

---

## User Stories

| ID  | As a…  | I want to…                              | So that…                                 |
|-----|--------|-----------------------------------------|------------------------------------------|
| U1  | User   | Trigger an email analysis run via API   | I get a fresh report on demand           |
| U2  | User   | Retrieve my latest report               | I can review it in my preferred tool     |
| U3  | User   | See emails grouped by category          | I can focus on action items first        |
| U4  | User   | See key highlights at the top           | I don't have to read the full report     |
| U5  | User   | Access historical reports               | I can compare or search past summaries   |

---

## Functional Requirements

### Email Fetching
- Connect to Gmail via OAuth2 (Google API)
- Fetch emails from the last N hours (configurable, default 24h)
- Store raw email data (subject, sender, body, timestamp, thread ID) in `email_records` table

### Email Analysis
- Per-email Claude call: classify category + extract 1-3 sentence summary + flag urgency
- Batch processing to stay within rate limits
- Store per-email analysis results alongside the raw record

### Report Generation
- Single Claude call over all analyzed emails to produce a Markdown report
- Report structure:
  1. **Executive Summary** (3-5 bullet points of most important items)
  2. **Action Required** section
  3. **Meetings & Calendar** section
  4. **Finance & Billing** section
  5. **FYI / Newsletters** section
  6. **Spam / Ignore** section
- Store report as Markdown text in `reports` table

### API
- `POST /run` — trigger a new agent run, return `{ run_id, status }`
- `GET /reports` — list all reports (id, created_at, email_count)
- `GET /reports/{run_id}` — return full report Markdown + metadata
- `GET /health` — liveness check

---

## Acceptance Criteria

- [ ] `POST /run` completes within 120 seconds for ≤100 emails
- [ ] Each email is assigned exactly one category
- [ ] Report Markdown renders correctly (valid headers, lists)
- [ ] All emails and reports are persisted with `run_id` linkage
- [ ] API returns appropriate HTTP error codes on failure
- [ ] Test coverage ≥ 80% on business logic

---

## Tech Stack

| Layer         | Technology                          |
|---------------|-------------------------------------|
| Orchestration | LangGraph                           |
| LLM           | Anthropic Claude Opus 4.8           |
| LLM Client    | LangChain + `anthropic` Python SDK  |
| Email         | Google Gmail API (OAuth2)           |
| API           | FastAPI                             |
| Database      | PostgreSQL 16 via SQLAlchemy async  |
| Migrations    | Alembic                             |
| Packaging     | UV (monorepo)                       |
| Runtime       | Docker-Compose                      |

---

## Milestones

| Milestone            | Deliverable                                      |
|----------------------|--------------------------------------------------|
| M1 — Base Project    | Monorepo scaffold, Docker, CI config             |
| M2 — Agent Core      | LangGraph graph running end-to-end (mock Gmail)  |
| M3 — Gmail Integration | Real Gmail OAuth2 fetch                        |
| M4 — API             | FastAPI endpoints wired to agent                 |
| M5 — Polish          | Error handling, retries, coverage ≥ 80%          |
