"""Canonical defensive scalar coercion helpers.

Single owner for the ``coerce_nonnegative_int`` helper that was previously
re-implemented in the scenario loader, the scenario compiler, and the RL
profile/tasking layers. Must stay dependency-free so both ``gym_envs`` and
``python.scenario`` can import it without cycles.
"""

from __future__ import annotations

from typing import Any


def coerce_nonnegative_int(value: Any, default: int = 0) -> int:
    """Coerce ``value`` to a non-negative int, falling back to ``default``.

    ``default`` is returned both when ``int(value)`` raises and when the
    coerced value is negative, matching all migrated call sites (the
    no-default variants used ``default=0`` semantics).
    """
    try:
        out = int(value)
    except Exception:
        return int(default)
    return out if out >= 0 else int(default)


__all__ = ["coerce_nonnegative_int"]
