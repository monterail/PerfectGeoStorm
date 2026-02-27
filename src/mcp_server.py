"""MCP server exposing GeoStorm perception data to LLM clients."""

from __future__ import annotations

import difflib
from typing import TYPE_CHECKING

from fastmcp import FastMCP

from src.container import (
    alert_service,
    project_repo,
    project_service,
    run_service,
    term_repo,
)
from src.schemas import (
    AlertResponse,
    ProjectResponse,
    ProjectSummary,
    RunDetailResponse,
    TrajectoryResponse,
)

if TYPE_CHECKING:
    import aiosqlite

_FUZZY_MATCH_THRESHOLD = 0.6


class ProjectNotFoundError(Exception):
    """Raised when a project cannot be resolved by ID or name."""

    def __init__(self, project: str, available: list[str]) -> None:
        names = ", ".join(available) or "none"
        super().__init__(f"Project '{project}' not found. Available projects: {names}")


class RunNotFoundError(Exception):
    """Raised when a run ID does not exist."""

    def __init__(self, run_id: str) -> None:
        super().__init__(f"Run '{run_id}' not found")


mcp = FastMCP(
    "GeoStorm",
    instructions=(
        "GeoStorm monitors how AI models perceive and recommend software products. "
        "Use these tools to explore projects, perception scores, runs, alerts, and trends."
    ),
)


async def _resolve_project(project: str) -> tuple[str, aiosqlite.Row]:
    """Resolve a project ID or fuzzy name to (project_id, row).

    Raises ProjectNotFoundError if no match is found.
    """
    # 1. Exact ID match
    row = await project_repo.get_project(project)
    if row:
        return (project, row)

    # 2. Fuzzy name matching against all projects
    all_projects = await project_service.list_projects()
    names: dict[str, str] = {p.id: p.name for p in all_projects}

    # Case-insensitive exact name match
    lower = project.lower()
    for pid, name in names.items():
        if name.lower() == lower:
            matched_row = await project_repo.get_project(pid)
            if matched_row:
                return (pid, matched_row)

    # Substring match
    for pid, name in names.items():
        if lower in name.lower():
            matched_row = await project_repo.get_project(pid)
            if matched_row:
                return (pid, matched_row)

    # difflib fuzzy match
    best_score = 0.0
    best_pid: str | None = None
    for pid, name in names.items():
        score = difflib.SequenceMatcher(None, lower, name.lower()).ratio()
        if score > best_score:
            best_score = score
            best_pid = pid

    if best_pid and best_score >= _FUZZY_MATCH_THRESHOLD:
        matched_row = await project_repo.get_project(best_pid)
        if matched_row:
            return (best_pid, matched_row)

    raise ProjectNotFoundError(project, list(names.values()))


@mcp.tool()
async def list_projects() -> list[ProjectResponse]:
    """List all monitored projects with their latest perception score, run count, and active alert count.

    Use this first to discover projects, then pass a project ID or name to other tools.
    """
    return await project_service.list_projects()


@mcp.tool()
async def get_project_summary(project: str) -> ProjectSummary:
    """Get a full summary for a project: detail, perception scores, breakdown, recent runs, and alerts.

    Args:
        project: Project ID or name (fuzzy matching supported).
    """
    project_id, row = await _resolve_project(project)

    detail = await project_service.get_project_detail(project_id, row)
    perception = await run_service.get_perception(project_id, None, None)
    term_rows = await term_repo.list_active_term_ids_and_names(project_id)
    term_names = {r["id"]: r["name"] for r in term_rows}
    breakdown = await run_service.get_perception_breakdown(project_id, term_names)
    runs_page = await run_service.list_runs(project_id, 10, 0, None)
    raw_alerts = await alert_service.list_alerts(project_id, limit=20, offset=0)
    alerts = [AlertResponse.model_validate(a.model_dump()) for a in raw_alerts]

    return ProjectSummary(
        project=detail,
        perception=perception,
        breakdown=breakdown,
        recent_runs=runs_page.items,
        alerts=alerts,
    )


@mcp.tool()
async def get_run_detail(run_id: str) -> RunDetailResponse:
    """Get details for a single monitoring run, including perception score and competitors detected.

    Args:
        run_id: The run ID (get this from get_project_summary's recent_runs).
    """
    result = await run_service.get_run_detail(run_id)
    if not result:
        raise RunNotFoundError(run_id)
    return result


@mcp.tool()
async def get_trajectory(
    project: str,
    start_date: str | None = None,
    end_date: str | None = None,
    period: str = "day",
) -> TrajectoryResponse:
    """Get historical trajectory data showing recommendation share, position, and competitor delta over time.

    Args:
        project: Project ID or name (fuzzy matching supported).
        start_date: Optional start date filter (YYYY-MM-DD).
        end_date: Optional end date filter (YYYY-MM-DD).
        period: Aggregation period — 'day', 'week', or 'month' (default 'day').
    """
    project_id, _ = await _resolve_project(project)
    return await run_service.get_trajectory(project_id, start_date, end_date, period)
