"""contextkeeper — Zero model drift between AI agents."""

from contextkeeper.client import ContextKeeperClient
from contextkeeper.exceptions import (
    BackendError,
    ContextKeeperError,
    HandoffNotFoundError,
    ProjectNotInitializedError,
    SchemaVersionError,
    SessionNotFoundError,
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

__version__ = "0.5.0"

__all__ = [
    # Client
    "ContextKeeperClient",
    # Models
    "AgentType",
    "Decision",
    "Handoff",
    "HandoffDiff",
    "ProjectConfig",
    "Session",
    "Task",
    "TaskStatus",
    # Exceptions
    "BackendError",
    "ContextKeeperError",
    "HandoffNotFoundError",
    "ProjectNotInitializedError",
    "SchemaVersionError",
    "SessionNotFoundError",
]
