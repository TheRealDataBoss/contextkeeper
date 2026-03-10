"""Primary SDK entry point for contextkeeper."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from contextkeeper.backends.base import ContextKeeperBackend
from contextkeeper.backends.file import FileBackend
from contextkeeper.backends.lock import LockManager
from contextkeeper.backends.sqlite import SQLiteBackend
from contextkeeper.exceptions import (
    BackendError,
    ContextKeeperError,
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


def _detect_backend(project_dir: Path) -> ContextKeeperBackend:
    """Auto-detect backend from config.json, falling back to FileBackend."""
    config_path = project_dir / ".contextkeeper" / "config.json"
    if config_path.exists():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            backend_type = data.get("backend", "file")
            if backend_type == "sqlite":
                return SQLiteBackend(project_dir)
        except (json.JSONDecodeError, OSError):
            pass
    return FileBackend(project_dir)


def _make_backend(backend_type: str, project_dir: Path) -> ContextKeeperBackend:
    """Create a backend by type name."""
    if backend_type == "sqlite":
        return SQLiteBackend(project_dir)
    return FileBackend(project_dir)


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
            self._backend = _detect_backend(self._project_dir)
        self._lock_manager = LockManager(self._backend)

    @property
    def backend(self) -> ContextKeeperBackend:
        return self._backend

    # ── init ──

    def init(
        self,
        name: str,
        coordination: str = "sequential",
        backend_type: str = "file",
    ) -> ProjectConfig:
        """Initialize a new contextkeeper project."""
        project_id = _slugify(name)
        config = ProjectConfig(
            project_id=project_id,
            name=name,
            coordination=coordination,
            backend=backend_type,
        )
        # Switch to the requested backend type
        self._backend = _make_backend(backend_type, self._project_dir)
        self._lock_manager = LockManager(self._backend)
        self._backend.init_project(config)
        logger.info("Initialized project '%s' with %s backend", project_id, backend_type)
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

        # Coordination enforcement
        if config.coordination == "sequential":
            acquired = self._lock_manager.acquire(
                config.project_id, session.id, agent,
            )
            if not acquired:
                lock = self._lock_manager.lock_info(config.project_id)
                holder = lock["session_id"][:8] if lock else "unknown"
                raise ContextKeeperError(
                    f"Cannot sync: project is locked by session {holder}... "
                    "Wait for the lock to expire or use coordination='lock' for advisory mode."
                )
        elif config.coordination in ("lock", "merge"):
            # Advisory: warn via logger but don't block
            if self._lock_manager.is_locked(config.project_id):
                lock = self._lock_manager.lock_info(config.project_id)
                holder = lock["session_id"][:8] if lock else "unknown"
                logger.warning(
                    "Advisory: project is locked by session %s...", holder,
                )
            self._lock_manager.acquire(
                config.project_id, session.id, agent,
            )

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

        # Release lock after write for sequential mode
        if config.coordination == "sequential":
            self._lock_manager.release(config.project_id, session.id)

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
            for st in TaskStatus:
                count = sum(1 for t in handoff.tasks if t.status == st)
                if count:
                    task_counts[st.value] = count
            latest_summary = (
                f"v{handoff.version} by {handoff.agent.value} "
                f"at {handoff.updated_at.isoformat()}"
            )

        return {
            "project_id": config.project_id,
            "name": config.name,
            "coordination": config.coordination,
            "backend": config.backend,
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

        # Check 3: backend type and path
        backend_name = config.backend
        if backend_name == "sqlite":
            db_path = ck_dir / "contextkeeper.db"
            if db_path.exists():
                size_kb = db_path.stat().st_size / 1024
                checks.append({
                    "name": "backend",
                    "status": "ok",
                    "message": f"sqlite ({size_kb:.1f} KB)",
                })
            else:
                checks.append({
                    "name": "backend",
                    "status": "fail",
                    "message": "sqlite configured but contextkeeper.db not found",
                })
        else:
            sessions_dir = ck_dir / "sessions"
            if sessions_dir.is_dir():
                session_count = len(list(sessions_dir.glob("*.json")))
                checks.append({
                    "name": "backend",
                    "status": "ok",
                    "message": f"file ({session_count} session file(s))",
                })
            else:
                checks.append({
                    "name": "backend",
                    "status": "warn",
                    "message": "file (sessions dir missing -- will be created on first sync)",
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

        # Check 5: lock status
        try:
            lock = self._backend.lock_info(config.project_id)
            if lock is not None:
                checks.append({
                    "name": "lock",
                    "status": "info",
                    "message": f"Locked by {lock['agent']} (session {lock['session_id'][:8]}...)",
                })
            else:
                checks.append({
                    "name": "lock",
                    "status": "ok",
                    "message": "Unlocked",
                })
        except Exception:
            checks.append({
                "name": "lock",
                "status": "ok",
                "message": "Unlocked",
            })

        healthy = all(c["status"] != "fail" for c in checks)
        return {"healthy": healthy, "checks": checks}

    # ── switch_backend ──

    def switch_backend(self, target: str) -> dict:
        """Migrate all data from current backend to target backend.

        Returns a summary dict with counts of migrated sessions and handoffs.
        """
        config = self._backend.read_config()

        if config.backend == target:
            raise ContextKeeperError(
                f"Already using '{target}' backend. Nothing to migrate."
            )

        # Create the target backend
        target_backend = _make_backend(target, self._project_dir)

        # Init target with updated config
        target_config = ProjectConfig(
            project_id=config.project_id,
            name=config.name,
            created_at=config.created_at,
            backend=target,
            coordination=config.coordination,
            schema_version=config.schema_version,
        )
        target_backend.init_project(target_config)

        # Migrate sessions
        sessions = self._backend.list_sessions(config.project_id)
        for session in sessions:
            target_backend.write_session(session)

        # Migrate handoffs — iterate all sessions, all versions
        handoff_count = 0
        for session in sessions:
            version = 1
            while True:
                try:
                    handoff = self._backend.read_handoff(session.id, version=version)
                    target_backend.write_handoff(handoff)
                    handoff_count += 1
                    version += 1
                except Exception:
                    break

        # Atomic switch: update config.json only after successful migration
        import os
        config_path = self._project_dir / ".contextkeeper" / "config.json"
        tmp = config_path.with_suffix(".tmp")
        try:
            tmp.write_text(target_config.model_dump_json(indent=2), encoding="utf-8")
            os.replace(str(tmp), str(config_path))
        except OSError:
            tmp.unlink(missing_ok=True)
            raise ContextKeeperError("Migration completed but failed to update config.json")

        # Switch the active backend
        self._backend = target_backend
        self._lock_manager = LockManager(self._backend)

        return {
            "from": config.backend,
            "to": target,
            "sessions": len(sessions),
            "handoffs": handoff_count,
        }


def _slugify(name: str) -> str:
    """Convert a project name to a slug-safe identifier."""
    return (
        name.lower()
        .replace(" ", "-")
        .replace("_", "-")
    )
