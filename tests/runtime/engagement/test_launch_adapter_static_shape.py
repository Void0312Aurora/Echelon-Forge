from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
ADAPTER_HEADER = REPO_ROOT / "src" / "core" / "engine" / "weapon_launch_adapter.h"
SIMULATION_KERNEL_HEADER = REPO_ROOT / "src" / "core" / "engine" / "simulation_kernel.h"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _struct_body(header: str, struct_name: str) -> str:
    pattern = rf"\bstruct\s+{re.escape(struct_name)}\b[^{{;]*\{{(?P<body>.*?)\n\}};"
    match = re.search(pattern, header, flags=re.DOTALL)
    assert match is not None, f"{struct_name} is missing from {ADAPTER_HEADER}"
    return match.group("body")


def _assert_fields_present(body: str, fields: tuple[str, ...]) -> None:
    missing = [
        field
        for field in fields
        if re.search(rf"\b{re.escape(field)}\b", body) is None
    ]
    assert not missing, f"missing fields: {', '.join(missing)}"


def test_weapon_launch_adapter_is_header_only_contract_converter() -> None:
    header = _text(ADAPTER_HEADER)

    assert '#include "runtime/contracts/engagement_contracts.h"' in header
    assert "namespace engagement_adapter" in header
    assert "inline LaunchRequest make_launch_request" in header
    assert "inline LaunchEvent make_launch_event" in header


def test_weapon_launch_adapter_does_not_depend_on_engine_owners_or_live_fire_calls() -> None:
    header = _text(ADAPTER_HEADER)
    include_lines = re.findall(r"^\s*#\s*include\s+[<\"]([^>\"]+)[>\"]", header, flags=re.MULTILINE)

    assert "core/engine" not in "\n".join(include_lines)
    assert "simulation_kernel" not in header
    assert "SimulationKernel" not in header
    assert "WorldBatchRuntime" not in header
    assert "flecs" not in header
    assert "fire_missile" not in header
    assert "fire_naval_weapon" not in header


def test_weapon_launch_adapter_snapshots_cover_launch_contract_fields() -> None:
    header = _text(ADAPTER_HEADER)

    request_snapshot = _struct_body(header, "LaunchRequestSnapshot")
    outcome_snapshot = _struct_body(header, "LegacyLaunchOutcomeSnapshot")

    _assert_fields_present(
        request_snapshot,
        (
            "world_index",
            "request_id",
            "shooter_entity_id",
            "target_entity_id",
            "has_target_entity",
            "target_track_id",
            "has_target_track",
            "station_id",
            "mount_id",
            "requested_munition_family",
            "authority",
            "requested_time_s",
            "merge_policy",
        ),
    )
    _assert_fields_present(
        outcome_snapshot,
        (
            "world_index",
            "event_id",
            "request_id",
            "accepted",
            "rejection_reason",
            "selected_launcher",
            "selected_munition",
            "ammo_delta",
            "cooldown_delta_s",
            "spawned_munition_entity_id",
            "event_time_s",
        ),
    )


def test_legacy_weapon_api_return_shapes_remain_unchanged_for_adapter_migration() -> None:
    header = _text(SIMULATION_KERNEL_HEADER)

    assert "flecs::entity fire_missile(uint64_t attacker_id, uint64_t target_id);" in header
    assert "bool fire_naval_weapon(uint64_t attacker_id, uint64_t target_id, int weapon_type_code);" in header
