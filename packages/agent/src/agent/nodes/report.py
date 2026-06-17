from __future__ import annotations

import logging
from collections import defaultdict
from datetime import UTC, datetime

from common.database import AsyncSessionLocal
from common.models import Report, Run
from sqlalchemy import select

from agent.llm import complete
from agent.state import AgentState, AnalyzedEmail

logger = logging.getLogger(__name__)


def _build_report_prompt(analyzed: list[AnalyzedEmail]) -> str:
    by_category: dict[str, list[AnalyzedEmail]] = defaultdict(list)
    for item in analyzed:
        by_category[item["category"]].append(item)

    sections: list[str] = []
    for category, items in by_category.items():
        lines = [f"### {category}"]
        for item in items:
            urgent_tag = " ⚠️ URGENT" if item["is_urgent"] else ""
            lines.append(f"- {item['summary']}{urgent_tag}")
        sections.append("\n".join(lines))

    categorized_text = "\n\n".join(sections)

    return f"""You are an executive assistant. Based on the email summaries below, produce a concise Markdown report.

Structure the report exactly as follows:
1. ## Executive Summary — 3-5 bullet points of the most important items
2. ## Action Required — emails needing a response or action
3. ## Meetings & Calendar — meeting invites, reminders
4. ## Finance & Billing — invoices, payments, financial alerts
5. ## FYI — informational emails
6. ## Newsletters — newsletters and marketing
7. ## Spam / Ignore — low-value emails

Email summaries by category:
{categorized_text}

Write the report now. Use Markdown formatting. Be concise."""


async def report_node(state: AgentState) -> AgentState:
    """Generate the final Markdown report using Claude and persist it.

    Args:
        state: Current agent state with analyzed emails.

    Returns:
        Updated state with report_markdown populated.
    """
    analyzed = state["analyzed"]
    run_id = state["run_id"]
    errors: list[str] = list(state.get("errors", []))

    if not analyzed:
        markdown = "# Email Report\n\nNo emails were successfully analyzed in this run."
    else:
        try:
            markdown = await complete(_build_report_prompt(analyzed), max_tokens=8192)
        except Exception as exc:
            logger.exception("Failed to generate report for run %s", run_id)
            errors.append(f"report: {exc}")
            markdown = "# Email Report\n\nReport generation failed."

    async with AsyncSessionLocal() as session:
        # Persist report
        report = Report(
            run_id=run_id,
            markdown=markdown,
            email_count=len(analyzed),
        )
        session.add(report)

        # Mark run as completed
        result = await session.execute(select(Run).where(Run.id == run_id))
        run = result.scalar_one_or_none()
        if run:
            run.status = "completed" if not errors else "completed_with_errors"
            run.completed_at = datetime.now(UTC)

        await session.commit()

    logger.info("Report generated for run %s (%d emails)", run_id, len(analyzed))
    return {**state, "report_markdown": markdown, "errors": errors}
