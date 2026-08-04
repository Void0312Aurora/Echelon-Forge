from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any


SCHEMA = "cuda_resident.cr2.production_matrix_probe.v1"
PROFILE = "cr2.production_matrix.fixed_air.v1"
SURFACE = "cuda_resident.cr2.matrix_backend_spi.v1"
FULL_WINDOW_SURFACE = "cuda_resident.full_window_spi.v1"
SELECTED_PAYLOAD_SCHEMA_REF = "cuda_resident.selected_slice_parity.v1"
SELECTED_PAYLOAD_POLICY_REF = "cuda_resident.cr2.selected_payload_release.v1"
SELECTED_PAYLOAD_POLICY_TRACE_PROFILE_REF = "cr2.full_window.fixed_air.v1"
SELECTED_PAYLOAD_REFERENCE_SCOPE = "field_projection_for_same_lane_reset_only"
WORLD_COUNTS = [1, 4, 16, 64, 256]
MODES = {
    "no_export_no_device": (False, False, True),
    "host_export_no_device": (True, False, True),
    "no_export_device_consumer": (False, True, False),
    "host_export_device_consumer": (True, True, False),
}
PRODUCTION_PROTOCOL = {
    "cold_samples": 10,
    "warmup_windows": 32,
    "measured_windows": 100,
    "rollout_samples": 10,
    "rollout_windows": 64,
    "percentile_method": "nearest_rank",
    "latency_clock": "steady_clock",
    "cold_semantics": "same_backend_reset_setup_then_first_window",
    "fresh_process_cold_available": False,
}
TOP_LEVEL_KEYS = {
    "schema_version",
    "profile_id",
    "lane",
    "backend_id",
    "build_config",
    "production_protocol",
    "invocation_surface",
    "full_window_surface_ref",
    "operation_sequence",
    "selected_payload_schema_ref",
    "selected_payload_policy_ref",
    "selected_payload_policy_trace_profile_ref",
    "selected_payload_reference_scope",
    "selected_payload_matrix_profile_released",
    "trace_signature_algorithm",
    "master_trace_world_count",
    "master_trace_signature",
    "world_counts",
    "modes",
    "protocol",
    "lane_configuration",
    "cuda_environment",
    "rows",
    "gates",
}
ROW_KEYS = {
    "world_count",
    "mode_id",
    "host_export",
    "device_consumer",
    "trace_signature",
    "available",
    "unavailable_reason",
    "effective_worker_threads",
    "latency",
    "reset_determinism",
    "consumer_diagnostics",
    "device_memory",
    "promotion_eligible",
}
LATENCY_KEYS = {
    "setup",
    "cold_reset_setup_plus_first_window",
    "cold_first_window",
    "warmed_end_to_end",
    "warmed_input_evaluate_advance",
    "warmed_collection",
    "rollout_total",
    "rollout_windows",
}
STATS_KEYS = {"sample_count", "p50_ms", "p95_ms", "min_ms", "max_ms", "mean_ms", "raw_ms"}
HEX64 = re.compile(r"^[0-9a-f]{16}$")


class MatrixProbeError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise MatrixProbeError(message)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        _require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_report(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    _require(isinstance(value, dict), "matrix probe root must be an object")
    return value


def _protocol(report: dict[str, Any], require_production: bool) -> dict[str, Any]:
    protocol = report["protocol"]
    _require(
        isinstance(protocol, dict) and set(protocol) == set(PRODUCTION_PROTOCOL),
        "matrix protocol schema drifted",
    )
    for field in (
        "cold_samples",
        "warmup_windows",
        "measured_windows",
        "rollout_samples",
        "rollout_windows",
    ):
        _require(
            isinstance(protocol[field], int)
            and not isinstance(protocol[field], bool)
            and protocol[field] > 0,
            f"matrix protocol {field} is invalid",
        )
    for field in ("percentile_method", "latency_clock", "cold_semantics"):
        _require(
            type(protocol[field]) is str and protocol[field] == PRODUCTION_PROTOCOL[field],
            f"matrix protocol semantic drift: {field}",
        )
    _require(
        protocol["fresh_process_cold_available"] is False,
        "matrix protocol semantic drift: fresh_process_cold_available",
    )
    if require_production:
        _require(protocol == PRODUCTION_PROTOCOL, "matrix does not use the production protocol")
    return protocol


def _validate_stats(stats: object, expected_count: int, label: str) -> None:
    _require(isinstance(stats, dict) and set(stats) == STATS_KEYS, f"{label} stats schema drifted")
    raw = stats["raw_ms"]
    _require(
        type(stats["sample_count"]) is int
        and stats["sample_count"] == expected_count
        and isinstance(raw, list)
        and len(raw) == expected_count,
        f"{label} sample count drifted",
    )
    _require(
        all(
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
            and value >= 0
            for value in raw
        ),
        f"{label} contains invalid raw samples",
    )
    sorted_values = sorted(float(value) for value in raw)

    def nearest_rank(percentile: float) -> float:
        index = max(1, math.ceil(percentile * len(sorted_values))) - 1
        return sorted_values[index]

    expected = {
        "p50_ms": nearest_rank(0.50),
        "p95_ms": nearest_rank(0.95),
        "min_ms": sorted_values[0],
        "max_ms": sorted_values[-1],
        "mean_ms": sum(sorted_values) / len(sorted_values),
    }
    for field, value in expected.items():
        _require(
            isinstance(stats[field], (int, float))
            and not isinstance(stats[field], bool)
            and math.isclose(float(stats[field]), value, rel_tol=1e-12, abs_tol=1e-12),
            f"{label}.{field} does not match raw samples",
        )


def _validate_available_row(
    row: dict[str, Any], lane: str, protocol: dict[str, Any], device_consumer: bool
) -> None:
    _require(row["unavailable_reason"] == "", "available matrix row has an unavailable reason")
    effective_workers = row["effective_worker_threads"]
    _require(
        type(effective_workers) is int
        and effective_workers >= 1
        and (
            effective_workers <= row["world_count"]
            if lane == "flecs_cpu_reference"
            else effective_workers == 1
        ),
        "effective worker count is invalid",
    )
    latency = row["latency"]
    _require(isinstance(latency, dict) and set(latency) == LATENCY_KEYS, "latency schema drifted")
    counts = {
        "setup": protocol["cold_samples"],
        "cold_reset_setup_plus_first_window": protocol["cold_samples"],
        "cold_first_window": protocol["cold_samples"],
        "warmed_end_to_end": protocol["measured_windows"],
        "warmed_input_evaluate_advance": protocol["measured_windows"],
        "warmed_collection": protocol["measured_windows"],
        "rollout_total": protocol["rollout_samples"],
    }
    for family, count in counts.items():
        _validate_stats(latency[family], count, family)
    _require(
        type(latency["rollout_windows"]) is int
        and latency["rollout_windows"] == protocol["rollout_windows"],
        "rollout size drifted",
    )
    for total, compute, collection in zip(
        latency["warmed_end_to_end"]["raw_ms"],
        latency["warmed_input_evaluate_advance"]["raw_ms"],
        latency["warmed_collection"]["raw_ms"],
        strict=True,
    ):
        _require(
            math.isclose(total, compute + collection, rel_tol=1e-9, abs_tol=1e-9),
            "warmed timing decomposition drifted",
        )
    for total, setup, first_window in zip(
        latency["cold_reset_setup_plus_first_window"]["raw_ms"],
        latency["setup"]["raw_ms"],
        latency["cold_first_window"]["raw_ms"],
        strict=True,
    ):
        _require(total + 1e-9 >= setup + first_window, "cold timing boundary drifted")
    determinism = row["reset_determinism"]
    _require(
        isinstance(determinism, dict)
        and set(determinism)
        == {
            "checked",
            "matched",
            "digest",
            "scope",
            "identity_excluded",
            "correctness_export_outside_timer",
        },
        "reset determinism schema drifted",
    )
    _require(determinism["checked"] is True and determinism["matched"] is True, "reset drifted")
    _require(
        type(determinism["digest"]) is str and HEX64.fullmatch(determinism["digest"]) is not None,
        "reset digest is invalid",
    )
    _require(
        determinism["scope"] == "released_selected_payload_identity_excluded"
        and determinism["identity_excluded"] is True
        and determinism["correctness_export_outside_timer"] is True,
        "reset identity or timing boundary drifted",
    )
    diagnostics = row["consumer_diagnostics"]
    _require(
        isinstance(diagnostics, dict)
        and set(diagnostics)
        == {
            "receipt_count",
            "materialized_count",
            "validation_outside_timer",
            "release_outside_timer",
            "max_deferred_rollout_receipts",
        },
        "consumer diagnostic schema drifted",
    )
    expected_receipts = 0
    if device_consumer:
        expected_receipts = (
            protocol["cold_samples"]
            + protocol["warmup_windows"]
            + protocol["measured_windows"]
            + protocol["rollout_samples"] * protocol["rollout_windows"]
        )
    _require(
        type(diagnostics["receipt_count"]) is int
        and diagnostics["receipt_count"] == expected_receipts,
        "consumer receipt count drifted",
    )
    _require(
        type(diagnostics["materialized_count"]) is int
        and diagnostics["materialized_count"] == (1 if device_consumer else 0),
        "consumer materialization count drifted",
    )
    _require(
        diagnostics["validation_outside_timer"] is True
        and diagnostics["release_outside_timer"] is True,
        "consumer diagnostic entered measured timing",
    )
    _require(
        type(diagnostics["max_deferred_rollout_receipts"]) is int
        and diagnostics["max_deferred_rollout_receipts"]
        == (protocol["rollout_windows"] if device_consumer else 0),
        "consumer rollout ownership drifted",
    )
    memory = row["device_memory"]
    _require(
        isinstance(memory, dict)
        and set(memory) == {"availability", "resident_bytes", "state_slot_bytes"},
        "device memory schema drifted",
    )
    if lane == "cuda_resident":
        _require(memory["availability"] == "candidate_owned_requested_bytes", "CUDA memory missing")
        _require(
            type(memory["resident_bytes"]) is int
            and memory["resident_bytes"] > 0
            and type(memory["state_slot_bytes"]) is int
            and memory["state_slot_bytes"] > 0,
            "CUDA memory values are invalid",
        )
    else:
        _require(
            memory
            == {
                "availability": "not_applicable",
                "resident_bytes": None,
                "state_slot_bytes": None,
            },
            "CPU row claims device memory",
        )


def _validate_rows(
    report: dict[str, Any], lane: str, world_counts: list[int], protocol: dict[str, Any]
) -> None:
    rows = report["rows"]
    _require(isinstance(rows, list), "matrix rows must be an array")
    indexed: dict[tuple[int, str], dict[str, Any]] = {}
    for row in rows:
        _require(isinstance(row, dict) and set(row) == ROW_KEYS, "matrix row schema drifted")
        world_count = row["world_count"]
        mode_id = row["mode_id"]
        _require(
            type(world_count) is int and world_count in world_counts,
            "matrix row world count is invalid",
        )
        _require(type(mode_id) is str and mode_id in MODES, "matrix row mode is invalid")
        key = (world_count, mode_id)
        _require(key not in indexed, f"duplicate matrix row: {key}")
        indexed[key] = row
    expected = {(world, mode) for world in world_counts for mode in MODES}
    _require(set(indexed) == expected, "matrix row inventory is incomplete")
    for world in world_counts:
        trace_signatures: set[str] = set()
        reset_digests: set[str] = set()
        effective_worker_counts: set[int] = set()
        cuda_memory_records: set[tuple[int, int]] = set()
        for mode, (host_export, device_consumer, cpu_available) in MODES.items():
            row = indexed[(world, mode)]
            _require(row["host_export"] is host_export, f"host export flag drifted: {mode}")
            _require(row["device_consumer"] is device_consumer, f"consumer flag drifted: {mode}")
            _require(row["promotion_eligible"] is False, "matrix row permits promotion")
            _require(
                type(row["trace_signature"]) is str
                and HEX64.fullmatch(row["trace_signature"]) is not None,
                "trace digest invalid",
            )
            trace_signatures.add(row["trace_signature"])
            available = lane == "cuda_resident" or cpu_available
            _require(row["available"] is available, f"matrix availability drifted: {mode}")
            if available:
                _validate_available_row(row, lane, protocol, device_consumer)
                reset_digests.add(row["reset_determinism"]["digest"])
                effective_worker_counts.add(row["effective_worker_threads"])
                if lane == "cuda_resident":
                    cuda_memory_records.add(
                        (
                            row["device_memory"]["resident_bytes"],
                            row["device_memory"]["state_slot_bytes"],
                        )
                    )
            else:
                _require(
                    row["unavailable_reason"] == "cpu_reference_has_no_device_observation_consumer",
                    "CPU consumer N/A reason drifted",
                )
                for field in (
                    "effective_worker_threads",
                    "latency",
                    "reset_determinism",
                    "consumer_diagnostics",
                    "device_memory",
                ):
                    _require(row[field] is None, f"unavailable row must keep {field} null")
        _require(len(trace_signatures) == 1, f"trace differs across modes for world {world}")
        _require(
            len(reset_digests) == 1,
            f"reset digest differs across available modes for world {world}",
        )
        _require(
            len(effective_worker_counts) == 1,
            f"effective worker count differs across available modes for world {world}",
        )
        if world == report["master_trace_world_count"]:
            _require(
                trace_signatures == {report["master_trace_signature"]},
                "master trace differs from its matrix row",
            )
        if lane == "cuda_resident":
            _require(
                len(cuda_memory_records) == 1,
                f"CUDA memory differs across modes for world {world}",
            )


def validate_report(report: dict[str, Any], *, require_production: bool) -> None:
    _require(set(report) == TOP_LEVEL_KEYS, "matrix probe top-level schema drifted")
    _require(report["schema_version"] == SCHEMA, "matrix probe schema mismatch")
    _require(report["profile_id"] == PROFILE, "matrix probe profile mismatch")
    lane = report["lane"]
    _require(lane in {"flecs_cpu_reference", "cuda_resident"}, "matrix lane is invalid")
    _require(
        report["backend_id"]
        == (
            "flecs_cpu_reference" if lane == "flecs_cpu_reference" else "cuda_resident.rb7_phase_d"
        ),
        "matrix backend id drifted",
    )
    _require(report["build_config"] == "Release", "matrix probe must be a Release build")
    _require(
        report["production_protocol"] is require_production, "production protocol flag drifted"
    )
    _require(report["invocation_surface"] == SURFACE, "matrix invocation surface drifted")
    _require(
        report["full_window_surface_ref"] == FULL_WINDOW_SURFACE,
        "full-window surface reference drifted",
    )
    _require(
        report["operation_sequence"]
        == [
            "inject",
            "evaluate_empty",
            "advance_world_batch",
            "optional_public_export",
            "optional_device_consumer",
        ],
        "matrix operation sequence drifted",
    )
    _require(
        report["selected_payload_schema_ref"] == SELECTED_PAYLOAD_SCHEMA_REF,
        "parity schema reference drifted",
    )
    _require(
        report["selected_payload_policy_ref"] == SELECTED_PAYLOAD_POLICY_REF,
        "parity policy reference drifted",
    )
    _require(
        report["selected_payload_policy_trace_profile_ref"]
        == SELECTED_PAYLOAD_POLICY_TRACE_PROFILE_REF,
        "parity policy trace reference drifted",
    )
    _require(
        report["selected_payload_reference_scope"] == SELECTED_PAYLOAD_REFERENCE_SCOPE
        and report["selected_payload_matrix_profile_released"] is False,
        "matrix profile overclaims the parity release",
    )
    _require(report["trace_signature_algorithm"] == "fnv1a64", "trace algorithm drifted")
    _require(
        type(report["master_trace_world_count"]) is int
        and report["master_trace_world_count"] == 256,
        "master trace world count drifted",
    )
    _require(
        type(report["master_trace_signature"]) is str
        and HEX64.fullmatch(report["master_trace_signature"]) is not None,
        "master trace invalid",
    )
    world_counts = report["world_counts"]
    _require(
        isinstance(world_counts, list)
        and bool(world_counts)
        and world_counts == sorted(set(world_counts))
        and all(type(value) is int and value in WORLD_COUNTS for value in world_counts),
        "matrix world count selection is invalid",
    )
    if require_production:
        _require(world_counts == WORLD_COUNTS, "production world matrix is incomplete")
    mode_rows = report["modes"]
    _require(isinstance(mode_rows, list) and len(mode_rows) == len(MODES), "mode catalog drifted")
    parsed_modes: dict[str, tuple[bool, bool, bool]] = {}
    for row in mode_rows:
        _require(
            isinstance(row, dict)
            and set(row) == {"mode_id", "host_export", "device_consumer", "cpu_available"},
            "mode catalog schema drifted",
        )
        mode_id = row["mode_id"]
        _require(type(mode_id) is str and mode_id not in parsed_modes, "mode id is invalid")
        _require(
            type(row["host_export"]) is bool
            and type(row["device_consumer"]) is bool
            and type(row["cpu_available"]) is bool,
            "mode catalog boolean type drifted",
        )
        parsed_modes[mode_id] = (
            row["host_export"],
            row["device_consumer"],
            row["cpu_available"],
        )
    _require(parsed_modes == MODES, "mode catalog fields drifted")
    protocol = _protocol(report, require_production)
    lane_configuration = report["lane_configuration"]
    expected_lane_configuration = (
        {
            "host_worker_request": 0,
            "host_worker_policy": "hardware_concurrency_capped_by_world_count",
            "device_parallelism": "not_applicable",
        }
        if lane == "flecs_cpu_reference"
        else {
            "host_worker_request": 1,
            "host_worker_policy": "single_host_orchestrator",
            "device_parallelism": "world_grid_128_threads_per_block",
        }
    )
    _require(
        isinstance(lane_configuration, dict)
        and set(lane_configuration) == set(expected_lane_configuration)
        and type(lane_configuration["host_worker_request"]) is int
        and lane_configuration["host_worker_request"]
        == expected_lane_configuration["host_worker_request"]
        and type(lane_configuration["host_worker_policy"]) is str
        and lane_configuration["host_worker_policy"]
        == expected_lane_configuration["host_worker_policy"]
        and type(lane_configuration["device_parallelism"]) is str
        and lane_configuration["device_parallelism"]
        == expected_lane_configuration["device_parallelism"],
        "lane worker policy drifted",
    )
    environment = report["cuda_environment"]
    if lane == "flecs_cpu_reference":
        _require(environment is None, "CPU report contains a CUDA environment")
    else:
        _require(
            isinstance(environment, dict)
            and set(environment)
            == {
                "device_ordinal",
                "device_name",
                "compute_capability",
                "total_global_memory_bytes",
                "driver_version",
                "runtime_version",
            }
            and type(environment["device_ordinal"]) is int
            and environment["device_ordinal"] >= 0
            and type(environment["device_name"]) is str
            and bool(environment["device_name"])
            and type(environment["compute_capability"]) is str
            and environment["compute_capability"] == "8.6"
            and type(environment["total_global_memory_bytes"]) is int
            and environment["total_global_memory_bytes"] > 0
            and type(environment["driver_version"]) is int
            and environment["driver_version"] > 0
            and type(environment["runtime_version"]) is int
            and environment["runtime_version"] > 0,
            "CUDA environment is invalid",
        )
    gates = report["gates"]
    expected_gates = {
        "cr2_4b_selected_payload_parity_required": True,
        "cr2_5_achieved_counter_gate_complete": False,
        "matrix_evidence_complete": False,
        "maintained_claim_allowed": False,
        "public_support_enabled": False,
        "promotion_allowed": False,
        "tuning_authorized": False,
    }
    _require(
        isinstance(gates, dict)
        and set(gates) == set(expected_gates)
        and all(gates[key] is expected for key, expected in expected_gates.items()),
        "matrix probe gates drifted",
    )
    _validate_rows(report, lane, world_counts, protocol)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a CR2-6 matrix probe report")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--production", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    validate_report(load_report(args.input), require_production=args.production)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
