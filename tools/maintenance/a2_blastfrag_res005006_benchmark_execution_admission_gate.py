#!/usr/bin/env python3
"""Generate a fail-closed RES-005/006 benchmark execution/admission gate.

This gate consumes the existing hash-only mechanism comparison evidence and
tries to strengthen it with local spreadsheet execution evidence. It does not
copy TP-21 prose/tables, expose selected spreadsheet raw values, consume any
benchmark for release, or grant authority.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
from zipfile import BadZipFile, ZipFile
import xml.etree.ElementTree as ET


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import (  # noqa: E402
    a2_blastfrag_mechanism_comparison_hashes as comparison_hashes,
)


PACKAGE_ID = comparison_hashes.PACKAGE_ID
SCHEMA_VERSION = "a2.res005006_benchmark_execution_admission_gate.v1"
RETAINED_MANIFEST_SCHEMA_VERSION = (
    "a2.res005006_benchmark_execution_admission_retained_manifest.v1"
)

PACKAGE_DIR = comparison_hashes.PACKAGE_DIR
SOURCE_PAYLOAD_PACK_DIR = comparison_hashes.SOURCE_PAYLOAD_PACK_DIR
MECHANISM_COMPARISON_HASHES_DIR = comparison_hashes.DEFAULT_RETAINED_DIR
DEFAULT_RETAINED_DIR = (
    PACKAGE_DIR
    / "retained_artifacts"
    / "res005006_benchmark_execution_admission_20260531"
)

GATE_FILENAME = "benchmark_execution_admission_gate.json"
RETAINED_MANIFEST_FILENAME = "manifest.json"

PYTHON_TOOL_MODULES = {
    "openpyxl": {
        "role": "xlsx_parser_cached_values_only",
        "spreadsheet_execution_capable": False,
    },
    "pandas": {
        "role": "tabular_parser_no_xlsx_formula_engine",
        "spreadsheet_execution_capable": False,
    },
    "pyoo": {
        "role": "libreoffice_bridge_requires_running_office",
        "spreadsheet_execution_capable": False,
    },
    "uno": {
        "role": "libreoffice_python_bridge_environment_dependent",
        "spreadsheet_execution_capable": False,
    },
    "calamine": {
        "role": "xlsx_parser_no_formula_execution",
        "spreadsheet_execution_capable": False,
    },
}

SPREADSHEET_EXECUTION_TIMEOUT_SECONDS = 90


def _rel(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def _command_result_hashes(result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    return {
        "returncode": result.returncode,
        "stdout_present": bool(result.stdout),
        "stderr_present": bool(result.stderr),
        "stdout_retained": False,
        "stderr_retained": False,
    }


def _version_for_executable(path: str) -> dict[str, Any]:
    try:
        result = subprocess.run(
            [path, "--version"],
            check=False,
            text=True,
            capture_output=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "version_probe_status": "failed",
            "version_probe_error": type(exc).__name__,
        }
    output = (result.stdout or result.stderr or "").strip().splitlines()
    return {
        "version_probe_status": "ok" if result.returncode == 0 else "failed",
        "version_probe_returncode": result.returncode,
        "version_string": output[0] if output else "",
    }


def detect_execution_tooling() -> dict[str, Any]:
    office_candidates: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    for name in ("libreoffice", "soffice"):
        path = shutil.which(name)
        if not path:
            office_candidates.append(
                {
                    "tool": name,
                    "available": False,
                    "spreadsheet_execution_capable": False,
                    "missing_reason": f"{name}_executable_not_found_on_path",
                }
            )
            continue
        if path in seen_paths:
            continue
        seen_paths.add(path)
        version = _version_for_executable(path)
        office_candidates.append(
            {
                "tool": name,
                "available": True,
                "path": path,
                "headless_mode_supported_by_probe": (
                    version.get("version_probe_status") == "ok"
                ),
                "spreadsheet_execution_capable": (
                    version.get("version_probe_status") == "ok"
                ),
                **version,
            }
        )

    python_modules = [
        {
            "module": module,
            "available": importlib.util.find_spec(module) is not None,
            **details,
        }
        for module, details in PYTHON_TOOL_MODULES.items()
    ]
    selected_office = next(
        (
            row
            for row in office_candidates
            if row.get("available") and row.get("spreadsheet_execution_capable")
        ),
        None,
    )
    blockers = []
    if selected_office is None:
        blockers.append(
            "missing executable/tooling blocker: neither libreoffice nor soffice "
            "was found as a working headless spreadsheet execution tool"
        )
    return {
        "tool_detection_status": (
            "spreadsheet_execution_tool_available"
            if selected_office
            else "spreadsheet_execution_tool_missing"
        ),
        "selected_spreadsheet_executor": selected_office,
        "office_candidates": office_candidates,
        "python_library_candidates": python_modules,
        "missing_execution_tooling_blockers": blockers,
        "dependency_install_attempted": False,
        "network_fetch_attempted": False,
    }


def _selected_hashes_from_workbook(
    *,
    workbook_path: Path,
    source_workbook_sha256: str,
) -> dict[str, Any]:
    try:
        with ZipFile(workbook_path) as zip_file:
            _, sheet_paths = comparison_hashes._sheet_records(zip_file)
            selected_hashes = []
            for selection in comparison_hashes.BECO_SELECTED_OUTPUTS:
                sheet_path = sheet_paths.get(selection["sheet"], "")
                cell_record = (
                    comparison_hashes._cell_record(
                        zip_file,
                        sheet_path,
                        selection["cell"],
                    )
                    if sheet_path
                    else {"exists": "false", "formula": "", "value": "", "type": ""}
                )
                row = comparison_hashes._selected_output_hash_record(
                    workbook_sha256=source_workbook_sha256,
                    selection=selection,
                    cell_record=cell_record,
                )
                row["calculation_source"] = (
                    "headless_spreadsheet_reopen_recalculate_copy"
                )
                selected_hashes.append(row)
    except (BadZipFile, ET.ParseError) as exc:
        return {
            "parse_status": "recalculated_workbook_unreadable_fail_closed",
            "parse_error": type(exc).__name__,
            "selected_recalculated_hashes": [],
        }
    selected_output_set = [
        {
            "comparison_id": row["comparison_id"],
            "sheet": row["sheet"],
            "cell": row["cell"],
            "output_role": row["output_role"],
            "comparison_output_sha256": row["comparison_output_sha256"],
        }
        for row in selected_hashes
        if row["comparison_output_sha256"]
    ]
    return {
        "parse_status": "recalculated_workbook_selected_hashes_retained",
        "selected_recalculated_hashes": selected_hashes,
        "selected_recalculated_output_count": len(selected_output_set),
        "selected_recalculated_output_set_sha256": _sha256_text(
            _canonical_json(selected_output_set)
        ),
    }


def _attempt_libo_recalculation(
    *,
    executable: str,
    workbook_path: Path,
    workbook_sha256: str,
    retained_dir: Path,
) -> dict[str, Any]:
    if not workbook_path.exists():
        return {
            "attempted": False,
            "execution_status": "blocked_fail_closed_workbook_missing",
            "blocking_reason": "retained BEC-O workbook is missing",
        }
    try:
        with tempfile.TemporaryDirectory(
            prefix="beco_recalc_",
            dir=retained_dir,
        ) as scratch_name:
            scratch = Path(scratch_name)
            input_dir = scratch / "input"
            output_dir = scratch / "output"
            profile_dir = scratch / "lo_profile"
            input_dir.mkdir()
            output_dir.mkdir()
            profile_dir.mkdir()
            input_path = input_dir / workbook_path.name
            shutil.copy2(workbook_path, input_path)
            command = [
                executable,
                "--headless",
                f"-env:UserInstallation={profile_dir.as_uri()}",
                "--convert-to",
                "xlsx",
                "--outdir",
                str(output_dir),
                str(input_path),
            ]
            result = subprocess.run(
                command,
                check=False,
                text=True,
                capture_output=True,
                timeout=SPREADSHEET_EXECUTION_TIMEOUT_SECONDS,
            )
            output_path = output_dir / workbook_path.name
            if result.returncode != 0 or not output_path.exists():
                return {
                    "attempted": True,
                    "execution_status": "blocked_fail_closed_reopen_recalculate_failed",
                    "executor": executable,
                    "command_form": (
                        "libreoffice --headless -env:UserInstallation=<scratch> "
                        "--convert-to xlsx --outdir <scratch> <workbook_copy>"
                    ),
                    "command_result": _command_result_hashes(result),
                    "blocking_reason": (
                        "headless spreadsheet conversion did not produce a "
                        "recalculated workbook copy"
                    ),
                }
            parsed = _selected_hashes_from_workbook(
                workbook_path=output_path,
                source_workbook_sha256=workbook_sha256,
            )
            return {
                "attempted": True,
                "execution_status": (
                    "reopen_recalculate_completed_hash_only_outputs_retained"
                ),
                "executor": executable,
                "command_form": (
                    "libreoffice --headless -env:UserInstallation=<scratch> "
                    "--convert-to xlsx --outdir <scratch> <workbook_copy>"
                ),
                "command_result": _command_result_hashes(result),
                "raw_values_retained": False,
                "temporary_workbook_copy_retained": False,
                **parsed,
            }
    except subprocess.TimeoutExpired as exc:
        return {
            "attempted": True,
            "execution_status": "blocked_fail_closed_reopen_recalculate_timeout",
            "executor": executable,
            "timeout_seconds": SPREADSHEET_EXECUTION_TIMEOUT_SECONDS,
            "blocking_reason": f"headless spreadsheet execution timed out: {type(exc).__name__}",
        }
    except OSError as exc:
        return {
            "attempted": True,
            "execution_status": "blocked_fail_closed_reopen_recalculate_os_error",
            "executor": executable,
            "blocking_reason": f"headless spreadsheet execution failed: {type(exc).__name__}",
        }


def _beco_execution_gate(
    *,
    mechanism_artifact: dict[str, Any],
    tooling: dict[str, Any],
    retained_dir: Path,
) -> dict[str, Any]:
    beco = mechanism_artifact["beco_workbook"]
    cached_by_id = {
        row["comparison_id"]: row
        for row in beco.get("selected_comparison_hashes", [])
    }
    selected_executor = tooling.get("selected_spreadsheet_executor")
    if not selected_executor:
        return {
            "residual_id": "RES-006",
            "gate_status": "blocked_fail_closed_beco_execution_tool_missing",
            "spreadsheet_execution_attempted": False,
            "spreadsheet_recalculation_admitted": False,
            "cached_hash_anchor_count": len(cached_by_id),
            "selected_recalculated_hash_count": 0,
            "selected_hashes_match_cached_anchors": False,
            "exact_blocker": tooling["missing_execution_tooling_blockers"][0],
        }

    workbook_path = REPO_ROOT / beco["relative_path"]
    attempt = _attempt_libo_recalculation(
        executable=selected_executor["path"],
        workbook_path=workbook_path,
        workbook_sha256=beco["workbook_sha256"],
        retained_dir=retained_dir,
    )
    recalculated_by_id = {
        row["comparison_id"]: row
        for row in attempt.get("selected_recalculated_hashes", [])
    }
    comparisons: list[dict[str, Any]] = []
    mismatch_ids: list[str] = []
    missing_ids: list[str] = []
    for selection in comparison_hashes.BECO_SELECTED_OUTPUTS:
        comparison_id = selection["comparison_id"]
        cached = cached_by_id.get(comparison_id, {})
        recalculated = recalculated_by_id.get(comparison_id, {})
        cached_hash = cached.get("comparison_output_sha256", "")
        recalculated_hash = recalculated.get("comparison_output_sha256", "")
        hashes_match = bool(cached_hash and recalculated_hash and cached_hash == recalculated_hash)
        if not recalculated_hash:
            missing_ids.append(comparison_id)
        elif not hashes_match:
            mismatch_ids.append(comparison_id)
        comparisons.append(
            {
                "comparison_id": comparison_id,
                "sheet": selection["sheet"],
                "cell": selection["cell"],
                "output_role": selection["output_role"],
                "cached_anchor_sha256": cached_hash,
                "recalculated_output_sha256": recalculated_hash,
                "hashes_match": hashes_match,
                "raw_value_disclosed": False,
            }
        )

    attempted_ok = attempt.get("execution_status") == (
        "reopen_recalculate_completed_hash_only_outputs_retained"
    )
    all_match = attempted_ok and not mismatch_ids and not missing_ids
    exact_blocker = ""
    if not attempted_ok:
        exact_blocker = attempt.get(
            "blocking_reason",
            "headless spreadsheet execution did not complete",
        )
    elif missing_ids:
        exact_blocker = (
            "headless spreadsheet execution completed but selected output hashes "
            f"were missing for: {', '.join(missing_ids)}"
        )
    elif mismatch_ids:
        exact_blocker = (
            "headless spreadsheet execution completed but selected output hashes "
            f"differed from cached anchors for: {', '.join(mismatch_ids)}"
        )

    return {
        "residual_id": "RES-006",
        "gate_status": (
            "partial_beco_recalculation_hashes_match_cached_anchors"
            if all_match
            else "blocked_fail_closed_beco_recalculation_not_admitted"
        ),
        "spreadsheet_execution_attempted": True,
        "spreadsheet_recalculation_admitted": all_match,
        "cached_hash_anchor_count": len(cached_by_id),
        "selected_recalculated_hash_count": len(recalculated_by_id),
        "selected_hashes_match_cached_anchors": all_match,
        "selected_hash_comparisons": comparisons,
        "execution_attempt": attempt,
        "exact_blocker": exact_blocker,
        "raw_values_retained": False,
    }


def _tp21_admission_gate(mechanism_artifact: dict[str, Any]) -> dict[str, Any]:
    tp21 = mechanism_artifact["tp21_criteria_vocabulary"]
    selected = tp21.get("selected_debris_output_hashes", [])
    selected_hashes_present = bool(selected)
    return {
        "residual_id": "RES-005",
        "gate_status": (
            "partial_tp21_selected_debris_hashes_present_review_required"
            if selected_hashes_present
            else "blocked_fail_closed_tp21_selected_debris_outputs_missing"
        ),
        "selected_debris_output_hash_count": len(selected),
        "selected_debris_output_hashes_present": selected_hashes_present,
        "criteria_vocabulary_sha256": tp21["criteria_vocabulary_sha256"],
        "source_text_copied_to_dataset": False,
        "source_tables_copied_to_dataset": False,
        "selected_output_requirements": tp21["selected_output_requirements"],
        "exact_blocker": (
            ""
            if selected_hashes_present
            else (
                "required reviewer-selected TP-21 debris comparison case artifacts "
                "are missing: page/section provenance outside this package plus "
                "hash-only selected debris outputs"
            )
        ),
    }


def _tolerance_policy() -> dict[str, Any]:
    return {
        "policy_status": "fail_closed_exact_hash_policy_only",
        "raw_numeric_tolerance_admitted": False,
        "admitted_tolerance": None,
        "selected_beco_policy": (
            "selected recalculated BEC-O output hashes must exactly match the "
            "cached hash anchors; no numeric tolerance is admitted without a "
            "separate reviewed allowed-output policy"
        ),
        "selected_tp21_policy": (
            "selected TP-21 debris cases must be reviewer-chosen and retained as "
            "hash-only outputs; source prose/tables must not be copied"
        ),
        "missing_policy_blocker": (
            "release-grade tolerance and allowed-output signoff is not present"
        ),
    }


def _non_authoritative_guards() -> dict[str, bool]:
    return {
        "stock_descriptor_created": False,
        "stock_database_authority_granted": False,
        "runtime_authority_granted": False,
        "fragment_mechanism_authority_granted": False,
        "blast_mechanism_authority_granted": False,
        "effect_scale_authority_granted": False,
        "component_failure_probability_authority_granted": False,
        "pk_authority_granted": False,
        "deterministic_fuze_authority_granted": False,
    }


def generate_benchmark_execution_admission_gate(
    *,
    repo_root: Path = REPO_ROOT,
    retained_dir: Path = DEFAULT_RETAINED_DIR,
    source_payload_pack_dir: Path = SOURCE_PAYLOAD_PACK_DIR,
    attempt_spreadsheet_execution: bool = True,
) -> dict[str, Any]:
    mechanism_artifact = comparison_hashes.generate_mechanism_comparison_hashes(
        repo_root=repo_root,
        source_payload_pack_dir=source_payload_pack_dir,
    )
    tooling = detect_execution_tooling()
    if not attempt_spreadsheet_execution:
        tooling = {
            **tooling,
            "tool_detection_status": "spreadsheet_execution_probe_skipped",
            "selected_spreadsheet_executor": None,
            "missing_execution_tooling_blockers": [
                "spreadsheet execution attempt disabled by caller"
            ],
        }
    retained_dir.mkdir(parents=True, exist_ok=True)
    beco_gate = _beco_execution_gate(
        mechanism_artifact=mechanism_artifact,
        tooling=tooling,
        retained_dir=retained_dir,
    )
    tp21_gate = _tp21_admission_gate(mechanism_artifact)
    tolerance_policy = _tolerance_policy()
    guards = _non_authoritative_guards()

    beco_admitted = bool(beco_gate["spreadsheet_recalculation_admitted"])
    tp21_admitted = bool(tp21_gate["selected_debris_output_hashes_present"])
    tolerance_admitted = False
    benchmark_consumed = False
    gate_closed = (
        beco_admitted
        and tp21_admitted
        and tolerance_admitted
        and benchmark_consumed
    )
    gate_status = (
        "passed_release_benchmark_execution_admission"
        if gate_closed
        else "partial_fail_closed_benchmark_execution_admission_gate"
    )

    blockers = []
    if beco_gate.get("exact_blocker"):
        blockers.append(beco_gate["exact_blocker"])
    if tp21_gate.get("exact_blocker"):
        blockers.append(tp21_gate["exact_blocker"])
    blockers.append(tolerance_policy["missing_policy_blocker"])
    blockers.append(
        "benchmark-consumption decision remains fail-closed; retained evidence is not consumed for release"
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "package_id": PACKAGE_ID,
        "status": gate_status,
        "review_target": "res_005_006_benchmark_execution_admission_gate",
        "source_payload_pack_ref": _rel(source_payload_pack_dir, repo_root),
        "mechanism_comparison_hashes_ref": _rel(
            MECHANISM_COMPARISON_HASHES_DIR
            / comparison_hashes.MECHANISM_COMPARISON_HASHES_FILENAME,
            repo_root,
        ),
        "mechanism_comparison_hashes_input_status": mechanism_artifact["status"],
        "tooling_detection": tooling,
        "beco_spreadsheet_execution_gate": beco_gate,
        "tp21_debris_admission_gate": tp21_gate,
        "tolerance_policy": tolerance_policy,
        "benchmark_consumption_decision": {
            "decision": "not_consumed_fail_closed",
            "benchmark_consumed_for_release": benchmark_consumed,
            "release_grade_validated": False,
            "closed_residual_ids_by_this_gate": [],
            "res005_closed": False,
            "res006_closed": False,
            "decision_reasons": blockers,
        },
        "current_gate_results": {
            "RES-005": tp21_gate["gate_status"],
            "RES-006": beco_gate["gate_status"],
        },
        "admission_summary": {
            "beco_recalculation_hashes_admitted": beco_admitted,
            "tp21_selected_debris_outputs_admitted": tp21_admitted,
            "tolerance_policy_admitted": tolerance_admitted,
            "benchmark_consumption_admitted": benchmark_consumed,
            "fail_closed": not gate_closed,
            "exact_blockers": blockers,
        },
        "non_authoritative_guards": guards,
        "authority_guards_all_false": not any(guards.values()),
        "behavior_risks": [
            "headless spreadsheet reopen/recalculate may be mistaken for release-grade spreadsheet review",
            "exact hash equality may be mistaken for a reviewed numeric tolerance policy",
            "TP-21 controlled vocabulary may be mistaken for selected debris benchmark outputs",
            "candidate retained payloads may be mistaken for benchmark consumption authority",
        ],
        "integration_notes": [
            "This gate only strengthens hash-only evidence; it does not close RES-005 or RES-006.",
            "BEC-O selected output raw values and formula text are not retained in this artifact.",
            "TP-21 source prose/tables are not copied; selected debris output requirements remain explicit.",
            "Pk and deterministic fuze authority remain out of scope and false.",
        ],
    }


def write_retained_artifacts(
    *,
    retained_dir: Path = DEFAULT_RETAINED_DIR,
    repo_root: Path = REPO_ROOT,
    source_payload_pack_dir: Path = SOURCE_PAYLOAD_PACK_DIR,
    attempt_spreadsheet_execution: bool = True,
) -> dict[str, Any]:
    artifact = generate_benchmark_execution_admission_gate(
        repo_root=repo_root,
        retained_dir=retained_dir,
        source_payload_pack_dir=source_payload_pack_dir,
        attempt_spreadsheet_execution=attempt_spreadsheet_execution,
    )
    retained_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = retained_dir / GATE_FILENAME
    _write_json(artifact_path, artifact)
    artifact_sha256 = _sha256_file(artifact_path)
    manifest = {
        "schema_version": RETAINED_MANIFEST_SCHEMA_VERSION,
        "package_id": PACKAGE_ID,
        "status": artifact["status"],
        "artifact_dir": _rel(retained_dir, repo_root),
        "benchmark_execution_admission_gate_artifact": {
            "filename": GATE_FILENAME,
            "relative_path": _rel(artifact_path, repo_root),
            "schema_version": artifact["schema_version"],
            "sha256": artifact_sha256,
        },
        "current_gate_results": artifact["current_gate_results"],
        "admission_summary": artifact["admission_summary"],
        "benchmark_consumption_decision": artifact["benchmark_consumption_decision"],
        "authority_guards_all_false": artifact["authority_guards_all_false"],
        "non_authoritative_guards": artifact["non_authoritative_guards"],
    }
    manifest_path = retained_dir / RETAINED_MANIFEST_FILENAME
    _write_json(manifest_path, manifest)
    artifact["retained_artifact_sha256"] = artifact_sha256
    artifact["retained_manifest_sha256"] = _sha256_file(manifest_path)
    return artifact


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the fail-closed A2 RES-005/006 benchmark execution/"
            "admission gate."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for a copy of the generated gate JSON.",
    )
    parser.add_argument(
        "--source-payload-pack-dir",
        type=Path,
        default=SOURCE_PAYLOAD_PACK_DIR,
        help="Retained source payload pack directory.",
    )
    parser.add_argument(
        "--retained-dir",
        type=Path,
        default=DEFAULT_RETAINED_DIR,
        help="Directory for retained benchmark execution/admission artifacts.",
    )
    parser.add_argument(
        "--skip-spreadsheet-execution",
        action="store_true",
        help="Detect tooling but do not attempt BEC-O headless recalculation.",
    )
    args = parser.parse_args()

    artifact = write_retained_artifacts(
        retained_dir=args.retained_dir,
        source_payload_pack_dir=args.source_payload_pack_dir,
        attempt_spreadsheet_execution=not args.skip_spreadsheet_execution,
    )
    if args.output:
        _write_json(args.output, artifact)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
