from __future__ import annotations

import logging
from datetime import datetime

from common.database import AsyncSessionLocal
from common.models import EmailRecord, Run
from sqlalchemy import select

from agent.state import AgentState, EmailMessage
from agent.tools.gmail import fetch_emails as gmail_fetch

logger = logging.getLogger(__name__)


async def fetch_emails_node(state: AgentState) -> AgentState:
    """Fetch emails from Gmail and persist raw records to the database.

    Args:
        state: Current agent state with run_id.

    Returns:
        Updated state with emails list populated.
    """
    run_id = state["run_id"]
    errors: list[str] = list(state.get("errors", []))

    try:
        email_messages: list[EmailMessage] = gmail_fetch()
    except Exception as exc:
        logger.exception("Failed to fetch emails from Gmail")
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Run).where(Run.id == run_id))
            run = result.scalar_one_or_none()
            if run:
                run.status = "failed"
                run.error = str(exc)
                await session.commit()
        return {**state, "emails": [], "errors": [*errors, f"fetch_emails: {exc}"]}

    async with AsyncSessionLocal() as session:
        for email in email_messages:
            received_at = datetime.fromisoformat(email["received_at"])
            record = EmailRecord(
                run_id=run_id,
                gmail_id=email["gmail_id"],
                thread_id=email["thread_id"],
                sender=email["sender"],
                subject=email["subject"],
                body_snippet=email["body_snippet"],
                received_at=received_at,
            )
            session.add(record)
        await session.commit()

    logger.info("Persisted %d email records for run %s", len(email_messages), run_id)
    return {**state, "emails": email_messages, "errors": errors}
