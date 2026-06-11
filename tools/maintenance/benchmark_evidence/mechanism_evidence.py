#!/usr/bin/env python3
"""Generate fail-closed A2 mechanism benchmark evidence for RES-003..006.

This manifest is narrower than the mechanism/source closeout gate: it asks
whether the current package has actual benchmark-consumed evidence for F-16
geometry uncertainty, AIM-120C-class warhead sensitivity, fragment methods and
blast methods. Existing ledgers, artifact pins and toy scaffold outputs are
recorded as evidence, but they do not become calibration authority.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance.candidate_artifacts import package_bundle as candidate_bundle # noqa: E402


PACKAGE_ID = (
  "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
  "beam_high_near_miss_0_35m_v0"
)
SCHEMA_VERSION = "a2.mechanism_benchmark_evidence.v1"
RESIDUAL_IDS = ("RES-003", "RES-004", "RES-005", "RES-006")

RELEASE_BENCHMARK_CONSUMPTION_STATUSES = {
  "release_retained_benchmark_input",
  "release_grade_benchmark_input",
  "consumed_for_release_benchmark",
}


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
    repo_root / "docs" / "task" / "air_combat" / "archive" / "a2_high_fidelity_damage_model"
  )


def _doc_refs(repo_root: Path) -> dict[str, Path]:
  package_dir = _package_dir(repo_root)
  a2_root = _a2_root(repo_root)
  data_root = a2_root / "data_collection"
  return {
    "artifact_pin_manifest": (
      package_dir / "artifact_pin_manifest_stage_b_effect_scale_20260530.zh.md"
    ),
    "target_geometry_assumptions": (
      package_dir / "target_geometry_assumptions_stage_b_effect_scale_20260530.zh.md"
    ),
    "warhead_scope_and_sensitivity": (
      package_dir / "warhead_scope_and_sensitivity_stage_b_effect_scale_20260530.zh.md"
    ),
    "mechanism_source_closeout_gate": (
      package_dir / "validation_mechanism_source_closeout_gate_20260531.zh.md"
    ),
    "stage_b_result_pack": (
      package_dir / "validation_result_pack_stage_b_effect_scale_20260530.zh.md"
    ),
    "stage_c_result_pack": (
      package_dir
      / "validation_result_pack_stage_c_component_probability_20260530.zh.md"
    ),
    "target_geometry_source_ledger": (
      data_root / "f16c_block50_target_geometry" / "source_ledger.zh.md"
    ),
    "warhead_source_ledger": (
      data_root / "aim120c_warhead_fuze" / "source_ledger.zh.md"
    ),
    "vps_blastfrag_source_ledger": (
      data_root / "vps_blast_fragmentation_methods" / "source_ledger.zh.md"
    ),
    "mechanism_model_source_ledger": (
      data_root / "mechanism_model_public_methods" / "source_ledger.zh.md"
    ),
  }


def _rel(path: Path, repo_root: Path) -> str:
  return path.relative_to(repo_root).as_posix()


def _read_text(path: Path) -> str:
  return path.read_text(encoding="utf-8")


def _strip_cell(cell: str) -> str:
  return cell.strip().strip("`").strip()


def _split_markdown_row(line: str) -> list[str]:
  return [_strip_cell(cell) for cell in line.strip().strip("|").split("|")]


def _find_source_row(text: str, source_id: str) -> str:
  pattern = re.compile(rf"\|\s*`{re.escape(source_id)}`\s*\|")
  for line in text.splitlines():
    if pattern.search(line):
      return line.strip()
  return ""


def _row_contains_any(row: str, needles: tuple[str, ...]) -> bool:
  normalized = row.lower()
  return any(needle in normalized for needle in needles)


def _source_evidence(
  *,
  ledger_ref: Path,
  source_ids: list[str],
  repo_root: Path,
) -> dict[str, Any]:
  text = _read_text(ledger_ref)
  rows: list[dict[str, Any]] = []
  for source_id in source_ids:
    row = _find_source_row(text, source_id)
    rows.append(
      {
        "source_id": source_id,
        "present": bool(row),
        "pending_acquisition": bool(
          row
          and _row_contains_any(
            row,
            (
              "pending_acquisition",
              "pending_artifact",
              "pending_artifact",
              "pending",
              "待",
              "未固定",
              "未确认",
            ),
          )
        ),
        "official_public_artifact_externally_verified": bool(
          row
          and _row_contains_any(
            row,
            (
              "official public artifact",
              "externally verified",
              "sha256",
              "http 200",
              "官方",
            ),
          )
        ),
        "candidate_only": bool(
          row
          and _row_contains_any(
            row,
            (
              "candidate_only",
              "candidate provenance",
              "candidate",
              "non-authoritative",
              "候选",
            ),
          )
        ),
        "rejected": bool(
          row
          and _row_contains_any(
            row,
            ("rejected", "拒绝", "not_admitted", "不得使用"),
          )
        ),
      }
    )
  return {
    "ledger_ref": _rel(ledger_ref, repo_root),
    "selected_source_ids": list(source_ids),
    "present_source_ids": [row["source_id"] for row in rows if row["present"]],
    "missing_source_ids": [row["source_id"] for row in rows if not row["present"]],
    "pending_acquisition_source_ids": [
      row["source_id"] for row in rows if row["pending_acquisition"]
    ],
    "externally_verified_source_ids": [
      row["source_id"]
      for row in rows
      if row["official_public_artifact_externally_verified"]
    ],
    "candidate_only_source_ids": [
      row["source_id"] for row in rows if row["candidate_only"]
    ],
    "rejected_source_ids": [row["source_id"] for row in rows if row["rejected"]],
    "all_selected_sources_present": all(row["present"] for row in rows),
    "rows": rows,
  }


PIN_TABLE_COLUMNS = [
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


def _parse_artifact_pin_rows(text: str) -> list[dict[str, str]]:
  rows: list[dict[str, str]] = []
  for line in text.splitlines():
    cells = _split_markdown_row(line) if line.startswith("|") else []
    if len(cells) < len(PIN_TABLE_COLUMNS):
      continue
    if not cells[0].startswith("PIN-"):
      continue
    rows.append(dict(zip(PIN_TABLE_COLUMNS, cells[: len(PIN_TABLE_COLUMNS)])))
  return rows


def _pin_evidence(
  *,
  rows: list[dict[str, str]],
  residual_id: str | None = None,
  pin_ids: list[str] | None = None,
) -> dict[str, Any]:
  selected = rows
  if residual_id is not None:
    selected = [row for row in selected if residual_id in row["residuals"]]
  if pin_ids is not None:
    pin_set = set(pin_ids)
    selected = [row for row in selected if row["artifact_id"] in pin_set]

  def ids_matching(field: str, needles: tuple[str, ...]) -> list[str]:
    return [
      row["artifact_id"]
      for row in selected
      if _row_contains_any(row[field], needles)
    ]

  release_consumed = [
    row["artifact_id"]
    for row in selected
    if row["consumption_status"] in RELEASE_BENCHMARK_CONSUMPTION_STATUSES
  ]
  return {
    "pin_ids": [row["artifact_id"] for row in selected],
    "source_ids": [row["source_id"] for row in selected],
    "artifact_status_by_pin": {
      row["artifact_id"]: row["artifact_status"] for row in selected
    },
    "consumption_status_by_pin": {
      row["artifact_id"]: row["consumption_status"] for row in selected
    },
    "retention_pending_pin_ids": ids_matching(
      "artifact_status", ("retention_pending",)
    ),
    "externally_verified_candidate_pin_ids": ids_matching(
      "artifact_status",
      ("verified_candidate_artifact", "verified_candidate_artifact_bundle"),
    ),
    "candidate_or_acquired_pin_ids": ids_matching(
      "consumption_status", ("acquired_for_candidate", "not_consumed")
    ),
    "sanity_only_pin_ids": ids_matching("consumption_status", ("sanity_only",)),
    "rejected_pin_ids": ids_matching("consumption_status", ("rejected",)),
    "release_benchmark_consumed_pin_ids": release_consumed,
    "any_release_benchmark_consumed": bool(release_consumed),
    "authority_boundaries": {
      row["artifact_id"]: row["authority_boundary"] for row in selected
    },
  }


def _lineage(
  *,
  lineage_id: str,
  residual_id: str,
  evidence_label: str,
  source_evidence: list[dict[str, Any]],
  pin_evidence: dict[str, Any] | None,
  candidate_or_scaffold_consumed: bool,
  benchmark_consumed: bool,
  release_grade_validated: bool,
  evidence_status: str,
  shortest_completion_path: list[str],
) -> dict[str, Any]:
  source_present = any(source["present_source_ids"] for source in source_evidence)
  pending_source_ids = sorted(
    {
      source_id
      for source in source_evidence
      for source_id in source["pending_acquisition_source_ids"]
    }
  )
  externally_verified_source_ids = sorted(
    {
      source_id
      for source in source_evidence
      for source_id in source["externally_verified_source_ids"]
    }
  )
  return {
    "lineage_id": lineage_id,
    "residual_id": residual_id,
    "evidence_label": evidence_label,
    "source_present": source_present,
    "pending_acquisition_source_ids": pending_source_ids,
    "externally_verified_source_ids": externally_verified_source_ids,
    "candidate_or_scaffold_consumed": candidate_or_scaffold_consumed,
    "benchmark_consumed": benchmark_consumed,
    "release_grade_validated": release_grade_validated,
    "evidence_status": evidence_status,
    "source_evidence": source_evidence,
    "pin_evidence": pin_evidence or {
      "pin_ids": [],
      "release_benchmark_consumed_pin_ids": [],
      "any_release_benchmark_consumed": False,
    },
    "shortest_completion_path": shortest_completion_path,
  }


def _artifact_refs(bundle: dict[str, Any]) -> dict[str, Any]:
  stage_b = bundle["validation_result_pack_summary"]
  stage_c = bundle["validation_stage_c_component_probability_result_pack_summary"]
  snapshot = bundle["validation_benchmark_snapshot_summary"]
  scaffold = bundle["validation_scaffold_summary"]
  return {
    "validation_scaffold_status": scaffold["validation_status"],
    "implemented_scaffold_benchmarks": scaffold["implemented_benchmarks"],
    "mechanism_load_vector": scaffold["mechanism_load_vector"],
    "stage_b_result_pack_status": stage_b["status"],
    "stage_b_all_hard_gates_pass": stage_b[
      "all_hard_gates_pass_in_current_snapshot"
    ],
    "stage_b_review_status": stage_b["review_status"],
    "stage_b_bm005_audit_outcome": stage_b["bm005_audit_outcome"],
    "stage_b_reviewed_benchmarks": snapshot["reviewed_benchmarks"],
    "stage_c_result_pack_status": stage_c["status"],
    "stage_c_review_status": stage_c["review_status"],
    "stage_c_baseline_component_probability_source": stage_c[
      "baseline_component_probability_source"
    ],
    "stage_c_gate_band_contains_primary_fragment_energy": stage_c[
      "gate_band_contains_primary_fragment_energy"
    ],
    "stage_c_gate_band_contains_primary_penetration_margin": stage_c[
      "gate_band_contains_primary_penetration_margin"
    ],
    "stage_c_gate_band_contains_primary_blast_impulse": stage_c[
      "gate_band_contains_primary_blast_impulse"
    ],
    "stage_c_gate_band_contains_primary_surface_incidence": stage_c[
      "gate_band_contains_primary_surface_incidence"
    ],
  }


def _build_lineages(
  *,
  refs: dict[str, Path],
  pin_rows: list[dict[str, str]],
  bundle: dict[str, Any],
  repo_root: Path,
) -> dict[str, list[dict[str, Any]]]:
  vps = refs["vps_blastfrag_source_ledger"]
  mechanism = refs["mechanism_model_source_ledger"]
  warhead = refs["warhead_source_ledger"]

  stage_b_reviewed = bundle["validation_benchmark_snapshot_summary"][
    "reviewed_benchmarks"
  ]
  scaffold_benchmarks = bundle["validation_scaffold_summary"][
    "implemented_benchmarks"
  ]

  fragment_lineages = [
    _lineage(
      lineage_id="FRAG-GURNEY-BRL405",
      residual_id="RES-005",
      evidence_label="Gurney initial fragment velocity source route",
      source_evidence=[
        _source_evidence(
          ledger_ref=vps,
          source_ids=["VPS-BFM-007"],
          repo_root=repo_root,
        ),
        _source_evidence(
          ledger_ref=mechanism,
          source_ids=["MECH-FRAG-002"],
          repo_root=repo_root,
        ),
        _source_evidence(
          ledger_ref=warhead,
          source_ids=["PHYS-BF-006"],
          repo_root=repo_root,
        ),
      ],
      pin_evidence=_pin_evidence(rows=pin_rows, pin_ids=[]),
      candidate_or_scaffold_consumed=False,
      benchmark_consumed=False,
      release_grade_validated=False,
      evidence_status="source_route_present_pending_official_artifact",
      shortest_completion_path=[
        "resolve the official public Gurney BRL-405 artifact, rights and checksum or explicitly exclude it",
        "freeze charge/casing assumptions and retained reference-output hashes before any velocity benchmark consumption",
      ],
    ),
    _lineage(
      lineage_id="FRAG-TP21-DEBRIS",
      residual_id="RES-005",
      evidence_label="DDESB TP-21 explosion-produced debris reference path",
      source_evidence=[
        _source_evidence(
          ledger_ref=vps,
          source_ids=["VPS-BFM-015"],
          repo_root=repo_root,
        ),
        _source_evidence(
          ledger_ref=mechanism,
          source_ids=["MECH-FRAG-004"],
          repo_root=repo_root,
        ),
      ],
      pin_evidence=_pin_evidence(rows=pin_rows, pin_ids=["PIN-BFM-002"]),
      candidate_or_scaffold_consumed=False,
      benchmark_consumed=False,
      release_grade_validated=False,
      evidence_status="official_public_source_present_benchmark_not_consumed",
      shortest_completion_path=[
        "create canonical TP-21 retention refs and allowed-output policy",
        "add reviewer-frozen fragment/debris comparison payload hashes and tolerances",
      ],
    ),
    _lineage(
      lineage_id="FRAG-TOY-SCAFFOLD",
      residual_id="RES-005",
      evidence_label="Stage B/C fragment hygiene scaffold",
      source_evidence=[
        _source_evidence(
          ledger_ref=vps,
          source_ids=[
            "VPS-BFM-001",
            "VPS-BFM-006",
            "VPS-BFM-013",
          ],
          repo_root=repo_root,
        )
      ],
      pin_evidence=_pin_evidence(rows=pin_rows, residual_id="RES-005"),
      candidate_or_scaffold_consumed=(
        "BFM-BM-002" in scaffold_benchmarks
        and "BFM-BM-005" in stage_b_reviewed
      ),
      benchmark_consumed=False,
      release_grade_validated=False,
      evidence_status="toy_probe_consumed_for_hygiene_not_calibration",
      shortest_completion_path=[
        "replace toy areal-density and energy checks with retained public/reference benchmark outputs",
        "obtain independent review that the scaffold is not treated as fragment authority",
      ],
    ),
  ]

  blast_lineages = [
    _lineage(
      lineage_id="BLAST-KINGERY-BULMASH",
      residual_id="RES-006",
      evidence_label="Kingery-Bulmash TNT airblast source route",
      source_evidence=[
        _source_evidence(
          ledger_ref=vps,
          source_ids=["VPS-BFM-003"],
          repo_root=repo_root,
        ),
        _source_evidence(
          ledger_ref=mechanism,
          source_ids=["MECH-BLAST-003"],
          repo_root=repo_root,
        ),
      ],
      pin_evidence=_pin_evidence(rows=pin_rows, pin_ids=[]),
      candidate_or_scaffold_consumed=False,
      benchmark_consumed=False,
      release_grade_validated=False,
      evidence_status="source_route_present_pending_official_artifact",
      shortest_completion_path=[
        "resolve the official public Kingery-Bulmash ARBRL-TR-02555 artifact or explicitly exclude it",
        "freeze coefficient/output provenance before any blast benchmark comparison",
      ],
    ),
    _lineage(
      lineage_id="BLAST-BEC-O-TP20",
      residual_id="RES-006",
      evidence_label="DDESB TP-20 / BEC-O public blast implementation path",
      source_evidence=[
        _source_evidence(
          ledger_ref=vps,
          source_ids=["VPS-BFM-014"],
          repo_root=repo_root,
        ),
        _source_evidence(
          ledger_ref=mechanism,
          source_ids=["MECH-BLAST-004"],
          repo_root=repo_root,
        ),
        _source_evidence(
          ledger_ref=warhead,
          source_ids=["PHYS-BF-002"],
          repo_root=repo_root,
        ),
      ],
      pin_evidence=_pin_evidence(rows=pin_rows, pin_ids=["PIN-BFM-001"]),
      candidate_or_scaffold_consumed=False,
      benchmark_consumed=False,
      release_grade_validated=False,
      evidence_status="official_public_source_present_benchmark_not_consumed",
      shortest_completion_path=[
        "freeze canonical TP-20/BEC-O retained refs, package version and allowed-output policy",
        "add selected comparison-output hashes, tolerances and applicability envelope",
      ],
    ),
    _lineage(
      lineage_id="BLAST-TOY-SCAFFOLD",
      residual_id="RES-006",
      evidence_label="Stage B/C blast scaled-distance and impulse hygiene scaffold",
      source_evidence=[
        _source_evidence(
          ledger_ref=vps,
          source_ids=["VPS-BFM-001", "VPS-BFM-002"],
          repo_root=repo_root,
        ),
        _source_evidence(
          ledger_ref=warhead,
          source_ids=["PHYS-BF-001"],
          repo_root=repo_root,
        ),
      ],
      pin_evidence=_pin_evidence(rows=pin_rows, residual_id="RES-006"),
      candidate_or_scaffold_consumed=(
        "BFM-BM-001" in scaffold_benchmarks
        and "BFM-BM-001" in stage_b_reviewed
      ),
      benchmark_consumed=False,
      release_grade_validated=False,
      evidence_status="toy_probe_consumed_for_hygiene_not_calibration",
      shortest_completion_path=[
        "compare the blast curve against retained BEC-O/public-tool outputs under frozen tolerances",
        "review TNT-equivalent, airburst/reflection and aircraft-coupling applicability before release",
      ],
    ),
  ]

  return {
    "fragment": fragment_lineages,
    "blast": blast_lineages,
  }


def _residual_evidence(
  *,
  refs: dict[str, Path],
  pin_rows: list[dict[str, str]],
  bundle: dict[str, Any],
  lineages: dict[str, list[dict[str, Any]]],
  repo_root: Path,
) -> list[dict[str, Any]]:
  target_sources = _source_evidence(
    ledger_ref=refs["target_geometry_source_ledger"],
    source_ids=[
      "F16-TG-SRC-001",
      "F16-TG-SRC-002",
      "F16-TG-SRC-004",
      "F16-TG-SRC-005",
      "F16-TG-SRC-012",
    ],
    repo_root=repo_root,
  )
  warhead_sources = _source_evidence(
    ledger_ref=refs["warhead_source_ledger"],
    source_ids=[
      "AIM120-WF-002",
      "AIM120-WF-006",
      "AIM120-WF-007",
      "PHYS-BF-001",
      "PHYS-BF-002",
      "PHYS-BF-006",
    ],
    repo_root=repo_root,
  )
  target_assumptions = bundle["target_geometry_assumption_summary"]
  warhead_scope = bundle["warhead_scope_summary"]
  artifact_refs = _artifact_refs(bundle)

  fragment_benchmark_consumed = all(
    row["benchmark_consumed"] for row in lineages["fragment"]
  )
  blast_benchmark_consumed = all(row["benchmark_consumed"] for row in lineages["blast"])

  return [
    {
      "residual_id": "RES-003",
      "evidence_target": "F-16 geometry uncertainty and review inputs",
      "evidence_status": "review_inputs_present_external_geometry_benchmark_missing",
      "gate_result": "blocked_fail_closed_release_grade_geometry_benchmark_missing",
      "source_present": target_sources["all_selected_sources_present"],
      "candidate_or_scaffold_consumed": (
        target_assumptions["author_status"] == "frozen_for_stage_b_review_only"
        and target_assumptions["used_by_stage_b_yes_count"] > 0
      ),
      "benchmark_consumed": False,
      "release_grade_validated": False,
      "observed_evidence": {
        "source_evidence": target_sources,
        "pin_evidence": _pin_evidence(rows=pin_rows, residual_id="RES-003"),
        "target_geometry_assumption_summary": target_assumptions,
        "stage_b_c_artifact_refs": artifact_refs,
      },
      "shortest_completion_path": [
        "freeze row-level uncertainty bounds for outer box, beam witness geometry and component projection rows",
        "obtain independent review that repo hitboxes are engineering scaffolds, not F-16 vulnerability geometry",
        "add or explicitly waive a release-grade geometry benchmark/comparison payload",
      ],
    },
    {
      "residual_id": "RES-004",
      "evidence_target": "AIM-120C-class warhead sensitivity boundary",
      "evidence_status": "scope_and_sensitivity_boundary_present_external_warhead_benchmark_missing",
      "gate_result": "blocked_fail_closed_release_grade_warhead_sensitivity_benchmark_missing",
      "source_present": warhead_sources["all_selected_sources_present"],
      "candidate_or_scaffold_consumed": (
        warhead_scope["weapon_class"] == "AIM-120C-class"
        and warhead_scope["weapon_family"] == "blast_fragmentation"
        and warhead_scope["consumed_by_surrogate_yes_count"] > 0
      ),
      "benchmark_consumed": False,
      "release_grade_validated": False,
      "observed_evidence": {
        "source_evidence": warhead_sources,
        "pin_evidence": _pin_evidence(rows=pin_rows, residual_id="RES-004"),
        "warhead_scope_summary": warhead_scope,
        "stage_b_c_artifact_refs": artifact_refs,
      },
      "shortest_completion_path": [
        "freeze an AIM-120C-class sensitivity envelope that never treats toy mass as C-model truth",
        "pin admitted benchmark/reference payloads for mass, TNT-equivalent or explicitly keep those out of scope",
        "keep deterministic fuze and Pk blocked unless a separate evidence chain exists",
      ],
    },
    {
      "residual_id": "RES-005",
      "evidence_target": "fragment evidence path",
      "evidence_status": "source_routes_present_benchmark_payload_not_consumed",
      "gate_result": "blocked_fail_closed_fragment_benchmark_payload_missing",
      "source_present": all(row["source_present"] for row in lineages["fragment"]),
      "candidate_or_scaffold_consumed": any(
        row["candidate_or_scaffold_consumed"] for row in lineages["fragment"]
      ),
      "benchmark_consumed": fragment_benchmark_consumed,
      "release_grade_validated": False,
      "observed_evidence": {
        "lineages": lineages["fragment"],
        "stage_b_c_artifact_refs": artifact_refs,
      },
      "shortest_completion_path": [
        "resolve or exclude Gurney BRL-405 before any release velocity benchmark",
        "freeze TP-21 retained refs, allowed-output policy, comparison hashes and tolerances",
        "replace toy fragment probe use with release-grade retained/reference benchmark consumption",
      ],
    },
    {
      "residual_id": "RES-006",
      "evidence_target": "blast evidence path",
      "evidence_status": "source_routes_present_benchmark_payload_not_consumed",
      "gate_result": "blocked_fail_closed_blast_benchmark_payload_missing",
      "source_present": all(row["source_present"] for row in lineages["blast"]),
      "candidate_or_scaffold_consumed": any(
        row["candidate_or_scaffold_consumed"] for row in lineages["blast"]
      ),
      "benchmark_consumed": blast_benchmark_consumed,
      "release_grade_validated": False,
      "observed_evidence": {
        "lineages": lineages["blast"],
        "stage_b_c_artifact_refs": artifact_refs,
      },
      "shortest_completion_path": [
        "resolve or explicitly exclude the original Kingery-Bulmash artifact",
        "freeze TP-20/BEC-O retained refs, package version, output policy, comparison hashes and tolerances",
        "review the blast applicability envelope before any release-grade pressure/impulse authority",
      ],
    },
  ]


def generate_mechanism_benchmark_evidence(
  *,
  repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
  refs = _doc_refs(repo_root)
  pin_rows = _parse_artifact_pin_rows(_read_text(refs["artifact_pin_manifest"]))
  bundle = candidate_bundle.generate_candidate_bundle(repo_root=repo_root)
  lineages = _build_lineages(
    refs=refs,
    pin_rows=pin_rows,
    bundle=bundle,
    repo_root=repo_root,
  )
  residuals = _residual_evidence(
    refs=refs,
    pin_rows=pin_rows,
    bundle=bundle,
    lineages=lineages,
    repo_root=repo_root,
  )
  closed_residuals = [
    row["residual_id"] for row in residuals if row["release_grade_validated"]
  ]

  return {
    "package_id": PACKAGE_ID,
    "schema_version": SCHEMA_VERSION,
    "status": "blocked_fail_closed_mechanism_benchmark_evidence_manifest",
    "review_target": "res_003_004_005_006_mechanism_benchmark_evidence_lane",
    "scope": {
      "target_type": "F-16C_Block50",
      "weapon_class": "AIM-120C-class",
      "weapon_family": "blast_fragmentation",
      "aspect_bucket": "beam",
      "closure_bucket": "high",
      "miss_distance_bucket": "near_miss_0_35m",
    },
    "doc_refs": {key: _rel(path, repo_root) for key, path in refs.items()},
    "benchmark_evidence_decision": {
      "mechanism_benchmark_evidence_ready": False,
      "mechanism_benchmark_evidence_blocked": True,
      "fail_closed": True,
      "closed_residual_ids_by_this_gate": closed_residuals,
      "candidate_or_toy_probe_is_calibration": False,
      "pk_authority_included": False,
      "deterministic_fuze_authority_included": False,
    },
    "current_gate_results": {
      row["residual_id"]: row["gate_result"] for row in residuals
    },
    "residual_benchmark_evidence": residuals,
    "fragment_blast_lineage_summary": lineages,
    "source_consumption_validation_matrix": [
      {
        "lineage_id": row["lineage_id"],
        "residual_id": row["residual_id"],
        "source_present": row["source_present"],
        "benchmark_consumed": row["benchmark_consumed"],
        "release_grade_validated": row["release_grade_validated"],
        "evidence_status": row["evidence_status"],
      }
      for group in ("fragment", "blast")
      for row in lineages[group]
    ],
    "non_authoritative_guards": {
      "stock_descriptor_created": False,
      "stock_database_authority_granted": False,
      "target_geometry_authority_granted": False,
      "aim120c_warhead_authority_granted": False,
      "fragment_mechanism_authority_granted": False,
      "blast_mechanism_authority_granted": False,
      "effect_scale_authority_granted": False,
      "component_failure_probability_authority_granted": False,
      "pk_authority_granted": False,
      "deterministic_fuze_authority_granted": False,
    },
    "remaining_release_grade_paths": {
      row["residual_id"]: row["shortest_completion_path"] for row in residuals
    },
    "behavior_risks": [
      "F-16 witness geometry could be mistaken for true vulnerability geometry if RES-003 is narrated as closed",
      "AIM-120C-class toy warhead inputs could be mistaken for C-model mass, TNT-equivalent or fuze truth if RES-004 is narrated as closed",
      "Gurney/TP-21 fragment routes could be mistaken for consumed calibration benchmarks if source presence is conflated with benchmark consumption",
      "Kingery-Bulmash/BEC-O blast routes could be mistaken for pressure/impulse authority if artifact verification is conflated with release validation",
    ],
    "integration_notes": [
      "this manifest does not update residual_register.zh.md and does not create runtime descriptors",
      "Stage B/C toy scaffold outputs are recorded only as hygiene evidence",
      "source_present, benchmark_consumed and release_grade_validated must be consumed as separate fields",
      "RES-013 Pk and RES-014 deterministic fuze remain outside this lane and stay false",
    ],
  }


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description=(
      "Generate the A2 blast-fragmentation mechanism benchmark evidence "
      "manifest for RES-003/004/005/006."
    )
  )
  parser.add_argument(
    "--output",
    type=Path,
    help="Optional JSON output path. Defaults to stdout.",
  )
  args = parser.parse_args(argv)

  artifact = generate_mechanism_benchmark_evidence()
  payload = json.dumps(artifact, indent=2, sort_keys=True)
  if args.output:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload + "\n", encoding="utf-8")
  else:
    print(payload)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
