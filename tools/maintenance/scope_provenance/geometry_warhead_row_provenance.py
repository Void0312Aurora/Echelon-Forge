#!/usr/bin/env python3
"""Generate the A2 geometry/warhead row provenance gate.

This gate is intentionally narrow and fail-closed. It consumes the current
RES-003/RES-004 evidence surface and records whether row-level geometry and
warhead provenance/bounds are release-grade for the fixed candidate scope. It
does not grant stock, effect-scale, component-probability, Pk, or fuze
authority.
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
PACKAGE_ID = (
  "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
  "beam_high_near_miss_0_35m_v0"
)
SCHEMA_VERSION = "a2.geometry_warhead_row_provenance_gate.v1"
ARTIFACT_DATE = "20260531"
RESIDUAL_IDS = ("RES-003", "RES-004")

def _package_dir(repo_root: Path) -> Path:
  return (
    repo_root
    / "docs"
    / "task"
    / "air_combat"
    / "archive"
    / "a2_high_fidelity_damage_model"
    / "calibration"
    / "vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m"
  )

def _a2_root(repo_root: Path) -> Path:
  return (
    repo_root
    / "docs"
    / "task"
    / "air_combat"
    / "archive"
    / "a2_high_fidelity_damage_model"
  )

def _default_retained_dir(repo_root: Path) -> Path:
  return (
    _package_dir(repo_root)
    / "retained_artifacts"
    / f"geometry_warhead_row_provenance_{ARTIFACT_DATE}"
  )

def _default_doc_path(repo_root: Path) -> Path:
  return (
    _package_dir(repo_root)
    / f"validation_geometry_warhead_row_provenance_gate_{ARTIFACT_DATE}.zh.md"
  )

def _input_refs(repo_root: Path) -> dict[str, tuple[Path, bool, str]]:
  package_dir = _package_dir(repo_root)
  data_root = _a2_root(repo_root) / "data_collection"
  mechanism_dir = (
    package_dir / "retained_artifacts" / f"mechanism_source_closeout_{ARTIFACT_DATE}"
  )
  return {
    "subagent_usage_policy": (
      repo_root / "docs" / "standards" / "governance" / "subagent_usage_policy.md",
      True,
      "governance_boundary",
    ),
    "residual_register": (
      package_dir / "residual_register.zh.md",
      True,
      "residual_status_source",
    ),
    "target_geometry_assumptions": (
      package_dir / "target_geometry_assumptions_stage_b_effect_scale_20260530.zh.md",
      True,
      "res_003_assumption_surface",
    ),
    "warhead_scope_and_sensitivity": (
      package_dir / "warhead_scope_and_sensitivity_stage_b_effect_scale_20260530.zh.md",
      True,
      "res_004_scope_surface",
    ),
    "artifact_pin_manifest": (
      package_dir / "artifact_pin_manifest_stage_b_effect_scale_20260530.zh.md",
      True,
      "source_pin_boundary",
    ),
    "target_geometry_source_ledger": (
      data_root / "f16c_block50_target_geometry" / "source_ledger.zh.md",
      True,
      "res_003_source_ledger",
    ),
    "warhead_source_ledger": (
      data_root / "aim120c_warhead_fuze" / "source_ledger.zh.md",
      True,
      "res_004_source_ledger",
    ),
    "mechanism_source_closeout_doc": (
      package_dir / f"validation_mechanism_source_closeout_gate_{ARTIFACT_DATE}.zh.md",
      False,
      "optional_upstream_closeout_doc",
    ),
    "mechanism_source_closeout_json": (
      mechanism_dir / "mechanism_source_closeout_gate.json",
      False,
      "optional_upstream_closeout_artifact",
    ),
  }

def _rel(path: Path, repo_root: Path) -> str:
  # Kept local: non-resolving; differs from manifest_integrity._display_path.
  try:
    return path.relative_to(repo_root).as_posix()
  except ValueError:
    return path.as_posix()

def _doc_link(path: Path, doc_path: Path, repo_root: Path) -> str:
  try:
    return Path(os.path.relpath(path.resolve(), doc_path.parent.resolve())).as_posix()
  except ValueError:
    return _rel(path, repo_root)

def _read_text(path: Path) -> str:
  return path.read_text(encoding="utf-8")

def _sha256_bytes(data: bytes) -> str:
  return hashlib.sha256(data).hexdigest()

def _input_record(
  *, key: str, path: Path, required: bool, role: str, repo_root: Path
) -> dict[str, Any]:
  exists = path.is_file()
  record: dict[str, Any] = {
    "input_id": key,
    "path": _rel(path, repo_root),
    "required": required,
    "role": role,
    "exists": exists,
  }
  if exists:
    digest = _sha256_file(path)
    record.update(
      {
        "sha256": digest,
        "content_hash": f"sha256:{digest}",
        "size_bytes": path.stat().st_size,
      }
    )
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

def _table_rows(text: str, first_column_prefixes: tuple[str, ...]) -> list[list[str]]:
  rows: list[list[str]] = []
  for line in text.splitlines():
    if not line.startswith("|"):
      continue
    cells = _split_markdown_row(line)
    if not cells:
      continue
    if cells[0].startswith(first_column_prefixes):
      rows.append(cells)
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
        "blocked_authority": cells[4],
        "register_status": cells[6],
      }
  return {
    "residual_id": residual_id,
    "area": "",
    "description": "",
    "blocked_authority": "",
    "register_status": "missing",
  }

def _source_ids_from_cell(cell: str) -> list[str]:
  source_ids: list[str] = []
  pattern = re.compile(
    r"(?P<prefix>(?:F16-TG-(?:SRC|3P)|AIM120-(?:WF|TPC|TPC-REJ)|PHYS-BF)-)"
    r"(?P<suffixes>\d{3}(?:/\d{3})*)"
  )
  for match in pattern.finditer(cell):
    prefix = match.group("prefix")
    for suffix in match.group("suffixes").split("/"):
      source_ids.append(f"{prefix}{suffix}")
  return source_ids

def _target_geometry_rows(text: str) -> list[dict[str, Any]]:
  rows: list[dict[str, Any]] = []
  for cells in _table_rows(
    text,
    (
      "outer_bbox",
      "beam_witness_panel",
      "nose_radar_rough_region",
      "engine_aft_region",
      "wing_and_control_surface_regions",
      "right_aileron_actuator_projection",
      "internal_material_or_armor",
      "occlusion_and_exposed_area_truth",
    ),
  ):
    if len(cells) < 8:
      continue
    support_level = cells[3]
    used_by_stage_b = cells[5]
    source_ids = _source_ids_from_cell(cells[2])
    row_release_ready = False
    if cells[0] == "outer_bbox":
      blocker = "dimension_anchor_has_no_reviewed_row_level_error_bound"
    elif cells[0] == "beam_witness_panel":
      blocker = "repo_authored_witness_geometry_lacks_true_3d_exposure_bounds"
    elif support_level == "unsupported":
      blocker = "unsupported_public_truth"
    else:
      blocker = "rough_candidate_layout_not_release_grade_vulnerability_geometry"
    rows.append(
      {
        "geometry_item": cells[0],
        "runtime_ref": cells[1],
        "source_ids": source_ids,
        "support_level": support_level,
        "value_or_bucket": cells[4],
        "used_by_stage_b": used_by_stage_b,
        "not_supported_claims": cells[6],
        "row_release_ready": row_release_ready,
        "row_status": "blocked_row_level_bounds_missing",
        "blocker": blocker,
      }
    )
  return rows

def _warhead_rows(text: str) -> list[dict[str, Any]]:
  rows: list[dict[str, Any]] = []
  for cells in _table_rows(
    text,
    ("WAR-001", "WAR-002", "WAR-003", "WAR-004", "WAR-005", "WAR-006", "WAR-007"),
  ):
    if len(cells) < 8:
      continue
    if cells[0] == "WAR-001":
      blocker = "family_label_trace_present_but_variant_specific_bounds_missing"
    elif cells[0] in {"WAR-002", "WAR-003"}:
      blocker = "repo_toy_numeric_input_not_calibrated_aim120c_truth"
    elif cells[0] == "WAR-006":
      blocker = "third_party_mass_cluster_sanity_only_not_authority"
    elif cells[0] == "WAR-007":
      blocker = "forum_game_commercial_values_rejected"
    else:
      blocker = "method_or_term_route_not_missile_specific_truth"
    rows.append(
      {
        "assumption_id": cells[0],
        "scope_claim": cells[1],
        "source_ids": _source_ids_from_cell(cells[2]),
        "third_party_candidates": cells[3],
        "consumed_by_surrogate": cells[4],
        "sensitivity_axis": cells[5],
        "forbidden_authority_claim": cells[6],
        "row_release_ready": False,
        "row_status": "blocked_warhead_bounds_missing",
        "blocker": blocker,
      }
    )
  return rows

PIN_COLUMNS = [
  "artifact_id",
  "source_id",
  "source_tier",
  "source_ref",
  "access_status",
  "artifact_status",
  "sha256",
  "retention_ref",
  "consumption_status",
  "candidate_use",
  "authority_boundary",
  "residuals",
]

def _pin_rows(text: str, residual_id: str) -> list[dict[str, str]]:
  rows: list[dict[str, str]] = []
  for line in text.splitlines():
    cells = _split_markdown_row(line) if line.startswith("|") else []
    if len(cells) < len(PIN_COLUMNS):
      continue
    if not cells[0].startswith("PIN-") or residual_id not in cells[11]:
      continue
    rows.append(dict(zip(PIN_COLUMNS, cells[: len(PIN_COLUMNS)])))
  return rows

def _pin_summary(pin_text: str, residual_id: str) -> dict[str, Any]:
  rows = _pin_rows(pin_text, residual_id)
  return {
    "pin_ids": [row["artifact_id"] for row in rows],
    "sha256_pinned_pin_ids": [
      row["artifact_id"] for row in rows if "hash_not_applicable" not in row["sha256"] and len(row["sha256"]) >= 64
    ],
    "release_consumed_pin_ids": [
      row["artifact_id"]
      for row in rows
      if row["consumption_status"]
      in {
        "release_retained_benchmark_input",
        "release_grade_benchmark_input",
        "consumed_for_release_benchmark",
      }
    ],
    "sanity_only_pin_ids": [
      row["artifact_id"] for row in rows if row["consumption_status"] == "sanity_only"
    ],
    "rejected_pin_ids": [
      row["artifact_id"] for row in rows if row["consumption_status"] == "rejected"
    ],
    "authority_boundaries": {
      row["artifact_id"]: row["authority_boundary"] for row in rows
    },
  }

def _source_id_presence(ledger_text: str, source_ids: list[str]) -> dict[str, Any]:
  present = [source_id for source_id in source_ids if f"`{source_id}`" in ledger_text]
  return {
    "expected_source_ids": source_ids,
    "present_source_ids": present,
    "missing_source_ids": [
      source_id for source_id in source_ids if source_id not in present
    ],
    "ledger_declares_non_authoritative": "non-authoritative" in ledger_text.lower(),
  }

def _load_optional_json(path: Path) -> dict[str, Any]:
  if not path.is_file():
    return {}
  return json.loads(_read_text(path))

def _authority_guard() -> dict[str, bool]:
  return {
    "stock_descriptor_created": False,
    "stock_database_authority_granted": False,
    "target_geometry_authority_granted": False,
    "row_level_geometry_authority_granted": False,
    "aim120c_warhead_authority_granted": False,
    "warhead_class_authority_granted": False,
    "effect_scale_authority_granted": False,
    "component_failure_probability_authority_granted": False,
    "pk_authority_granted": False,
    "deterministic_fuze_authority_granted": False,
    "fuze_authority_granted": False,
  }

def _gate_check(
  *,
  check_id: str,
  residual_id: str,
  surface: str,
  author_side_evidence_present: bool,
  release_grade_satisfied: bool,
  status: str,
  evidence: dict[str, Any],
  blockers: list[str],
) -> dict[str, Any]:
  return {
    "check_id": check_id,
    "residual_id": residual_id,
    "surface": surface,
    "author_side_evidence_present": author_side_evidence_present,
    "release_grade_satisfied": release_grade_satisfied,
    "status": status,
    "evidence": evidence,
    "release_blockers": blockers,
  }

def generate_geometry_warhead_row_provenance_gate(
  *, repo_root: Path = REPO_ROOT
) -> dict[str, Any]:
  refs = _input_refs(repo_root)
  consumed_inputs = [
    _input_record(
      key=key, path=path, required=required, role=role, repo_root=repo_root
    )
    for key, (path, required, role) in refs.items()
  ]
  missing_inputs = [
    record
    for record in consumed_inputs
    if record["required"] and not record["exists"]
  ]

  optional_mechanism_dir = (
    _package_dir(repo_root)
    / "retained_artifacts"
    / f"mechanism_source_closeout_{ARTIFACT_DATE}"
  )
  optional_retained_inputs = [
    _input_record(
      key=f"mechanism_source_closeout_retained_file:{_rel(path, repo_root)}",
      path=path,
      required=False,
      role="optional_upstream_closeout_retained_artifact",
      repo_root=repo_root,
    )
    for path in sorted(optional_mechanism_dir.glob("**/*"))
    if path.is_file()
  ]

  residual_text = _read_text(refs["residual_register"][0])
  target_text = _read_text(refs["target_geometry_assumptions"][0])
  warhead_text = _read_text(refs["warhead_scope_and_sensitivity"][0])
  pin_text = _read_text(refs["artifact_pin_manifest"][0])
  target_ledger_text = _read_text(refs["target_geometry_source_ledger"][0])
  warhead_ledger_text = _read_text(refs["warhead_source_ledger"][0])
  mechanism_json = _load_optional_json(refs["mechanism_source_closeout_json"][0])

  target_rows = _target_geometry_rows(target_text)
  warhead_rows = _warhead_rows(warhead_text)
  used_geometry_rows = [
    row for row in target_rows if row["used_by_stage_b"] == "yes"
  ]
  unsupported_geometry_rows = [
    row for row in target_rows if row["support_level"] == "unsupported"
  ]
  consumed_warhead_rows = [
    row for row in warhead_rows if row["consumed_by_surrogate"] == "yes"
  ]
  rejected_warhead_rows = [
    row for row in warhead_rows if row["assumption_id"] == "WAR-007"
  ]

  target_source_ids = [
    "F16-TG-SRC-001",
    "F16-TG-SRC-002",
    "F16-TG-SRC-004",
    "F16-TG-SRC-005",
    "F16-TG-SRC-012",
  ]
  warhead_source_ids = [
    "AIM120-WF-002",
    "AIM120-WF-006",
    "AIM120-WF-007",
    "PHYS-BF-001",
    "PHYS-BF-002",
    "PHYS-BF-006",
  ]

  res003_sources = _source_id_presence(target_ledger_text, target_source_ids)
  res004_sources = _source_id_presence(warhead_ledger_text, warhead_source_ids)
  mechanism_results = mechanism_json.get("current_gate_results", {})
  mechanism_guards = mechanism_json.get("non_authoritative_guards", {})

  checks = [
    _gate_check(
      check_id="ROWWAR-RES003-001",
      residual_id="RES-003",
      surface="target_geometry_assumption_row_trace",
      author_side_evidence_present=bool(target_rows) and bool(used_geometry_rows),
      release_grade_satisfied=False,
      status="blocked_row_level_bounds_missing",
      evidence={
        "target_type": _extract_field(target_text, "target_type"),
        "author_status": _extract_field(target_text, "author_status"),
        "used_by_stage_b_geometry_items": [
          row["geometry_item"] for row in used_geometry_rows
        ],
        "unsupported_geometry_items": [
          row["geometry_item"] for row in unsupported_geometry_rows
        ],
        "row_findings": target_rows,
      },
      blockers=[
        "outer_bbox is only a coarse dimension anchor and has no reviewed row-level uncertainty bound",
        "beam_witness_panel is repo-authored witness bookkeeping and lacks true 3D exposure/occlusion bounds",
        "material, armor, occlusion and exposed-area truth are explicitly unsupported",
      ],
    ),
    _gate_check(
      check_id="ROWWAR-RES003-002",
      residual_id="RES-003",
      surface="target_geometry_source_and_pin_links",
      author_side_evidence_present=not res003_sources["missing_source_ids"],
      release_grade_satisfied=False,
      status="blocked_source_retention_review_missing",
      evidence={
        "source_evidence": res003_sources,
        "pin_evidence": _pin_summary(pin_text, "RES-003"),
      },
      blockers=[
        "target geometry ledgers support candidate/public anchors but not internal vulnerability geometry",
        "PIN-F16 rows do not provide release-grade internal component geometry, materials or vulnerability area",
      ],
    ),
    _gate_check(
      check_id="ROWWAR-RES004-001",
      residual_id="RES-004",
      surface="warhead_scope_row_trace",
      author_side_evidence_present=bool(warhead_rows) and bool(consumed_warhead_rows),
      release_grade_satisfied=False,
      status="blocked_warhead_class_bounds_missing",
      evidence={
        "weapon_class": _extract_field(warhead_text, "weapon_class"),
        "weapon_family": _extract_field(warhead_text, "weapon_family"),
        "consumed_by_surrogate_assumptions": [
          row["assumption_id"] for row in consumed_warhead_rows
        ],
        "rejected_assumptions": [
          row["assumption_id"] for row in rejected_warhead_rows
        ],
        "row_findings": warhead_rows,
      },
      blockers=[
        "AIM-120C-class blast-fragmentation family label is traceable, but variant-specific warhead internals remain out of scope",
        "repo warhead.mass_kg and lethal_radius fields are toy inputs/bookkeeping, not calibrated AIM-120C truth",
        "no release-grade sensitivity envelope binds mass, TNT equivalent, fragment pattern or casing assumptions",
      ],
    ),
    _gate_check(
      check_id="ROWWAR-RES004-002",
      residual_id="RES-004",
      surface="warhead_source_rights_rejection_guard",
      author_side_evidence_present=not res004_sources["missing_source_ids"],
      release_grade_satisfied=False,
      status="blocked_warhead_bounds_and_rights_review_missing",
      evidence={
        "source_evidence": res004_sources,
        "pin_evidence": _pin_summary(pin_text, "RES-004"),
      },
      blockers=[
        "third-party 40 lb / 18 kg cluster remains sanity-only and not a runtime row",
        "forum, game, commercial-sim, fuze-radius, damage and Pk values remain rejected",
        "public TDD/burst-point terms do not authorize trigger threshold, delay, reliability or deterministic fuze behavior",
      ],
    ),
  ]

  residual_status = {
    "RES-003": {
      "status": "blocked_row_level_bounds_missing",
      "register": _residual_register_status(residual_text, "RES-003"),
      "upstream_mechanism_gate_result": mechanism_results.get("RES-003", "missing"),
      "author_side_subslice_ready": True,
      "release_grade": False,
      "closed_by_this_gate": False,
    },
    "RES-004": {
      "status": "blocked_warhead_class_bounds_missing",
      "register": _residual_register_status(residual_text, "RES-004"),
      "upstream_mechanism_gate_result": mechanism_results.get("RES-004", "missing"),
      "author_side_subslice_ready": True,
      "release_grade": False,
      "closed_by_this_gate": False,
    },
  }
  release_blockers = {
    residual_id: [
      blocker
      for check in checks
      if check["residual_id"] == residual_id
      for blocker in check["release_blockers"]
    ]
    for residual_id in RESIDUAL_IDS
  }

  return {
    "package_id": PACKAGE_ID,
    "schema_version": SCHEMA_VERSION,
    "status": "blocked_non_authoritative_geometry_warhead_row_provenance_candidate",
    "review_target": "res_003_004_geometry_warhead_row_provenance_lane",
    "scope": {
      "target_type": "F-16C_Block50",
      "weapon_class": "AIM-120C-class",
      "weapon_family": "blast_fragmentation",
      "aspect_bucket": "beam",
      "closure_bucket": "high",
      "miss_distance_bucket": "near_miss_0_35m",
    },
    "required_inputs": [
      {
        "input_id": key,
        "path": _rel(path, repo_root),
        "required": required,
        "role": role,
      }
      for key, (path, required, role) in refs.items()
    ],
    "consumed_inputs": consumed_inputs + optional_retained_inputs,
    "missing_inputs": missing_inputs,
    "residual_status": residual_status,
    "gate_checks": checks,
    "release_blockers": release_blockers,
    "authority_guard": _authority_guard(),
    "upstream_authority_guard_observed": {
      key: mechanism_guards.get(key)
      for key in sorted(mechanism_guards)
      if key.endswith("_granted") or key == "stock_descriptor_created"
    },
    "decision": {
      "row_level_geometry_release_grade": False,
      "warhead_provenance_bounds_release_grade": False,
      "release_grade_for_current_narrow_scope": False,
      "authority_release_included": False,
      "closed_residual_ids_by_this_gate": [],
      "blocking_residual_ids": list(RESIDUAL_IDS),
    },
    "behavior_risks": [
      "coarse F-16 dimensions or beam witness bookkeeping could be mistaken for true vulnerability geometry",
      "repo AIM-120C-class toy warhead fields could be mistaken for variant-specific warhead or fuze truth",
      "source links and source pins could be over-read as release-grade rights/retention or calibrated row authority",
    ],
    "integration_notes": [
      "this gate does not edit residual_register.zh.md and does not close RES-003 or RES-004",
      "RES-013 Pk and RES-014 deterministic fuze remain outside this gate and stay false in authority_guard",
      "downstream consumers must read residual_status together with authority_guard; author-side trace presence is not release authority",
    ],
  }

def _artifact_paths(
  *,
  repo_root: Path,
  retained_dir: Path | None,
  doc_output: Path | None,
) -> tuple[Path, Path, Path]:
  out_dir = retained_dir or _default_retained_dir(repo_root)
  return (
    out_dir / "geometry_warhead_row_provenance_gate.json",
    out_dir / "manifest.json",
    doc_output or _default_doc_path(repo_root),
  )

def _json_dump(data: dict[str, Any]) -> str:
  return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"

def _write_json(path: Path, data: dict[str, Any]) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(_json_dump(data), encoding="utf-8")

def _manifest(
  *,
  gate_path: Path,
  gate_sha256: str,
  gate: dict[str, Any],
  repo_root: Path,
) -> dict[str, Any]:
  return {
    "package_id": PACKAGE_ID,
    "schema_version": "a2.geometry_warhead_row_provenance_manifest.v1",
    "status": "retained_manifest_for_blocked_gate",
    "artifact_date": ARTIFACT_DATE,
    "artifacts": [
      {
        "artifact_id": "geometry_warhead_row_provenance_gate",
        "path": _rel(gate_path, repo_root),
        "sha256": gate_sha256,
        "content_hash": f"sha256:{gate_sha256}",
        "schema_version": gate["schema_version"],
      }
    ],
    "consumed_inputs": gate["consumed_inputs"],
    "authority_guard": gate["authority_guard"],
    "release_grade_for_current_narrow_scope": False,
  }

def _validation_doc(
  *,
  gate: dict[str, Any],
  gate_path: Path,
  gate_sha256: str,
  manifest_path: Path,
  manifest_sha256: str,
  doc_path: Path,
  repo_root: Path,
) -> str:
  res003 = gate["residual_status"]["RES-003"]
  res004 = gate["residual_status"]["RES-004"]
  return f"""# Validation Geometry / Warhead Row Provenance Gate - 2026-05-31

状态：`generated_from_geometry_warhead_row_provenance_gate / non-authoritative / blocked`。

本文记录 `RES-003 target geometry` 与 `RES-004 warhead scope` 的 row-level provenance / bounds gate。该 gate 消费现有 target geometry assumptions、warhead scope/sensitivity、source ledgers、artifact pin manifest、以及可用的 mechanism/source closeout retained artifact。

本文不修改 [residual_register.zh.md](residual_register.zh.md)，不创建 runtime descriptor，不授予 target geometry、warhead、effect-scale、component probability、Pk 或 deterministic-fuze authority。

## 1. Retained Artifact

| 字段 | 值 |
|---|---|
| `package_id` | `{gate["package_id"]}` |
| `schema_version` | `{gate["schema_version"]}` |
| `tool_ref` | [damage_model.py]({_doc_link(repo_root / "tools" / "maintenance" / "damage_model.py", doc_path, repo_root)}) `scope-provenance row-provenance` |
| `retained_artifact` | [{gate_path.name}]({_doc_link(gate_path, doc_path, repo_root)}) |
| `retained_artifact_sha256` | `{gate_sha256}` |
| `manifest` | [{manifest_path.name}]({_doc_link(manifest_path, doc_path, repo_root)}) |
| `manifest_sha256` | `{manifest_sha256}` |
| `overall_status` | `{gate["status"]}` |

## 2. Current Gate Results

| residual | gate result | register status | upstream mechanism gate | true close by this gate | shortest remaining path |
|---|---|---|---|---:|---|
| `RES-003` target geometry | `{res003["status"]}` | `{res003["register"]["register_status"]}` | `{res003["upstream_mechanism_gate_result"]}` | `false` | freeze row-level geometry provenance and reviewed uncertainty bounds for coarse bbox / beam witness rows |
| `RES-004` warhead scope | `{res004["status"]}` | `{res004["register"]["register_status"]}` | `{res004["upstream_mechanism_gate_result"]}` | `false` | freeze release-grade warhead class/sensitivity envelope without consuming toy mass or fuze/Pk values as truth |

## 3. Non-Authoritative Guards

| guard | current value |
|---|---:|
| `stock_descriptor_created` | `false` |
| `stock_database_authority_granted` | `false` |
| `target_geometry_authority_granted` | `false` |
| `row_level_geometry_authority_granted` | `false` |
| `aim120c_warhead_authority_granted` | `false` |
| `warhead_class_authority_granted` | `false` |
| `effect_scale_authority_granted` | `false` |
| `component_failure_probability_authority_granted` | `false` |
| `pk_authority_granted` | `false` |
| `deterministic_fuze_authority_granted` | `false` |
| `fuze_authority_granted` | `false` |

`RES-013 Pk boundary` 和 `RES-014 deterministic fuze boundary` 不属于本 gate；当前 gate 明确保持 `Pk=false`、`deterministic_fuze=false`。

## 4. Current Decision

当前可审计结论为：

> `RES-003/004 have machine-readable author-side row provenance evidence, but row-level geometry uncertainty bounds and release-grade warhead class/sensitivity bounds are still missing; neither residual is closed`.

行为风险：

- 如果忽略 `RES-003`，coarse bbox 或 beam witness bookkeeping 可能被误写为真实 vulnerability geometry。
- 如果忽略 `RES-004`，repo toy warhead fields 或 third-party sanity values 可能被误写为 AIM-120C variant-specific truth。
- 如果忽略 source/pin 边界，candidate links 可能被误写为 release-grade rights、retention 或 authority。
"""

def write_retained_artifacts(
  *,
  repo_root: Path = REPO_ROOT,
  retained_dir: Path | None = None,
  doc_output: Path | None = None,
) -> dict[str, Any]:
  gate_path, manifest_path, doc_path = _artifact_paths(
    repo_root=repo_root, retained_dir=retained_dir, doc_output=doc_output
  )
  gate = generate_geometry_warhead_row_provenance_gate(repo_root=repo_root)
  gate_sha = write_and_hash_json(gate_path, gate, ensure_ascii=False)
  manifest = _manifest(
    gate_path=gate_path,
    gate_sha256=gate_sha,
    gate=gate,
    repo_root=repo_root,
  )
  manifest_sha = write_and_hash_json(manifest_path, manifest, ensure_ascii=False)
  doc_path.parent.mkdir(parents=True, exist_ok=True)
  doc_path.write_text(
    _validation_doc(
      gate=gate,
      gate_path=gate_path,
      gate_sha256=gate_sha,
      manifest_path=manifest_path,
      manifest_sha256=manifest_sha,
      doc_path=doc_path,
      repo_root=repo_root,
    ),
    encoding="utf-8",
  )
  return {
    "gate_path": _rel(gate_path, repo_root),
    "gate_sha256": gate_sha,
    "manifest_path": _rel(manifest_path, repo_root),
    "manifest_sha256": manifest_sha,
    "doc_path": _rel(doc_path, repo_root),
  }

def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description="Generate the RES-003/RES-004 geometry/warhead row provenance gate."
  )
  parser.add_argument(
    "--retained-dir",
    type=Path,
    help="Optional retained artifact directory. Defaults to the candidate retained path.",
  )
  parser.add_argument(
    "--doc-output",
    type=Path,
    help="Optional validation markdown output. Defaults to the candidate validation path.",
  )
  parser.add_argument(
    "--print-json",
    action="store_true",
    help="Print the gate JSON instead of writing retained artifacts.",
  )
  args = parser.parse_args(argv)

  if args.print_json:
    print(_json_dump(generate_geometry_warhead_row_provenance_gate()), end="")
    return 0

  summary = write_retained_artifacts(
    retained_dir=args.retained_dir,
    doc_output=args.doc_output,
  )
  print(_json_dump(summary), end="")
  return 0

if __name__ == "__main__":
  raise SystemExit(main())
