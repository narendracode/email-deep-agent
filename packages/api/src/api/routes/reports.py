from __future__ import annotations

import logging
from datetime import datetime

from agent.graph import run_agent
from common.database import get_session
from common.models import Report, Run
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter()


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


async def _run_agent_task(run_id: str) -> None:
    """Background task wrapper for the agent graph."""
    try:
        await run_agent(run_id=run_id)
    except Exception:
        logger.exception("Agent run %s failed", run_id)


@router.post("/run", response_model=RunResponse, status_code=202)
async def trigger_run(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> RunResponse:
    """Trigger a new email analysis run.

    Returns:
        The new run ID and initial status.
    """
    run = Run()
    session.add(run)
    await session.commit()
    await session.refresh(run)

    background_tasks.add_task(_run_agent_task, run.id)

    return RunResponse(run_id=run.id, status=run.status)


@router.get("/reports", response_model=list[ReportSummary])
async def list_reports(
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> list[ReportSummary]:
    """List all generated reports (newest first).

    Returns:
        List of report summaries.
    """
    result = await session.execute(
        select(Report).order_by(Report.created_at.desc()).limit(50)
    )
    reports = result.scalars().all()
    return [
        ReportSummary(
            run_id=r.run_id,
            email_count=r.email_count,
            created_at=r.created_at,
        )
        for r in reports
    ]


@router.get("/reports/{run_id}", response_model=ReportDetail)
async def get_report(
    run_id: str,
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> ReportDetail:
    """Retrieve a specific report by run ID.

    Args:
        run_id: The run identifier.

    Returns:
        Full report detail including Markdown content.

    Raises:
        HTTPException: 404 if the report does not exist.
    """
    result = await session.execute(select(Report).where(Report.run_id == run_id))
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=404, detail=f"Report not found for run_id={run_id}")

    return ReportDetail(
        run_id=report.run_id,
        markdown=report.markdown,
        email_count=report.email_count,
        created_at=report.created_at,
    )
