from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from python.angles import wrap_signed_deg

# Public name preserved as a thin alias; semantics owned by python.angles.
wrap_deg = wrap_signed_deg


def load_json_dict(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def make_args_stub() -> Any:
    class _Args:
        include_visual = None
        include_proprio = None
        action_mode = None
        mission_obs_mode = None
        visual_downsample = None
        visual_update_interval = None
        execution_step_runtime_mode = None

    return _Args()


@dataclass(frozen=True)
class LeaderActionMapping:
    phase_bucket: str
    heading_bias_deg: float
    altitude_bias_m: float
    speed_bias_mps: float
    report_bucket: str
    report_status_value: float
