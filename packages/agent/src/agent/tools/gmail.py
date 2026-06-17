from __future__ import annotations

import base64
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path

from common.config import get_settings
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from agent.state import EmailMessage

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def _get_credentials() -> Credentials:
    """Load or refresh Gmail OAuth2 credentials."""
    settings = get_settings()
    token_path = Path(settings.gmail_token_json)
    creds: Credentials | None = None

    if token_path.exists() and token_path.stat().st_size > 10:
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        except ValueError:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                settings.gmail_credentials_json, SCOPES
            )
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json())

    return creds


def _decode_body(payload: dict) -> str:  # type: ignore[type-arg]
    """Extract plain text body from a Gmail message payload."""
    if payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    for part in payload.get("parts", []):
        result = _decode_body(part)
        if result:
            return result

    return ""


def fetch_emails(fetch_hours: int | None = None, max_results: int | None = None) -> list[EmailMessage]:
    """Fetch recent emails from Gmail.

    Args:
        fetch_hours: How many hours back to look. Defaults to settings value.
        max_results: Maximum number of emails to fetch. Defaults to settings value.

    Returns:
        List of EmailMessage dicts.
    """
    settings = get_settings()
    hours = fetch_hours or settings.gmail_fetch_hours
    limit = max_results or settings.gmail_max_results

    creds = _get_credentials()
    service = build("gmail", "v1", credentials=creds)

    after_ts = int((datetime.now(UTC) - timedelta(hours=hours)).timestamp())
    query = f"after:{after_ts}"

    results = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=limit)
        .execute()
    )
    message_refs = results.get("messages", [])

    emails: list[EmailMessage] = []
    for ref in message_refs:
        msg = service.users().messages().get(userId="me", id=ref["id"], format="full").execute()
        headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}

        body = _decode_body(msg["payload"])
        snippet = body[:500].strip() if body else msg.get("snippet", "")

        date_str = headers.get("Date", "")
        try:
            received_at = datetime.strptime(date_str[:25], "%a, %d %b %Y %H:%M:%S").isoformat()
        except ValueError:
            received_at = datetime.now(UTC).isoformat()

        emails.append(
            EmailMessage(
                gmail_id=msg["id"],
                thread_id=msg.get("threadId", ""),
                sender=headers.get("From", ""),
                subject=headers.get("Subject", "(no subject)"),
                body_snippet=snippet,
                received_at=received_at,
            )
        )
        logger.debug("Fetched email %s: %s", msg["id"], headers.get("Subject", ""))

    logger.info("Fetched %d emails from Gmail (last %dh)", len(emails), hours)
    return emails
