from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from fastapi import Request


class LearnerIdentityProvider(Protocol):
    """Resolve a learner identity from trusted server-side authentication."""

    def __call__(self, request: Request) -> str | None: ...


class PreparationContextProvider(Protocol):
    """Load a learner-scoped preparation context from trusted application state.

    Implementations must use authenticated server-side data. They must not treat
    query parameters, request bodies, or arbitrary headers as proof of identity.
    """

    def load_context(
        self,
        learner_id: str,
        *,
        request: Request,
    ) -> Mapping[str, Any]: ...


class PreparationContextUnavailable(RuntimeError):
    """Raised when the learner has no ready-to-use preparation context."""


__all__ = [
    "LearnerIdentityProvider",
    "PreparationContextProvider",
    "PreparationContextUnavailable",
]
