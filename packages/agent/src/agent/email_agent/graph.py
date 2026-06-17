from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import uuid4

from common.database import AsyncSessionLocal
from common.models import Run
from langgraph.graph import END, StateGraph

from agent.email_agent.state import AgentState
from agent.nodes.analyze import analyze_node
from agent.nodes.fetch_emails import fetch_emails_node
from agent.nodes.report import report_node

logger = logging.getLogger(__name__)

_graph = (
    StateGraph(AgentState)
    .add_node("fetch_emails", fetch_emails_node)
    .add_node("analyze", analyze_node)
    .add_node("report", report_node)
    .add_edge("fetch_emails", "analyze")
    .add_edge("analyze", "report")
    .add_edge("report", END)
    .set_entry_point("fetch_emails")
    .compile()
)


async def run_agent(run_id: str | None = None) -> AgentState:
    """Invoke the email LangGraph agent, creating a Run record only if needed.

    Args:
        run_id: Existing run ID (already persisted by the API). Creates a new
                Run row only when None (e.g. direct/CLI invocation).

    Returns:
        Final AgentState after the graph completes.
    """
    if run_id is None:
        run_id = str(uuid4())
        async with AsyncSessionLocal() as session:
            run = Run(id=run_id, started_at=datetime.now(UTC))
            session.add(run)
            await session.commit()

    initial_state = AgentState(
        run_id=run_id,
        emails=[],
        analyzed=[],
        report_markdown="",
        errors=[],
    )

    logger.info("Starting email agent run %s", run_id)
    final_state: AgentState = await _graph.ainvoke(initial_state)
    logger.info(
        "Completed email agent run %s with %d errors",
        run_id,
        len(final_state.get("errors", [])),
    )
    return final_state
