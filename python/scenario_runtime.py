from __future__ import annotations

"""Compatibility shim for the packaged scenario runtime."""

from python.scenario.runtime import *  # noqa: F401,F403
from python.scenario.runtime.batch_apply import (  # noqa: F401
    _apply_world_setup_request,
    _load_compiled_scenario_batch_direct,
    _prepare_compiled_batch_world_context,
)
from python.scenario.runtime.geometry import _primary_runway_heading_deg  # noqa: F401
from python.scenario.runtime.roster import (  # noqa: F401
    _attach_active_roster_to_applied_world,
    _normalized_cooperative_roster_members,
)
