"""Small, dependency-free authority boundary for the experimental GCA service.

This module intentionally contains no model, mesh, blockchain, or FastAPI imports so
its default-deny behavior can be tested without booting the experimental runtime.
"""

from __future__ import annotations

import os
import secrets
from typing import Mapping, Optional

_TRUTHY = frozenset({"1", "true", "yes", "on"})

# Paths that can mutate or propagate state outside the local request/response flow.
EXPERIMENTAL_SIDE_EFFECT_PATHS = frozenset(
    {
        "/v1/chain/transaction/proposal",
        "/v1/chain/transaction/vote",
        "/v1/chain/mine",
        "/v1/swarm/task",
        "/v1/memory/sync",
    }
)


def env_flag(name: str, env: Optional[Mapping[str, str]] = None) -> bool:
    """Return True only for an explicit affirmative environment value."""

    source = os.environ if env is None else env
    return source.get(name, "").strip().lower() in _TRUTHY


def configured_api_key(config: Mapping[str, object], env: Optional[Mapping[str, str]] = None) -> Optional[str]:
    """Resolve the GCA API key without inventing an insecure fallback."""

    source = os.environ if env is None else env
    value = source.get("GCA_API_KEY")
    if value:
        return value

    security = config.get("security", {})
    if isinstance(security, Mapping):
        configured = security.get("api_key")
        if isinstance(configured, str) and configured:
            return configured
    return None


def api_key_status(expected: Optional[str], provided: Optional[str]) -> int:
    """Return the HTTP status implied by the API-key boundary.

    200 means the key is valid, 503 means the service has no key configured, and
    403 means a configured key was not supplied correctly.
    """

    if not expected:
        return 503
    if provided and secrets.compare_digest(provided, expected):
        return 200
    return 403


def side_effect_allowed(path: str, runtime_enabled: bool) -> bool:
    """Experimental network/governance mutation is disabled unless opted in."""

    return path not in EXPERIMENTAL_SIDE_EFFECT_PATHS or runtime_enabled
