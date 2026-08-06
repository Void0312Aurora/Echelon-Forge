from __future__ import annotations

import math
import re
from typing import Any


MANIFEST_SCHEMA = "cuda_resident.cr2.production_matrix_campaign_manifest.v1"
EVIDENCE_SCHEMA = "cuda_resident.cr2.production_matrix_evidence.v1"
ITERATION = "CR2-6b"
WORLD_COUNTS = (1, 4, 16, 64, 256)
COMMON_MODES = ("no_export_no_device", "host_export_no_device")
DEVICE_MODES = ("no_export_device_consumer", "host_export_device_consumer")
METRICS = {
    "warmed_end_to_end_p50": ("warmed_end_to_end", "p50_ms", 1),
    "warmed_end_to_end_p95": ("warmed_end_to_end", "p95_ms", 1),
    "rollout_per_window_p50": ("rollout_total", "p50_ms", 64),
    "rollout_per_window_p95": ("rollout_total", "p95_ms", 64),
}
SHA256 = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")


class MatrixEvidenceError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise MatrixEvidenceError(message)


def selection_policy_contract() -> dict[str, Any]:
    return {
        "status": "experimental_advisory_complete",
        "maintained_default_backend": "flecs_cpu_reference",
        "applies_only_to_measured_world_counts": True,
        "rules": [
            {
                "world_counts": [1],
                "mode_ids": list(COMMON_MODES),
                "default_backend": "flecs_cpu_reference",
                "basis": "all_order_balanced_warmed_and_rollout_p50_p95_metrics",
            },
            {
                "world_counts": [4],
                "mode_ids": ["no_export_no_device"],
                "default_backend": "cuda_resident",
                "basis": "all_order_balanced_warmed_and_rollout_p50_p95_metrics",
            },
            {
                "world_counts": [4],
                "mode_ids": ["host_export_no_device"],
                "default_backend": "flecs_cpu_reference",
                "median_throughput_opt_in_backend": "cuda_resident",
                "basis": "cuda_wins_both_p50_metrics_but_rollout_p95_reverses_by_campaign",
            },
            {
                "world_counts": [16, 64, 256],
                "mode_ids": list(COMMON_MODES),
                "default_backend": "cuda_resident",
                "basis": "all_order_balanced_warmed_and_rollout_p50_p95_metrics",
            },
            {
                "world_counts": list(WORLD_COUNTS),
                "mode_ids": list(DEVICE_MODES),
                "required_backend": "cuda_resident",
                "comparative_performance_claimed": False,
                "basis": "cpu_reference_has_no_device_observation_consumer",
            },
        ],
    }


def _strict_descriptor(value: object, *, parity: bool = False) -> None:
    keys = {"path", "bytes", "sha256"}
    if parity:
        keys |= {
            "schema_version",
            "status",
            "released_numeric_field_count",
            "trace_signature_sha256",
        }
    require(isinstance(value, dict) and set(value) == keys, "evidence descriptor drifted")
    require(type(value["path"]) is str and bool(value["path"]), "descriptor path invalid")
    require(type(value["bytes"]) is int and value["bytes"] > 0, "descriptor bytes invalid")
    require(
        type(value["sha256"]) is str and SHA256.fullmatch(value["sha256"]) is not None,
        "descriptor hash invalid",
    )
    if parity:
        require(
            type(value["trace_signature_sha256"]) is str
            and SHA256.fullmatch(value["trace_signature_sha256"]) is not None,
            "parity trace hash invalid",
        )


def _strict_source_descriptor(value: object) -> None:
    require(
        isinstance(value, dict)
        and set(value) == {"path", "canonicalization", "canonical_bytes", "sha256"},
        "source descriptor schema drifted",
    )
    require(type(value["path"]) is str and bool(value["path"]), "source path invalid")
    require(value["canonicalization"] == "utf8_lf", "source canonicalization drifted")
    require(
        type(value["canonical_bytes"]) is int and value["canonical_bytes"] > 0,
        "source canonical bytes invalid",
    )
    require(
        type(value["sha256"]) is str and SHA256.fullmatch(value["sha256"]) is not None,
        "source canonical hash invalid",
    )


def _strict_report_descriptor(value: object) -> None:
    require(
        isinstance(value, dict)
        and set(value) == {"path", "captured_utc", "elapsed_process_seconds", "bytes", "sha256"},
        "report descriptor schema drifted",
    )
    _strict_descriptor({key: value[key] for key in ("path", "bytes", "sha256")})
    require(
        type(value["captured_utc"]) is str and value["captured_utc"].endswith("Z"),
        "report capture time invalid",
    )
    elapsed = value["elapsed_process_seconds"]
    require(
        isinstance(elapsed, (int, float))
        and not isinstance(elapsed, bool)
        and math.isfinite(elapsed)
        and elapsed > 0,
        "report elapsed time invalid",
    )


def _validate_campaigns(campaigns: object) -> None:
    expected = (
        ("campaign_01_cpu_then_cuda", ["flecs_cpu_reference", "cuda_resident"]),
        ("campaign_02_cuda_then_cpu", ["cuda_resident", "flecs_cpu_reference"]),
    )
    require(isinstance(campaigns, list) and len(campaigns) == 2, "campaign inventory drifted")
    for campaign, (campaign_id, order) in zip(campaigns, expected, strict=True):
        require(
            isinstance(campaign, dict)
            and set(campaign) == {"campaign_id", "execution_order", "reports"},
            "campaign schema drifted",
        )
        require(campaign["campaign_id"] == campaign_id, "campaign id drifted")
        require(campaign["execution_order"] == order, "campaign order drifted")
        reports = campaign["reports"]
        require(
            isinstance(reports, dict) and set(reports) == {"flecs_cpu_reference", "cuda_resident"},
            "campaign report inventory drifted",
        )
        for descriptor in reports.values():
            _strict_report_descriptor(descriptor)
        first_lane, second_lane = order
        require(
            reports[first_lane]["captured_utc"] < reports[second_lane]["captured_utc"],
            "campaign timestamps contradict execution order",
        )


def _metric_direction(campaigns: list[dict[str, Any]]) -> tuple[str, list[float]]:
    ratios: list[float] = []
    expected_ids = ("campaign_01_cpu_then_cuda", "campaign_02_cuda_then_cpu")
    require(len(campaigns) == 2, "metric campaign inventory drifted")
    for campaign, expected_id in zip(campaigns, expected_ids, strict=True):
        require(
            isinstance(campaign, dict)
            and set(campaign)
            == {"campaign_id", "cpu_ms", "cuda_ms", "cpu_over_cuda", "faster_lane"},
            "metric campaign schema drifted",
        )
        require(campaign["campaign_id"] == expected_id, "metric campaign order drifted")
        values = [campaign[field] for field in ("cpu_ms", "cuda_ms", "cpu_over_cuda")]
        require(
            all(
                isinstance(value, (int, float))
                and not isinstance(value, bool)
                and math.isfinite(value)
                and value > 0
                for value in values
            ),
            "metric campaign value invalid",
        )
        ratio = campaign["cpu_ms"] / campaign["cuda_ms"]
        require(
            math.isclose(campaign["cpu_over_cuda"], ratio, rel_tol=1e-12, abs_tol=1e-12),
            "metric ratio drifted",
        )
        require(not math.isclose(ratio, 1.0, rel_tol=1e-12), "metric tie is not classified")
        lane = "cuda_resident" if ratio > 1 else "flecs_cpu_reference"
        require(campaign["faster_lane"] == lane, "metric faster lane drifted")
        ratios.append(ratio)
    direction = (
        "cuda_resident"
        if all(value > 1 for value in ratios)
        else "flecs_cpu_reference"
        if all(value < 1 for value in ratios)
        else "mixed"
    )
    return direction, ratios


def _validate_comparisons(comparisons: object) -> None:
    require(
        isinstance(comparisons, list) and len(comparisons) == 10, "comparison inventory drifted"
    )
    indexed: dict[tuple[int, str], dict[str, Any]] = {}
    for row in comparisons:
        require(
            isinstance(row, dict)
            and set(row) == {"world_count", "mode_id", "metrics", "all_metric_direction"},
            "comparison row schema drifted",
        )
        world = row["world_count"]
        mode = row["mode_id"]
        require(type(world) is int and world in WORLD_COUNTS, "comparison world invalid")
        require(type(mode) is str and mode in COMMON_MODES, "comparison mode invalid")
        require((world, mode) not in indexed, "duplicate comparison row")
        metrics = row["metrics"]
        require(
            isinstance(metrics, dict) and set(metrics) == set(METRICS), "metric inventory drifted"
        )
        directions = []
        for metric in metrics.values():
            require(
                isinstance(metric, dict)
                and set(metric)
                == {"campaigns", "min_cpu_over_cuda", "max_cpu_over_cuda", "direction"},
                "metric summary schema drifted",
            )
            direction, ratios = _metric_direction(metric["campaigns"])
            require(metric["direction"] == direction, "metric direction drifted")
            require(
                isinstance(metric["min_cpu_over_cuda"], (int, float))
                and not isinstance(metric["min_cpu_over_cuda"], bool)
                and isinstance(metric["max_cpu_over_cuda"], (int, float))
                and not isinstance(metric["max_cpu_over_cuda"], bool)
                and math.isclose(metric["min_cpu_over_cuda"], min(ratios), rel_tol=1e-12)
                and math.isclose(metric["max_cpu_over_cuda"], max(ratios), rel_tol=1e-12),
                "metric ratio range drifted",
            )
            directions.append(direction)
        row_direction = (
            "cuda_resident"
            if all(value == "cuda_resident" for value in directions)
            else "flecs_cpu_reference"
            if all(value == "flecs_cpu_reference" for value in directions)
            else "mixed"
        )
        require(row["all_metric_direction"] == row_direction, "row direction drifted")
        indexed[(world, mode)] = row
    require(
        set(indexed) == {(world, mode) for world in WORLD_COUNTS for mode in COMMON_MODES},
        "comparison matrix incomplete",
    )


def validate_evidence(evidence: dict[str, Any]) -> None:
    keys = {
        "schema_version",
        "iteration",
        "evidence_date",
        "source_commit",
        "inputs",
        "host_environment",
        "capture_design",
        "campaigns",
        "comparison_definition",
        "comparisons",
        "selection_policy",
        "parity_confirmation",
        "counter_status",
        "limitations",
        "gates",
    }
    require(set(evidence) == keys, "matrix evidence top-level schema drifted")
    require(evidence["schema_version"] == EVIDENCE_SCHEMA, "matrix evidence schema mismatch")
    require(evidence["iteration"] == ITERATION, "matrix evidence iteration drifted")
    require(evidence["evidence_date"] == "2026-08-04", "matrix evidence date drifted")
    require(
        type(evidence["source_commit"]) is str
        and COMMIT.fullmatch(evidence["source_commit"]) is not None,
        "matrix evidence source commit invalid",
    )
    inputs = evidence["inputs"]
    require(
        isinstance(inputs, dict)
        and set(inputs)
        == {
            "manifest",
            "collector_source",
            "schema_source",
            "binary_inputs",
            "source_inputs",
            "prior_evidence_inputs",
        },
        "matrix evidence input schema drifted",
    )
    _strict_descriptor(inputs["manifest"])
    _strict_source_descriptor(inputs["collector_source"])
    _strict_source_descriptor(inputs["schema_source"])
    input_groups = {
        "binary_inputs": {"matrix_cpu", "matrix_cuda", "full_window_cpu", "full_window_cuda"},
        "source_inputs": {
            "matrix_contract",
            "matrix_probe",
            "matrix_validator",
            "parity_comparator",
        },
        "prior_evidence_inputs": {"counter_evidence", "resource_evidence"},
    }
    for group, names in input_groups.items():
        values = inputs[group]
        require(isinstance(values, dict) and set(values) == names, f"{group} drifted")
        for descriptor in values.values():
            if group in {"source_inputs", "prior_evidence_inputs"}:
                _strict_source_descriptor(descriptor)
            else:
                _strict_descriptor(descriptor)
    host = evidence["host_environment"]
    host_keys = {
        "cpu_name",
        "cpu_physical_cores",
        "cpu_logical_processors",
        "memory_bytes",
        "operating_system",
        "operating_system_version",
        "operating_system_build",
        "power_scheme_guid",
        "power_scheme_name",
        "process_affinity_pinned",
        "gpu_exclusive_mode",
        "background_load_controlled",
    }
    require(isinstance(host, dict) and set(host) == host_keys, "host environment schema drifted")
    for field in ("cpu_physical_cores", "cpu_logical_processors", "memory_bytes"):
        require(type(host.get(field)) is int and host[field] > 0, f"host {field} invalid")
    for field in ("process_affinity_pinned", "gpu_exclusive_mode", "background_load_controlled"):
        require(host.get(field) is False, f"host control overclaim: {field}")
    design = evidence["capture_design"]
    require(
        isinstance(design, dict)
        and set(design)
        == {
            "campaign_count",
            "order_balanced",
            "lanes_run_concurrently",
            "source_worktree_clean_at_capture",
            "interpretation_scope",
            "unmeasured_world_counts_may_be_extrapolated",
        }
        and type(design.get("campaign_count")) is int
        and design.get("campaign_count") == 2
        and design.get("order_balanced") is True
        and design.get("lanes_run_concurrently") is False
        and design.get("source_worktree_clean_at_capture") is True
        and design.get("interpretation_scope")
        == "host_specific_experimental_selection_advisory_only"
        and design.get("unmeasured_world_counts_may_be_extrapolated") is False,
        "capture design drifted",
    )
    _validate_campaigns(evidence["campaigns"])
    require(
        evidence["comparison_definition"]
        == {
            "ratio": "cpu_ms_over_cuda_ms",
            "ratio_above_one_means": "cuda_resident_faster",
            "metrics": list(METRICS),
            "common_modes_only": list(COMMON_MODES),
            "device_modes_are_not_cpu_comparisons": list(DEVICE_MODES),
            "cold_and_setup_excluded_reason": "selection_advisory_targets_steady_windows",
            "rollout_p95_semantics": "nearest_rank_maximum_of_10_rollouts",
        },
        "comparison definition drifted",
    )
    _validate_comparisons(evidence["comparisons"])
    expected_policy = selection_policy_contract()
    policy = evidence["selection_policy"]
    require(
        policy == expected_policy
        and policy["applies_only_to_measured_world_counts"] is True
        and policy["rules"][-1]["comparative_performance_claimed"] is False,
        "selection policy contract drifted",
    )
    _strict_descriptor(evidence["parity_confirmation"], parity=True)
    require(
        evidence["parity_confirmation"]["schema_version"]
        == "cuda_resident.selected_slice_parity.comparison.v1"
        and evidence["parity_confirmation"]["status"] == "pass"
        and type(evidence["parity_confirmation"]["released_numeric_field_count"]) is int
        and evidence["parity_confirmation"]["released_numeric_field_count"] == 12,
        "parity confirmation drifted",
    )
    counter = evidence["counter_status"]
    expected_counter = {
        "resource_static_and_topology_complete": True,
        "achieved_counter_gate_complete": False,
        "counter_disposition": "documented_external_blocker",
        "counter_blocker_code": "ERR_NVGPUCTRPERM",
        "tuning_authorized": False,
    }
    require(
        isinstance(counter, dict)
        and set(counter) == set(expected_counter)
        and counter["resource_static_and_topology_complete"] is True
        and counter["achieved_counter_gate_complete"] is False
        and counter["counter_disposition"] == expected_counter["counter_disposition"]
        and counter["counter_blocker_code"] == expected_counter["counter_blocker_code"]
        and counter["tuning_authorized"] is False,
        "counter status drifted",
    )
    expected_limitations = {
        "host_specific": True,
        "balanced_power_scheme": True,
        "background_load_uncontrolled": True,
        "no_process_affinity": True,
        "no_gpu_exclusive_mode": True,
        "unmeasured_world_counts_unclassified": True,
        "rollout_p95_is_maximum_of_10": True,
        "performance_tuning_claimed": False,
        "promotion_claimed": False,
    }
    limitations = evidence["limitations"]
    require(
        isinstance(limitations, dict)
        and set(limitations) == set(expected_limitations)
        and all(limitations[key] is value for key, value in expected_limitations.items()),
        "matrix evidence limitations drifted",
    )
    expected_gates = {
        "cr2_5_achieved_counter_gate_complete": False,
        "cr2_6_matrix_evidence_complete": True,
        "cr2_6_selection_advisory_complete": True,
        "maintained_claim_allowed": False,
        "promotion_allowed": False,
        "public_support_enabled": False,
        "tuning_authorized": False,
    }
    gates = evidence["gates"]
    require(
        isinstance(gates, dict)
        and set(gates) == set(expected_gates)
        and all(gates[key] is value for key, value in expected_gates.items()),
        "matrix evidence gates drifted",
    )
