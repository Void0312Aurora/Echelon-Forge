"""Pure step-timing dict coercion helper shared with gym_envs.

Runtime adapters import ``coerce_timing_dict`` directly; remaining scaling
helpers stay ``python.rl``-internal because ``gym_envs`` never needs them.
"""

from __future__ import annotations

from typing import Any


def coerce_timing_dict(raw: Any) -> dict[str, float]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, float] = {}
    for key, value in raw.items():
        try:
            out[str(key)] = float(value)
        except Exception:
            pass
    return out


__all__ = ["coerce_timing_dict"]
