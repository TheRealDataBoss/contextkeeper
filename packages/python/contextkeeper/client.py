"""Primary SDK entry point for contextkeeper."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from contextkeeper.backends.base import ContextKeeperBackend
from contextkeeper.backends.file import FileBackend
from contextkeeper.exceptions import (
    BackendError,
    ProjectNotInitializedError,
)
from contextkeeper.models import (
    AgentType,
    Decision,
    Handoff,
    HandoffDiff,
    ProjectConfig,
    Session,
    Task,
    TaskStatus,
)
from contextkeeper.renderer import render_bootstrap

logger = logging.getLogger("contextkeeper.client")


class ContextKeeperClient:
    """High-level client for contextkeeper operations.

    All business logic lives here. The CLI is a thin wrapper.
    """

    def __init__(
        self,
        project_dir: Path | None = None,
        backend: ContextKeeperBackend | None = None,
    ) -> None:
        self._project_dir = Path(project_dir) if project_dir else Path(".")
        if backend is not None:
            self._backend = backend
        else:
            self._backend = FileBackend(self._project_dir)

    @property
    def backend(self) -> ContextKeeperBackend:
        return self._backend

    # ── init ──

    def init(
        self,
        name: str,
        coordination: str = "sequential",
    ) -> ProjectConfig:
        """Initialize a new contextkeeper project."""
        project_id = _slugify(name)
        config = ProjectConfig(
            project_id=project_id,
            name=name,
            coordination=coordination,
        )
        self._backend.init_project(config)
        logger.info("Initialized project '%s'", project_id)
        return config

    # ── sync ──

    def sync(
        self,
        tasks: list[dict] | None = None,
        decisions: list[dict] | None = None,
        open_questions: list[str] | None = None,
        next_steps: list[str] | None = None,
        notes: str = "",
        agent: str = "custom",
        agent_version: str = "",
    ) -> Handoff:
        """Create or continue a session and write a versioned handoff."""
        config = self._backend.read_config()
        agent_enum = AgentType(agent)

        # Resolve session: use the latest open session or create a new one
        sessions = self._backend.list_sessions(config.project_id)
        open_sessions = [s for s in sessions if s.closed_at is None]

        if open_sessions:
            session = open_sessions[-1]
        else:
            session = Session(
                project_id=config.project_id,
                agent=agent_enum,
            )
            self._backend.write_session(session)

        # Determine version
        try:
            latest = self._backend.read_handoff(session.id)
            version = latest.version + 1
        except Exception:
            version = 1

        # Build typed lists
        task_list = [Task.model_validate(t) for t in (tasks or [])]
        dec_list = [Decision.model_validate(d) for d in (decisions or [])]

        handoff = Handoff(
            session_id=session.id,
            project_id=config.project_id,
            version=version,
            agent=agent_enum,
            agent_version=agent_version,
            tasks=task_list,
            decisions=dec_list,
            open_questions=open_questions or [],
            next_steps=next_steps or [],
            raw_notes=notes,
        )

        self._backend.write_handoff(handoff)
        logger.info(
            "Synced handoff v%d for session %s",
            version,
            session.id,
        )
        return handoff

    # ── bootstrap ──

    def bootstrap(self) -> str:
        """Generate a bootstrap briefing from the latest handoff."""
        config = self._backend.read_config()
        handoff = self._backend.read_latest_handoff(config.project_id)
        if handoff is None:
            return (
                f"Project '{config.name}' is initialized but has no handoffs yet.\n"
                "Run 'contextkeeper sync' to create the first handoff."
            )
        return render_bootstrap(handoff, config)

    # ── status ──

    def status(self) -> dict:
        """Return a summary of the current project state."""
        config = self._backend.read_config()
        sessions = self._backend.list_sessions(config.project_id)
        handoff = self._backend.read_latest_handoff(config.project_id)

        task_counts: dict[str, int] = {}
        latest_summary = "No handoffs yet"
        if handoff is not None:
            for status in TaskStatus:
                count = sum(1 for t in handoff.tasks if t.status == status)
                if count:
                    task_counts[status.value] = count
            latest_summary = (
                f"v{handoff.version} by {handoff.agent.value} "
                f"at {handoff.updated_at.isoformat()}"
            )

        return {
            "project_id": config.project_id,
            "name": config.name,
            "coordination": config.coordination,
            "session_count": len(sessions),
            "latest_handoff": latest_summary,
            "task_counts": task_counts,
        }

    # ── diff ──

    def diff(self, from_version: int, to_version: int) -> HandoffDiff:
        """Compute the diff between two handoff versions."""
        config = self._backend.read_config()
        return self._backend.diff(config.project_id, from_version, to_version)

    # ── doctor ──

    def doctor(self) -> dict:
        """Run health checks and return results."""
        checks: list[dict] = []

        # Check 1: .contextkeeper exists
        ck_dir = self._project_dir / ".contextkeeper"
        if ck_dir.is_dir():
            checks.append({"name": ".contextkeeper directory", "status": "ok", "message": "Found"})
        else:
            checks.append({
                "name": ".contextkeeper directory",
                "status": "fail",
                "message": "Not found. Run 'contextkeeper init'.",
            })
            return {"healthy": False, "checks": checks}

        # Check 2: config.json is valid
        try:
            config = self._backend.read_config()
            checks.append({
                "name": "config.json",
                "status": "ok",
                "message": f"Project '{config.name}' ({config.project_id})",
            })
        except Exception as exc:
            checks.append({
                "name": "config.json",
                "status": "fail",
                "message": str(exc),
            })
            return {"healthy": False, "checks": checks}

        # Check 3: sessions directory exists
        sessions_dir = ck_dir / "sessions"
        if sessions_dir.is_dir():
            session_count = len(list(sessions_dir.glob("*.json")))
            checks.append({
                "name": "sessions directory",
                "status": "ok",
                "message": f"{session_count} session(s)",
            })
        else:
            checks.append({
                "name": "sessions directory",
                "status": "warn",
                "message": "Missing — will be created on first sync",
            })

        # Check 4: latest handoff readable
        try:
            handoff = self._backend.read_latest_handoff(config.project_id)
            if handoff is not None:
                checks.append({
                    "name": "latest handoff",
                    "status": "ok",
                    "message": f"v{handoff.version} ({handoff.session_id[:8]}...)",
                })
            else:
                checks.append({
                    "name": "latest handoff",
                    "status": "info",
                    "message": "No handoffs yet",
                })
        except Exception as exc:
            checks.append({
                "name": "latest handoff",
                "status": "fail",
                "message": str(exc),
            })

        healthy = all(c["status"] != "fail" for c in checks)
        return {"healthy": healthy, "checks": checks}


def _slugify(name: str) -> str:
    """Convert a project name to a slug-safe identifier."""
    return (
        name.lower()
        .replace(" ", "-")
        .replace("_", "-")
    )
