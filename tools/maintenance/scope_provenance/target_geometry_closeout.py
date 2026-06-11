#!/usr/bin/env python3
"""Close out RES-003 only for Stage B witness-geometry bookkeeping.

This gate consumes the existing RES-003 target geometry assumption surface plus
retained provenance and Stage B review gates. It can close only the narrow
Stage B effect-scale witness-geometry bookkeeping slice. It deliberately keeps
real F-16 component geometry, materials, occlusion, stock runtime, component
probability, Pk, and deterministic-fuze authority blocked.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
PACKAGE_ID = (
  "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
  "beam_high_near_miss_0_35m_v0"
)
GATE_SCHEMA_VERSION = "a2.res003_target_geometry_closeout_gate.v1"
MANIFEST_SCHEMA_VERSION = "a2.res003_target_geometry_closeout_manifest.v1"
GENERATED_ON = "2026-05-31"
WORKER_ID = "A2-RES003-GEOMETRY-CLOSEOUT"

PACKAGE_DIR = (
  REPO_ROOT
  / "docs"
  / "task"
  / "air_combat"
  / "archive"
  / "a2_high_fidelity_damage_model"
  / "calibration"
  / "vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m"
)
DEFAULT_OUTPUT_DIR = (
  PACKAGE_DIR / "retained_artifacts" / "res003_target_geometry_closeout_20260531"
)
DEFAULT_DOC_OUTPUT = (
  PACKAGE_DIR / "validation_res003_target_geometry_closeout_gate_20260531.zh.md"
)

EXPECTED_USED_GEOMETRY_ITEMS = ["outer_bbox", "beam_witness_panel"]
EXPECTED_UNUSED_GEOMETRY_ITEMS = [
  "nose_radar_rough_region",
  "engine_aft_region",
  "wing_and_control_surface_regions",
  "right_aileron_actuator_projection",
]
EXPECTED_UNSUPPORTED_GEOMETRY_ITEMS = [
  "internal_material_or_armor",
  "occlusion_and_exposed_area_truth",
]
EXPECTED_STAGE_B_SOURCE_IDS = [
  "F16-TG-SRC-001",
  "F16-TG-SRC-002",
  "F16-TG-SRC-012",
]


def _evidence_refs(package_dir: Path) -> dict[str, tuple[Path, bool, str]]:
  retained = package_dir / "retained_artifacts"
  return {
    "residual_register": (
      package_dir / "residual_register.zh.md",
      True,
      "canonical_residual_status",
    ),
    "target_geometry_assumptions": (
      package_dir / "target_geometry_assumptions_stage_b_effect_scale_20260530.zh.md",
      True,
      "res003_stage_b_assumption_surface",
    ),
    "geometry_warhead_row_provenance_gate": (
      retained
      / "geometry_warhead_row_provenance_20260531"
      / "geometry_warhead_row_provenance_gate.json",
      True,
      "res003_row_provenance_interlock",
    ),
    "stage_b_independent_review_gate": (
      retained
      / "stage_b_independent_review_20260531"
      / "stage_b_independent_review_gate.json",
      True,
      "stage_b_independent_review_boundary",
    ),
    "scope_bucket_independent_review_gate": (
      retained
      / "scope_bucket_independent_review_20260531"
      / "scope_bucket_independent_review_gate.json",
      True,
      "stage_b_scope_bucket_boundary",
    ),
  }


def _display_path(path: Path, repo_root: Path) -> str:
  try:
    return path.relative_to(repo_root).as_posix()
  except ValueError:
    return str(path)


def _doc_link(path: Path, doc_output: Path, repo_root: Path) -> str:
  try:
    return Path(os.path.relpath(path.resolve(), doc_output.parent.resolve())).as_posix()
  except ValueError:
    return _display_path(path, repo_root)


def _canonical_json(payload: dict[str, Any]) -> str:
  return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)


def _sha256_bytes(data: bytes) -> str:
  return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
  return _sha256_bytes(path.read_bytes())


def _payload_sha256(payload: dict[str, Any]) -> str:
  return _sha256_bytes(_canonical_json(payload).encode("utf-8"))


def _read_text(path: Path) -> str:
  if not path.is_file():
    return ""
  return path.read_text(encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any] | None:
  if not path.is_file():
    return None
  return json.loads(path.read_text(encoding="utf-8"))


def _evidence_record(
  *, evidence_id: str, path: Path, required: bool, role: str, repo_root: Path
) -> dict[str, Any]:
  record: dict[str, Any] = {
    "evidence_id": evidence_id,
    "path": _display_path(path, repo_root),
    "required": required,
    "role": role,
    "present": path.is_file(),
  }
  if path.is_file():
    digest = _sha256_file(path)
    record.update(
      {
        "content_sha256": digest,
        "content_hash": f"sha256:{digest}",
        "size_bytes": path.stat().st_size,
      }
    )
    if path.suffix == ".json":
      payload = _load_json(path) or {}
      record["schema_version"] = payload.get("schema_version", "")
      record["status"] = payload.get("status", "")
  return record


def _strip_cell(cell: str) -> str:
  return cell.strip().strip("`").strip()


def _split_markdown_row(line: str) -> list[str]:
  return [_strip_cell(cell) for cell in line.strip().strip("|").split("|")]


def _extract_field(text: str, field: str) -> str:
  for line in text.splitlines():
    if not line.startswith("|"):
      continue
    cells = _split_markdown_row(line)
    if len(cells) >= 2 and cells[0] == field:
      return cells[1]
  return ""


def _source_ids_from_cell(cell: str) -> list[str]:
  source_ids: list[str] = []
  pattern = re.compile(
    r"(?P<prefix>F16-TG-(?:SRC|3P)-)(?P<suffixes>\d{3}(?:/\d{3})*)"
  )
  for match in pattern.finditer(cell):
    prefix = match.group("prefix")
    for suffix in match.group("suffixes").split("/"):
      source_ids.append(f"{prefix}{suffix}")
  return source_ids


def _target_geometry_rows(text: str) -> dict[str, dict[str, Any]]:
  rows: dict[str, dict[str, Any]] = {}
  expected = set(
    EXPECTED_USED_GEOMETRY_ITEMS
    + EXPECTED_UNUSED_GEOMETRY_ITEMS
    + EXPECTED_UNSUPPORTED_GEOMETRY_ITEMS
  )
  for line in text.splitlines():
    if not line.startswith("|"):
      continue
    cells = _split_markdown_row(line)
    if len(cells) < 8 or cells[0] not in expected:
      continue
    rows[cells[0]] = {
      "geometry_item": cells[0],
      "runtime_ref": cells[1],
      "source_ids": _source_ids_from_cell(cells[2]),
      "support_level": cells[3],
      "value_or_bucket": cells[4],
      "used_by_stage_b": cells[5],
      "not_supported_claims": cells[6],
      "residual": cells[7],
    }
  return rows


def _residual_register_status(text: str, residual_id: str) -> dict[str, str]:
  for line in text.splitlines():
    if f"`{residual_id}`" not in line:
      continue
    cells = _split_markdown_row(line)
    if len(cells) >= 7:
      return {
        "residual_id": residual_id,
        "area": cells[1],
        "description": cells[2],
        "scope_impact": cells[3],
        "blocked_authority": cells[4],
        "close_condition": cells[5],
        "register_status": cells[6],
      }
  return {
    "residual_id": residual_id,
    "area": "",
    "description": "",
    "scope_impact": "",
    "blocked_authority": "",
    "close_condition": "",
    "register_status": "missing",
  }


def _check(check_id: str, summary: str, passed: bool) -> dict[str, Any]:
  return {
    "check_id": check_id,
    "summary": summary,
    "pass": bool(passed),
  }


def _all_authority_values_false(guards: dict[str, Any] | None) -> bool:
  if not guards:
    return False
  return not any(value is True for value in guards.values())


def _authority_guards() -> dict[str, bool]:
  return {
    "stock_descriptor_created": False,
    "stock_database_authority_granted": False,
    "stock_runtime_authority_granted": False,
    "runtime_descriptor_created": False,
    "runtime_authority_granted": False,
    "target_geometry_authority_granted": False,
    "target_component_geometry_authority_granted": False,
    "target_material_authority_granted": False,
    "target_occlusion_authority_granted": False,
    "row_level_geometry_authority_granted": False,
    "witness_geometry_bookkeeping_promoted_to_truth": False,
    "effect_scale_authority_granted": False,
    "effect_scale_authority_in_stock": False,
    "effect_scale_authority_released": False,
    "component_failure_probability_authority_granted": False,
    "component_failure_probability_authority_in_stock": False,
    "component_failure_probability_authority_released": False,
    "pk_authority_granted": False,
    "pk_authority_released": False,
    "deterministic_fuze_authority_granted": False,
    "deterministic_fuze_authority_released": False,
    "formal_validation_manifest_promoted": False,
    "hard_gate_pass_is_release": False,
    "replacement_allowed": False,
  }


def _find_benchmark_row(payload: dict[str, Any], benchmark_id: str) -> dict[str, Any]:
  rows = payload.get("benchmark_input_independence_review", {}).get(
    "benchmark_independence_rows", []
  )
  for row in rows:
    if row.get("benchmark_id") == benchmark_id:
      return row
  return {}


def _stage_b_assumption_review(target_text: str) -> dict[str, Any]:
  rows = _target_geometry_rows(target_text)
  used_rows = [rows.get(item, {}) for item in EXPECTED_USED_GEOMETRY_ITEMS]
  unused_rows = [rows.get(item, {}) for item in EXPECTED_UNUSED_GEOMETRY_ITEMS]
  unsupported_rows = [
    rows.get(item, {}) for item in EXPECTED_UNSUPPORTED_GEOMETRY_ITEMS
  ]
  used_source_ids = sorted(
    {
      source_id
      for row in used_rows
      for source_id in row.get("source_ids", [])
    }
  )

  checks = [
    _check(
      "RES003-ASSUME-001",
      "target geometry assumption manifest is frozen for Stage B review only",
      _extract_field(target_text, "package_id") == PACKAGE_ID
      and _extract_field(target_text, "primary_release_scope")
      == "effect_scale_authority_only"
      and _extract_field(target_text, "author_status")
      == "frozen_for_stage_b_review_only",
    ),
    _check(
      "RES003-ASSUME-002",
      "only outer_bbox and beam_witness_panel are used by Stage B",
      [row.get("geometry_item") for row in used_rows]
      == EXPECTED_USED_GEOMETRY_ITEMS
      and all(row.get("used_by_stage_b") == "yes" for row in used_rows)
      and all(
        row.get("used_by_stage_b") in {"no_direct_numeric_use_in_stage_b", "no_for_stage_b_effect_scale_only"}
        for row in unused_rows
      ),
    ),
    _check(
      "RES003-ASSUME-003",
      "Stage B witness rows are candidate/bookkeeping rows with expected source IDs",
      rows.get("outer_bbox", {}).get("support_level")
      == "candidate_dimension_anchor"
      and rows.get("beam_witness_panel", {}).get("support_level")
      == "repo_authored_witness_geometry"
      and set(EXPECTED_STAGE_B_SOURCE_IDS).issubset(used_source_ids),
    ),
    _check(
      "RES003-ASSUME-004",
      "component geometry, material, and occlusion truth are excluded or unsupported",
      all(row.get("used_by_stage_b") != "yes" for row in unused_rows)
      and all(row.get("support_level") == "unsupported" for row in unsupported_rows)
      and "runtime geometry authority" in target_text
      and "true F-16 internal vulnerability geometry" in target_text,
    ),
    _check(
      "RES003-ASSUME-005",
      "documented current decision limits the claim to candidate effect-scale bookkeeping",
      "enough for candidate effect-scale bookkeeping" in target_text
      and "not enough for internal-vulnerability authority" in target_text,
    ),
  ]
  return {
    "status": (
      "stage_b_assumption_surface_bounded"
      if all(row["pass"] for row in checks)
      else "stage_b_assumption_surface_incomplete"
    ),
    "used_by_stage_b_geometry_items": EXPECTED_USED_GEOMETRY_ITEMS,
    "excluded_stage_b_geometry_items": EXPECTED_UNUSED_GEOMETRY_ITEMS,
    "unsupported_truth_items": EXPECTED_UNSUPPORTED_GEOMETRY_ITEMS,
    "stage_b_source_ids": used_source_ids,
    "row_findings": rows,
    "checks": checks,
  }


def _provenance_review(payload: dict[str, Any] | None) -> dict[str, Any]:
  payload = payload or {}
  res003 = payload.get("residual_status", {}).get("RES-003", {})
  release_blockers = payload.get("release_blockers", {}).get("RES-003", [])
  checks = [
    _check(
      "RES003-PROV-001",
      "geometry/warhead provenance gate is present and keeps RES-003 non-authoritative",
      payload.get("schema_version")
      == "a2.geometry_warhead_row_provenance_gate.v1"
      and payload.get("status")
      == "blocked_non_authoritative_geometry_warhead_row_provenance_candidate",
    ),
    _check(
      "RES003-PROV-002",
      "provenance gate marks the author-side RES-003 subslice ready but not release-grade",
      res003.get("author_side_subslice_ready") is True
      and res003.get("release_grade") is False
      and res003.get("closed_by_this_gate") is False,
    ),
    _check(
      "RES003-PROV-003",
      "provenance gate explicitly blocks true 3D exposure, occlusion, and material authority",
      any("3D exposure" in blocker for blocker in release_blockers)
      and any("material" in blocker for blocker in release_blockers)
      and any("occlusion" in blocker for blocker in release_blockers),
    ),
    _check(
      "RES003-PROV-004",
      "provenance gate grants no target, stock, effect-scale, component, Pk, or fuze authority",
      _all_authority_values_false(payload.get("authority_guard")),
    ),
  ]
  return {
    "status": (
      "row_provenance_interlock_preserved"
      if all(row["pass"] for row in checks)
      else "row_provenance_interlock_incomplete"
    ),
    "upstream_status": payload.get("status", "missing"),
    "upstream_res003_status": res003,
    "release_blockers_preserved": release_blockers,
    "checks": checks,
  }


def _stage_b_review_interlock(
  *,
  independent_payload: dict[str, Any] | None,
  scope_payload: dict[str, Any] | None,
) -> dict[str, Any]:
  independent_payload = independent_payload or {}
  scope_payload = scope_payload or {}
  bfm003 = _find_benchmark_row(independent_payload, "BFM-BM-003")
  release_decision = independent_payload.get("release_decision", {})

  checks = [
    _check(
      "RES003-STAGEB-001",
      "retained Stage B independent review passed but remains release-blocked",
      independent_payload.get("schema_version")
      == "a2.stage_b_independent_review_gate.v1"
      and independent_payload.get("status")
      == "independent_review_passed_release_blocked"
      and release_decision.get("release_blocked") is True,
    ),
    _check(
      "RES003-STAGEB-002",
      "BFM-BM-003 is limited to sampler replay inside witness-geometry bookkeeping",
      bfm003.get("benchmark_id") == "BFM-BM-003"
      and bfm003.get("allowed_claim")
      == "sampling replay and convergence inside witness-geometry bookkeeping"
      and bfm003.get("independence_class")
      == "independent_for_sampler_replay_not_for_target_truth"
      and bfm003.get("forbidden_claim")
      == "true F-16 exposure geometry or direction-pattern truth",
    ),
    _check(
      "RES003-STAGEB-003",
      "Stage B independent review does not convert hard-gate pass into release authority",
      release_decision.get("hard_gate_pass_is_release") is False
      and release_decision.get("stage_c_component_probability_release_included")
      is False
      and release_decision.get("stock_runtime_authority_granted") is False,
    ),
    _check(
      "RES003-STAGEB-004",
      "scope bucket independent review is passed only as a review record and remains release-blocked",
      scope_payload.get("schema_version")
      == "a2.scope_bucket_independent_review_gate.v1"
      and scope_payload.get("status")
      == "scope_bucket_independent_review_passed_release_blocked"
      and scope_payload.get("release_target") == "none_review_gate_record_only",
    ),
    _check(
      "RES003-STAGEB-005",
      "retained Stage B review gates grant no stock, effect-scale, component, Pk, or fuze authority",
      _all_authority_values_false(independent_payload.get("non_authoritative_guards"))
      and _all_authority_values_false(scope_payload.get("authority_guards")),
    ),
  ]
  return {
    "status": (
      "stage_b_review_interlock_bounded"
      if all(row["pass"] for row in checks)
      else "stage_b_review_interlock_incomplete"
    ),
    "bfm_bm_003_independence_row": bfm003,
    "independent_review_status": independent_payload.get("status", "missing"),
    "scope_review_status": scope_payload.get("status", "missing"),
    "checks": checks,
  }


def _minimum_gap_list(
  *, closeout_allowed: bool, failed_checks: list[dict[str, Any]], missing: list[dict[str, Any]]
) -> list[dict[str, str]]:
  if closeout_allowed:
    return [
      {
        "gap_id": "RES003-PHASE5-AUTHORITY-001",
        "owner": "same_scope_phase5_component_probability_geometry_worker",
        "minimum_next_step": (
          "bind real component geometry/material/occlusion/exposed-area evidence "
          "before any release-grade component_failure_probability_authority or vulnerability authority claim"
        ),
      },
      {
        "gap_id": "RES003-GLOBAL-001",
        "owner": "main_thread_acceptance_owner",
        "minimum_next_step": (
          "if accepted, update the residual register only as a Stage B witness-geometry "
          "bookkeeping narrow closeout, not as global target-geometry authority"
        ),
      },
    ]

  gaps = [
    {
      "gap_id": f"missing:{row['evidence_id']}",
      "owner": "res003_closeout_worker_or_evidence_owner",
      "minimum_next_step": f"restore required evidence at {row['path']}",
    }
    for row in missing
  ]
  gaps.extend(
    {
      "gap_id": f"failed:{row['check_id']}",
      "owner": "res003_closeout_worker_or_upstream_gate_owner",
      "minimum_next_step": row["summary"],
    }
    for row in failed_checks
  )
  return gaps


def generate_res003_target_geometry_closeout_gate(
  *,
  repo_root: Path = REPO_ROOT,
  package_dir: Path = PACKAGE_DIR,
) -> dict[str, Any]:
  refs = _evidence_refs(package_dir)
  consumed_evidence = [
    _evidence_record(
      evidence_id=evidence_id,
      path=path,
      required=required,
      role=role,
      repo_root=repo_root,
    )
    for evidence_id, (path, required, role) in refs.items()
  ]
  missing_evidence = [
    row for row in consumed_evidence if row["required"] and not row["present"]
  ]

  residual_text = _read_text(refs["residual_register"][0])
  target_text = _read_text(refs["target_geometry_assumptions"][0])
  provenance_payload = _load_json(refs["geometry_warhead_row_provenance_gate"][0])
  independent_payload = _load_json(refs["stage_b_independent_review_gate"][0])
  scope_payload = _load_json(refs["scope_bucket_independent_review_gate"][0])

  assumption_review = _stage_b_assumption_review(target_text)
  provenance_review = _provenance_review(provenance_payload)
  stage_b_review = _stage_b_review_interlock(
    independent_payload=independent_payload,
    scope_payload=scope_payload,
  )
  all_checks = (
    assumption_review["checks"]
    + provenance_review["checks"]
    + stage_b_review["checks"]
  )
  failed_checks = [row for row in all_checks if not row["pass"]]
  closeout_allowed = not missing_evidence and not failed_checks

  decision_status = (
    "res003_stage_b_effect_scale_witness_geometry_closeout_pass_release_blocked"
    if closeout_allowed
    else "res003_target_geometry_closeout_fail_closed"
  )

  return {
    "package_id": PACKAGE_ID,
    "schema_version": GATE_SCHEMA_VERSION,
    "generated_on": GENERATED_ON,
    "status": decision_status,
    "worker_identity": {
      "worker_id": WORKER_ID,
      "nickname": "res003-geometry-closeout-worker",
      "independence_class": "project_internal_closeout_worker",
      "external_validation_claimed": False,
    },
    "review_target": "RES-003_target_geometry_closeout",
    "release_target": "stage_b_effect_scale_witness_geometry_bookkeeping_only",
    "scope": {
      "target_type": "F-16C_Block50",
      "weapon_class": "AIM-120C-class",
      "weapon_family": "blast_fragmentation",
      "aspect_bucket": "beam",
      "closure_bucket": "high",
      "candidate_scope_label": "near_miss_0_35m",
      "stage_b_scope": "effect_scale_only",
    },
    "consumed_evidence": consumed_evidence,
    "missing_evidence": missing_evidence,
    "stage_b_assumption_review": assumption_review,
    "provenance_interlock": provenance_review,
    "stage_b_review_interlock": stage_b_review,
    "residual_register_snapshot": _residual_register_status(
      residual_text, "RES-003"
    ),
    "residual_closeout_decisions": {
      "RES-003": {
        "stage_b_effect_scale_witness_geometry": (
          "closed_narrow_non_authoritative"
          if closeout_allowed
          else "fail_closed"
        ),
        "closed_residual_subscope": (
          "stage_b_effect_scale_witness_geometry_bookkeeping"
          if closeout_allowed
          else "none"
        ),
        "global_target_geometry_authority": "not_granted",
        "real_f16_component_geometry_material_occlusion": "blocked",
        "row_level_geometry_release_grade": "not_granted",
        "phase5_component_probability_geometry_dependency": "blocked",
        "residual_register_edit_required_by_this_gate": False,
        "main_thread_register_integration_note": (
          "may mark only the Stage B witness-geometry bookkeeping subscope "
          "as closed if accepted; do not mark global RES-003 geometry authority closed"
        ),
      }
    },
    "closeout_decision": {
      "stage_b_effect_scale_witness_geometry_closeout_complete": closeout_allowed,
      "stage_b_effect_scale_closeout_is_release_authority": False,
      "global_res003_target_geometry_closeout_complete": False,
      "real_f16_vulnerability_geometry_closeout_complete": False,
      "component_material_occlusion_closeout_complete": False,
      "closed_residual_ids_by_this_gate": [],
      "closed_residual_subscopes_by_this_gate": (
        ["RES-003:stage_b_effect_scale_witness_geometry_bookkeeping"]
        if closeout_allowed
        else []
      ),
      "release_ready": False,
      "release_blocked": True,
      "authority_release_included": False,
    },
    "authority_guards": _authority_guards(),
    "explicit_boundaries": [
      "The closeout is limited to Stage B effect-scale witness-geometry bookkeeping.",
      "outer_bbox is a coarse F-16 dimension anchor, not true section or station geometry.",
      "beam_witness_panel is repo-authored sampler bookkeeping, not true 3D exposure geometry.",
      "No real F-16 component coordinates, materials, armor, occlusion, or exposed vulnerable area authority is granted.",
      "No stock descriptor, runtime authority, component probability, Pk, deterministic fuze, or formal validation promotion is granted.",
      "Phase 5 component_failure_probability authority remains blocked until component geometry/material/occlusion evidence and independent fragility truth exist.",
    ],
    "minimum_gap_list": _minimum_gap_list(
      closeout_allowed=closeout_allowed,
      failed_checks=failed_checks,
      missing=missing_evidence,
    ),
    "behavior_risks": [
      "coarse outer dimensions may be over-read as true F-16C section or station geometry",
      "beam witness sampler bookkeeping may be over-read as real 3D exposure or occlusion truth",
      "Stage B narrow closeout may be mistaken for Phase 5 component-geometry or fragility authority",
    ],
    "integration_notes": [
      "This gate supersedes RES-003 only for the bounded Stage B witness-geometry bookkeeping subscope.",
      "Existing geometry/warhead provenance evidence remains valid and still blocks release-grade row-level geometry authority.",
      "Main-thread acceptance should preserve RES-004/005/006 and Phase 5 authority blockers unless their own gates close.",
      "RES-013 Pk and RES-014 deterministic-fuze boundaries remain outside this package.",
    ],
  }


def _manifest_payload(
  *, artifact: dict[str, Any], output_dir: Path, repo_root: Path
) -> dict[str, Any]:
  gate_path = output_dir / "res003_target_geometry_closeout_gate.json"
  return {
    "package_id": PACKAGE_ID,
    "schema_version": MANIFEST_SCHEMA_VERSION,
    "generated_on": GENERATED_ON,
    "status": "res003_target_geometry_closeout_retained_release_blocked",
    "artifacts": [
      {
        "artifact_key": "res003_target_geometry_closeout_gate",
        "path": _display_path(gate_path, repo_root),
        "content_sha256": _sha256_file(gate_path),
        "size_bytes": gate_path.stat().st_size,
      }
    ],
    "closeout_decision": artifact["closeout_decision"],
    "authority_guards": artifact["authority_guards"],
    "worker_identity": artifact["worker_identity"],
  }


def _render_doc(
  *,
  artifact: dict[str, Any],
  manifest: dict[str, Any],
  gate_sha256: str,
  manifest_sha256: str,
  output_dir: Path,
  doc_output: Path,
  repo_root: Path,
) -> str:
  res003 = artifact["residual_closeout_decisions"]["RES-003"]
  guards = artifact["authority_guards"]
  guard_rows = "\n".join(
    f"| `{key}` | `{str(value).lower()}` |" for key, value in guards.items()
  )
  evidence_rows = "\n".join(
    f"| `{row['evidence_id']}` | `{row['present']}` | `{row.get('status', 'n/a')}` | `{row['path']}` |"
    for row in artifact["consumed_evidence"]
  )
  gap_rows = "\n".join(
    f"| `{row['gap_id']}` | `{row['owner']}` | {row['minimum_next_step']} |"
    for row in artifact["minimum_gap_list"]
  )
  boundary_rows = "\n".join(
    f"- {boundary}" for boundary in artifact["explicit_boundaries"]
  )
  return f"""# Validation RES-003 Target Geometry Closeout Gate - 2026-05-31

状态：`generated_from_res003_target_geometry_closeout_gate / non-authoritative / release_blocked`。

本文记录 `RES-003 target geometry` 的窄域 closeout。该 gate 只允许关闭 Stage B `effect_scale` 的 witness-geometry bookkeeping 子范围；不关闭真实 F-16 component geometry、material、occlusion、exposed area 或 Phase 5 `component_failure_probability_authority` 依赖。

## 1. Retained Artifact

| 字段 | 值 |
|---|---|
| `package_id` | `{artifact['package_id']}` |
| `schema_version` | `{artifact['schema_version']}` |
| `tool_ref` | [damage_model.py]({_doc_link(repo_root / "tools" / "maintenance" / "damage_model.py", doc_output, repo_root)}) `scope-provenance target-geometry-closeout` |
| `retained_artifact` | [{output_dir.name}/res003_target_geometry_closeout_gate.json]({_doc_link(output_dir / 'res003_target_geometry_closeout_gate.json', doc_output, repo_root)}) |
| `retained_artifact_sha256` | `{gate_sha256}` |
| `manifest` | [{output_dir.name}/manifest.json]({_doc_link(output_dir / 'manifest.json', doc_output, repo_root)}) |
| `manifest_sha256` | `{manifest_sha256}` |
| `overall_status` | `{artifact['status']}` |
| `manifest_status` | `{manifest['status']}` |

## 2. Decision

| 字段 | 值 |
|---|---|
| `stage_b_effect_scale_witness_geometry` | `{res003['stage_b_effect_scale_witness_geometry']}` |
| `closed_residual_subscope` | `{res003['closed_residual_subscope']}` |
| `global_target_geometry_authority` | `{res003['global_target_geometry_authority']}` |
| `real_f16_component_geometry_material_occlusion` | `{res003['real_f16_component_geometry_material_occlusion']}` |
| `phase5_component_probability_geometry_dependency` | `{res003['phase5_component_probability_geometry_dependency']}` |
| `release_ready` | `{str(artifact['closeout_decision']['release_ready']).lower()}` |
| `release_blocked` | `{str(artifact['closeout_decision']['release_blocked']).lower()}` |

当前可审计结论：

> `RES-003 is narrowly closed only for Stage B effect-scale witness-geometry bookkeeping; real F-16 vulnerability geometry, material, occlusion, Phase 5 component_failure_probability_authority, stock runtime, Pk and deterministic-fuze authority remain blocked`.

## 3. Consumed Evidence

| evidence | present | upstream status | path |
|---|---:|---|---|
{evidence_rows}

## 4. Non-Authoritative Guards

| guard | current value |
|---|---:|
{guard_rows}

## 5. Boundaries

{boundary_rows}

## 6. Remaining Paths

| gap | owner | minimum next step |
|---|---|---|
{gap_rows}
"""


def write_retained_outputs(
  *,
  artifact: dict[str, Any],
  output_dir: Path = DEFAULT_OUTPUT_DIR,
  doc_output: Path = DEFAULT_DOC_OUTPUT,
  repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
  output_dir.mkdir(parents=True, exist_ok=True)
  gate_path = output_dir / "res003_target_geometry_closeout_gate.json"
  gate_path.write_text(_canonical_json(artifact) + "\n", encoding="utf-8")
  gate_sha256 = _sha256_file(gate_path)

  manifest = _manifest_payload(
    artifact=artifact, output_dir=output_dir, repo_root=repo_root
  )
  manifest_path = output_dir / "manifest.json"
  manifest_path.write_text(_canonical_json(manifest) + "\n", encoding="utf-8")
  manifest_sha256 = _sha256_file(manifest_path)

  doc_output.parent.mkdir(parents=True, exist_ok=True)
  doc_output.write_text(
    _render_doc(
      artifact=artifact,
      manifest=manifest,
      gate_sha256=gate_sha256,
      manifest_sha256=manifest_sha256,
      output_dir=output_dir,
      doc_output=doc_output,
      repo_root=repo_root,
    ),
    encoding="utf-8",
  )

  return {
    "status": artifact["status"],
    "gate_path": _display_path(gate_path, repo_root),
    "gate_sha256": gate_sha256,
    "manifest_path": _display_path(manifest_path, repo_root),
    "manifest_sha256": manifest_sha256,
    "doc_path": _display_path(doc_output, repo_root),
    "closeout_decision": artifact["closeout_decision"],
  }


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description="Generate the RES-003 target geometry narrow closeout gate."
  )
  parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
  parser.add_argument("--doc-output", type=Path, default=DEFAULT_DOC_OUTPUT)
  args = parser.parse_args(argv)

  artifact = generate_res003_target_geometry_closeout_gate()
  summary = write_retained_outputs(
    artifact=artifact,
    output_dir=args.output_dir,
    doc_output=args.doc_output,
  )
  print(_canonical_json(summary))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
