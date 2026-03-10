"""contextkeeper REST API server — FastAPI, backed by ContextKeeperClient."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from contextkeeper.client import ContextKeeperClient
from contextkeeper.exceptions import (
    ContextKeeperError,
    HandoffNotFoundError,
    ProjectNotInitializedError,
    SessionNotFoundError,
)
from contextkeeper.models import (
    Handoff,
    HandoffDiff,
    ProjectConfig,
    Session,
)


# ── Request/Response schemas ──


class InitRequest(BaseModel):
    name: str
    backend: str = "file"
    coordination: str = "sequential"


class SyncRequest(BaseModel):
    notes: str = ""
    agent: str = "custom"
    agent_version: str = ""
    tasks: list[dict] = Field(default_factory=list)
    decisions: list[dict] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)


class SessionRequest(BaseModel):
    agent: str = "custom"
    agent_version: str = ""


class TaskRequest(BaseModel):
    task_id: str
    title: str
    status: str = "pending"
    owner: str = "human"
    depends_on: list[str] = Field(default_factory=list)
    notes: str = ""


class TaskStatusUpdate(BaseModel):
    status: str


class DecisionRequest(BaseModel):
    decision_id: str
    summary: str
    rationale: str = ""
    made_by: str = "human"
    supersedes: str | None = None


class BootstrapResponse(BaseModel):
    briefing: str


class StatusResponse(BaseModel):
    project_id: str
    name: str
    coordination: str
    backend: str
    session_count: int
    latest_handoff: str
    task_counts: dict[str, int]


class DoctorCheck(BaseModel):
    name: str
    status: str
    message: str


class DoctorResponse(BaseModel):
    healthy: bool
    checks: list[DoctorCheck]


# ── helpers ──


def _get_client(project_dir_header: str | None = None) -> ContextKeeperClient:
    if project_dir_header:
        return ContextKeeperClient(project_dir=Path(project_dir_header))
    return ContextKeeperClient(project_dir=Path("."))


def _handle(exc: ContextKeeperError) -> HTTPException:
    if isinstance(exc, ProjectNotInitializedError):
        return HTTPException(status_code=503, detail=str(exc))
    if isinstance(exc, SessionNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, HandoffNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    return HTTPException(status_code=500, detail=str(exc))


# ── app ──


app = FastAPI(
    title="contextkeeper",
    description="Zero model drift between AI agents.",
    version="0.5.0",  # keep in sync with pyproject.toml
)

cors_origins = os.environ.get("CONTEXTKEEPER_CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── project endpoints ──


@app.post("/projects/init", response_model=ProjectConfig)
def init_project(
    req: InitRequest,
    x_project_dir: str | None = Header(None),
):
    try:
        client = _get_client(x_project_dir)
        return client.init(
            name=req.name,
            backend_type=req.backend,
            coordination=req.coordination,
        )
    except ContextKeeperError as exc:
        raise _handle(exc)


@app.get("/projects/status", response_model=StatusResponse)
def get_status(x_project_dir: str | None = Header(None)):
    try:
        client = _get_client(x_project_dir)
        return StatusResponse(**client.status())
    except ContextKeeperError as exc:
        raise _handle(exc)


@app.get("/projects/doctor", response_model=DoctorResponse)
def get_doctor(x_project_dir: str | None = Header(None)):
    try:
        client = _get_client(x_project_dir)
        result = client.doctor()
        return DoctorResponse(
            healthy=result["healthy"],
            checks=[DoctorCheck(**c) for c in result["checks"]],
        )
    except ContextKeeperError as exc:
        raise _handle(exc)


# ── session endpoints ──


@app.post("/sessions", response_model=Session)
def create_session(
    req: SessionRequest,
    x_project_dir: str | None = Header(None),
):
    try:
        client = _get_client(x_project_dir)
        return client.open_session(agent=req.agent, agent_version=req.agent_version)
    except ContextKeeperError as exc:
        raise _handle(exc)


@app.get("/sessions", response_model=list[Session])
def list_sessions(x_project_dir: str | None = Header(None)):
    try:
        client = _get_client(x_project_dir)
        return client.list_sessions()
    except ContextKeeperError as exc:
        raise _handle(exc)


@app.get("/sessions/{session_id}", response_model=Session)
def get_session(session_id: str, x_project_dir: str | None = Header(None)):
    try:
        client = _get_client(x_project_dir)
        return client.get_session(session_id)
    except ContextKeeperError as exc:
        raise _handle(exc)


@app.delete("/sessions/{session_id}", response_model=Session)
def close_session(session_id: str, x_project_dir: str | None = Header(None)):
    try:
        client = _get_client(x_project_dir)
        return client.close_session(session_id)
    except ContextKeeperError as exc:
        raise _handle(exc)


# ── handoff endpoints ──


@app.post("/handoffs", response_model=Handoff)
def create_handoff(
    req: SyncRequest,
    x_project_dir: str | None = Header(None),
):
    try:
        client = _get_client(x_project_dir)
        return client.sync(
            notes=req.notes,
            agent=req.agent,
            agent_version=req.agent_version,
            tasks=req.tasks or None,
            decisions=req.decisions or None,
            open_questions=req.open_questions or None,
            next_steps=req.next_steps or None,
        )
    except ContextKeeperError as exc:
        raise _handle(exc)


@app.get("/handoffs/latest", response_model=Handoff | None)
def get_latest_handoff(x_project_dir: str | None = Header(None)):
    try:
        client = _get_client(x_project_dir)
        config = client.backend.read_config()
        return client.backend.read_latest_handoff(config.project_id)
    except ContextKeeperError as exc:
        raise _handle(exc)


@app.get("/handoffs/{session_id}", response_model=list[Handoff])
def list_handoffs(session_id: str, x_project_dir: str | None = Header(None)):
    try:
        client = _get_client(x_project_dir)
        return client.list_handoffs(session_id)
    except ContextKeeperError as exc:
        raise _handle(exc)


@app.get("/handoffs/{session_id}/{version}", response_model=Handoff)
def get_handoff(
    session_id: str,
    version: int,
    x_project_dir: str | None = Header(None),
):
    try:
        client = _get_client(x_project_dir)
        return client.get_handoff(session_id, version)
    except ContextKeeperError as exc:
        raise _handle(exc)


# ── bootstrap ──


@app.get("/bootstrap", response_model=BootstrapResponse)
def get_bootstrap(x_project_dir: str | None = Header(None)):
    try:
        client = _get_client(x_project_dir)
        return BootstrapResponse(briefing=client.bootstrap())
    except ContextKeeperError as exc:
        raise _handle(exc)


# ── task endpoints ──


@app.post("/tasks", response_model=Handoff)
def add_task(req: TaskRequest, x_project_dir: str | None = Header(None)):
    try:
        client = _get_client(x_project_dir)
        return client.add_task(
            task_id=req.task_id,
            title=req.title,
            status=req.status,
            owner=req.owner,
            depends_on=req.depends_on,
            notes=req.notes,
        )
    except HandoffNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ContextKeeperError as exc:
        raise _handle(exc)


@app.patch("/tasks/{task_id}/status", response_model=Handoff)
def update_task_status(
    task_id: str,
    req: TaskStatusUpdate,
    x_project_dir: str | None = Header(None),
):
    try:
        client = _get_client(x_project_dir)
        return client.update_task_status(task_id, req.status)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except HandoffNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ContextKeeperError as exc:
        raise _handle(exc)


# ── decision endpoints ──


@app.post("/decisions", response_model=Handoff)
def add_decision(req: DecisionRequest, x_project_dir: str | None = Header(None)):
    try:
        client = _get_client(x_project_dir)
        return client.add_decision(
            decision_id=req.decision_id,
            summary=req.summary,
            rationale=req.rationale,
            made_by=req.made_by,
            supersedes=req.supersedes,
        )
    except HandoffNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ContextKeeperError as exc:
        raise _handle(exc)


# ── diff ──


@app.get("/diff/{from_version}/{to_version}", response_model=HandoffDiff)
def get_diff(
    from_version: int,
    to_version: int,
    x_project_dir: str | None = Header(None),
):
    try:
        client = _get_client(x_project_dir)
        return client.diff(from_version, to_version)
    except HandoffNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ContextKeeperError as exc:
        raise _handle(exc)


def main():
    """Entry point for contextkeeper-server command."""
    import uvicorn
    uvicorn.run("contextkeeper.server:app", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
