from __future__ import annotations

import asyncio
import json
import logging

from common.database import AsyncSessionLocal
from common.models import EmailRecord
from sqlalchemy import update

from agent.email_agent.state import AgentState, AnalyzedEmail, EmailMessage
from agent.llm import complete

logger = logging.getLogger(__name__)

CATEGORIES = ["ActionRequired", "Meeting", "Finance", "FYI", "Newsletter", "Spam"]
BATCH_SIZE = 10


def _build_analyze_prompt(email: EmailMessage) -> str:
    return f"""Analyze the following email and respond with a JSON object only — no prose.

Email:
From: {email["sender"]}
Subject: {email["subject"]}
Body: {email["body_snippet"]}

Respond with exactly this JSON structure:
{{
  "category": "<one of: ActionRequired | Meeting | Finance | FYI | Newsletter | Spam>",
  "summary": "<1-3 sentence summary of the email>",
  "is_urgent": <true | false>
}}"""


async def _analyze_one(email: EmailMessage) -> AnalyzedEmail | None:
    """Analyze a single email with Claude. Returns None on failure."""
    try:
        raw = await complete(_build_analyze_prompt(email), max_tokens=512)
        # Extract JSON from response (Claude may wrap it in markdown code fences)
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text.strip())
        category = data.get("category", "FYI")
        if category not in CATEGORIES:
            category = "FYI"
        return AnalyzedEmail(
            gmail_id=email["gmail_id"],
            category=category,
            summary=data.get("summary", ""),
            is_urgent=bool(data.get("is_urgent", False)),
        )
    except Exception as exc:
        logger.warning("Failed to analyze email %s: %s", email["gmail_id"], exc)
        return None


async def analyze_node(state: AgentState) -> AgentState:
    """Classify and summarize each email using Claude.

    Args:
        state: Current agent state with emails list.

    Returns:
        Updated state with analyzed list populated.
    """
    emails = state["emails"]
    run_id = state["run_id"]
    errors: list[str] = list(state.get("errors", []))
    analyzed: list[AnalyzedEmail] = []

    # Process in batches to avoid overwhelming the API
    for i in range(0, len(emails), BATCH_SIZE):
        batch = emails[i : i + BATCH_SIZE]
        results = await asyncio.gather(*[_analyze_one(e) for e in batch])
        for email, result in zip(batch, results, strict=True):
            if result:
                analyzed.append(result)
            else:
                errors.append(f"analyze: failed for gmail_id={email['gmail_id']}")

    # Persist analysis results back to DB
    async with AsyncSessionLocal() as session:
        for item in analyzed:
            await session.execute(
                update(EmailRecord)
                .where(EmailRecord.gmail_id == item["gmail_id"])
                .where(EmailRecord.run_id == run_id)
                .values(
                    category=item["category"],
                    summary=item["summary"],
                    is_urgent=item["is_urgent"],
                )
            )
        await session.commit()

    logger.info("Analyzed %d/%d emails for run %s", len(analyzed), len(emails), run_id)
    return {**state, "analyzed": analyzed, "errors": errors}
