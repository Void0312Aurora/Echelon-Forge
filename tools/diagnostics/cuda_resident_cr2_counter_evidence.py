from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path
from typing import Any

if __package__:
    from . import cuda_resident_cr2_resource_evidence as resource
    from .cuda_resident_cr2_counter_parser import (
        COUNTER_FAMILIES,
        COUNTER_FAMILY_UNITS,
        PERMISSION_CODE,
        command_template,
        empty_counter_families,
        export_counter_csv,
        parse_attempt_log,
        parse_counter_csv,
        required_launch_count,
    )
    from .cuda_resident_cr2_json_types import StrictJson
    from .cuda_resident_cr2_resource_schema import profile_version_of
else:
    import cuda_resident_cr2_resource_evidence as resource  # type: ignore[no-redef]
    from cuda_resident_cr2_counter_parser import (  # type: ignore[no-redef]
        COUNTER_FAMILIES,
        COUNTER_FAMILY_UNITS,
        PERMISSION_CODE,
        command_template,
        empty_counter_families,
        export_counter_csv,
        parse_attempt_log,
        parse_counter_csv,
        required_launch_count,
    )
    from cuda_resident_cr2_json_types import StrictJson  # type: ignore[no-redef]
    from cuda_resident_cr2_resource_schema import profile_version_of  # type: ignore[no-redef]


SCHEMA = "cuda_resident.cr2.achieved_counter_evidence.v1"
PROFILE = resource.PROFILE
EXPECTED_TOOLCHAIN = {
    "target_processes": "application-only",
    "profile_from_start": False,
    "replay_mode": "kernel",
    "kernel_name_base": "demangled",
    "counter_set": "full",
    "command_paths": "absolute_paths_hashed_and_redacted",
}
EXPECTED_CAPTURE = {
    "range": "cudaProfilerApi",
    "world_count": 256,
    "window_count": 1,
    "build_config": "Release",
    "cuda_architecture": "sm_86",
    "trace_signature_algorithm": "fnv1a64",
    "trace_signature_digest": "cb31675ee34e5015",
    "consumer_await_completed": True,
    "diagnostic_materialization_called": False,
}
TOP_LEVEL_KEYS = {
    "schema_version",
    "profile_id",
    "evidence_date",
    "source",
    "inputs",
    "toolchain",
    "capture",
    "attempt",
    "achieved_counters",
    "interpretation",
    "gates",
}
INPUT_KEYS = {
    "source_hash_canonicalization",
    "ncu_executable_sha256",
    "binary_sha256",
    "probe_output_sha256",
    "resource_evidence_sha256",
    "attempt_log_sha256",
    "ncu_report_sha256",
    "launcher_stdout_sha256",
    "launcher_stderr_sha256",
    "command_argv_sha256",
    "collector_source_sha256",
    "contract_source_sha256",
}
TOOLCHAIN_KEYS = {
    "nsight_compute_version",
    "target_processes",
    "profile_from_start",
    "replay_mode",
    "kernel_name_base",
    "counter_set",
    "launch_count_limit",
    "command_paths",
    "command_template",
}
CAPTURE_KEYS = {
    "range",
    "world_count",
    "window_count",
    "build_config",
    "cuda_architecture",
    "trace_signature_algorithm",
    "trace_signature_digest",
    "consumer_await_completed",
    "diagnostic_materialization_called",
}
INTERPRETATION_KEYS = {
    "cr2_5a_resource_evidence_validated",
    "theoretical_occupancy_is_not_achieved_occupancy",
    "nsys_launch_metadata_is_not_an_achieved_counter",
    "missing_counters_are_not_zero",
    "external_permission_is_not_a_kernel_result",
}
GATE_KEYS = {
    "cr2_5a_static_resource_complete",
    "cr2_5a_launch_topology_complete",
    "cr2_5b_counter_attempt_complete",
    "cr2_5_achieved_counter_gate_complete",
    "cr2_5_disposition",
    "maintained_claim_allowed",
    "public_support_enabled",
    "promotion_allowed",
    "tuning_authorized",
}
ATTEMPT_KEYS = {
    "status",
    "exit_code",
    "connected_pid",
    "disconnected_pid",
    "application_completed",
    "report_created",
    "blocker_code",
    "blocker_kind",
    "required_launch_count",
    "collected_launch_count",
    "log_error_codes",
    "recognized_error_line_sha256",
}
FAMILY_KEYS = {"unit", "provenance", "metric_names", "values_by_launch"}


class CounterEvidenceError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CounterEvidenceError(message)


_STRICT = StrictJson(_require)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bytes_sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _argv_sha256(argv: list[str]) -> str:
    return hashlib.sha256("\0".join(argv).encode("utf-8")).hexdigest()


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        _require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    _require(isinstance(value, dict), f"JSON root must be an object: {path.name}")
    return value


def _generation_of(profile_id: object, label: str) -> int:
    """Resolve a profile id to its generation via the schema identity table,
    fail closed. Launch counts and unit maps follow the generation: a new one
    registers once in the identity table and the parser unit map, no re-pins."""
    _require(type(profile_id) is str, f"{label} must be a string")
    try:
        return profile_version_of(str(profile_id))
    except resource.EvidenceError as error:
        raise CounterEvidenceError(f"{label} is not a known generation") from error


def _git_head(path: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=path.resolve().parent,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout.strip()


def ncu_version(ncu: Path) -> str:
    completed = subprocess.run(
        [str(ncu), "--version"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    text = completed.stdout + completed.stderr
    match = re.search(r"^Version ([^\r\n]+)$", text, flags=re.MULTILINE)
    _require(match is not None, "Nsight Compute version line is missing")
    version = match.group(1).strip()
    _require(version.startswith("2025.3.1.0 "), "unexpected Nsight Compute version")
    return version


def _validate_families(status: str, families: object, generation: int) -> None:
    families = _STRICT.object(families, set(COUNTER_FAMILIES), "counter families")
    # A report carries exactly its declared generation's measured-unit map.
    # Direct lookup replaces inference from the observed units: v2 and v3 share
    # one measured unit map, so units alone can no longer name a generation.
    _require(generation in COUNTER_FAMILY_UNITS, f"no unit map for generation {generation}")
    expected_units = COUNTER_FAMILY_UNITS[generation]
    launch_count = required_launch_count(generation)
    for family, unit in expected_units.items():
        row = _STRICT.object(families[family], FAMILY_KEYS, family)
        _STRICT.exact_scalar(row["unit"], unit, f"{family}.unit")
        if status != "available":
            for field in ("provenance", "metric_names", "values_by_launch"):
                _require(row[field] is None, f"unavailable {family}.{field} must remain null")
            continue
        _require(
            type(row["provenance"]) is str
            and row["provenance"] == "nsight_compute_hardware_counter",
            f"{family} has non-hardware provenance",
        )
        names = _STRICT.list(row["metric_names"], f"{family}.metric_names")
        _require(
            bool(names)
            and all(type(name) is str and name for name in names)
            and len(names) == len(set(names)),
            f"{family} metric names are incomplete",
        )
        values = _STRICT.list(row["values_by_launch"], f"{family}.values_by_launch")
        _require(
            len(values) == launch_count,
            f"{family} must contain all launch values",
        )
        for value in values:
            _require(
                type(value) in {int, float} and math.isfinite(value) and value >= 0,
                f"{family} contains an invalid achieved value",
            )
            if unit == "ratio":
                _require(value <= 1.0, f"{family} ratio exceeds one")


def validate_report(report: dict[str, Any]) -> None:
    report = _STRICT.object(report, TOP_LEVEL_KEYS, "counter evidence")
    _STRICT.exact_scalar(report["schema_version"], SCHEMA, "counter evidence schema")
    # Every launch-count and unit expectation below follows the generation the
    # report declares; validate_parent_link binds a capture to its parent.
    generation = _generation_of(report["profile_id"], "counter evidence profile")
    launch_count = required_launch_count(generation)
    _require(
        type(report["evidence_date"]) is str
        and re.fullmatch(r"\d{4}-\d{2}-\d{2}", report["evidence_date"]) is not None,
        "evidence date is invalid",
    )
    source = _STRICT.object(
        report["source"], {"baseline_commit", "candidate_state"}, "counter evidence source"
    )
    _require(
        type(source["baseline_commit"]) is str
        and re.fullmatch(r"[0-9a-f]{40}", source["baseline_commit"]) is not None,
        "baseline commit is invalid",
    )
    _STRICT.exact_scalar(
        source["candidate_state"],
        "cr2_5b_unpromoted_worktree",
        "counter candidate state",
    )
    inputs = _STRICT.object(report["inputs"], INPUT_KEYS, "counter inputs")
    _STRICT.exact_scalar(
        inputs["source_hash_canonicalization"], "utf8_lf", "counter source hash mode"
    )
    for key in INPUT_KEYS - {"source_hash_canonicalization", "ncu_report_sha256"}:
        _require(
            type(inputs[key]) is str and re.fullmatch(r"[0-9a-f]{64}", inputs[key]) is not None,
            f"{key} is not a SHA-256 digest",
        )
    _require(
        inputs["ncu_report_sha256"] is None
        or (
            type(inputs["ncu_report_sha256"]) is str
            and re.fullmatch(r"[0-9a-f]{64}", inputs["ncu_report_sha256"]) is not None
        ),
        "NCU report hash is invalid",
    )
    toolchain = _STRICT.object(report["toolchain"], TOOLCHAIN_KEYS, "counter toolchain")
    _require(
        type(toolchain["nsight_compute_version"]) is str
        and toolchain["nsight_compute_version"].startswith("2025.3.1.0 "),
        "Nsight Compute version drifted",
    )
    _STRICT.exact_members(toolchain, EXPECTED_TOOLCHAIN, "counter toolchain")
    _STRICT.exact_integer(toolchain["launch_count_limit"], launch_count, "launch count limit")
    _STRICT.exact_list(
        toolchain["command_template"], command_template(launch_count), "command template"
    )
    capture = _STRICT.object(report["capture"], CAPTURE_KEYS, "counter capture")
    _STRICT.exact_members(capture, EXPECTED_CAPTURE, "counter capture")
    interpretation = _STRICT.object(
        report["interpretation"], INTERPRETATION_KEYS, "counter interpretation"
    )
    _require(all(value is True for value in interpretation.values()), "interpretation weakened")
    attempt = _STRICT.object(report["attempt"], ATTEMPT_KEYS, "counter attempt")
    status = attempt["status"]
    _require(
        type(status) is str and status in {"available", "external_blocked", "collection_failed"},
        "attempt status is invalid",
    )
    exit_code = _STRICT.integer(attempt["exit_code"], "attempt exit code")
    _STRICT.boolean(attempt["application_completed"], "application completed", True)
    connected_pid = _STRICT.positive_integer(attempt["connected_pid"], "connected PID")
    disconnected_pid = _STRICT.positive_integer(attempt["disconnected_pid"], "disconnected PID")
    _require(disconnected_pid == connected_pid, "profiled process lifecycle is invalid")
    report_created = _STRICT.boolean(attempt["report_created"], "report created")
    _STRICT.exact_integer(attempt["required_launch_count"], launch_count, "required launch count")
    error_codes = _STRICT.list(attempt["log_error_codes"], "log error code inventory")
    _require(
        all(type(code) is str and code for code in error_codes),
        "log error code inventory is invalid",
    )
    if status == "available":
        _require(exit_code == 0, "available evidence requires exit code zero")
        _require(report_created is True, "available evidence requires an NCU report")
        _STRICT.exact_integer(
            attempt["collected_launch_count"],
            launch_count,
            "available collected launch count",
        )
        for field in ("blocker_code", "blocker_kind", "recognized_error_line_sha256"):
            _require(attempt[field] is None, f"available attempt must clear {field}")
        _STRICT.exact_list(error_codes, (), "available log errors")
        _require(inputs["ncu_report_sha256"] is not None, "available report hash is missing")
    elif status == "external_blocked":
        _require(exit_code != 0, "blocked evidence cannot have exit code zero")
        _require(report_created is False, "blocked evidence cannot claim a report")
        _STRICT.exact_integer(
            attempt["collected_launch_count"], 0, "blocked collected launch count"
        )
        _STRICT.exact_scalar(attempt["blocker_code"], PERMISSION_CODE, "permission blocker code")
        _STRICT.exact_scalar(
            attempt["blocker_kind"], "external_permission", "permission blocker kind"
        )
        _STRICT.exact_list(error_codes, (PERMISSION_CODE,), "permission attempt errors")
        _require(
            type(attempt["recognized_error_line_sha256"]) is str
            and re.fullmatch(r"[0-9a-f]{64}", attempt["recognized_error_line_sha256"]) is not None,
            "permission error provenance is missing",
        )
        _require(inputs["ncu_report_sha256"] is None, "blocked attempt cannot hash an NCU report")
    else:
        _require(exit_code != 0, "failed collection cannot have exit code zero")
        _STRICT.exact_integer(attempt["collected_launch_count"], 0, "failed collected launch count")
        for field in ("blocker_code", "blocker_kind", "recognized_error_line_sha256"):
            _require(attempt[field] is None, f"generic failure must clear {field}")
    _validate_families(status, report["achieved_counters"], generation)
    gates = _STRICT.object(report["gates"], GATE_KEYS, "counter gates")
    expected_gate = status == "available"
    _STRICT.boolean(gates["cr2_5a_static_resource_complete"], "static resource gate", True)
    _STRICT.boolean(gates["cr2_5a_launch_topology_complete"], "launch topology gate", True)
    _STRICT.boolean(
        gates["cr2_5b_counter_attempt_complete"],
        "counter attempt gate",
        status != "collection_failed",
    )
    _STRICT.boolean(
        gates["cr2_5_achieved_counter_gate_complete"], "achieved counter gate", expected_gate
    )
    dispositions = {
        "available": "achieved_counter_evidence_complete",
        "external_blocked": "documented_external_blocker",
        "collection_failed": "collection_failed",
    }
    _STRICT.exact_scalar(gates["cr2_5_disposition"], dispositions[status], "CR2-5 disposition")
    for flag in (
        "maintained_claim_allowed",
        "public_support_enabled",
        "promotion_allowed",
        "tuning_authorized",
    ):
        _STRICT.boolean(gates[flag], flag, False)


def validate_parent_link(
    parent: dict[str, Any],
    binary_sha256: str,
    probe_sha256: str,
    counter_report: dict[str, Any] | None = None,
) -> None:
    resource.validate_report(parent)
    _generation_of(parent["profile_id"], "parent resource profile")
    _require(
        parent["inputs"]["binary_sha256"] == binary_sha256,
        "binary differs from the parent resource evidence",
    )
    _require(
        parent["inputs"]["probe_sha256"] == probe_sha256,
        "probe output differs from the parent resource evidence",
    )
    # A report claiming another generation than its hashed parent dies here.
    if counter_report is not None:
        _require(
            counter_report.get("profile_id") == parent["profile_id"],
            "counter evidence generation differs from its parent resource evidence",
        )


def validate_report_pair(report: dict[str, Any], parent_bytes: bytes) -> None:
    """Complete, non-optional binding of a counter report to its parent bytes.

    validate_report alone cannot see the parent, so relabeled generations or
    swapped parents are only detectable here: the parent bytes must hash to
    what the report recorded, and the generation and capture hashes must agree.
    """
    validate_report(report)
    _require(
        _bytes_sha256(parent_bytes) == report["inputs"]["resource_evidence_sha256"],
        "parent resource evidence bytes differ from the hash the report records",
    )
    parent = json.loads(parent_bytes.decode("utf-8"), object_pairs_hook=_unique_object)
    _require(isinstance(parent, dict), "parent resource evidence root must be an object")
    validate_parent_link(
        parent,
        report["inputs"]["binary_sha256"],
        report["inputs"]["probe_output_sha256"],
        counter_report=report,
    )


def _validated_inputs(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    _require(
        args.baseline_commit == _git_head(args.contract_source), "baseline does not match HEAD"
    )
    probe = resource.load_probe(args.probe_output)
    parent = load_json(args.resource_evidence)
    validate_parent_link(parent, _sha256(args.binary), _sha256(args.probe_output))
    return probe, parent


def _parent_generation(args: argparse.Namespace) -> int:
    # Launch budget and report shape follow the declared parent generation;
    # the full parent validation still happens in build_report.
    parent = load_json(args.resource_evidence)
    return _generation_of(parent.get("profile_id"), "parent resource profile")


def _command(
    ncu: Path, binary: Path, raw_dir: Path, launch_count: int
) -> tuple[list[str], Path, Path, Path]:
    report_base = raw_dir / "full-window-256"
    attempt_log = raw_dir / "attempt.log"
    probe_output = raw_dir / "probe-output.json"
    argv = [
        str(ncu.resolve()),
        "--target-processes",
        "application-only",
        "--profile-from-start",
        "off",
        "--replay-mode",
        "kernel",
        "--kernel-name-base",
        "demangled",
        "--set",
        "full",
        "--launch-count",
        str(launch_count),
        "--force-overwrite",
        "--export",
        str(report_base),
        "--log-file",
        str(attempt_log),
        str(binary.resolve()),
        "--output",
        str(probe_output),
    ]
    return argv, report_base.with_suffix(".ncu-rep"), attempt_log, probe_output


def execute_attempt(
    args: argparse.Namespace,
) -> tuple[subprocess.CompletedProcess[bytes], list[str]]:
    _require(not args.raw_dir.exists(), "raw attempt directory must be fresh")
    args.raw_dir.mkdir(parents=True)
    launch_count = required_launch_count(_parent_generation(args))
    argv, _, _, _ = _command(args.ncu, args.binary, args.raw_dir, launch_count)
    completed = subprocess.run(argv, cwd=args.working_directory, capture_output=True)
    return completed, argv


def build_report(
    args: argparse.Namespace,
    completed: subprocess.CompletedProcess[bytes],
    argv: list[str],
    version: str,
) -> dict[str, Any]:
    generation = _parent_generation(args)
    launch_count = required_launch_count(generation)
    _, ncu_report, attempt_log, probe_output = _command(
        args.ncu, args.binary, args.raw_dir, launch_count
    )
    _require(attempt_log.is_file(), "Nsight Compute attempt log is missing")
    _require(probe_output.is_file(), "profile application did not write its probe output")
    args.probe_output = probe_output
    probe, parent = _validated_inputs(args)
    parsed = parse_attempt_log(attempt_log.read_text(encoding="utf-8", errors="replace"))
    connected = parsed["connected_pids"]
    disconnected = parsed["disconnected_pids"]
    _require(
        len(connected) == 1 and disconnected == connected, "profiler process lifecycle drifted"
    )
    if completed.returncode == 0:
        _require(ncu_report.exists(), "NCU reported success without writing a report")
        _require(
            not parsed["permission_denied"],
            "NCU reported success but the log still contains a permission denial",
        )
        counters = parse_counter_csv(
            export_counter_csv(args.ncu, ncu_report),
            resource.probe_generation(probe),
        )
        status = "available"
        collected_launch_count = launch_count
        achieved_counters = counters["families"]
        blocker_code = None
        blocker_kind = None
        error_hash = None
    else:
        external = parsed["permission_denied"] and not ncu_report.exists()
        status = "external_blocked" if external else "collection_failed"
        collected_launch_count = 0
        achieved_counters = empty_counter_families(generation)
        blocker_code = PERMISSION_CODE if external else None
        blocker_kind = "external_permission" if external else None
        error_hash = parsed["permission_line_sha256"] if external else None
    attempt = {
        "status": status,
        "exit_code": completed.returncode,
        "connected_pid": connected[0],
        "disconnected_pid": disconnected[0],
        "application_completed": True,
        "report_created": ncu_report.exists(),
        "blocker_code": blocker_code,
        "blocker_kind": blocker_kind,
        "required_launch_count": launch_count,
        "collected_launch_count": collected_launch_count,
        "log_error_codes": parsed["error_codes"],
        "recognized_error_line_sha256": error_hash,
    }
    dispositions = {
        "available": "achieved_counter_evidence_complete",
        "external_blocked": "documented_external_blocker",
        "collection_failed": "collection_failed",
    }
    report = {
        "schema_version": SCHEMA,
        # Inherit the parent resource capture's identity rather than hardcoding
        # v1: a counter capture describes the same profile as the static capture
        # it links to, and stamping v1 onto a v2 capture misreports provenance.
        "profile_id": parent["profile_id"],
        "evidence_date": args.evidence_date,
        "source": {
            "baseline_commit": args.baseline_commit,
            "candidate_state": "cr2_5b_unpromoted_worktree",
        },
        "inputs": {
            "source_hash_canonicalization": "utf8_lf",
            "ncu_executable_sha256": _sha256(args.ncu),
            "binary_sha256": _sha256(args.binary),
            "probe_output_sha256": _sha256(probe_output),
            "resource_evidence_sha256": _sha256(args.resource_evidence),
            "attempt_log_sha256": _sha256(attempt_log),
            "ncu_report_sha256": _sha256(ncu_report) if ncu_report.exists() else None,
            "launcher_stdout_sha256": _bytes_sha256(completed.stdout),
            "launcher_stderr_sha256": _bytes_sha256(completed.stderr),
            "command_argv_sha256": _argv_sha256(argv),
            "collector_source_sha256": resource.source_sha256(Path(__file__)),
            "contract_source_sha256": resource.source_sha256(args.contract_source),
        },
        "toolchain": {
            "nsight_compute_version": version,
            "target_processes": "application-only",
            "profile_from_start": False,
            "replay_mode": "kernel",
            "kernel_name_base": "demangled",
            "counter_set": "full",
            "launch_count_limit": launch_count,
            "command_paths": "absolute_paths_hashed_and_redacted",
            "command_template": list(command_template(launch_count)),
        },
        "capture": {
            "range": probe["capture"]["range"],
            "world_count": probe["world_count"],
            "window_count": probe["window_count"],
            "build_config": probe["build_config"],
            "cuda_architecture": probe["cuda_architecture"],
            "trace_signature_algorithm": probe["trace_signature_algorithm"],
            "trace_signature_digest": probe["trace_signature_digest"],
            "consumer_await_completed": probe["result"]["consumer_await_completed"],
            "diagnostic_materialization_called": probe["result"][
                "diagnostic_materialization_called"
            ],
        },
        "attempt": attempt,
        "achieved_counters": achieved_counters,
        "interpretation": {
            "cr2_5a_resource_evidence_validated": True,
            "theoretical_occupancy_is_not_achieved_occupancy": True,
            "nsys_launch_metadata_is_not_an_achieved_counter": True,
            "missing_counters_are_not_zero": True,
            "external_permission_is_not_a_kernel_result": True,
        },
        "gates": {
            "cr2_5a_static_resource_complete": parent["gates"]["cr2_5a_static_resource_complete"],
            "cr2_5a_launch_topology_complete": parent["gates"]["cr2_5a_launch_topology_complete"],
            "cr2_5b_counter_attempt_complete": status in {"available", "external_blocked"},
            "cr2_5_achieved_counter_gate_complete": status == "available",
            "cr2_5_disposition": dispositions[status],
            # Collecting counters closes a measurement gate. It does not grant
            # promotion, maintained support, or tuning authority: those need a
            # separate recorded decision with an independent review.
            "maintained_claim_allowed": False,
            "public_support_enabled": False,
            "promotion_allowed": False,
            "tuning_authorized": False,
        },
    }
    validate_report(report)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture fail-closed CR2-5b NCU evidence")
    parser.add_argument("--ncu", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--resource-evidence", type=Path, required=True)
    parser.add_argument("--contract-source", type=Path, required=True)
    parser.add_argument("--baseline-commit", required=True)
    parser.add_argument("--evidence-date", required=True)
    parser.add_argument("--working-directory", type=Path, required=True)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    _require(re.fullmatch(r"[0-9a-f]{40}", args.baseline_commit) is not None, "invalid commit")
    _require(args.ncu.is_file(), "Nsight Compute executable is missing")
    _require(args.binary.is_file(), "resource probe binary is missing")
    version = ncu_version(args.ncu)
    completed, argv = execute_attempt(args)
    report = build_report(args, completed, argv, version)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
