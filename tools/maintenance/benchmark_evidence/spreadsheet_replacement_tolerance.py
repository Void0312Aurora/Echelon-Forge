#!/usr/bin/env python3
"""Generate the RES-006 BEC-O replacement/tolerance admission review packet.

This packet is deliberately downstream of the 20260531 BEC-O recalculation
gate. It reads only retained JSON evidence, keeps raw spreadsheet values and
tool output out of the artifact, and fails closed unless independent lineage,
allowed-output, tolerance, and replacement-anchor signoffs are all present.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT_HINT = str(Path(__file__).resolve().parents[3])
if _REPO_ROOT_HINT not in sys.path:
  sys.path.insert(0, _REPO_ROOT_HINT)

from python.runtime_bootstrap import ensure_repo_imports, repo_root

ensure_repo_imports()

REPO_ROOT = Path(repo_root())

from tools.maintenance.retained_artifacts.manifest_integrity import (
  _sha256_file,
  write_and_hash_json,
)
from tools.maintenance.benchmark_evidence import comparison_hashes # noqa: E402

PACKAGE_ID = comparison_hashes.PACKAGE_ID
SCHEMA_VERSION = "a2.res006_beco_replacement_tolerance_admission_gate.v1"
RETAINED_MANIFEST_SCHEMA_VERSION = (
  "a2.res006_beco_replacement_tolerance_admission_retained_manifest.v1"
)

PACKAGE_DIR = comparison_hashes.PACKAGE_DIR
RETAINED_ROOT = PACKAGE_DIR / "retained_artifacts"
RES006_RECALCULATION_DIR = (
  RETAINED_ROOT / "res006_beco_recalculation_admission_20260531"
)
MECHANISM_COMPARISON_HASHES_DIR = comparison_hashes.DEFAULT_RETAINED_DIR
SOURCE_RIGHTS_OUTPUT_POLICY_DIR = (
  RETAINED_ROOT / "source_rights_output_policy_20260531"
)
DEFAULT_RETAINED_DIR = (
  RETAINED_ROOT / "res006_beco_replacement_tolerance_admission_20260601"
)

RES006_RECALCULATION_GATE_FILENAME = "res006_beco_recalculation_admission_gate.json"
BECO_RECALCULATED_ANCHOR_SET_FILENAME = "beco_recalculated_hash_anchor_set.json"
MECHANISM_COMPARISON_HASHES_FILENAME = (
  comparison_hashes.MECHANISM_COMPARISON_HASHES_FILENAME
)
SOURCE_RIGHTS_OUTPUT_POLICY_GATE_FILENAME = "source_rights_output_policy_gate.json"
GATE_FILENAME = "res006_beco_replacement_tolerance_admission_gate.json"
RETAINED_MANIFEST_FILENAME = "manifest.json"

DEFAULT_RES006_RECALCULATION_GATE = (
  RES006_RECALCULATION_DIR / RES006_RECALCULATION_GATE_FILENAME
)
DEFAULT_BECO_RECALCULATED_ANCHOR_SET = (
  RES006_RECALCULATION_DIR / BECO_RECALCULATED_ANCHOR_SET_FILENAME
)
DEFAULT_MECHANISM_COMPARISON_HASHES = (
  MECHANISM_COMPARISON_HASHES_DIR / MECHANISM_COMPARISON_HASHES_FILENAME
)
DEFAULT_SOURCE_RIGHTS_OUTPUT_POLICY_GATE = (
  SOURCE_RIGHTS_OUTPUT_POLICY_DIR / SOURCE_RIGHTS_OUTPUT_POLICY_GATE_FILENAME
)

def _rel(path: Path, repo_root: Path) -> str:
  # Kept local: non-resolving; differs from manifest_integrity._display_path.
  try:
    return path.relative_to(repo_root).as_posix()
  except ValueError:
    return path.as_posix()

def _write_json(path: Path, payload: dict[str, Any]) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(
    json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
  )

def _load_json(path: Path) -> dict[str, Any]:
  return json.loads(path.read_text(encoding="utf-8"))

def _input_ref(
  *,
  artifact_key: str,
  path: Path,
  repo_root: Path,
) -> dict[str, Any]:
  ref: dict[str, Any] = {
    "artifact_key": artifact_key,
    "relative_path": _rel(path, repo_root),
    "present": path.is_file(),
  }
  if not path.is_file():
    ref["status"] = "missing_fail_closed"
    return ref

  ref["sha256"] = _sha256_file(path)
  try:
    payload = _load_json(path)
  except json.JSONDecodeError:
    ref["status"] = "json_parse_failed_fail_closed"
    return ref

  ref["schema_version"] = payload.get("schema_version", "")
  ref["status"] = payload.get("status", "")
  return ref

def _authority_guards() -> dict[str, bool]:
  return {
    "stock_descriptor_created": False,
    "stock_database_authority_granted": False,
    "runtime_authority_granted": False,
    "blast_mechanism_authority_granted": False,
    "fragment_mechanism_authority_granted": False,
    "effect_scale_authority_granted": False,
    "component_failure_probability_authority_granted": False,
    "component_authority_granted": False,
    "pk_authority_granted": False,
    "fuze_authority_granted": False,
    "deterministic_fuze_authority_granted": False,
    "replacement_anchor_authority_granted": False,
    "benchmark_consumption_authority_granted": False,
  }

def _source_rights_summary(
  *,
  source_rights_output_policy_gate: dict[str, Any] | None,
  source_rights_ref: dict[str, Any],
) -> dict[str, Any]:
  if source_rights_output_policy_gate is None:
    return {
      "relative_path": source_rights_ref["relative_path"],
      "present": False,
      "sha256": "",
      "status": "missing_fail_closed",
      "allowed_output_policy_status": "missing_fail_closed",
      "allowed_output_signoff_present": False,
      "release_grade_satisfied": False,
      "selected_comparison_output_hashes_admitted": False,
      "recording_level": "path_sha_status_only",
    }

  policy = source_rights_output_policy_gate.get("allowed_output_policy", {})
  selected_hashes = policy.get("current_selected_comparison_output_hashes", [])
  return {
    "relative_path": source_rights_ref["relative_path"],
    "present": True,
    "sha256": source_rights_ref.get("sha256", ""),
    "schema_version": source_rights_ref.get("schema_version", ""),
    "status": source_rights_ref.get("status", ""),
    "allowed_output_policy_status": policy.get("policy_status", ""),
    "release_grade_satisfied": bool(policy.get("release_grade_satisfied")),
    "selected_comparison_output_hash_count": len(selected_hashes),
    "selected_comparison_output_hashes_admitted": False,
    "allowed_output_signoff_present": False,
    "recording_level": "path_sha_status_only",
  }

def _cached_rows(
  mechanism_comparison_hashes: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
  if mechanism_comparison_hashes is None:
    return {}
  beco = mechanism_comparison_hashes.get("beco_workbook", {})
  rows = beco.get("selected_comparison_hashes", [])
  return {
    row.get("comparison_id", ""): row
    for row in rows
    if row.get("comparison_id")
  }

def _recalculated_rows(
  beco_recalculated_anchor_set: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
  if beco_recalculated_anchor_set is None:
    return {}
  rows = beco_recalculated_anchor_set.get("selected_recalculated_hashes", [])
  return {
    row.get("comparison_id", ""): row
    for row in rows
    if row.get("comparison_id")
  }

def _ordered_comparison_ids(
  *,
  res006_recalculation_gate: dict[str, Any] | None,
  cached_by_id: dict[str, dict[str, Any]],
  recalculated_by_id: dict[str, dict[str, Any]],
) -> list[str]:
  ordered: list[str] = []
  if res006_recalculation_gate is not None:
    lineage = res006_recalculation_gate.get("mismatch_lineage", {})
    for row in lineage.get("hash_only_comparison_rows", []):
      comparison_id = row.get("comparison_id")
      if comparison_id and comparison_id not in ordered:
        ordered.append(comparison_id)
  for comparison_id in [*cached_by_id, *recalculated_by_id]:
    if comparison_id and comparison_id not in ordered:
      ordered.append(comparison_id)
  return ordered

def _cached_vs_recalculated_summary(
  *,
  res006_recalculation_gate: dict[str, Any] | None,
  mechanism_comparison_hashes: dict[str, Any] | None,
  beco_recalculated_anchor_set: dict[str, Any] | None,
) -> dict[str, Any]:
  cached_by_id = _cached_rows(mechanism_comparison_hashes)
  recalculated_by_id = _recalculated_rows(beco_recalculated_anchor_set)
  comparison_ids = _ordered_comparison_ids(
    res006_recalculation_gate=res006_recalculation_gate,
    cached_by_id=cached_by_id,
    recalculated_by_id=recalculated_by_id,
  )

  comparison_rows: list[dict[str, Any]] = []
  matching_ids: list[str] = []
  mismatch_ids: list[str] = []
  missing_cached_ids: list[str] = []
  missing_recalculated_ids: list[str] = []
  for comparison_id in comparison_ids:
    cached = cached_by_id.get(comparison_id, {})
    recalculated = recalculated_by_id.get(comparison_id, {})
    cached_hash = cached.get("comparison_output_sha256", "")
    recalculated_hash = recalculated.get("recalculated_output_sha256", "")
    if not cached_hash:
      missing_cached_ids.append(comparison_id)
    if not recalculated_hash:
      missing_recalculated_ids.append(comparison_id)
    hashes_match = bool(
      cached_hash and recalculated_hash and cached_hash == recalculated_hash
    )
    if hashes_match:
      matching_ids.append(comparison_id)
    elif cached_hash and recalculated_hash:
      mismatch_ids.append(comparison_id)

    comparison_rows.append(
      {
        "comparison_id": comparison_id,
        "source_artifact_label": (
          cached.get("source_artifact_label")
          or recalculated.get("source_artifact_label")
          or "BEC-O-V1.xlsx"
        ),
        "sheet": cached.get("sheet") or recalculated.get("sheet", ""),
        "cell": cached.get("cell") or recalculated.get("cell", ""),
        "output_role": cached.get("output_role")
        or recalculated.get("output_role", ""),
        "unit_family": cached.get("unit_family")
        or recalculated.get("unit_family", ""),
        "cached_anchor_sha256": cached_hash,
        "recalculated_output_sha256": recalculated_hash,
        "formula_sha256": cached.get("formula_sha256")
        or recalculated.get("formula_sha256", ""),
        "hashes_match": hashes_match,
        "raw_value_disclosed": False,
        "formula_text_disclosed": False,
      }
    )

  exact_hash_check_passed = bool(
    comparison_rows
    and not mismatch_ids
    and not missing_cached_ids
    and not missing_recalculated_ids
  )
  source_lineage = {}
  if res006_recalculation_gate is not None:
    source_lineage = res006_recalculation_gate.get("mismatch_lineage", {})

  return {
    "status": (
      "cached_and_recalculated_hashes_match_review_still_required"
      if exact_hash_check_passed
      else "cached_vs_recalculated_hash_mismatch_fail_closed"
    ),
    "source_recalculation_lineage_status": source_lineage.get("status", ""),
    "cached_anchor_count": sum(
      1 for row in cached_by_id.values() if row.get("comparison_output_sha256")
    ),
    "recalculated_anchor_count": sum(
      1
      for row in recalculated_by_id.values()
      if row.get("recalculated_output_sha256")
    ),
    "comparison_row_count": len(comparison_rows),
    "matching_count": len(matching_ids),
    "mismatch_count": len(mismatch_ids),
    "missing_cached_count": len(missing_cached_ids),
    "missing_recalculated_count": len(missing_recalculated_ids),
    "matching_comparison_ids": matching_ids,
    "mismatch_comparison_ids": mismatch_ids,
    "missing_cached_comparison_ids": missing_cached_ids,
    "missing_recalculated_comparison_ids": missing_recalculated_ids,
    "exact_hash_check_passed": exact_hash_check_passed,
    "cached_selected_output_set_sha256": (
      mechanism_comparison_hashes.get("beco_workbook", {}).get(
        "selected_comparison_output_set_sha256", ""
      )
      if mechanism_comparison_hashes
      else ""
    ),
    "recalculated_selected_output_set_sha256": (
      beco_recalculated_anchor_set.get(
        "selected_recalculated_output_set_sha256", ""
      )
      if beco_recalculated_anchor_set
      else ""
    ),
    "hash_only_comparison_rows": comparison_rows,
    "raw_selected_values_retained": False,
    "formula_text_retained": False,
    "temporary_workbook_copy_retained": False,
    "stdout_retained": False,
    "stderr_retained": False,
  }

def _replacement_candidate_summary(
  *,
  beco_recalculated_anchor_set: dict[str, Any] | None,
  beco_recalculated_anchor_set_ref: dict[str, Any],
) -> dict[str, Any]:
  if beco_recalculated_anchor_set is None:
    return {
      "relative_path": beco_recalculated_anchor_set_ref["relative_path"],
      "present": False,
      "candidate_replacement_anchor_set_retained": False,
      "replacement_anchor_set_admitted": False,
      "replacement_anchor_signoff_present": False,
      "status": "candidate_replacement_anchor_set_missing_fail_closed",
    }

  return {
    "relative_path": beco_recalculated_anchor_set_ref["relative_path"],
    "sha256": beco_recalculated_anchor_set_ref.get("sha256", ""),
    "present": True,
    "schema_version": beco_recalculated_anchor_set_ref.get("schema_version", ""),
    "status": beco_recalculated_anchor_set.get("status", ""),
    "candidate_replacement_anchor_set_retained": bool(
      beco_recalculated_anchor_set.get(
        "all_selected_recalculated_hashes_present"
      )
    ),
    "recalculated_hash_count": int(
      beco_recalculated_anchor_set.get("recalculated_hash_count", 0)
    ),
    "expected_selected_hash_count": int(
      beco_recalculated_anchor_set.get("expected_selected_hash_count", 0)
    ),
    "selected_recalculated_output_set_sha256": beco_recalculated_anchor_set.get(
      "selected_recalculated_output_set_sha256", ""
    ),
    "raw_selected_values_retained": False,
    "formula_text_retained": False,
    "temporary_workbook_copy_retained": False,
    "stdout_retained": False,
    "stderr_retained": False,
    "replacement_anchor_set_admitted": False,
    "replacement_anchor_signoff_present": False,
    "replacement_anchor_authority_granted": False,
    "benchmark_consumed_for_release": False,
  }

def _required_signoff_items(
  *,
  source_rights_summary: dict[str, Any],
  replacement_candidate_summary: dict[str, Any],
) -> list[dict[str, Any]]:
  return [
    {
      "signoff_id": "independent_lineage_review_signoff",
      "required": True,
      "current_status": "missing",
      "signed_off": False,
      "admitted": False,
      "owner_input_needed": (
        "named independent reviewer acceptance of BEC-O recalculation "
        "runtime/version lineage and retained hash-only evidence"
      ),
      "fail_closed_reason": (
        "existing recalculation evidence is local retained evidence, "
        "not an independent lineage review"
      ),
    },
    {
      "signoff_id": "allowed_output_policy_signoff",
      "required": True,
      "current_status": (
        "missing"
        if not source_rights_summary["allowed_output_signoff_present"]
        else "present"
      ),
      "signed_off": source_rights_summary["allowed_output_signoff_present"],
      "admitted": False,
      "owner_input_needed": (
        "release owner or rights reviewer must explicitly admit selected "
        "BEC-O comparison output hashes under the allowed-output policy"
      ),
      "fail_closed_reason": (
        "source rights policy remains fail-closed for selected comparison "
        "outputs"
      ),
    },
    {
      "signoff_id": "numeric_tolerance_policy_signoff",
      "required": True,
      "current_status": "missing",
      "signed_off": False,
      "admitted": False,
      "owner_input_needed": (
        "release-grade numeric tolerance policy or exact-hash replacement "
        "policy for cached-vs-recalculated BEC-O output differences"
      ),
      "fail_closed_reason": (
        "this packet retains hashes only and admits no raw numeric "
        "tolerance"
      ),
    },
    {
      "signoff_id": "replacement_anchor_signoff",
      "required": True,
      "current_status": (
        "missing"
        if not replacement_candidate_summary[
          "replacement_anchor_signoff_present"
        ]
        else "present"
      ),
      "signed_off": replacement_candidate_summary[
        "replacement_anchor_signoff_present"
      ],
      "admitted": False,
      "owner_input_needed": (
        "explicit retained decision promoting or rejecting the "
        "recalculated hash anchor set without mutating cached anchors "
        "in place"
      ),
      "fail_closed_reason": (
        "candidate recalculated anchor set is retained but not admitted"
        if replacement_candidate_summary[
          "candidate_replacement_anchor_set_retained"
        ]
        else "candidate recalculated anchor set is unavailable"
      ),
    },
  ]

def _admission_decision(
  *,
  cached_vs_recalculated_mismatch_summary: dict[str, Any],
  required_signoff_items: list[dict[str, Any]],
) -> dict[str, Any]:
  missing_items = [
    item["signoff_id"]
    for item in required_signoff_items
    if not item["signed_off"] or not item["admitted"]
  ]
  exact_hash_check_passed = cached_vs_recalculated_mismatch_summary[
    "exact_hash_check_passed"
  ]
  residual_closed = False

  blockers = [
    item["fail_closed_reason"]
    for item in required_signoff_items
    if not item["signed_off"] or not item["admitted"]
  ]
  if not exact_hash_check_passed:
    blockers.insert(
      0,
      "cached-vs-recalculated selected hashes do not satisfy exact-hash admission",
    )

  return {
    "residual_id": "RES-006",
    "decision": "res006_remains_blocked_fail_closed",
    "status": "blocked_fail_closed",
    "residual_closed": residual_closed,
    "res006_narrowly_closed": residual_closed,
    "closed_residual_ids_by_this_gate": [],
    "exact_hash_check_passed": exact_hash_check_passed,
    "independent_lineage_review_present": False,
    "allowed_output_signoff_present": False,
    "tolerance_policy_admitted": False,
    "replacement_anchor_set_admitted": False,
    "release_grade_validated": False,
    "benchmark_consumed_for_release": False,
    "raw_selected_values_retained": False,
    "current_missing_items": missing_items,
    "remaining_blockers": blockers,
  }

def _load_existing_inputs(
  *,
  res006_recalculation_gate_path: Path,
  beco_recalculated_anchor_set_path: Path,
  mechanism_comparison_hashes_path: Path,
  source_rights_output_policy_gate_path: Path,
) -> dict[str, dict[str, Any] | None]:
  paths = {
    "res006_recalculation_gate": res006_recalculation_gate_path,
    "beco_recalculated_anchor_set": beco_recalculated_anchor_set_path,
    "mechanism_comparison_hashes": mechanism_comparison_hashes_path,
    "source_rights_output_policy_gate": source_rights_output_policy_gate_path,
  }
  loaded: dict[str, dict[str, Any] | None] = {}
  for key, path in paths.items():
    if not path.is_file():
      loaded[key] = None
      continue
    loaded[key] = _load_json(path)
  return loaded

def generate_res006_beco_replacement_tolerance_admission_gate(
  *,
  repo_root: Path = REPO_ROOT,
  retained_dir: Path = DEFAULT_RETAINED_DIR,
  res006_recalculation_gate_path: Path = DEFAULT_RES006_RECALCULATION_GATE,
  beco_recalculated_anchor_set_path: Path = DEFAULT_BECO_RECALCULATED_ANCHOR_SET,
  mechanism_comparison_hashes_path: Path = DEFAULT_MECHANISM_COMPARISON_HASHES,
  source_rights_output_policy_gate_path: Path = (
    DEFAULT_SOURCE_RIGHTS_OUTPUT_POLICY_GATE
  ),
) -> dict[str, Any]:
  input_refs = [
    _input_ref(
      artifact_key="res006_beco_recalculation_admission_gate",
      path=res006_recalculation_gate_path,
      repo_root=repo_root,
    ),
    _input_ref(
      artifact_key="beco_recalculated_hash_anchor_set",
      path=beco_recalculated_anchor_set_path,
      repo_root=repo_root,
    ),
    _input_ref(
      artifact_key="mechanism_comparison_hashes",
      path=mechanism_comparison_hashes_path,
      repo_root=repo_root,
    ),
    _input_ref(
      artifact_key="source_rights_output_policy_gate",
      path=source_rights_output_policy_gate_path,
      repo_root=repo_root,
    ),
  ]
  refs_by_key = {ref["artifact_key"]: ref for ref in input_refs}
  loaded = _load_existing_inputs(
    res006_recalculation_gate_path=res006_recalculation_gate_path,
    beco_recalculated_anchor_set_path=beco_recalculated_anchor_set_path,
    mechanism_comparison_hashes_path=mechanism_comparison_hashes_path,
    source_rights_output_policy_gate_path=source_rights_output_policy_gate_path,
  )
  source_rights = _source_rights_summary(
    source_rights_output_policy_gate=loaded["source_rights_output_policy_gate"],
    source_rights_ref=refs_by_key["source_rights_output_policy_gate"],
  )
  mismatch_summary = _cached_vs_recalculated_summary(
    res006_recalculation_gate=loaded["res006_recalculation_gate"],
    mechanism_comparison_hashes=loaded["mechanism_comparison_hashes"],
    beco_recalculated_anchor_set=loaded["beco_recalculated_anchor_set"],
  )
  replacement_candidate = _replacement_candidate_summary(
    beco_recalculated_anchor_set=loaded["beco_recalculated_anchor_set"],
    beco_recalculated_anchor_set_ref=refs_by_key[
      "beco_recalculated_hash_anchor_set"
    ],
  )
  required_signoffs = _required_signoff_items(
    source_rights_summary=source_rights,
    replacement_candidate_summary=replacement_candidate,
  )
  decision = _admission_decision(
    cached_vs_recalculated_mismatch_summary=mismatch_summary,
    required_signoff_items=required_signoffs,
  )
  guards = _authority_guards()

  return {
    "schema_version": SCHEMA_VERSION,
    "package_id": PACKAGE_ID,
    "residual_id": "RES-006",
    "status": "blocked_fail_closed_res006_beco_replacement_tolerance_admission_review",
    "review_target": "RES-006_BEC-O_replacement_tolerance_admission_review",
    "artifact_dir": _rel(retained_dir, repo_root),
    "residual": {
      "residual_id": "RES-006",
      "residual_label": "BEC-O cached-vs-recalculated output hash replacement/tolerance admission",
      "closure_claimed_by_this_gate": False,
    },
    "input_refs": input_refs,
    "source_rights_output_policy_summary": source_rights,
    "cached_vs_recalculated_mismatch_summary": mismatch_summary,
    "replacement_candidate_summary": replacement_candidate,
    "required_signoff_items": required_signoffs,
    "current_missing_items": decision["current_missing_items"],
    "admission_decision": decision,
    "current_gate_results": {
      "RES-006": "blocked_fail_closed_replacement_tolerance_admission_review"
    },
    "benchmark_consumed_for_release": False,
    "raw_selected_values_retained": False,
    "formula_text_retained": False,
    "temporary_workbook_copy_retained": False,
    "stdout_retained": False,
    "stderr_retained": False,
    "raw_output_tables_retained": False,
    "authority_guards": guards,
    "authority_guards_all_false": not any(guards.values()),
    "behavior_risks": [
      "candidate recalculated hashes could be mistaken for an admitted replacement anchor",
      "hash mismatch could be mistaken for numeric tolerance evidence even though raw values are not retained",
      "local recalculation lineage could be mistaken for independent review",
      "source rights policy could be mistaken for selected-output admission despite remaining fail-closed",
    ],
    "integration_notes": [
      "This packet does not replace cached BEC-O anchors or close RES-006.",
      "Only retained JSON inputs are read; workbook contents, raw selected values, formulas, stdout and stderr are not retained.",
      "Release use requires independent lineage, allowed-output, tolerance, and replacement-anchor signoff.",
      "Blast/component/effect/stock/runtime/Pk/fuze/replacement-anchor authority guards remain false.",
    ],
  }

def write_retained_artifacts(
  *,
  retained_dir: Path = DEFAULT_RETAINED_DIR,
  repo_root: Path = REPO_ROOT,
  res006_recalculation_gate_path: Path = DEFAULT_RES006_RECALCULATION_GATE,
  beco_recalculated_anchor_set_path: Path = DEFAULT_BECO_RECALCULATED_ANCHOR_SET,
  mechanism_comparison_hashes_path: Path = DEFAULT_MECHANISM_COMPARISON_HASHES,
  source_rights_output_policy_gate_path: Path = (
    DEFAULT_SOURCE_RIGHTS_OUTPUT_POLICY_GATE
  ),
) -> dict[str, Any]:
  artifact = generate_res006_beco_replacement_tolerance_admission_gate(
    repo_root=repo_root,
    retained_dir=retained_dir,
    res006_recalculation_gate_path=res006_recalculation_gate_path,
    beco_recalculated_anchor_set_path=beco_recalculated_anchor_set_path,
    mechanism_comparison_hashes_path=mechanism_comparison_hashes_path,
    source_rights_output_policy_gate_path=source_rights_output_policy_gate_path,
  )
  gate_path = retained_dir / GATE_FILENAME
  gate_sha256 = write_and_hash_json(gate_path, artifact, ensure_ascii=False)
  gate_artifact = {
    "artifact_key": "res006_beco_replacement_tolerance_admission_gate",
    "filename": GATE_FILENAME,
    "relative_path": _rel(gate_path, repo_root),
    "schema_version": artifact["schema_version"],
    "sha256": gate_sha256,
  }

  manifest = {
    "schema_version": RETAINED_MANIFEST_SCHEMA_VERSION,
    "package_id": PACKAGE_ID,
    "residual_id": "RES-006",
    "status": artifact["status"],
    "artifact_dir": _rel(retained_dir, repo_root),
    "artifacts": [gate_artifact],
    "input_refs": artifact["input_refs"],
    "current_gate_results": artifact["current_gate_results"],
    "admission_decision": artifact["admission_decision"],
    "required_signoff_items": artifact["required_signoff_items"],
    "current_missing_items": artifact["current_missing_items"],
    "benchmark_consumed_for_release": False,
    "raw_selected_values_retained": False,
    "authority_guards": artifact["authority_guards"],
    "authority_guards_all_false": artifact["authority_guards_all_false"],
  }
  manifest_path = retained_dir / RETAINED_MANIFEST_FILENAME
  manifest_sha256 = write_and_hash_json(manifest_path, manifest, ensure_ascii=False)

  artifact["retained_artifact_sha256"] = gate_sha256
  artifact["retained_manifest_sha256"] = manifest_sha256
  return artifact

def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description=(
      "Generate the fail-closed RES-006 BEC-O replacement/tolerance "
      "admission review packet."
    )
  )
  parser.add_argument(
    "--output",
    type=Path,
    help="Optional path for a copy of the generated gate JSON.",
  )
  parser.add_argument(
    "--retained-dir",
    type=Path,
    default=DEFAULT_RETAINED_DIR,
    help="Directory for retained RES-006 replacement/tolerance artifacts.",
  )
  parser.add_argument(
    "--res006-recalculation-gate",
    type=Path,
    default=DEFAULT_RES006_RECALCULATION_GATE,
    help="Existing retained RES-006 recalculation admission gate JSON.",
  )
  parser.add_argument(
    "--beco-recalculated-anchor-set",
    type=Path,
    default=DEFAULT_BECO_RECALCULATED_ANCHOR_SET,
    help="Existing retained BEC-O recalculated hash anchor set JSON.",
  )
  parser.add_argument(
    "--mechanism-comparison-hashes",
    type=Path,
    default=DEFAULT_MECHANISM_COMPARISON_HASHES,
    help="Existing retained mechanism comparison hashes JSON.",
  )
  parser.add_argument(
    "--source-rights-output-policy-gate",
    type=Path,
    default=DEFAULT_SOURCE_RIGHTS_OUTPUT_POLICY_GATE,
    help="Existing retained source rights output policy gate JSON.",
  )
  args = parser.parse_args(argv)

  artifact = write_retained_artifacts(
    retained_dir=args.retained_dir,
    res006_recalculation_gate_path=args.res006_recalculation_gate,
    beco_recalculated_anchor_set_path=args.beco_recalculated_anchor_set,
    mechanism_comparison_hashes_path=args.mechanism_comparison_hashes,
    source_rights_output_policy_gate_path=args.source_rights_output_policy_gate,
  )
  if args.output:
    _write_json(args.output, artifact)
  return 0

if __name__ == "__main__":
  raise SystemExit(main())
