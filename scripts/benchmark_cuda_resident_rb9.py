"""Merge the separately built RB9 CPU/CUDA diagnostic evidence reports.

The candidate is not admitted through RuntimeFacade, so this script computes
only a provisional internal comparison. It never turns incomplete telemetry or
a private CUDA phase sequence into a maintained-backend promotion claim.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import re
from pathlib import Path
from typing import Any


SCHEMA = "cuda_resident.performance_evidence.v1"
SUMMARY_SCHEMA = "cuda_resident.performance_comparison.v1"
PROFILE = "resident_state.unmaintained_candidate"
WORLD_COUNTS = [1, 4, 16, 64, 256]
MODES = [
    "no_export_no_device",
    "host_export_no_device",
    "no_export_device_consumer",
    "host_export_device_consumer",
]
PARITY_BUDGET_REF = "parity_budget.resident_state.unmaintained_candidate.v1"
EXPECTED_INVOCATION_SURFACES = {
    "flecs_cpu_reference": "backend_spi_world_batch",
    "cuda_resident": "backend_private_phase_sequence",
}
EXPECTED_PROTOCOL = {
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
DETERMINISM_SCOPE = "identity_inclusive_reset_diagnostic"
RAW_TRACE_ALGORITHM = "rb8_canonical_trace_v1"
COMPACT_TRACE_ALGORITHM = "sha256_over_rb8_canonical_trace_v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"RB9 report must be a JSON object: {path}")
    return value


def _json_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"RB9 {label} is not a lowercase SHA-256 identity")
    return value


def compact_report(report: dict[str, Any]) -> dict[str, Any]:
    """Replace repeated canonical trace payloads with content-addressed identities."""

    compact = deepcopy(report)
    algorithm = compact.get("trace_signature_algorithm")
    if algorithm == COMPACT_TRACE_ALGORITHM:
        return compact
    if algorithm != RAW_TRACE_ALGORITHM:
        raise ValueError("RB9 raw report trace-signature algorithm is not recognized")

    def digest(value: Any, label: str) -> str:
        if not isinstance(value, str) or not value:
            raise ValueError(f"RB9 raw report is missing {label}")
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    compact["master_trace_signature"] = digest(
        compact.get("master_trace_signature"), "master trace signature"
    )
    rows = compact.get("rows")
    if not isinstance(rows, list):
        raise ValueError("RB9 raw report rows must be an array")
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("RB9 raw report contains a non-object row")
        row["trace_signature"] = digest(row.get("trace_signature"), "row trace signature")
    compact["trace_signature_algorithm"] = COMPACT_TRACE_ALGORITHM
    return compact


def _rows(report: dict[str, Any], lane: str) -> dict[tuple[int, str], dict[str, Any]]:
    if report.get("schema_version") != SCHEMA:
        raise ValueError(f"{lane} report schema mismatch")
    if report.get("profile_id") != PROFILE:
        raise ValueError(f"{lane} report profile mismatch")
    if report.get("lane") != lane:
        raise ValueError(f"expected {lane} report")
    if report.get("world_counts") != WORLD_COUNTS:
        raise ValueError(f"{lane} report does not contain the frozen world matrix")
    if report.get("build_config") != "Release":
        raise ValueError(f"{lane} report is not a Release build")
    if report.get("promotion_allowed") is not False:
        raise ValueError(f"{lane} report unexpectedly permits promotion")
    if report.get("trace_signature_algorithm") != COMPACT_TRACE_ALGORITHM:
        raise ValueError(f"{lane} report does not use compact content-addressed traces")
    if report.get("parity_budget_ref") != PARITY_BUDGET_REF:
        raise ValueError(f"{lane} report parity budget reference mismatch")
    if report.get("invocation_surface") != EXPECTED_INVOCATION_SURFACES[lane]:
        raise ValueError(f"{lane} report invocation surface mismatch")
    if report.get("protocol") != EXPECTED_PROTOCOL:
        raise ValueError(f"{lane} report protocol is not the frozen Release protocol")
    for field, expected in {
        "full_facade_available": False,
        "complete_rollout_collection_available": True,
        "learner_consumption_available": False,
        "maintained_claim": False,
        "required_metrics_complete": False,
        "break_even_eligible": False,
    }.items():
        if report.get(field) is not expected:
            raise ValueError(f"{lane} report {field} must remain fail-closed")

    indexed: dict[tuple[int, str], dict[str, Any]] = {}
    for row in report.get("rows", []):
        if not isinstance(row, dict):
            raise ValueError(f"{lane} report contains a non-object row")
        if type(row.get("world_count")) is not int or not isinstance(row.get("mode_id"), str):
            raise ValueError(f"{lane} report row world/mode types are not canonical")
        key = (row["world_count"], row["mode_id"])
        if key in indexed:
            raise ValueError(f"{lane} report contains duplicate row {key}")
        indexed[key] = row
    expected = {(world, mode) for world in WORLD_COUNTS for mode in MODES}
    if set(indexed) != expected:
        missing = sorted(expected - set(indexed))
        extra = sorted(set(indexed) - expected)
        raise ValueError(f"{lane} matrix mismatch: missing={missing}, extra={extra}")
    for world in WORLD_COUNTS:
        world_rows = [indexed[(world, mode)] for mode in MODES]
        expected_trace = _require_sha256(
            world_rows[0].get("trace_signature"), f"{lane} world={world} trace signature"
        )
        for row in world_rows:
            mode = str(row.get("mode_id"))
            if _require_sha256(row.get("trace_signature"), f"{lane} row trace signature") != expected_trace:
                raise ValueError(f"{lane} trace differs across modes at world_count={world}")
            if row.get("host_snapshot") is not (mode.startswith("host_export_")):
                raise ValueError(f"{lane} host-export flag mismatches mode {mode}")
            if row.get("device_consumer") is not ("device_consumer" in mode):
                raise ValueError(f"{lane} device-consumer flag mismatches mode {mode}")
            if row.get("master_trace_prefix_world_count") != 256:
                raise ValueError(f"{lane} trace prefix marker is not frozen at 256")
            if row.get("learner_equivalent") is not False:
                raise ValueError(f"{lane} row unexpectedly claims learner equivalence: {mode}")
            if row.get("promotion_eligible") is not False:
                raise ValueError(f"{lane} row unexpectedly permits promotion: {mode}")
            if row.get("parity_status") != "rb8_selected_slice_quarantined":
                raise ValueError(f"{lane} row parity status escaped quarantine: {mode}")
            expected_available = lane == "cuda_resident" or "device_consumer" not in mode
            if row.get("available") is not expected_available:
                raise ValueError(f"{lane} availability mismatch for world={world}, mode={mode}")
            if expected_available:
                if row.get("unavailable_reason") != "":
                    raise ValueError(f"{lane} available row has an unavailable reason: {mode}")
                latency = row.get("latency")
                if not isinstance(latency, dict):
                    raise ValueError(f"{lane} available row lacks latency: {mode}")
                expected_samples = {
                    "setup": EXPECTED_PROTOCOL["cold_samples"],
                    "cold_reset_setup_plus_first_window": EXPECTED_PROTOCOL["cold_samples"],
                    "cold_first_window": EXPECTED_PROTOCOL["cold_samples"],
                    "warmed_end_to_end": EXPECTED_PROTOCOL["measured_windows"],
                    "warmed_advance": EXPECTED_PROTOCOL["measured_windows"],
                    "warmed_collection": EXPECTED_PROTOCOL["measured_windows"],
                    "rollout_total": EXPECTED_PROTOCOL["rollout_samples"],
                }
                for family, expected_count in expected_samples.items():
                    stats = latency.get(family)
                    if not isinstance(stats, dict):
                        raise ValueError(f"{lane} row lacks {family} statistics: {mode}")
                    raw = stats.get("raw_ms")
                    if stats.get("sample_count") != expected_count or not isinstance(raw, list):
                        raise ValueError(f"{lane} row {family} sample count mismatch: {mode}")
                    if len(raw) != expected_count or any(
                        not isinstance(value, (int, float)) or value < 0 for value in raw
                    ):
                        raise ValueError(f"{lane} row {family} raw samples mismatch: {mode}")
                    for percentile in ("p50_ms", "p95_ms", "min_ms", "max_ms", "mean_ms"):
                        value = stats.get(percentile)
                        if not isinstance(value, (int, float)) or value < 0:
                            raise ValueError(
                                f"{lane} row {family}.{percentile} is invalid: {mode}"
                            )
                if latency.get("rollout_windows") != EXPECTED_PROTOCOL["rollout_windows"]:
                    raise ValueError(f"{lane} row rollout window count mismatch: {mode}")
                determinism = row.get("determinism")
                if not isinstance(determinism, dict) or determinism.get("checked") is not True:
                    raise ValueError(f"{lane} available row lacks determinism diagnostics: {mode}")
                if determinism.get("scope") != DETERMINISM_SCOPE:
                    raise ValueError(f"{lane} determinism scope is not identity-inclusive: {mode}")
                if determinism.get("identity_inclusive") is not True:
                    raise ValueError(f"{lane} determinism identity scope is missing: {mode}")
                if not isinstance(determinism.get("matched"), bool):
                    raise ValueError(f"{lane} determinism matched flag is not boolean: {mode}")
                if determinism.get("matched") is False and determinism.get("mismatch_reason") != (
                    "reset_allocates_fresh_entity_ids"
                ):
                    raise ValueError(f"{lane} false determinism result lacks reset explanation: {mode}")
                memory = row.get("device_memory")
                if not isinstance(memory, dict):
                    raise ValueError(f"{lane} available row lacks device memory metadata: {mode}")
                expected_memory_availability = (
                    "candidate_owned_requested_bytes"
                    if lane == "cuda_resident"
                    else "not_applicable"
                )
                if memory.get("availability") != expected_memory_availability:
                    raise ValueError(f"{lane} device memory availability mismatch: {mode}")
            else:
                if row.get("latency") is not None:
                    raise ValueError(f"{lane} unavailable row must not provide latency: {mode}")
                if row.get("unavailable_reason") != (
                    "cpu_reference_has_no_device_observation_consumer"
                ):
                    raise ValueError(f"{lane} unavailable row reason is not the frozen N/A reason: {mode}")
                memory = row.get("device_memory")
                if not isinstance(memory, dict) or memory.get("availability") != "not_applicable":
                    raise ValueError(f"{lane} unavailable row must carry device-memory N/A: {mode}")
    master_trace = _require_sha256(report.get("master_trace_signature"), f"{lane} master trace")
    if master_trace != indexed[(256, MODES[0])].get("trace_signature"):
        raise ValueError(f"{lane} master trace does not match the frozen 256-world row")
    return indexed


def _latency(row: dict[str, Any], family: str, percentile: str) -> float:
    if not row.get("available"):
        raise ValueError(f"unavailable row cannot provide latency: {row.get('mode_id')}")
    latency = row.get("latency")
    if not isinstance(latency, dict):
        raise ValueError("available RB9 row is missing latency")
    stats = latency.get(family)
    if not isinstance(stats, dict):
        raise ValueError(f"RB9 row is missing {family} statistics")
    value = stats.get(percentile)
    if not isinstance(value, (int, float)) or value <= 0:
        raise ValueError(f"RB9 {family}.{percentile} must be positive")
    return float(value)


def _speedup(cpu_ms: float, cuda_ms: float) -> float:
    return 1.0 - cuda_ms / cpu_ms


def build_summary(
    cpu: dict[str, Any], cuda: dict[str, Any], *, cpu_sha256: str, cuda_sha256: str
) -> dict[str, Any]:
    cpu_rows = _rows(cpu, "flecs_cpu_reference")
    cuda_rows = _rows(cuda, "cuda_resident")
    if cpu.get("master_trace_signature") != cuda.get("master_trace_signature"):
        raise ValueError("RB9 lane master trace signatures differ")
    if cpu.get("protocol") != cuda.get("protocol"):
        raise ValueError("RB9 lane measurement protocols differ")
    if cpu.get("invocation_surface") != EXPECTED_INVOCATION_SURFACES["flecs_cpu_reference"]:
        raise ValueError("CPU report invocation surface changed")
    if cuda.get("invocation_surface") != EXPECTED_INVOCATION_SURFACES["cuda_resident"]:
        raise ValueError("CUDA report hides the private publish-stage sequence")
    if cpu.get("parity_budget_ref") != cuda.get("parity_budget_ref"):
        raise ValueError("RB9 lane parity budget references differ")
    for world in WORLD_COUNTS:
        for mode in MODES:
            cpu_row = cpu_rows[(world, mode)]
            cuda_row = cuda_rows[(world, mode)]
            if cpu_row.get("trace_signature") != cuda_row.get("trace_signature"):
                raise ValueError(f"RB9 trace signature differs at world_count={world}, mode={mode}")
            if cpu_row.get("available") and not cuda_row.get("available"):
                raise ValueError(f"CUDA row unexpectedly unavailable at world_count={world}, mode={mode}")
            if "device_consumer" in mode and cpu_row.get("available"):
                raise ValueError(f"CPU device-consumer row must remain N/A at world_count={world}")
    if cuda.get("full_facade_available") is not False:
        raise ValueError("CUDA report unexpectedly claims full facade availability")
    counters = cuda.get("achieved_hardware_counters")
    if not isinstance(counters, dict) or counters.get("availability") != "unavailable":
        raise ValueError("CUDA achieved-counter availability must fail closed")
    if counters.get("reason") != "ERR_NVGPUCTRPERM":
        raise ValueError("CUDA achieved-counter rejection reason is not preserved")
    for metric in (
        "achieved_occupancy",
        "branch_divergence",
        "global_memory_traffic",
        "local_memory_traffic",
        "shared_memory_traffic",
    ):
        if counters.get(metric, "missing") is not None:
            raise ValueError(f"unavailable CUDA counter {metric} must be null")

    comparisons: list[dict[str, Any]] = []
    provisional_threshold: int | None = None
    for world in WORLD_COUNTS:
        cpu_row = cpu_rows[(world, "host_export_no_device")]
        cuda_row = cuda_rows[(world, "host_export_no_device")]
        if cpu_row.get("trace_signature") != cuda_row.get("trace_signature"):
            raise ValueError(f"RB9 trace signature differs at world_count={world}")
        cpu_p50 = _latency(cpu_row, "warmed_end_to_end", "p50_ms")
        cpu_p95 = _latency(cpu_row, "warmed_end_to_end", "p95_ms")
        cuda_p50 = _latency(cuda_row, "warmed_end_to_end", "p50_ms")
        cuda_p95 = _latency(cuda_row, "warmed_end_to_end", "p95_ms")
        cpu_rollout = _latency(cpu_row, "rollout_total", "p50_ms")
        cuda_rollout = _latency(cuda_row, "rollout_total", "p50_ms")
        p50_speedup = _speedup(cpu_p50, cuda_p50)
        p95_speedup = _speedup(cpu_p95, cuda_p95)
        rollout_speedup = _speedup(cpu_rollout, cuda_rollout)
        if provisional_threshold is None and p50_speedup >= 0.15 and rollout_speedup >= 0.15:
            provisional_threshold = world
        comparisons.append(
            {
                "world_count": world,
                "mode_id": "host_export_no_device",
                "trace_signature": cpu_row["trace_signature"],
                "cpu_warmed_p50_ms": cpu_p50,
                "cpu_warmed_p95_ms": cpu_p95,
                "cuda_warmed_p50_ms": cuda_p50,
                "cuda_warmed_p95_ms": cuda_p95,
                "provisional_p50_speedup_fraction": p50_speedup,
                "provisional_p95_speedup_fraction": p95_speedup,
                "cpu_rollout_p50_ms": cpu_rollout,
                "cuda_rollout_p50_ms": cuda_rollout,
                "provisional_rollout_speedup_fraction": rollout_speedup,
                "break_even_eligible": False,
            }
        )

    return {
        "schema_version": SUMMARY_SCHEMA,
        "profile_id": PROFILE,
        "parity_budget_ref": cpu.get("parity_budget_ref"),
        "world_counts": WORLD_COUNTS,
        "mode_matrix": MODES,
        "matrix_complete": True,
        "master_trace_signature": cpu["master_trace_signature"],
        "trace_signature_algorithm": COMPACT_TRACE_ALGORITHM,
        "protocol": cpu["protocol"],
        "invocation_surfaces": {
            "cpu": cpu["invocation_surface"],
            "cuda": cuda["invocation_surface"],
        },
        "determinism_diagnostic": {
            "scope": DETERMINISM_SCOPE,
            "identity_inclusive": True,
            "false_match_interpretation": "reset_allocates_fresh_entity_ids",
            "promotion_metric": False,
        },
        "inputs": {
            "cpu_sha256": cpu_sha256,
            "cuda_sha256": cuda_sha256,
        },
        "comparisons": comparisons,
        "provisional_internal_threshold_world_count": provisional_threshold,
        "threshold_is_promotion_gate": False,
        "full_facade_available": False,
        "learner_consumption_available": False,
        "required_metrics_complete": False,
        "break_even_eligible": False,
        "maintained_claim": False,
        "promotion_allowed": False,
        "decision_input": "hold_required",
        "hold_reasons": [
            "cuda_candidate_not_on_full_runtime_facade_window",
            "cpu_and_cuda_invocation_surfaces_are_not_equivalent",
            "learner_consumption_unavailable",
            "device_consumer_is_smoke_only_and_has_hidden_host_validation_readback",
            "achieved_gpu_counters_unavailable:ERR_NVGPUCTRPERM",
            "rb8_selected_slice_parity_remains_quarantined",
            "identity_inclusive_reset_determinism_is_diagnostic_only",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge held RB9 CPU/CUDA evidence.")
    parser.add_argument("--cpu-report", type=Path, required=True)
    parser.add_argument("--cuda-report", type=Path, required=True)
    parser.add_argument("--cpu-output", type=Path, required=True)
    parser.add_argument("--cuda-output", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cpu = compact_report(_load(args.cpu_report))
    cuda = compact_report(_load(args.cuda_report))
    cpu_bytes = _json_bytes(cpu)
    cuda_bytes = _json_bytes(cuda)
    args.cpu_output.parent.mkdir(parents=True, exist_ok=True)
    args.cuda_output.parent.mkdir(parents=True, exist_ok=True)
    args.cpu_output.write_bytes(cpu_bytes)
    args.cuda_output.write_bytes(cuda_bytes)
    summary = build_summary(
        cpu,
        cuda,
        cpu_sha256=hashlib.sha256(cpu_bytes).hexdigest(),
        cuda_sha256=hashlib.sha256(cuda_bytes).hexdigest(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(_json_bytes(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
