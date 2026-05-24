from __future__ import annotations

from .batch_apply import (
    apply_world_layouts_to_setup_target,
    load_compiled_scenario_for_setup_target,
)
from .geometry import apply_runtime_world_yaw_inplace, apply_world_yaw_inplace, rotate_xy_clockwise
from .kernel_apply import apply_world_layout_to_kernel, build_compiled_world_layout, prepare_scenario_world_layout
from .models import (
    AppliedScenarioRosterMember,
    AppliedScenarioWorld,
    BatchWorldApplyBuffer,
    PreparedScenarioWorldContext,
    RuntimeWorldLayoutRequestCompat,
    RuntimeWorldLayoutResultCompat,
    ScenarioRosterMemberLayout,
    ScenarioSpawnLayout,
    ScenarioWorldLayout,
    ScenarioZoneLayout,
)
from .roster import active_roster_world_entity_refs, find_active_roster_member, resolve_active_controllable_roster
from .world_setup import (
    apply_runtime_world_layout_request_maintained,
    apply_world_setup_payload_maintained,
    apply_world_setup_request_maintained,
    build_batch_world_setup_request,
    build_runtime_world_layout_request,
    extract_batch_world_setup_entity_ids,
    extract_runtime_world_layout_entity_ids,
    normalize_world_setup_terrain_assignments,
)

__all__ = [
    "AppliedScenarioRosterMember",
    "AppliedScenarioWorld",
    "BatchWorldApplyBuffer",
    "PreparedScenarioWorldContext",
    "RuntimeWorldLayoutRequestCompat",
    "RuntimeWorldLayoutResultCompat",
    "ScenarioRosterMemberLayout",
    "ScenarioSpawnLayout",
    "ScenarioWorldLayout",
    "ScenarioZoneLayout",
    "active_roster_world_entity_refs",
    "apply_runtime_world_yaw_inplace",
    "apply_world_layout_to_kernel",
    "apply_world_layouts_to_setup_target",
    "apply_world_yaw_inplace",
    "build_compiled_world_layout",
    "build_batch_world_setup_request",
    "build_runtime_world_layout_request",
    "extract_runtime_world_layout_entity_ids",
    "extract_batch_world_setup_entity_ids",
    "normalize_world_setup_terrain_assignments",
    "find_active_roster_member",
    "load_compiled_scenario_for_setup_target",
    "prepare_scenario_world_layout",
    "resolve_active_controllable_roster",
    "rotate_xy_clockwise",
    "apply_runtime_world_layout_request_maintained",
    "apply_world_setup_request_maintained",
    "apply_world_setup_payload_maintained",
]
