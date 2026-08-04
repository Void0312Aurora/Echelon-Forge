from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from tools.diagnostics import cuda_resident_cr2_matrix_probe as matrix_probe
    from tools.diagnostics.cuda_resident_cr2_matrix_evidence_schema import (
        COMMIT,
        COMMON_MODES,
        DEVICE_MODES,
        EVIDENCE_SCHEMA,
        ITERATION,
        MANIFEST_SCHEMA,
        METRICS,
        SHA256,
        require as _require,
        selection_policy_contract,
        validate_evidence,
    )
except ModuleNotFoundError:
    import cuda_resident_cr2_matrix_probe as matrix_probe
    from cuda_resident_cr2_matrix_evidence_schema import (
        COMMIT,
        COMMON_MODES,
        DEVICE_MODES,
        EVIDENCE_SCHEMA,
        ITERATION,
        MANIFEST_SCHEMA,
        METRICS,
        SHA256,
        require as _require,
        selection_policy_contract,
        validate_evidence,
    )


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        _require(key not in value, f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    _require(isinstance(value, dict), f"{path.name} must contain an object")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_text_bytes(path: Path) -> bytes:
    text = path.read_text(encoding="utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def _canonical_source_descriptor(root: Path, path: Path) -> dict[str, Any]:
    payload = _canonical_text_bytes(path)
    return {
        "path": path.relative_to(root).as_posix(),
        "canonicalization": "utf8_lf",
        "canonical_bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _resolve(root: Path, relative: object, label: str) -> Path:
    _require(type(relative) is str and bool(relative), f"{label} path is invalid")
    candidate = Path(relative)
    _require(not candidate.is_absolute(), f"{label} path must be repository-relative")
    resolved = (root / candidate).resolve()
    _require(resolved.is_relative_to(root.resolve()), f"{label} path escapes the repository")
    _require(resolved.is_file(), f"{label} file is missing")
    return resolved


def _verify_descriptor(root: Path, descriptor: object, label: str) -> Path:
    _require(
        isinstance(descriptor, dict) and set(descriptor) == {"path", "bytes", "sha256"},
        f"{label} descriptor schema drifted",
    )
    path = _resolve(root, descriptor["path"], label)
    _require(type(descriptor["bytes"]) is int and descriptor["bytes"] > 0, f"{label} size invalid")
    _require(
        type(descriptor["sha256"]) is str and SHA256.fullmatch(descriptor["sha256"]) is not None,
        f"{label} hash invalid",
    )
    _require(path.stat().st_size == descriptor["bytes"], f"{label} size mismatch")
    _require(_sha256(path) == descriptor["sha256"], f"{label} hash mismatch")
    return path


def _verify_source_descriptor(root: Path, descriptor: object, label: str) -> Path:
    _require(
        isinstance(descriptor, dict)
        and set(descriptor) == {"path", "canonicalization", "canonical_bytes", "sha256"},
        f"{label} source descriptor schema drifted",
    )
    path = _resolve(root, descriptor["path"], label)
    payload = _canonical_text_bytes(path)
    _require(descriptor["canonicalization"] == "utf8_lf", f"{label} canonicalization drifted")
    _require(
        type(descriptor["canonical_bytes"]) is int
        and descriptor["canonical_bytes"] == len(payload),
        f"{label} canonical size mismatch",
    )
    _require(
        type(descriptor["sha256"]) is str
        and SHA256.fullmatch(descriptor["sha256"]) is not None
        and hashlib.sha256(payload).hexdigest() == descriptor["sha256"],
        f"{label} canonical hash mismatch",
    )
    return path


def _verify_report_descriptor(root: Path, descriptor: object, label: str) -> Path:
    _require(
        isinstance(descriptor, dict)
        and set(descriptor)
        == {"path", "captured_utc", "elapsed_process_seconds", "bytes", "sha256"},
        f"{label} report descriptor schema drifted",
    )
    path = _verify_descriptor(
        root,
        {key: descriptor[key] for key in ("path", "bytes", "sha256")},
        label,
    )
    _require(
        type(descriptor["captured_utc"]) is str and descriptor["captured_utc"].endswith("Z"),
        f"{label} capture time invalid",
    )
    elapsed = descriptor["elapsed_process_seconds"]
    _require(
        isinstance(elapsed, (int, float))
        and not isinstance(elapsed, bool)
        and math.isfinite(elapsed)
        and elapsed > 0,
        f"{label} elapsed time invalid",
    )
    return path


def _validate_host_environment(value: object) -> None:
    keys = {
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
    _require(isinstance(value, dict) and set(value) == keys, "host environment schema drifted")
    for field in ("cpu_physical_cores", "cpu_logical_processors", "memory_bytes"):
        _require(type(value[field]) is int and value[field] > 0, f"host {field} invalid")
    for field in (
        "cpu_name",
        "operating_system",
        "operating_system_version",
        "operating_system_build",
        "power_scheme_guid",
        "power_scheme_name",
    ):
        _require(type(value[field]) is str and bool(value[field]), f"host {field} invalid")
    for field in ("process_affinity_pinned", "gpu_exclusive_mode", "background_load_controlled"):
        _require(value[field] is False, f"host control overclaim: {field}")


def _validate_manifest(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    top_keys = {
        "schema_version",
        "evidence_date",
        "source_commit",
        "host_environment",
        "capture_design",
        "binary_inputs",
        "source_inputs",
        "prior_evidence_inputs",
        "parity_output_path",
        "campaigns",
    }
    _require(set(manifest) == top_keys, "campaign manifest top-level schema drifted")
    _require(manifest["schema_version"] == MANIFEST_SCHEMA, "campaign manifest schema mismatch")
    _require(manifest["evidence_date"] == "2026-08-04", "campaign evidence date drifted")
    _require(
        type(manifest["source_commit"]) is str
        and COMMIT.fullmatch(manifest["source_commit"]) is not None,
        "campaign source commit invalid",
    )
    completed = subprocess.run(
        ["git", "merge-base", "--is-ancestor", manifest["source_commit"], "HEAD"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    _require(completed.returncode == 0, "campaign source commit is not an ancestor of HEAD")
    _validate_host_environment(manifest["host_environment"])
    design = manifest["capture_design"]
    _require(
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
        and type(design["campaign_count"]) is int
        and design["campaign_count"] == 2
        and design["order_balanced"] is True
        and design["lanes_run_concurrently"] is False
        and design["source_worktree_clean_at_capture"] is True
        and design["interpretation_scope"] == "host_specific_experimental_selection_advisory_only"
        and design["unmeasured_world_counts_may_be_extrapolated"] is False,
        "campaign capture design drifted",
    )
    expected_inputs = {
        "binary_inputs": {"matrix_cpu", "matrix_cuda", "full_window_cpu", "full_window_cuda"},
        "source_inputs": {
            "matrix_contract",
            "matrix_probe",
            "matrix_validator",
            "parity_comparator",
        },
        "prior_evidence_inputs": {"counter_evidence", "resource_evidence"},
    }
    paths: dict[str, Path] = {}
    for group, names in expected_inputs.items():
        value = manifest[group]
        _require(isinstance(value, dict) and set(value) == names, f"{group} inventory drifted")
        for name in sorted(names):
            verifier = (
                _verify_source_descriptor
                if group in {"source_inputs", "prior_evidence_inputs"}
                else _verify_descriptor
            )
            paths[name] = verifier(root, value[name], f"{group}.{name}")
    parity_path = Path(manifest["parity_output_path"])
    _require(
        not parity_path.is_absolute()
        and (root / parity_path).resolve().is_relative_to(root.resolve()),
        "parity output path is invalid",
    )
    campaigns = manifest["campaigns"]
    _require(isinstance(campaigns, list) and len(campaigns) == 2, "campaign inventory drifted")
    expected_campaigns = (
        ("campaign_01_cpu_then_cuda", ["flecs_cpu_reference", "cuda_resident"]),
        ("campaign_02_cuda_then_cpu", ["cuda_resident", "flecs_cpu_reference"]),
    )
    reports: dict[tuple[str, str], dict[str, Any]] = {}
    for campaign, (expected_id, expected_order) in zip(campaigns, expected_campaigns, strict=True):
        _require(
            isinstance(campaign, dict)
            and set(campaign) == {"campaign_id", "execution_order", "reports"},
            "campaign schema drifted",
        )
        _require(campaign["campaign_id"] == expected_id, "campaign id drifted")
        _require(campaign["execution_order"] == expected_order, "campaign order drifted")
        descriptors = campaign["reports"]
        _require(
            isinstance(descriptors, dict)
            and set(descriptors) == {"flecs_cpu_reference", "cuda_resident"},
            "campaign lane inventory drifted",
        )
        for lane in ("flecs_cpu_reference", "cuda_resident"):
            path = _verify_report_descriptor(root, descriptors[lane], f"{expected_id}.{lane}")
            report = matrix_probe.load_report(path)
            matrix_probe.validate_report(report, require_production=True)
            _require(report["lane"] == lane, f"{expected_id} lane mismatch")
            reports[(expected_id, lane)] = report
        first_lane, second_lane = expected_order
        _require(
            descriptors[first_lane]["captured_utc"] < descriptors[second_lane]["captured_utc"],
            "campaign timestamps contradict execution order",
        )
    return {"paths": paths, "reports": reports}


def _report_invariant(report: dict[str, Any]) -> dict[str, Any]:
    top = {key: report[key] for key in report if key not in {"rows"}}
    rows = []
    for row in report["rows"]:
        rows.append({key: row[key] for key in row if key != "latency"})
    return {"top": top, "rows_without_latency": rows}


def _validate_campaign_invariants(reports: dict[tuple[str, str], dict[str, Any]]) -> None:
    campaign_ids = ("campaign_01_cpu_then_cuda", "campaign_02_cuda_then_cpu")
    for lane in ("flecs_cpu_reference", "cuda_resident"):
        first = _report_invariant(reports[(campaign_ids[0], lane)])
        second = _report_invariant(reports[(campaign_ids[1], lane)])
        _require(first == second, f"{lane} non-timing report fields drifted across campaigns")
    cpu_master = reports[(campaign_ids[0], "flecs_cpu_reference")]["master_trace_signature"]
    cuda_master = reports[(campaign_ids[0], "cuda_resident")]["master_trace_signature"]
    _require(cpu_master == cuda_master, "CPU/CUDA matrix trace signature drifted")


def _run_parity(root: Path, manifest: dict[str, Any], paths: dict[str, Path]) -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable,
            str(paths["parity_comparator"]),
            "--cpu",
            str(paths["full_window_cpu"]),
            "--cuda",
            str(paths["full_window_cuda"]),
        ],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    _require(completed.returncode == 0, f"fresh parity comparator failed: {completed.stderr}")
    parity = json.loads(completed.stdout, object_pairs_hook=_unique_object)
    _require(isinstance(parity, dict), "fresh parity output is not an object")
    _require(
        parity.get("schema_version") == "cuda_resident.selected_slice_parity.comparison.v1"
        and parity.get("status") == "pass",
        "fresh parity comparison did not pass",
    )
    coverage = parity.get("coverage")
    _require(
        isinstance(coverage, dict)
        and type(coverage.get("released_numeric_field_count")) is int
        and coverage.get("released_numeric_field_count") == 12
        and coverage.get("partition_complete") is True,
        "fresh parity coverage drifted",
    )
    for family in (
        parity.get("cross_lane_fields"),
        *parity.get("same_backend_reset_fields", {}).values(),
    ):
        _require(
            isinstance(family, list) and len(family) == 12, "fresh parity field inventory drifted"
        )
        _require(
            all(
                type(row["matched_count"]) is int
                and type(row["comparison_count"]) is int
                and row["matched_count"] == row["comparison_count"] > 0
                for row in family
            ),
            "fresh parity field comparison failed",
        )
    _require(
        parity.get("candidate_promotion_blocked") is True
        and parity.get("maintained_claim_allowed") is False
        and parity.get("public_support_enabled") is False,
        "fresh parity gates drifted",
    )
    output_path = (root / manifest["parity_output_path"]).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(parity, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return {
        "path": output_path.relative_to(root).as_posix(),
        "bytes": output_path.stat().st_size,
        "sha256": _sha256(output_path),
        "schema_version": parity["schema_version"],
        "status": parity["status"],
        "released_numeric_field_count": coverage["released_numeric_field_count"],
        "trace_signature_sha256": parity["trace_signature_sha256"],
    }


def _validate_prior_evidence(paths: dict[str, Path]) -> dict[str, Any]:
    counter = _load(paths["counter_evidence"])
    counter_gates = counter.get("gates")
    _require(
        isinstance(counter_gates, dict)
        and counter_gates.get("cr2_5_achieved_counter_gate_complete") is False
        and counter_gates.get("cr2_5_disposition") == "documented_external_blocker"
        and counter_gates.get("cr2_5a_launch_topology_complete") is True
        and counter_gates.get("cr2_5a_static_resource_complete") is True,
        "CR2-5 counter gate state drifted",
    )
    _require(
        counter.get("attempt", {}).get("status") == "external_blocked"
        and counter.get("attempt", {}).get("blocker_code") == "ERR_NVGPUCTRPERM"
        and type(counter.get("attempt", {}).get("collected_launch_count")) is int
        and counter.get("attempt", {}).get("collected_launch_count") == 0,
        "CR2-5 counter blocker drifted",
    )
    for metric in counter.get("achieved_counters", {}).values():
        _require(metric.get("values_by_launch") is None, "blocked counter contains values")
    resource = _load(paths["resource_evidence"])
    resource_gates = resource.get("gates")
    _require(
        isinstance(resource_gates, dict)
        and resource_gates.get("cr2_5a_launch_topology_complete") is True
        and resource_gates.get("cr2_5a_static_resource_complete") is True
        and resource_gates.get("cr2_5_achieved_counter_gate_complete") is False,
        "CR2-5 resource gate state drifted",
    )
    return {
        "resource_static_and_topology_complete": True,
        "achieved_counter_gate_complete": False,
        "counter_disposition": "documented_external_blocker",
        "counter_blocker_code": "ERR_NVGPUCTRPERM",
        "tuning_authorized": False,
    }


def _available_rows(report: dict[str, Any]) -> dict[tuple[int, str], dict[str, Any]]:
    return {(row["world_count"], row["mode_id"]): row for row in report["rows"] if row["available"]}


def _comparison_rows(reports: dict[tuple[str, str], dict[str, Any]]) -> list[dict[str, Any]]:
    campaign_ids = ("campaign_01_cpu_then_cuda", "campaign_02_cuda_then_cpu")
    indexed = {key: _available_rows(report) for key, report in reports.items()}
    comparisons: list[dict[str, Any]] = []
    for world_count in matrix_probe.WORLD_COUNTS:
        for mode_id in COMMON_MODES:
            metrics: dict[str, Any] = {}
            for metric_id, (family, statistic, divisor) in METRICS.items():
                campaign_values = []
                ratios = []
                for campaign_id in campaign_ids:
                    cpu = indexed[(campaign_id, "flecs_cpu_reference")][(world_count, mode_id)]
                    cuda = indexed[(campaign_id, "cuda_resident")][(world_count, mode_id)]
                    cpu_ms = cpu["latency"][family][statistic] / divisor
                    cuda_ms = cuda["latency"][family][statistic] / divisor
                    _require(cpu_ms > 0 and cuda_ms > 0, "matrix comparison contains zero latency")
                    ratio = cpu_ms / cuda_ms
                    _require(not math.isclose(ratio, 1.0, rel_tol=1e-12), "matrix ratio is tied")
                    direction = "cuda_resident" if ratio > 1 else "flecs_cpu_reference"
                    ratios.append(ratio)
                    campaign_values.append(
                        {
                            "campaign_id": campaign_id,
                            "cpu_ms": cpu_ms,
                            "cuda_ms": cuda_ms,
                            "cpu_over_cuda": ratio,
                            "faster_lane": direction,
                        }
                    )
                metric_direction = (
                    "cuda_resident"
                    if all(value > 1 for value in ratios)
                    else "flecs_cpu_reference"
                    if all(value < 1 for value in ratios)
                    else "mixed"
                )
                metrics[metric_id] = {
                    "campaigns": campaign_values,
                    "min_cpu_over_cuda": min(ratios),
                    "max_cpu_over_cuda": max(ratios),
                    "direction": metric_direction,
                }
            row_direction = (
                "cuda_resident"
                if all(value["direction"] == "cuda_resident" for value in metrics.values())
                else "flecs_cpu_reference"
                if all(value["direction"] == "flecs_cpu_reference" for value in metrics.values())
                else "mixed"
            )
            comparisons.append(
                {
                    "world_count": world_count,
                    "mode_id": mode_id,
                    "metrics": metrics,
                    "all_metric_direction": row_direction,
                }
            )
    return comparisons


def _selection_policy(comparisons: list[dict[str, Any]]) -> dict[str, Any]:
    indexed = {(row["world_count"], row["mode_id"]): row for row in comparisons}
    for mode in COMMON_MODES:
        _require(
            indexed[(1, mode)]["all_metric_direction"] == "flecs_cpu_reference",
            "world 1 policy drifted",
        )
    _require(
        indexed[(4, "no_export_no_device")]["all_metric_direction"] == "cuda_resident",
        "world 4 no-export policy drifted",
    )
    world4_export = indexed[(4, "host_export_no_device")]
    _require(world4_export["all_metric_direction"] == "mixed", "world 4 export ambiguity drifted")
    _require(
        world4_export["metrics"]["warmed_end_to_end_p50"]["direction"] == "cuda_resident"
        and world4_export["metrics"]["rollout_per_window_p50"]["direction"] == "cuda_resident"
        and world4_export["metrics"]["rollout_per_window_p95"]["direction"] == "mixed",
        "world 4 export median/tail split drifted",
    )
    for world in (16, 64, 256):
        for mode in COMMON_MODES:
            _require(
                indexed[(world, mode)]["all_metric_direction"] == "cuda_resident",
                f"world {world} CUDA policy drifted",
            )
    return selection_policy_contract()


def collect(root: Path, manifest_path: Path) -> dict[str, Any]:
    manifest = _load(manifest_path)
    validated = _validate_manifest(root, manifest)
    reports = validated["reports"]
    paths = validated["paths"]
    _validate_campaign_invariants(reports)
    parity = _run_parity(root, manifest, paths)
    counter_status = _validate_prior_evidence(paths)
    comparisons = _comparison_rows(reports)
    policy = _selection_policy(comparisons)
    campaigns = []
    for campaign in manifest["campaigns"]:
        campaigns.append(
            {
                "campaign_id": campaign["campaign_id"],
                "execution_order": campaign["execution_order"],
                "reports": campaign["reports"],
            }
        )
    evidence = {
        "schema_version": EVIDENCE_SCHEMA,
        "iteration": ITERATION,
        "evidence_date": manifest["evidence_date"],
        "source_commit": manifest["source_commit"],
        "inputs": {
            "manifest": {
                "path": manifest_path.relative_to(root).as_posix(),
                "bytes": manifest_path.stat().st_size,
                "sha256": _sha256(manifest_path),
            },
            "collector_source": _canonical_source_descriptor(root, Path(__file__)),
            "schema_source": _canonical_source_descriptor(
                root, Path(__file__).with_name("cuda_resident_cr2_matrix_evidence_schema.py")
            ),
            "binary_inputs": manifest["binary_inputs"],
            "source_inputs": manifest["source_inputs"],
            "prior_evidence_inputs": manifest["prior_evidence_inputs"],
        },
        "host_environment": manifest["host_environment"],
        "capture_design": manifest["capture_design"],
        "campaigns": campaigns,
        "comparison_definition": {
            "ratio": "cpu_ms_over_cuda_ms",
            "ratio_above_one_means": "cuda_resident_faster",
            "metrics": list(METRICS),
            "common_modes_only": list(COMMON_MODES),
            "device_modes_are_not_cpu_comparisons": list(DEVICE_MODES),
            "cold_and_setup_excluded_reason": "selection_advisory_targets_steady_windows",
            "rollout_p95_semantics": "nearest_rank_maximum_of_10_rollouts",
        },
        "comparisons": comparisons,
        "selection_policy": policy,
        "parity_confirmation": parity,
        "counter_status": counter_status,
        "limitations": {
            "host_specific": True,
            "balanced_power_scheme": True,
            "background_load_uncontrolled": True,
            "no_process_affinity": True,
            "no_gpu_exclusive_mode": True,
            "unmeasured_world_counts_unclassified": True,
            "rollout_p95_is_maximum_of_10": True,
            "performance_tuning_claimed": False,
            "promotion_claimed": False,
        },
        "gates": {
            "cr2_5_achieved_counter_gate_complete": False,
            "cr2_6_matrix_evidence_complete": True,
            "cr2_6_selection_advisory_complete": True,
            "maintained_claim_allowed": False,
            "promotion_allowed": False,
            "public_support_enabled": False,
            "tuning_authorized": False,
        },
    }
    validate_evidence(evidence)
    return evidence


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect and validate CR2-6b matrix evidence")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[2]
    manifest = args.manifest.resolve()
    output = args.output.resolve()
    _require(manifest.is_relative_to(root), "manifest must be inside the repository")
    _require(output.is_relative_to(root), "output must be inside the repository")
    evidence = collect(root, manifest)
    output.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
