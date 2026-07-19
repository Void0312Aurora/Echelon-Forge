#!/usr/bin/env python3
"""Generate the fail-closed RES-005 TP-21 debris admission gate.

The gate is intentionally narrow: it may retain metadata, controlled criteria
keys, provenance-label requirements, and hash-only selected-output anchors. It
does not copy TP-21 prose/tables/raw values, consume TP-21 as a release
benchmark, or grant any stock/runtime/effect/Pk/fuze authority.
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

from tools.maintenance.retained_artifacts.manifest_integrity import _sha256_file, _sha256_text
from tools.maintenance.benchmark_evidence import comparison_hashes # noqa: E402

PACKAGE_ID = comparison_hashes.PACKAGE_ID
SCHEMA_VERSION = "a2.res005_tp21_debris_admission_gate.v1"
ANCHOR_SET_SCHEMA_VERSION = "a2.res005_tp21_selected_debris_anchor_set.v1"
RETAINED_MANIFEST_SCHEMA_VERSION = (
  "a2.res005_tp21_debris_admission_retained_manifest.v1"
)

PACKAGE_DIR = comparison_hashes.PACKAGE_DIR
MECHANISM_COMPARISON_HASHES_PATH = (
  comparison_hashes.DEFAULT_RETAINED_DIR
  / comparison_hashes.MECHANISM_COMPARISON_HASHES_FILENAME
)
SOURCE_RIGHTS_POLICY_PATH = (
  PACKAGE_DIR
  / "retained_artifacts"
  / "source_rights_output_policy_20260531"
  / "source_rights_output_policy_gate.json"
)
DEFAULT_RETAINED_DIR = (
  PACKAGE_DIR / "retained_artifacts" / "res005_tp21_debris_admission_20260531"
)

GATE_FILENAME = "res005_tp21_debris_admission_gate.json"
ANCHOR_SET_FILENAME = "selected_debris_output_anchor_set.json"
RETAINED_MANIFEST_FILENAME = "manifest.json"

REQUIRED_PROVENANCE_LABELS = [
  {
    "requirement_id": "TP21-PROV-001",
    "label_key": "tp21_page_locator_label",
    "required_status": "reviewer_selected_page_or_page_range_label",
  },
  {
    "requirement_id": "TP21-PROV-002",
    "label_key": "tp21_section_or_figure_locator_label",
    "required_status": "reviewer_selected_section_figure_or_table_label",
  },
  {
    "requirement_id": "TP21-PROV-003",
    "label_key": "reviewer_case_selection_id",
    "required_status": "stable_reviewer_selected_case_identifier",
  },
  {
    "requirement_id": "TP21-PROV-004",
    "label_key": "selected_output_preimage_sha256",
    "required_status": "hash_of_redacted_selected_output_preimage",
  },
  {
    "requirement_id": "TP21-PROV-005",
    "label_key": "allowed_output_signoff_id",
    "required_status": "rights_policy_admits_hash_only_selected_outputs",
  },
]

def _rel(path: Path, repo_root: Path) -> str:
  # Kept local: non-resolving; differs from manifest_integrity._display_path.
  try:
    return path.relative_to(repo_root).as_posix()
  except ValueError:
    return path.as_posix()

def _canonical_json(payload: Any) -> str:
  return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def _write_json(path: Path, payload: dict[str, Any]) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

def _load_json(path: Path) -> dict[str, Any]:
  return json.loads(path.read_text(encoding="utf-8"))

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

def _tp21_policy_row(source_rights_policy: dict[str, Any]) -> dict[str, Any]:
  for row in source_rights_policy.get("payload_rights_inventory", []):
    if row.get("residual_id") == "RES-005":
      return row
  return {}

def _criteria_vocabulary(
  mechanism_artifact: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
  tp21 = mechanism_artifact.get("tp21_criteria_vocabulary", {})
  criteria = [
    {
      "criteria_key": row["criteria_key"],
      "allowed_use": row["allowed_use"],
    }
    for row in tp21.get("allowed_criteria_vocabulary", [])
  ]
  return tp21, criteria

def _selected_output_requirements(
  criteria: list[dict[str, Any]],
) -> list[dict[str, Any]]:
  requirements: list[dict[str, Any]] = []
  for index, row in enumerate(criteria, start=1):
    requirements.append(
      {
        "requirement_id": f"TP21-SELECTED-{index:03d}",
        "residual_id": "RES-005",
        "criteria_key": row["criteria_key"],
        "required_action": (
          "record the reviewer-selected case field as a redacted "
          "hash-only preimage component; do not retain TP-21 source "
          "prose, tables, figures, or raw numeric values"
        ),
        "current_status": "selected_output_preimage_missing",
        "missing_reason": (
          "no reviewer-selected TP-21 debris case preimage was found "
          "in the retained package"
        ),
        "source_content_must_not_be_copied_to_dataset": True,
      }
    )
  return requirements

def _provenance_requirements(
  *,
  current_outputs_admitted: bool,
) -> list[dict[str, Any]]:
  rows: list[dict[str, Any]] = []
  for row in REQUIRED_PROVENANCE_LABELS:
    if row["label_key"] == "allowed_output_signoff_id":
      current_status = (
        "present" if current_outputs_admitted else "missing_allowed_output_signoff"
      )
      missing_reason = (
        ""
        if current_outputs_admitted
        else "source-rights policy current_comparison_outputs_admitted is false"
      )
    else:
      current_status = "missing_reviewer_selection"
      missing_reason = "reviewer-selected concrete TP-21 case label is absent"
    rows.append(
      {
        **row,
        "current_status": current_status,
        "missing_reason": missing_reason,
        "raw_source_content_retained": False,
      }
    )
  return rows

def _empty_anchor_set(
  *,
  repo_root: Path,
  tp21: dict[str, Any],
  criteria: list[dict[str, Any]],
  source_rights_policy_path: Path,
  source_rights_policy: dict[str, Any],
  mechanism_comparison_hashes_path: Path,
) -> dict[str, Any]:
  rights_row = _tp21_policy_row(source_rights_policy)
  output_policy = rights_row.get("output_policy", {})
  selected_outputs: list[dict[str, Any]] = []
  return {
    "schema_version": ANCHOR_SET_SCHEMA_VERSION,
    "package_id": PACKAGE_ID,
    "residual_id": "RES-005",
    "source_id": tp21.get("source_id", "VPS-BFM-015"),
    "source_artifact_label": tp21.get("source_artifact_label", "TP-21 PDF"),
    "source_artifact_sha256": tp21.get("artifact_sha256", ""),
    "source_artifact_relative_path": tp21.get("relative_path", ""),
    "mechanism_comparison_hashes_ref": _rel(
      mechanism_comparison_hashes_path, repo_root
    ),
    "source_rights_policy_ref": _rel(source_rights_policy_path, repo_root),
    "source_rights_policy_sha256": _sha256_file(source_rights_policy_path),
    "source_rights_policy_status": output_policy.get("policy_status", ""),
    "current_comparison_outputs_admitted": bool(
      output_policy.get("current_comparison_outputs_admitted")
    ),
    "allowed_hash_outputs": output_policy.get("hash_allowed_outputs", []),
    "controlled_criteria_keys": [row["criteria_key"] for row in criteria],
    "controlled_criteria_vocabulary_sha256": tp21.get(
      "criteria_vocabulary_sha256", ""
    ),
    "selected_debris_output_hashes": selected_outputs,
    "selected_debris_output_hash_count": len(selected_outputs),
    "selected_debris_output_set_sha256": _sha256_text(
      _canonical_json(selected_outputs)
    ),
    "selected_output_preimages_retained": False,
    "raw_tp21_source_content_retained": False,
    "source_tables_retained": False,
    "source_figures_retained": False,
    "source_numeric_values_retained": False,
    "benchmark_consumed_for_release": False,
    "anchor_set_status": "empty_fail_closed_no_reviewer_selected_case",
  }

def generate_tp21_debris_admission_gate(
  *,
  repo_root: Path = REPO_ROOT,
  mechanism_comparison_hashes_path: Path = MECHANISM_COMPARISON_HASHES_PATH,
  source_rights_policy_path: Path = SOURCE_RIGHTS_POLICY_PATH,
) -> dict[str, Any]:
  mechanism_artifact = _load_json(mechanism_comparison_hashes_path)
  source_rights_policy = _load_json(source_rights_policy_path)
  tp21, criteria = _criteria_vocabulary(mechanism_artifact)
  anchor_set = _empty_anchor_set(
    repo_root=repo_root,
    tp21=tp21,
    criteria=criteria,
    source_rights_policy_path=source_rights_policy_path,
    source_rights_policy=source_rights_policy,
    mechanism_comparison_hashes_path=mechanism_comparison_hashes_path,
  )
  current_outputs_admitted = anchor_set["current_comparison_outputs_admitted"]
  selected_hashes_present = anchor_set["selected_debris_output_hash_count"] > 0
  reviewer_selection_present = False
  reviewer_signoff_present = False
  release_grade_validated = (
    selected_hashes_present
    and reviewer_selection_present
    and reviewer_signoff_present
    and current_outputs_admitted
  )
  blockers = [
    "missing page/section provenance labels for a reviewer-selected TP-21 debris comparison case",
    "missing selected output preimage hash for the reviewer-selected concrete case",
    "missing independent reviewer signoff for the selected TP-21 debris case",
    "source-rights allowed-output policy does not admit current comparison output hashes",
  ]
  guards = _non_authoritative_guards()

  return {
    "schema_version": SCHEMA_VERSION,
    "package_id": PACKAGE_ID,
    "status": "blocked_fail_closed_tp21_debris_admission_gate",
    "review_target": "res_005_tp21_debris_admission_gate",
    "residual_id": "RES-005",
    "source_payload_pack_ref": _rel(
      comparison_hashes.SOURCE_PAYLOAD_PACK_DIR, repo_root
    ),
    "mechanism_comparison_hashes_ref": _rel(
      mechanism_comparison_hashes_path, repo_root
    ),
    "mechanism_comparison_hashes_input_status": mechanism_artifact.get(
      "status", ""
    ),
    "source_rights_policy_ref": _rel(source_rights_policy_path, repo_root),
    "source_rights_policy_status": source_rights_policy.get(
      "allowed_output_policy", {}
    ).get("policy_status", ""),
    "criteria_vocabulary": {
      "status": tp21.get("criteria_vocabulary_status", ""),
      "criteria_vocabulary_sha256": tp21.get("criteria_vocabulary_sha256", ""),
      "criteria_vocabulary_is_calibration": False,
      "controlled_criteria_keys": [row["criteria_key"] for row in criteria],
      "controlled_criteria_key_count": len(criteria),
      "controlled_criteria_keys_only": True,
    },
    "reviewer_selected_case_artifact": {
      "artifact_status": "missing_fail_closed",
      "page_section_provenance_labels_present": False,
      "selected_output_preimage_hash_present": False,
      "selected_output_hashes_present": selected_hashes_present,
      "reviewer_signoff_present": reviewer_signoff_present,
      "allowed_output_signoff_present": current_outputs_admitted,
      "source_content_copied_to_dataset": False,
      "source_tables_copied_to_dataset": False,
      "source_numeric_values_copied_to_dataset": False,
    },
    "selected_debris_output_anchor_set": anchor_set,
    "selected_output_requirements": _selected_output_requirements(criteria),
    "page_section_provenance_requirements": _provenance_requirements(
      current_outputs_admitted=current_outputs_admitted
    ),
    "admission_decision": {
      "decision": "not_admitted_fail_closed",
      "narrowly_closes_res005": False,
      "closed_residual_ids_by_this_gate": [],
      "closed_residual_subscopes_by_this_gate": [],
      "selected_tp21_case_admitted_for_release": False,
      "benchmark_consumed_for_release": False,
      "release_grade_validated": release_grade_validated,
      "exact_blockers": blockers,
    },
    "output_policy": {
      "hash_only_selected_outputs_required": True,
      "selected_output_preimage_disclosure": (
        "hash_only; no TP-21 source prose, tables, figures, or raw "
        "numeric values may be retained in this package"
      ),
      "raw_source_content_retained": False,
      "source_tables_retained": False,
      "source_figures_retained": False,
      "source_numeric_values_retained": False,
      "benchmark_consumption_allowed": False,
    },
    "non_authoritative_guards": guards,
    "authority_guards_all_false": not any(guards.values()),
    "behavior_risks": [
      "controlled criteria keys may be mistaken for a concrete TP-21 debris benchmark case",
      "an empty hash anchor set may be mistaken for admitted comparison evidence",
      "public source retention may be mistaken for rights approval to consume document examples",
      "this gate does not grant component probability, stock, runtime, Pk, or deterministic fuze authority",
    ],
    "integration_notes": [
      "RES-005 remains open; this gate narrows it to selected-case preimage, provenance, reviewer signoff, and allowed-output signoff.",
      "TP-21 prose, tables, figures, and raw values are not copied or retained.",
      "No benchmark output is consumed for release by this gate.",
    ],
  }

def write_retained_artifacts(
  *,
  retained_dir: Path = DEFAULT_RETAINED_DIR,
  repo_root: Path = REPO_ROOT,
  mechanism_comparison_hashes_path: Path = MECHANISM_COMPARISON_HASHES_PATH,
  source_rights_policy_path: Path = SOURCE_RIGHTS_POLICY_PATH,
) -> dict[str, Any]:
  artifact = generate_tp21_debris_admission_gate(
    repo_root=repo_root,
    mechanism_comparison_hashes_path=mechanism_comparison_hashes_path,
    source_rights_policy_path=source_rights_policy_path,
  )
  retained_dir.mkdir(parents=True, exist_ok=True)

  anchor_set_path = retained_dir / ANCHOR_SET_FILENAME
  _write_json(anchor_set_path, artifact["selected_debris_output_anchor_set"])
  anchor_set_sha256 = _sha256_file(anchor_set_path)

  artifact_path = retained_dir / GATE_FILENAME
  _write_json(artifact_path, artifact)
  artifact_sha256 = _sha256_file(artifact_path)

  manifest = {
    "schema_version": RETAINED_MANIFEST_SCHEMA_VERSION,
    "package_id": PACKAGE_ID,
    "status": artifact["status"],
    "artifact_dir": _rel(retained_dir, repo_root),
    "res005_tp21_debris_admission_gate_artifact": {
      "filename": GATE_FILENAME,
      "relative_path": _rel(artifact_path, repo_root),
      "schema_version": artifact["schema_version"],
      "sha256": artifact_sha256,
    },
    "selected_debris_output_anchor_set_artifact": {
      "filename": ANCHOR_SET_FILENAME,
      "relative_path": _rel(anchor_set_path, repo_root),
      "schema_version": ANCHOR_SET_SCHEMA_VERSION,
      "sha256": anchor_set_sha256,
    },
    "admission_decision": artifact["admission_decision"],
    "criteria_vocabulary": artifact["criteria_vocabulary"],
    "authority_guards_all_false": artifact["authority_guards_all_false"],
    "non_authoritative_guards": artifact["non_authoritative_guards"],
  }
  manifest_path = retained_dir / RETAINED_MANIFEST_FILENAME
  _write_json(manifest_path, manifest)
  artifact["retained_artifact_sha256"] = artifact_sha256
  artifact["retained_anchor_set_sha256"] = anchor_set_sha256
  artifact["retained_manifest_sha256"] = _sha256_file(manifest_path)
  return artifact

def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description="Generate the fail-closed A2 RES-005 TP-21 debris admission gate."
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
    help="Directory for retained RES-005 debris admission artifacts.",
  )
  parser.add_argument(
    "--mechanism-comparison-hashes",
    type=Path,
    default=MECHANISM_COMPARISON_HASHES_PATH,
    help="Retained mechanism comparison hashes JSON.",
  )
  parser.add_argument(
    "--source-rights-policy",
    type=Path,
    default=SOURCE_RIGHTS_POLICY_PATH,
    help="Retained source-rights output policy gate JSON.",
  )
  args = parser.parse_args(argv)

  artifact = write_retained_artifacts(
    retained_dir=args.retained_dir,
    mechanism_comparison_hashes_path=args.mechanism_comparison_hashes,
    source_rights_policy_path=args.source_rights_policy,
  )
  if args.output:
    _write_json(args.output, artifact)
  return 0

if __name__ == "__main__":
  raise SystemExit(main())
