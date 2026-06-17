from __future__ import annotations

from typing import TypedDict


class EmailMessage(TypedDict):
    """Raw email data fetched from Gmail."""

    gmail_id: str
    thread_id: str
    sender: str
    subject: str
    body_snippet: str
    received_at: str  # ISO 8601


class AnalyzedEmail(TypedDict):
    """Per-email analysis result from Claude."""

    gmail_id: str
    category: str  # ActionRequired | Meeting | Finance | FYI | Newsletter | Spam
    summary: str   # 1-3 sentences
    is_urgent: bool


class AgentState(TypedDict):
    """LangGraph state passed between nodes."""

    run_id: str
    emails: list[EmailMessage]
    analyzed: list[AnalyzedEmail]
    report_markdown: str
    errors: list[str]
