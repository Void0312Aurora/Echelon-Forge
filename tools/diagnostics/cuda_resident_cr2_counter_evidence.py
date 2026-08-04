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
else:
    import cuda_resident_cr2_resource_evidence as resource  # type: ignore[no-redef]


SCHEMA = "cuda_resident.cr2.achieved_counter_evidence.v1"
PROFILE = resource.PROFILE
PERMISSION_CODE = "ERR_NVGPUCTRPERM"
REQUIRED_LAUNCH_COUNT = 12
COUNTER_FAMILIES = {
    "achieved_occupancy": "ratio",
    "branch_divergence": "ratio",
    "global_memory_traffic": "bytes",
    "local_memory_traffic": "bytes",
    "shared_memory_traffic": "bytes",
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


def parse_attempt_log(text: str) -> dict[str, Any]:
    connected = re.findall(r"^==PROF== Connected to process (\d+) ", text, flags=re.MULTILINE)
    disconnected = re.findall(
        r"^==PROF== Disconnected from process (\d+)\s*$", text, flags=re.MULTILINE
    )
    error_lines = re.findall(r"^==ERROR== ([^\r\n]+)$", text, flags=re.MULTILINE)
    error_codes: list[str] = []
    for line in error_lines:
        match = re.match(r"([A-Z][A-Z0-9_]+)\b", line)
        _require(match is not None, "Nsight Compute error line has no stable code")
        error_codes.append(match.group(1))
    permission_lines = [line for line in error_lines if line.startswith(f"{PERMISSION_CODE} ")]
    permission_message = "does not have permission to access NVIDIA GPU Performance Counters"
    permission_denied = (
        len(permission_lines) == 1
        and permission_message in permission_lines[0]
        and error_codes == [PERMISSION_CODE]
    )
    return {
        "connected_pids": [int(value) for value in connected],
        "disconnected_pids": [int(value) for value in disconnected],
        "error_codes": error_codes,
        "permission_denied": permission_denied,
        "permission_line_sha256": (
            hashlib.sha256(permission_lines[0].encode("utf-8")).hexdigest()
            if permission_denied
            else None
        ),
    }


def _empty_counter_families() -> dict[str, dict[str, Any]]:
    return {
        family: {
            "unit": unit,
            "provenance": None,
            "metric_names": None,
            "values_by_launch": None,
        }
        for family, unit in COUNTER_FAMILIES.items()
    }


def _validate_families(status: str, families: object) -> None:
    _require(isinstance(families, dict), "counter families must be an object")
    _require(set(families) == set(COUNTER_FAMILIES), "counter family inventory drifted")
    for family, unit in COUNTER_FAMILIES.items():
        row = families[family]
        _require(isinstance(row, dict) and set(row) == FAMILY_KEYS, f"{family} schema drifted")
        _require(row["unit"] == unit, f"{family} unit drifted")
        if status != "available":
            for field in ("provenance", "metric_names", "values_by_launch"):
                _require(row[field] is None, f"unavailable {family}.{field} must remain null")
            continue
        _require(
            row["provenance"] == "nsight_compute_hardware_counter",
            f"{family} has non-hardware provenance",
        )
        names = row["metric_names"]
        _require(
            isinstance(names, list)
            and bool(names)
            and all(isinstance(name, str) and name for name in names)
            and len(names) == len(set(names)),
            f"{family} metric names are incomplete",
        )
        values = row["values_by_launch"]
        _require(
            isinstance(values, list) and len(values) == REQUIRED_LAUNCH_COUNT,
            f"{family} must contain all launch values",
        )
        for value in values:
            _require(
                isinstance(value, (int, float))
                and not isinstance(value, bool)
                and math.isfinite(value)
                and value >= 0,
                f"{family} contains an invalid achieved value",
            )
            if unit == "ratio":
                _require(value <= 1.0, f"{family} ratio exceeds one")


def validate_report(report: dict[str, Any]) -> None:
    _require(set(report) == TOP_LEVEL_KEYS, "counter evidence top-level keys drifted")
    _require(report["schema_version"] == SCHEMA, "counter evidence schema mismatch")
    _require(report["profile_id"] == PROFILE, "counter evidence profile mismatch")
    _require(
        isinstance(report["evidence_date"], str)
        and re.fullmatch(r"\d{4}-\d{2}-\d{2}", report["evidence_date"]) is not None,
        "evidence date is invalid",
    )
    source = report["source"]
    _require(
        isinstance(source, dict) and set(source) == {"baseline_commit", "candidate_state"},
        "counter evidence source schema drifted",
    )
    _require(
        re.fullmatch(r"[0-9a-f]{40}", source["baseline_commit"]) is not None,
        "baseline commit is invalid",
    )
    _require(
        source["candidate_state"] == "cr2_5b_unpromoted_worktree",
        "candidate state drifted",
    )
    inputs = report["inputs"]
    _require(isinstance(inputs, dict) and set(inputs) == INPUT_KEYS, "input schema drifted")
    _require(inputs["source_hash_canonicalization"] == "utf8_lf", "source hash mode drifted")
    for key in INPUT_KEYS - {"source_hash_canonicalization", "ncu_report_sha256"}:
        _require(
            re.fullmatch(r"[0-9a-f]{64}", inputs[key]) is not None,
            f"{key} is not a SHA-256 digest",
        )
    _require(
        inputs["ncu_report_sha256"] is None
        or re.fullmatch(r"[0-9a-f]{64}", inputs["ncu_report_sha256"]) is not None,
        "NCU report hash is invalid",
    )
    toolchain = report["toolchain"]
    _require(
        isinstance(toolchain, dict) and set(toolchain) == TOOLCHAIN_KEYS,
        "toolchain schema drifted",
    )
    _require(
        isinstance(toolchain["nsight_compute_version"], str)
        and toolchain["nsight_compute_version"].startswith("2025.3.1.0 "),
        "Nsight Compute version drifted",
    )
    expected_toolchain = {
        "target_processes": "application-only",
        "profile_from_start": False,
        "replay_mode": "kernel",
        "kernel_name_base": "demangled",
        "counter_set": "full",
        "launch_count_limit": REQUIRED_LAUNCH_COUNT,
        "command_paths": "absolute_paths_hashed_and_redacted",
    }
    for key, value in expected_toolchain.items():
        _require(toolchain[key] == value, f"toolchain option drifted: {key}")
    _require(
        isinstance(toolchain["command_template"], list)
        and len(toolchain["command_template"]) == 12,
        "command template drifted",
    )
    capture = report["capture"]
    _require(isinstance(capture, dict) and set(capture) == CAPTURE_KEYS, "capture schema drifted")
    expected_capture = {
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
    _require(capture == expected_capture, "capture facts drifted")
    interpretation = report["interpretation"]
    _require(
        isinstance(interpretation, dict) and set(interpretation) == INTERPRETATION_KEYS,
        "interpretation schema drifted",
    )
    _require(all(value is True for value in interpretation.values()), "interpretation weakened")
    attempt = report["attempt"]
    _require(isinstance(attempt, dict) and set(attempt) == ATTEMPT_KEYS, "attempt schema drifted")
    status = attempt["status"]
    _require(
        status in {"available", "external_blocked", "collection_failed"},
        "attempt status is invalid",
    )
    _require(
        isinstance(attempt["exit_code"], int) and not isinstance(attempt["exit_code"], bool),
        "attempt exit code is invalid",
    )
    _require(attempt["application_completed"] is True, "profile application did not complete")
    _require(
        isinstance(attempt["connected_pid"], int)
        and attempt["connected_pid"] > 0
        and attempt["disconnected_pid"] == attempt["connected_pid"],
        "profiled process lifecycle is invalid",
    )
    _require(isinstance(attempt["report_created"], bool), "report-created flag is invalid")
    _require(
        attempt["required_launch_count"] == REQUIRED_LAUNCH_COUNT,
        "required launch count drifted",
    )
    _require(
        isinstance(attempt["log_error_codes"], list)
        and all(isinstance(code, str) and code for code in attempt["log_error_codes"]),
        "log error code inventory is invalid",
    )
    if status == "available":
        _require(attempt["exit_code"] == 0, "available evidence requires exit code zero")
        _require(attempt["report_created"] is True, "available evidence requires an NCU report")
        _require(
            attempt["collected_launch_count"] == REQUIRED_LAUNCH_COUNT,
            "available evidence requires all launch counters",
        )
        for field in ("blocker_code", "blocker_kind", "recognized_error_line_sha256"):
            _require(attempt[field] is None, f"available attempt must clear {field}")
        _require(attempt["log_error_codes"] == [], "available attempt contains profiler errors")
        _require(inputs["ncu_report_sha256"] is not None, "available report hash is missing")
    elif status == "external_blocked":
        _require(attempt["exit_code"] != 0, "blocked evidence cannot have exit code zero")
        _require(attempt["report_created"] is False, "blocked evidence cannot claim a report")
        _require(attempt["collected_launch_count"] == 0, "blocked counters cannot claim launches")
        _require(attempt["blocker_code"] == PERMISSION_CODE, "permission blocker code drifted")
        _require(
            attempt["blocker_kind"] == "external_permission",
            "permission blocker kind drifted",
        )
        _require(
            attempt["log_error_codes"] == [PERMISSION_CODE],
            "permission attempt contains a different profiler error",
        )
        _require(
            re.fullmatch(r"[0-9a-f]{64}", attempt["recognized_error_line_sha256"]) is not None,
            "permission error provenance is missing",
        )
        _require(inputs["ncu_report_sha256"] is None, "blocked attempt cannot hash an NCU report")
    else:
        _require(attempt["exit_code"] != 0, "failed collection cannot have exit code zero")
        _require(attempt["collected_launch_count"] == 0, "failed collection cannot claim launches")
        for field in ("blocker_code", "blocker_kind", "recognized_error_line_sha256"):
            _require(attempt[field] is None, f"generic failure must clear {field}")
    _validate_families(status, report["achieved_counters"])
    gates = report["gates"]
    _require(isinstance(gates, dict) and set(gates) == GATE_KEYS, "counter gate schema drifted")
    expected_gate = status == "available"
    _require(
        gates.get("cr2_5a_static_resource_complete") is True,
        "CR2-5a static resource gate regressed",
    )
    _require(
        gates.get("cr2_5a_launch_topology_complete") is True,
        "CR2-5a launch topology gate regressed",
    )
    _require(
        gates.get("cr2_5b_counter_attempt_complete") is (status != "collection_failed"),
        "counter-attempt gate contradicts status",
    )
    _require(
        gates.get("cr2_5_achieved_counter_gate_complete") is expected_gate,
        "achieved-counter gate contradicts status",
    )
    dispositions = {
        "available": "achieved_counter_evidence_complete",
        "external_blocked": "documented_external_blocker",
        "collection_failed": "collection_failed",
    }
    _require(gates.get("cr2_5_disposition") == dispositions[status], "CR2-5 disposition drifted")
    for flag in (
        "maintained_claim_allowed",
        "public_support_enabled",
        "promotion_allowed",
        "tuning_authorized",
    ):
        _require(gates.get(flag) is False, f"CR2-5b must keep {flag}=false")


def validate_parent_link(parent: dict[str, Any], binary_sha256: str, probe_sha256: str) -> None:
    resource.validate_report(parent)
    _require(parent["profile_id"] == PROFILE, "CR2-5a profile drifted")
    _require(
        parent["inputs"]["binary_sha256"] == binary_sha256,
        "binary differs from CR2-5a resource evidence",
    )
    _require(
        parent["inputs"]["probe_sha256"] == probe_sha256,
        "probe output differs from CR2-5a resource evidence",
    )


def _validated_inputs(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    _require(
        args.baseline_commit == _git_head(args.contract_source), "baseline does not match HEAD"
    )
    probe = resource.load_probe(args.probe_output)
    parent = load_json(args.resource_evidence)
    validate_parent_link(parent, _sha256(args.binary), _sha256(args.probe_output))
    return probe, parent


def _command(ncu: Path, binary: Path, raw_dir: Path) -> tuple[list[str], Path, Path, Path]:
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
        str(REQUIRED_LAUNCH_COUNT),
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
    argv, _, _, _ = _command(args.ncu, args.binary, args.raw_dir)
    completed = subprocess.run(argv, cwd=args.working_directory, capture_output=True)
    return completed, argv


def build_report(
    args: argparse.Namespace,
    completed: subprocess.CompletedProcess[bytes],
    argv: list[str],
    version: str,
) -> dict[str, Any]:
    _, ncu_report, attempt_log, probe_output = _command(args.ncu, args.binary, args.raw_dir)
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
        raise CounterEvidenceError(
            "NCU completed successfully; a reviewed hardware-counter report parser is required"
        )
    external = parsed["permission_denied"] and not ncu_report.exists()
    status = "external_blocked" if external else "collection_failed"
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
        "required_launch_count": REQUIRED_LAUNCH_COUNT,
        "collected_launch_count": 0,
        "log_error_codes": parsed["error_codes"],
        "recognized_error_line_sha256": error_hash,
    }
    dispositions = {
        "external_blocked": "documented_external_blocker",
        "collection_failed": "collection_failed",
    }
    report = {
        "schema_version": SCHEMA,
        "profile_id": PROFILE,
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
            "launch_count_limit": REQUIRED_LAUNCH_COUNT,
            "command_paths": "absolute_paths_hashed_and_redacted",
            "command_template": [
                "ncu",
                "--target-processes=application-only",
                "--profile-from-start=off",
                "--replay-mode=kernel",
                "--kernel-name-base=demangled",
                "--set=full",
                "--launch-count=12",
                "--force-overwrite",
                "--export=<raw>/full-window-256",
                "--log-file=<raw>/attempt.log",
                "<resource-probe>",
                "--output=<raw>/probe-output.json",
            ],
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
        "achieved_counters": _empty_counter_families(),
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
            "cr2_5b_counter_attempt_complete": status == "external_blocked",
            "cr2_5_achieved_counter_gate_complete": False,
            "cr2_5_disposition": dispositions[status],
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
