from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Any


TRACE_SIGNATURE_SHA256 = "54c0a905d07bf19212da7fa0dee1baa23599d4f80dc84e38f1f9957c41b28e3c"
FIELD_RULES = (
    ("agent_observations.sim_time", 1.0e-8, 1.0e-12, "abs_rel"),
    ("agent_observations.x", 5.0e-4, 1.0e-7, "abs_rel"),
    ("agent_observations.y", 0.0, 0.0, "exact"),
    ("agent_observations.z", 5.0e-4, 1.0e-7, "abs_rel"),
    ("agent_observations.vx", 5.0e-2, 1.0e-4, "abs_rel"),
    ("agent_observations.vy", 0.0, 0.0, "exact"),
    ("agent_observations.vz", 2.0e-3, 1.0e-4, "abs_rel"),
    ("agent_observations.heading", 0.0, 0.0, "exact"),
    ("agent_observations.roll", 0.0, 0.0, "exact"),
    ("agent_observations.speed", 5.0e-2, 1.0e-4, "abs_rel"),
    ("agent_observations.gear_state", 0.0, 0.0, "exact"),
    ("instrument_states.throttle_pos", 0.0, 0.0, "exact"),
)
EXCLUDED_FIELDS = (
    ("agent_observations.pitch", "semantic_divergence"),
    ("agent_observations.health", "outside_minimal_release"),
    ("agent_observations.contact_count", "outside_minimal_release"),
    ("agent_observations.rwr_warning_count", "outside_minimal_release"),
    ("agent_observations.missiles_remaining", "outside_minimal_release"),
    ("agent_observations.can_fire", "outside_minimal_release"),
    ("agent_observations.throttle", "semantic_divergence"),
    ("agent_observations.total_reward", "ownership_divergence"),
    ("instrument_states.alt_baro_m", "outside_minimal_release"),
    ("instrument_states.alt_radar_m", "outside_minimal_release"),
    ("instrument_states.ias_mps", "outside_minimal_release"),
    ("instrument_states.mach", "outside_minimal_release"),
    ("instrument_states.vvi_mps", "outside_minimal_release"),
    ("instrument_states.pitch_deg", "semantic_divergence"),
    ("instrument_states.roll_deg", "outside_minimal_release"),
    ("instrument_states.heading_deg", "outside_minimal_release"),
    ("instrument_states.aoa_deg", "semantic_divergence"),
    ("instrument_states.beta_deg", "outside_minimal_release"),
    ("instrument_states.g_load_normal", "semantic_divergence"),
    ("instrument_states.g_load_axial", "semantic_divergence"),
    ("instrument_states.p_deg_s", "outside_minimal_release"),
    ("instrument_states.q_deg_s", "outside_minimal_release"),
    ("instrument_states.r_deg_s", "outside_minimal_release"),
    ("instrument_states.engine_rpm_pct", "outside_minimal_release"),
    ("instrument_states.engine_temp_c", "ownership_divergence"),
    ("instrument_states.fuel_flow_kg_h", "ownership_divergence"),
    ("instrument_states.fuel_internal_kg", "ownership_divergence"),
    ("instrument_states.fuel_external_kg", "outside_minimal_release"),
    ("instrument_states.gear_pos", "outside_minimal_release"),
    ("instrument_states.flaps_pos", "outside_minimal_release"),
    ("instrument_states.speedbrake_pos", "outside_minimal_release"),
    ("instrument_states.master_arm", "outside_minimal_release"),
    ("instrument_states.oat_c", "outside_minimal_release"),
    ("instrument_states.cmd_heading_deg", "outside_minimal_release"),
    ("instrument_states.cmd_alt_m", "outside_minimal_release"),
    ("instrument_states.cmd_speed_mps", "outside_minimal_release"),
    ("instrument_states.rwr_active", "outside_minimal_release"),
    ("instrument_states.weapon_selected", "outside_minimal_release"),
    ("instrument_states.missiles_remaining", "outside_minimal_release"),
    ("instrument_states.lat_deg", "outside_minimal_release"),
    ("instrument_states.lon_deg", "outside_minimal_release"),
    ("instrument_states.vn_mps", "outside_minimal_release"),
    ("instrument_states.ve_mps", "outside_minimal_release"),
    ("instrument_states.vd_mps", "outside_minimal_release"),
    ("instrument_states.ground_speed_mps", "outside_minimal_release"),
    ("instrument_states.ground_track_deg", "outside_minimal_release"),
    ("instrument_states.wind_speed_mps", "outside_minimal_release"),
    ("instrument_states.wind_dir_deg", "outside_minimal_release"),
    ("instrument_states.gps_available", "outside_minimal_release"),
    ("instrument_states.position_uncertainty_m", "outside_minimal_release"),
    ("instrument_states.gear_stress", "outside_minimal_release"),
    ("instrument_states.gear_collapsed", "outside_minimal_release"),
    ("instrument_states.on_runway", "outside_minimal_release"),
)
IDENTITY_FIELDS = (
    {
        "path": "agent_observations.id",
        "disposition": "lane_local_diagnostic_excluded_from_digest",
    },
)
BARRIERS = (
    {
        "barrier": "input_injection",
        "disposition": "trace_only",
        "reason": "trace_signature_covers_all_pilot_action_fields",
    },
    {
        "barrier": "window_commit",
        "disposition": "metadata_only",
        "reason": "no_common_host_payload_at_commit_boundary",
    },
    {
        "barrier": "export",
        "disposition": "payload_released",
        "reason": "real_common_public_dto_export",
    },
)
POLICY = {
    "schema_version": "cuda_resident.selected_slice_parity.v1",
    "policy_id": "cuda_resident.cr2.selected_payload_release.v1",
    "source_budget_ref": "parity_budget.resident_state.unmaintained_candidate.v1",
    "trace_profile_id": "cr2.full_window.fixed_air.v1",
    "trace_signature_sha256": TRACE_SIGNATURE_SHA256,
    "payload_barrier": "export",
    "payload_capture_path": "host_diagnostic_export",
    "canonical_world_key": "(session_index,window_index,world_slot,field_path)",
    "identity_policy": "allocator_id_lane_local_diagnostic_excluded_from_digest.v1",
    "reset_policy": "same_backend_two_runner_released_value_exact.v1",
    "raw_field_count": 66,
    "partition_complete": True,
    "candidate_promotion_blocked": True,
    "maintained_claim_allowed": False,
    "public_support_enabled": False,
    "measured_consumer_path_unchanged": True,
    "outer_lane_evidence_fields": ["lane", "backend_id"],
    "diagnostic_only_metadata_fields": [
        "snapshot.lineage",
        "snapshot.source_backend_id",
        "export.provenance",
        "reset_generation",
        "source_snapshot_version",
    ],
}


def _run_probe(path: Path, database: str) -> dict[str, Any]:
    completed = subprocess.run(
        [str(path), "--database", database, "--parity-release"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"probe failed ({path}, exit={completed.returncode}): {completed.stderr.strip()}"
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"probe stdout is not pure JSON ({path}): {error}") from error
    if not isinstance(payload, dict):
        raise RuntimeError(f"probe payload is not an object: {path}")
    return payload


def _mapping(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} must be an object")
    return value


def _list(value: object, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise RuntimeError(f"{label} must be a list")
    return value


def _exact_keys(value: dict[str, Any], keys: set[str], label: str) -> None:
    if set(value) != keys:
        raise RuntimeError(f"{label} keys diverged: {sorted(value)}")


def _expected_operations() -> list[dict[str, Any]]:
    result = [
        {
            "window_index": 0,
            "request_id": "cr2.full_window.fixed_air",
            "operation": "setup",
            "succeeded": True,
            "barrier_id": "",
        }
    ]
    sequence = (
        ("input_injection", "input_injection"),
        ("evaluation", ""),
        ("advance", "window_commit"),
        ("export", "export"),
    )
    for window in range(2):
        result.extend(
            {
                "window_index": window,
                "request_id": f"cr2.window.{window}",
                "operation": operation,
                "succeeded": True,
                "barrier_id": barrier,
            }
            for operation, barrier in sequence
        )
    return result


def _validate_contract(release: dict[str, Any]) -> None:
    expected_keys = set(POLICY) | {
        "released_numeric_fields",
        "identity_diagnostic_fields",
        "excluded_fields",
        "declared_barriers",
        "sessions",
    }
    _exact_keys(release, expected_keys, "parity_release")
    for key, value in POLICY.items():
        if release.get(key) != value:
            raise RuntimeError(f"parity release policy field diverged: {key}")
    expected_rules = [
        {
            "path": path,
            "absolute_tolerance": absolute,
            "relative_tolerance": relative,
            "comparator": comparator,
            "finite_required": True,
            "normalize_signed_zero": True,
        }
        for path, absolute, relative, comparator in FIELD_RULES
    ]
    if release["released_numeric_fields"] != expected_rules:
        raise RuntimeError("released numeric field contract diverged")
    if release["identity_diagnostic_fields"] != list(IDENTITY_FIELDS):
        raise RuntimeError("identity diagnostic field contract diverged")
    expected_excluded = [{"path": path, "reason": reason} for path, reason in EXCLUDED_FIELDS]
    if release["excluded_fields"] != expected_excluded:
        raise RuntimeError("excluded field contract diverged")
    if release["declared_barriers"] != list(BARRIERS):
        raise RuntimeError("declared barrier contract diverged")
    dispositions = {path for path, *_ in FIELD_RULES}
    dispositions |= {field["path"] for field in IDENTITY_FIELDS}
    dispositions |= {path for path, _ in EXCLUDED_FIELDS}
    if len(dispositions) != 66:
        raise RuntimeError("field disposition partition is not complete and disjoint")


def _number(value: object, key: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuntimeError(f"released field is not numeric: {key}")
    result = float(value)
    if not math.isfinite(result):
        raise RuntimeError(f"released field is not finite: {key}")
    return 0.0 if result == 0.0 else result


def _validate_session(
    session: dict[str, Any], lane: str, session_index: int, session_label: str
) -> dict[str, Any]:
    _exact_keys(
        session,
        {
            "session_index",
            "session_label",
            "lane",
            "backend_id",
            "trace_signature",
            "completed",
            "failure",
            "operations",
            "frames",
        },
        f"{lane}.{session_label}",
    )
    if session["session_index"] != session_index or session["session_label"] != session_label:
        raise RuntimeError(f"{lane} reset session identity diverged")
    if session["lane"] != lane or not session["backend_id"]:
        raise RuntimeError(f"{lane} lane/backend evidence is invalid")
    if session["completed"] is not True or session["failure"] is not None:
        raise RuntimeError(f"{lane}.{session_label} did not complete cleanly")
    signature = session["trace_signature"]
    if not isinstance(signature, str):
        raise RuntimeError(f"{lane}.{session_label} trace signature is invalid")
    digest = hashlib.sha256(signature.encode("utf-8")).hexdigest()
    if digest != TRACE_SIGNATURE_SHA256:
        raise RuntimeError(f"{lane}.{session_label} frozen trace signature diverged")
    operations = _list(session["operations"], f"{lane}.{session_label}.operations")
    if operations != _expected_operations():
        raise RuntimeError(f"{lane}.{session_label} operation projection diverged")
    frames = _list(session["frames"], f"{lane}.{session_label}.frames")
    if len(frames) != 2:
        raise RuntimeError(f"{lane}.{session_label} must contain two export frames")
    values: dict[tuple[int, int, str], float] = {}
    identities: dict[tuple[int, int], int] = {}
    observation_fields = {
        path.split(".", 1)[1] for path, *_ in FIELD_RULES if path.startswith("agent_")
    }
    instrument_fields = {
        path.split(".", 1)[1] for path, *_ in FIELD_RULES if path.startswith("instrument_")
    }
    for window, frame_value in enumerate(frames):
        frame = _mapping(frame_value, f"{lane}.{session_label}.frame[{window}]")
        _exact_keys(
            frame,
            {"window_index", "request_id", "source_barrier", "capture_barrier", "worlds"},
            f"{lane}.{session_label}.frame[{window}]",
        )
        if (
            frame["window_index"] != window
            or frame["request_id"] != f"cr2.window.{window}"
            or frame["source_barrier"] != "window_commit"
            or frame["capture_barrier"] != "export"
        ):
            raise RuntimeError(f"{lane}.{session_label} frame/barrier evidence diverged")
        worlds = _list(frame["worlds"], f"{lane}.{session_label}.frame[{window}].worlds")
        if len(worlds) != 2:
            raise RuntimeError(f"{lane}.{session_label} frame must contain two worlds")
        for world_slot, world_value in enumerate(worlds):
            world = _mapping(world_value, f"{lane}.{session_label}.world[{world_slot}]")
            _exact_keys(world, {"world_slot", "released", "diagnostic_identity"}, "world")
            if world["world_slot"] != world_slot:
                raise RuntimeError(f"{lane}.{session_label} canonical world_slot diverged")
            released = _mapping(world["released"], "released")
            _exact_keys(released, {"agent_observations", "instrument_states"}, "released")
            observation = _mapping(released["agent_observations"], "agent_observations")
            instrument = _mapping(released["instrument_states"], "instrument_states")
            _exact_keys(observation, observation_fields, "released.agent_observations")
            _exact_keys(instrument, instrument_fields, "released.instrument_states")
            diagnostic = _mapping(world["diagnostic_identity"], "diagnostic_identity")
            _exact_keys(diagnostic, {"agent_observations"}, "diagnostic_identity")
            identity_observation = _mapping(diagnostic["agent_observations"], "identity")
            _exact_keys(identity_observation, {"id"}, "diagnostic_identity.agent_observations")
            entity_id = identity_observation["id"]
            if isinstance(entity_id, bool) or not isinstance(entity_id, int):
                raise RuntimeError(f"{lane}.{session_label} allocator id is invalid")
            identities[(window, world_slot)] = entity_id
            for path, *_ in FIELD_RULES:
                owner, field = path.split(".", 1)
                values[(window, world_slot, path)] = _number(released[owner][field], path)
    for world_slot in range(2):
        if identities[(0, world_slot)] != identities[(1, world_slot)]:
            raise RuntimeError(f"{lane}.{session_label} allocator id changed within one setup")
    return {
        "backend_id": session["backend_id"],
        "trace_signature": signature,
        "operations": operations,
        "values": values,
        "identities": identities,
    }


def _validate_probe(payload: dict[str, Any], lane: str) -> tuple[dict[str, Any], dict[str, Any]]:
    _exact_keys(
        payload,
        {
            "schema_version",
            "surface_id",
            "lane",
            "backend_id",
            "trace_signature",
            "completed",
            "failure",
            "operations",
            "parity_release",
        },
        f"{lane}.outer_probe",
    )
    if payload.get("schema_version") != "cuda_resident.full_window_probe.v1":
        raise RuntimeError(f"{lane} outer probe schema diverged")
    if payload.get("surface_id") != "cuda_resident.full_window_spi.v1":
        raise RuntimeError(f"{lane} outer surface diverged")
    if payload.get("lane") != lane or payload.get("completed") is not True:
        raise RuntimeError(f"{lane} outer probe did not complete cleanly")
    if payload.get("failure") is not None:
        raise RuntimeError(f"{lane} outer probe reported failure")
    release = _mapping(payload.get("parity_release"), f"{lane}.parity_release")
    _validate_contract(release)
    sessions = _list(release["sessions"], f"{lane}.sessions")
    if len(sessions) != 2:
        raise RuntimeError(f"{lane} requires first/reset sessions")
    first = _validate_session(_mapping(sessions[0], "first"), lane, 0, "first")
    reset = _validate_session(_mapping(sessions[1], "reset"), lane, 1, "same_backend_reset")
    if (
        first["backend_id"] != reset["backend_id"]
        or payload.get("backend_id") != first["backend_id"]
    ):
        raise RuntimeError(f"{lane} same-backend reset evidence diverged")
    if payload.get("trace_signature") != first["trace_signature"]:
        raise RuntimeError(f"{lane} outer/session trace signature diverged")
    if payload.get("operations") != first["operations"]:
        raise RuntimeError(f"{lane} outer/session operation projection diverged")
    return first, reset


def _compare_fields(
    left: dict[tuple[int, int, str], float],
    right: dict[tuple[int, int, str], float],
    *,
    label: str,
    exact: bool,
) -> list[dict[str, Any]]:
    if set(left) != set(right):
        raise RuntimeError(f"{label} canonical value keys diverged")
    results: list[dict[str, Any]] = []
    for path, configured_absolute, configured_relative, comparator in FIELD_RULES:
        absolute_tolerance = 0.0 if exact else configured_absolute
        relative_tolerance = 0.0 if exact else configured_relative
        keys = sorted(key for key in left if key[2] == path)
        max_absolute = 0.0
        max_relative = 0.0
        matched = 0
        for key in keys:
            left_value = left[key]
            right_value = right[key]
            absolute = abs(left_value - right_value)
            scale = max(abs(left_value), abs(right_value))
            relative = 0.0 if scale == 0.0 else absolute / scale
            limit = max(absolute_tolerance, relative_tolerance * scale)
            max_absolute = max(max_absolute, absolute)
            max_relative = max(max_relative, relative)
            matched += int(absolute <= limit)
        if matched != len(keys):
            raise RuntimeError(f"{label} field diverged: {path}")
        results.append(
            {
                "path": path,
                "comparator": "physical_exact" if exact else comparator,
                "observed_max_abs": max_absolute,
                "observed_max_rel": max_relative,
                "absolute_tolerance": absolute_tolerance,
                "relative_tolerance": relative_tolerance,
                "comparison_count": len(keys),
                "matched_count": matched,
            }
        )
    return results


def compare(cpu: dict[str, Any], cuda: dict[str, Any]) -> dict[str, Any]:
    cpu_first, cpu_reset = _validate_probe(cpu, "cpu_reference")
    cuda_first, cuda_reset = _validate_probe(cuda, "cuda_resident")
    if cpu_first["backend_id"] == cuda_first["backend_id"]:
        raise RuntimeError("CPU and CUDA backend identifiers unexpectedly match")
    if cpu_first["trace_signature"] != cuda_first["trace_signature"]:
        raise RuntimeError("CPU/CUDA frozen trace signatures diverged")
    cross_lane = _compare_fields(
        cpu_first["values"], cuda_first["values"], label="cross_lane", exact=False
    )
    cpu_reset_fields = _compare_fields(
        cpu_first["values"], cpu_reset["values"], label="cpu_reset", exact=True
    )
    cuda_reset_fields = _compare_fields(
        cuda_first["values"], cuda_reset["values"], label="cuda_reset", exact=True
    )
    return {
        "schema_version": "cuda_resident.selected_slice_parity.comparison.v1",
        "status": "pass",
        "trace_profile_id": POLICY["trace_profile_id"],
        "trace_signature_sha256": TRACE_SIGNATURE_SHA256,
        "canonical_world_key": POLICY["canonical_world_key"],
        "coverage": {
            "raw_field_count": 66,
            "released_numeric_field_count": len(FIELD_RULES),
            "identity_diagnostic_field_count": len(IDENTITY_FIELDS),
            "excluded_field_count": len(EXCLUDED_FIELDS),
            "partition_complete": True,
        },
        "cross_lane_fields": cross_lane,
        "same_backend_reset_fields": {
            "cpu_reference": cpu_reset_fields,
            "cuda_resident": cuda_reset_fields,
        },
        "identity_diagnostics": {
            "policy": POLICY["identity_policy"],
            "cpu_reset_changed_count": sum(
                cpu_first["identities"][key] != cpu_reset["identities"][key]
                for key in cpu_first["identities"]
            ),
            "cuda_reset_changed_count": sum(
                cuda_first["identities"][key] != cuda_reset["identities"][key]
                for key in cuda_first["identities"]
            ),
            "raw_allocator_ids_required_to_match": False,
        },
        "candidate_promotion_blocked": True,
        "maintained_claim_allowed": False,
        "public_support_enabled": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cpu", type=Path, required=True, help="CPU probe executable")
    parser.add_argument("--cuda", type=Path, required=True, help="CUDA probe executable")
    parser.add_argument("--database", default="examples/config/database")
    args = parser.parse_args()
    summary = compare(_run_probe(args.cpu, args.database), _run_probe(args.cuda, args.database))
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
