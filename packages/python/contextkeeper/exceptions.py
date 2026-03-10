"""Typed exceptions for contextkeeper."""


class ContextKeeperError(Exception):
    """Base exception for all contextkeeper errors."""


class ProjectNotInitializedError(ContextKeeperError):
    """Raised when operating on a project that hasn't been initialized."""

    def __init__(self, path: str = ".") -> None:
        super().__init__(
            f"No contextkeeper project found at '{path}'. "
            "Run 'contextkeeper init' first."
        )
        self.path = path


class SessionNotFoundError(ContextKeeperError):
    """Raised when a session ID doesn't exist in the backend."""

    def __init__(self, session_id: str) -> None:
        super().__init__(f"Session not found: {session_id}")
        self.session_id = session_id


class HandoffNotFoundError(ContextKeeperError):
    """Raised when a handoff doesn't exist in the backend."""

    def __init__(self, session_id: str, version: int | None = None) -> None:
        detail = f"session={session_id}"
        if version is not None:
            detail += f", version={version}"
        super().__init__(f"Handoff not found: {detail}")
        self.session_id = session_id
        self.version = version


class BackendError(ContextKeeperError):
    """Raised when a backend operation fails (I/O, corruption, etc.)."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.__cause__ = cause


class SchemaVersionError(ContextKeeperError):
    """Raised when schema version is incompatible."""

    def __init__(self, expected: str, got: str) -> None:
        super().__init__(
            f"Schema version mismatch: expected {expected}, got {got}"
        )
        self.expected = expected
        self.got = got
