"""Pure step-timing dict coercion helper shared with gym_envs.

``python.rl.runtime.execution_runtime`` re-exports ``coerce_timing_dict`` as a
compatibility shell and keeps using it locally for ``scale_timing_dict``/
``copy_info_with_scaled_timing``, which stay ``python.rl``-internal since
``gym_envs`` never needed them directly.
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
