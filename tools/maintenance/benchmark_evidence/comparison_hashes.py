#!/usr/bin/env python3
"""Generate A2 mechanism comparison-output hash evidence for RES-005/006.

This tool is intentionally narrow and fail-closed. It can hash retained
public-payload metadata and selected cached spreadsheet outputs, but it does
not execute spreadsheet calculations, copy source document prose into a
dataset, consume the payloads for release, or grant any authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any
from zipfile import BadZipFile, ZipFile
import xml.etree.ElementTree as ET

_REPO_ROOT_HINT = str(Path(__file__).resolve().parents[3])
if _REPO_ROOT_HINT not in sys.path:
  sys.path.insert(0, _REPO_ROOT_HINT)

from python.runtime_bootstrap import ensure_repo_imports, repo_root

ensure_repo_imports()

REPO_ROOT = Path(repo_root())

from tools.maintenance.retained_artifacts.manifest_integrity import (
  _sha256_file,
  _sha256_text,
  write_and_hash_json,
)
PACKAGE_ID = (
  "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
  "beam_high_near_miss_0_35m_v0"
)
SCHEMA_VERSION = "a2.mechanism_comparison_hashes.v1"
RETAINED_MANIFEST_SCHEMA_VERSION = (
  "a2.mechanism_comparison_hashes_retained_manifest.v1"
)
SELECTED_HASH_SCHEMA_VERSION = "a2.selected_comparison_output_hash.v1"

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
SOURCE_PAYLOAD_PACK_DIR = (
  PACKAGE_DIR / "retained_artifacts" / "source_payload_pack_20260531"
)
DEFAULT_RETAINED_DIR = (
  PACKAGE_DIR / "retained_artifacts" / "mechanism_comparison_hashes_20260531"
)

MECHANISM_COMPARISON_HASHES_FILENAME = "mechanism_comparison_hashes.json"
RETAINED_MANIFEST_FILENAME = "manifest.json"

EXPECTED_PAYLOADS = {
  "TP-20 PDF": {
    "filename": "TP-20.pdf",
    "source_id": "VPS-BFM-014",
    "residual_id": "RES-006",
    "expected_sha256": (
      "293c5fd15a56b7ec4e6f4ad37d35f73a8e010083ce20baad56e39fb8423f165f"
    ),
  },
  "BEC-O-V1.xlsx": {
    "filename": "BEC-O-V1.xlsx",
    "source_id": "VPS-BFM-014",
    "residual_id": "RES-006",
    "expected_sha256": (
      "82815469317eb0b3dcf03b7687aae75075798b4345657a08399d8059c9de18fc"
    ),
  },
  "TP-21 PDF": {
    "filename": "TP-21.pdf",
    "source_id": "VPS-BFM-015",
    "residual_id": "RES-005",
    "expected_sha256": (
      "84b72dee13dff247cff5018c8f3e4d560569ee301835fdc324a9ff5043979de8"
    ),
  },
}

BECO_SELECTED_OUTPUTS = [
  {
    "comparison_id": "BEC-O-METRIC-DEFAULT-001",
    "sheet": "METRIC UNITS",
    "cell": "E36",
    "output_role": "scaled_distance_metric_default",
    "unit_family": "scaled_distance",
  },
  {
    "comparison_id": "BEC-O-METRIC-DEFAULT-002",
    "sheet": "METRIC UNITS",
    "cell": "E38",
    "output_role": "time_of_arrival_metric_default",
    "unit_family": "time",
  },
  {
    "comparison_id": "BEC-O-METRIC-DEFAULT-003",
    "sheet": "METRIC UNITS",
    "cell": "E40",
    "output_role": "incident_pressure_metric_default",
    "unit_family": "pressure",
  },
  {
    "comparison_id": "BEC-O-METRIC-DEFAULT-004",
    "sheet": "METRIC UNITS",
    "cell": "E43",
    "output_role": "reflected_pressure_metric_default",
    "unit_family": "pressure",
  },
  {
    "comparison_id": "BEC-O-METRIC-DEFAULT-005",
    "sheet": "METRIC UNITS",
    "cell": "E45",
    "output_role": "positive_phase_duration_metric_default",
    "unit_family": "time",
  },
  {
    "comparison_id": "BEC-O-METRIC-DEFAULT-006",
    "sheet": "METRIC UNITS",
    "cell": "E48",
    "output_role": "positive_phase_impulse_metric_default",
    "unit_family": "pressure_time",
  },
  {
    "comparison_id": "BEC-O-METRIC-DEFAULT-007",
    "sheet": "METRIC UNITS",
    "cell": "E51",
    "output_role": "reflected_impulse_metric_default",
    "unit_family": "pressure_time",
  },
  {
    "comparison_id": "BEC-O-METRIC-DEFAULT-008",
    "sheet": "METRIC UNITS",
    "cell": "E54",
    "output_role": "dynamic_overpressure_metric_default",
    "unit_family": "pressure",
  },
  {
    "comparison_id": "BEC-O-METRIC-DEFAULT-009",
    "sheet": "METRIC UNITS",
    "cell": "E57",
    "output_role": "dynamic_impulse_metric_default",
    "unit_family": "pressure_time",
  },
]

TP21_ALLOWED_CRITERIA_VOCABULARY = [
  {
    "criteria_key": "debris_item_class",
    "allowed_use": "classification_key_for_selected_debris_comparison_only",
  },
  {
    "criteria_key": "debris_mass_bin",
    "allowed_use": "reviewer_selected_bin_key_not_source_content",
  },
  {
    "criteria_key": "debris_velocity_or_throw_bin",
    "allowed_use": "reviewer_selected_bin_key_not_source_content",
  },
  {
    "criteria_key": "standoff_or_separation_bin",
    "allowed_use": "reviewer_selected_distance_key_not_source_content",
  },
  {
    "criteria_key": "target_exposure_or_area_bin",
    "allowed_use": "normalization_key_for_future_hash_only_output",
  },
  {
    "criteria_key": "unit_system",
    "allowed_use": "unit_family_marker_for_future_recalculation_manifest",
  },
  {
    "criteria_key": "applicability_limit",
    "allowed_use": "review_boundary_marker_not_calibration_value",
  },
  {
    "criteria_key": "exclusion_reason",
    "allowed_use": "fail_closed_reason_when_a_debris_case_is_not_admitted",
  },
]

XML_NS = {
  "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
  "dc": "http://purl.org/dc/elements/1.1/",
  "dcterms": "http://purl.org/dc/terms/",
  "ep": "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties",
  "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
  "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}

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

def _local_name(tag: str) -> str:
  return tag.rsplit("}", 1)[-1]

def _numeric(value: str) -> bool:
  try:
    float(value)
  except ValueError:
    return False
  return True

def _column_row(cell_ref: str) -> tuple[str, int]:
  match = re.fullmatch(r"([A-Z]+)([0-9]+)", cell_ref)
  if not match:
    raise ValueError(f"unsupported cell reference: {cell_ref}")
  return match.group(1), int(match.group(2))

def _payload_paths(source_payload_pack_dir: Path) -> dict[str, Path]:
  return {
    label: source_payload_pack_dir / "payloads" / details["filename"]
    for label, details in EXPECTED_PAYLOADS.items()
  }

def _payload_inventory(
  *,
  source_payload_pack_dir: Path,
  repo_root: Path,
) -> dict[str, Any]:
  paths = _payload_paths(source_payload_pack_dir)
  rows: list[dict[str, Any]] = []
  for label, details in EXPECTED_PAYLOADS.items():
    path = paths[label]
    actual_sha256 = _sha256_file(path) if path.exists() else ""
    rows.append(
      {
        "source_artifact_label": label,
        "source_id": details["source_id"],
        "residual_id": details["residual_id"],
        "relative_path": _rel(path, repo_root),
        "expected_sha256": details["expected_sha256"],
        "actual_sha256": actual_sha256,
        "payload_exists": path.exists(),
        "hash_matches_expected": actual_sha256 == details["expected_sha256"],
        "benchmark_consumed_for_release": False,
        "source_presence_is_calibration": False,
      }
    )
  return {
    "source_payload_pack_dir": _rel(source_payload_pack_dir, repo_root),
    "payloads": rows,
    "all_payloads_exist": all(row["payload_exists"] for row in rows),
    "all_payload_hashes_match": all(row["hash_matches_expected"] for row in rows),
  }

def _read_xml(zip_file: ZipFile, name: str) -> ET.Element | None:
  try:
    return ET.fromstring(zip_file.read(name))
  except KeyError:
    return None

def _hashed_xml_properties(root: ET.Element | None) -> dict[str, Any]:
  if root is None:
    return {
      "present": False,
      "property_keys": [],
      "property_value_sha256_by_key": {},
    }
  values: dict[str, str] = {}
  for child in list(root):
    key = _local_name(child.tag)
    value = "".join(child.itertext()).strip()
    if value:
      values[key] = value
  return {
    "present": True,
    "property_keys": sorted(values),
    "property_value_sha256_by_key": {
      key: _sha256_text(values[key]) for key in sorted(values)
    },
  }

def _workbook_relationships(zip_file: ZipFile) -> dict[str, str]:
  rels_root = _read_xml(zip_file, "xl/_rels/workbook.xml.rels")
  if rels_root is None:
    return {}
  return {
    rel.attrib["Id"]: rel.attrib["Target"]
    for rel in rels_root
    if rel.attrib.get("Id") and rel.attrib.get("Target")
  }

def _sheet_path(target: str) -> str:
  if target.startswith("/"):
    return target.lstrip("/")
  if target.startswith("xl/"):
    return target
  return f"xl/{target}"

def _sheet_records(zip_file: ZipFile) -> tuple[list[dict[str, Any]], dict[str, str]]:
  workbook = _read_xml(zip_file, "xl/workbook.xml")
  if workbook is None:
    return [], {}
  rels = _workbook_relationships(zip_file)
  records: list[dict[str, Any]] = []
  sheet_paths: dict[str, str] = {}
  for sheet in workbook.findall("main:sheets/main:sheet", XML_NS):
    name = sheet.attrib["name"]
    relationship_id = sheet.attrib.get(f"{{{XML_NS['rel']}}}id", "")
    target = rels.get(relationship_id, "")
    path = _sheet_path(target) if target else ""
    sheet_paths[name] = path
    root = _read_xml(zip_file, path) if path else None
    dimension = ""
    formula_count = 0
    cached_formula_value_count = 0
    numeric_cached_formula_value_count = 0
    populated_cell_count = 0
    if root is not None:
      dim = root.find("main:dimension", XML_NS)
      dimension = dim.attrib.get("ref", "") if dim is not None else ""
      for cell in root.findall(".//main:c", XML_NS):
        populated_cell_count += 1
        formula = cell.find("main:f", XML_NS)
        value = cell.find("main:v", XML_NS)
        if formula is not None:
          formula_count += 1
          if value is not None and value.text not in (None, ""):
            cached_formula_value_count += 1
            if _numeric(value.text):
              numeric_cached_formula_value_count += 1
    records.append(
      {
        "sheet_name": name,
        "state": sheet.attrib.get("state", "visible"),
        "relationship_id": relationship_id,
        "target": path,
        "dimension": dimension,
        "populated_cell_count": populated_cell_count,
        "formula_cell_count": formula_count,
        "cached_formula_value_count": cached_formula_value_count,
        "numeric_cached_formula_value_count": numeric_cached_formula_value_count,
      }
    )
  return records, sheet_paths

def _cell_record(zip_file: ZipFile, sheet_path: str, cell_ref: str) -> dict[str, str]:
  root = _read_xml(zip_file, sheet_path)
  if root is None:
    return {"exists": "false", "formula": "", "value": "", "type": ""}
  for cell in root.findall(".//main:c", XML_NS):
    if cell.attrib.get("r") != cell_ref:
      continue
    formula = cell.find("main:f", XML_NS)
    value = cell.find("main:v", XML_NS)
    return {
      "exists": "true",
      "formula": formula.text if formula is not None and formula.text else "",
      "value": value.text if value is not None and value.text else "",
      "type": cell.attrib.get("t", ""),
    }
  return {"exists": "false", "formula": "", "value": "", "type": ""}

def _selected_output_hash_record(
  *,
  workbook_sha256: str,
  selection: dict[str, str],
  cell_record: dict[str, str],
) -> dict[str, Any]:
  formula_sha256 = _sha256_text(cell_record["formula"]) if cell_record["formula"] else ""
  has_cached_value = bool(cell_record["value"])
  has_numeric_cached_value = has_cached_value and _numeric(cell_record["value"])
  preimage = {
    "schema_version": SELECTED_HASH_SCHEMA_VERSION,
    "source_artifact_sha256": workbook_sha256,
    "sheet": selection["sheet"],
    "cell": selection["cell"],
    "output_role": selection["output_role"],
    "unit_family": selection["unit_family"],
    "value_type": cell_record["type"] or "numeric",
    "cached_formula_value": cell_record["value"],
    "formula_sha256": formula_sha256,
  }
  comparison_output_sha256 = _sha256_text(_canonical_json(preimage))
  return {
    "comparison_id": selection["comparison_id"],
    "residual_id": "RES-006",
    "source_id": "VPS-BFM-014",
    "source_artifact_label": "BEC-O-V1.xlsx",
    "sheet": selection["sheet"],
    "cell": selection["cell"],
    "output_role": selection["output_role"],
    "unit_family": selection["unit_family"],
    "value_kind": "cached_formula_numeric" if has_numeric_cached_value else "missing",
    "cell_exists": cell_record["exists"] == "true",
    "formula_present": bool(cell_record["formula"]),
    "formula_sha256": formula_sha256,
    "cached_formula_value_present": has_cached_value,
    "numeric_cached_formula_value_present": has_numeric_cached_value,
    "comparison_output_sha256": (
      comparison_output_sha256 if has_numeric_cached_value else ""
    ),
    "hash_preimage_disclosure": (
      "hash_only; cached workbook value and formula text are not retained in "
      "this manifest"
    ),
    "calculation_source": "workbook_cached_formula_value_not_recomputed",
    "benchmark_consumed_for_release": False,
    "comparison_hash_is_calibration": False,
  }

def _selected_output_requirements(
  selected_hashes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
  requirements: list[dict[str, Any]] = []
  for row in selected_hashes:
    missing_reasons = []
    if not row["cell_exists"]:
      missing_reasons.append("selected_cell_missing")
    if not row["formula_present"]:
      missing_reasons.append("formula_missing")
    if not row["cached_formula_value_present"]:
      missing_reasons.append("cached_value_missing")
    if not row["numeric_cached_formula_value_present"]:
      missing_reasons.append("numeric_cached_value_missing")
    requirements.append(
      {
        "requirement_id": f"{row['comparison_id']}-EXECUTION-REQ",
        "residual_id": row["residual_id"],
        "source_artifact_label": row["source_artifact_label"],
        "sheet": row["sheet"],
        "cell": row["cell"],
        "output_role": row["output_role"],
        "required_action": (
          "execute the retained workbook or an independently reviewed "
          "equivalent tool, then record the same hash-only output cell "
          "preimage under frozen tolerance and rights policy"
        ),
        "current_status": (
          "cached_hash_available_recalculation_required"
          if row["comparison_output_sha256"]
          else "selected_output_hash_missing"
        ),
        "missing_reasons": missing_reasons,
        "raw_source_value_must_not_be_copied_to_dataset": True,
      }
    )
  return requirements

def _parse_beco_workbook(
  *,
  workbook_path: Path,
  workbook_sha256: str,
  repo_root: Path,
) -> dict[str, Any]:
  if not workbook_path.exists():
    return {
      "source_artifact_label": "BEC-O-V1.xlsx",
      "relative_path": _rel(workbook_path, repo_root),
      "workbook_sha256": "",
      "parse_status": "missing_workbook",
      "sheet_inventory": [],
      "selected_comparison_hashes": [],
      "selected_output_requirements": [],
    }
  try:
    with ZipFile(workbook_path) as zip_file:
      sheet_inventory, sheet_paths = _sheet_records(zip_file)
      metadata = {
        "core": _hashed_xml_properties(_read_xml(zip_file, "docProps/core.xml")),
        "app": _hashed_xml_properties(_read_xml(zip_file, "docProps/app.xml")),
      }
      selected_hashes = []
      for selection in BECO_SELECTED_OUTPUTS:
        sheet_path = sheet_paths.get(selection["sheet"], "")
        cell_record = (
          _cell_record(zip_file, sheet_path, selection["cell"])
          if sheet_path
          else {"exists": "false", "formula": "", "value": "", "type": ""}
        )
        selected_hashes.append(
          _selected_output_hash_record(
            workbook_sha256=workbook_sha256,
            selection=selection,
            cell_record=cell_record,
          )
        )
  except (BadZipFile, ET.ParseError) as exc:
    return {
      "source_artifact_label": "BEC-O-V1.xlsx",
      "relative_path": _rel(workbook_path, repo_root),
      "workbook_sha256": workbook_sha256,
      "parse_status": "unreadable_workbook_fail_closed",
      "parse_error": type(exc).__name__,
      "sheet_inventory": [],
      "selected_comparison_hashes": [],
      "selected_output_requirements": [
        {
          "requirement_id": "BEC-O-WORKBOOK-PARSE-REQ",
          "required_action": (
            "provide a readable retained workbook or independent "
            "reviewer-run selected output hash set"
          ),
          "current_status": "workbook_metadata_unavailable",
        }
      ],
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
  all_selected_hashes_present = len(selected_output_set) == len(BECO_SELECTED_OUTPUTS)
  return {
    "source_artifact_label": "BEC-O-V1.xlsx",
    "source_id": "VPS-BFM-014",
    "residual_id": "RES-006",
    "relative_path": _rel(workbook_path, repo_root),
    "workbook_sha256": workbook_sha256,
    "parse_status": "metadata_and_cached_formula_hashes_retained",
    "spreadsheet_calculation_executed": False,
    "spreadsheet_execution_status": (
      "not_executed_fail_closed_cached_values_only"
    ),
    "sheet_inventory": sheet_inventory,
    "workbook_metadata_hashes": metadata,
    "selected_comparison_hashes": selected_hashes,
    "selected_comparison_output_count": len(selected_output_set),
    "selected_comparison_output_set_sha256": _sha256_text(
      _canonical_json(selected_output_set)
    ),
    "all_selected_cached_hashes_present": all_selected_hashes_present,
    "selected_output_requirements": _selected_output_requirements(selected_hashes),
    "benchmark_consumed_for_release": False,
    "cached_workbook_values_are_calibration": False,
  }

def _tp20_reference(*, tp20_path: Path, repo_root: Path) -> dict[str, Any]:
  return {
    "source_artifact_label": "TP-20 PDF",
    "source_id": "VPS-BFM-014",
    "residual_id": "RES-006",
    "relative_path": _rel(tp20_path, repo_root),
    "artifact_sha256": _sha256_file(tp20_path) if tp20_path.exists() else "",
    "documentation_role": "blast_effects_computer_reference_context_only",
    "text_extracted_to_dataset": False,
    "benchmark_consumed_for_release": False,
    "source_presence_is_calibration": False,
  }

def _tp21_vocabulary(*, tp21_path: Path, repo_root: Path) -> dict[str, Any]:
  canonical_vocabulary = {
    "schema_version": "a2.tp21.criteria_vocabulary.v1",
    "source_artifact_sha256": _sha256_file(tp21_path) if tp21_path.exists() else "",
    "allowed_criteria_vocabulary": TP21_ALLOWED_CRITERIA_VOCABULARY,
  }
  vocabulary_sha256 = _sha256_text(_canonical_json(canonical_vocabulary))
  selected_requirements = [
    {
      "requirement_id": f"TP21-{index:03d}-HASH-ONLY-REQ",
      "residual_id": "RES-005",
      "criteria_key": row["criteria_key"],
      "required_action": (
        "reviewer selects a concrete TP-21 comparison case using this "
        "controlled key, records page/section provenance separately, and "
        "retains only hash-only comparison outputs in this package"
      ),
      "current_status": "selected_debris_output_hash_missing",
      "source_text_must_not_be_copied_to_dataset": True,
    }
    for index, row in enumerate(TP21_ALLOWED_CRITERIA_VOCABULARY, start=1)
  ]
  return {
    "source_artifact_label": "TP-21 PDF",
    "source_id": "VPS-BFM-015",
    "residual_id": "RES-005",
    "relative_path": _rel(tp21_path, repo_root),
    "artifact_sha256": canonical_vocabulary["source_artifact_sha256"],
    "criteria_vocabulary_status": (
      "controlled_vocabulary_hash_retained_no_source_text_dataset"
    ),
    "allowed_criteria_vocabulary": TP21_ALLOWED_CRITERIA_VOCABULARY,
    "criteria_vocabulary_sha256": vocabulary_sha256,
    "source_text_copied_to_dataset": False,
    "selected_debris_output_hashes": [],
    "selected_output_requirements": selected_requirements,
    "benchmark_consumed_for_release": False,
    "criteria_vocabulary_is_calibration": False,
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

def generate_mechanism_comparison_hashes(
  *,
  repo_root: Path = REPO_ROOT,
  source_payload_pack_dir: Path = SOURCE_PAYLOAD_PACK_DIR,
) -> dict[str, Any]:
  payload_paths = _payload_paths(source_payload_pack_dir)
  payload_inventory = _payload_inventory(
    source_payload_pack_dir=source_payload_pack_dir,
    repo_root=repo_root,
  )
  beco_path = payload_paths["BEC-O-V1.xlsx"]
  beco_sha256 = _sha256_file(beco_path) if beco_path.exists() else ""
  beco = _parse_beco_workbook(
    workbook_path=beco_path,
    workbook_sha256=beco_sha256,
    repo_root=repo_root,
  )
  tp21 = _tp21_vocabulary(tp21_path=payload_paths["TP-21 PDF"], repo_root=repo_root)
  tp20 = _tp20_reference(tp20_path=payload_paths["TP-20 PDF"], repo_root=repo_root)

  beco_hashes_present = bool(beco.get("all_selected_cached_hashes_present"))
  res006_gate_result = (
    "partial_fail_closed_beco_cached_comparison_hashes_present_"
    "spreadsheet_execution_required"
    if beco_hashes_present
    else "blocked_fail_closed_beco_selected_output_requirements_only"
  )
  guards = _non_authoritative_guards()

  return {
    "schema_version": SCHEMA_VERSION,
    "package_id": PACKAGE_ID,
    "status": "partial_fail_closed_mechanism_comparison_hash_manifest",
    "review_target": "res_005_006_mechanism_comparison_output_hashes",
    "source_payload_pack_ref": _rel(source_payload_pack_dir, repo_root),
    "current_gate_results": {
      "RES-005": (
        "partial_fail_closed_tp21_criteria_vocabulary_hash_present_"
        "selected_debris_output_requirements_open"
      ),
      "RES-006": res006_gate_result,
    },
    "comparison_hash_decision": {
      "closed_residual_ids_by_this_gate": [],
      "fail_closed": True,
      "source_presence_is_calibration": False,
      "beco_cached_hashes_are_calibration": False,
      "tp21_vocabulary_is_calibration": False,
      "benchmark_consumed_for_release": False,
      "release_grade_validated": False,
      "selected_beco_cached_output_hashes_present": beco_hashes_present,
      "tp21_selected_debris_output_hashes_present": False,
    },
    "payload_inventory": payload_inventory,
    "tp20_reference": tp20,
    "beco_workbook": beco,
    "tp21_criteria_vocabulary": tp21,
    "fail_closed_selected_output_requirements": {
      "RES-005": tp21["selected_output_requirements"],
      "RES-006": beco["selected_output_requirements"],
    },
    "source_consumption_validation_matrix": [
      {
        "lineage_id": "FRAG-TP21-DEBRIS",
        "residual_id": "RES-005",
        "source_present": payload_paths["TP-21 PDF"].exists(),
        "comparison_output_hash_present": False,
        "benchmark_consumed": False,
        "release_grade_validated": False,
        "evidence_status": (
          "criteria_vocabulary_hash_present_selected_outputs_missing"
        ),
      },
      {
        "lineage_id": "BLAST-BEC-O-TP20",
        "residual_id": "RES-006",
        "source_present": payload_paths["BEC-O-V1.xlsx"].exists()
        and payload_paths["TP-20 PDF"].exists(),
        "comparison_output_hash_present": beco_hashes_present,
        "benchmark_consumed": False,
        "release_grade_validated": False,
        "evidence_status": (
          "cached_spreadsheet_comparison_hashes_present_execution_missing"
          if beco_hashes_present
          else "selected_output_requirements_only"
        ),
      },
    ],
    "non_authoritative_guards": guards,
    "authority_guards_all_false": not any(guards.values()),
    "integration_notes": [
      "BEC-O cached formula hashes are retained as hash-only comparison anchors, not calibration.",
      "Spreadsheet calculation was not executed; release use still requires a reviewed execution chain.",
      "TP-21 is represented by a controlled criteria vocabulary hash and selected-output requirements, not copied source prose or tables.",
      "RES-005/006 remain fail-closed and do not release effect-scale, component-probability, Pk, or deterministic-fuze authority.",
    ],
    "behavior_risks": [
      "cached spreadsheet values could be mistaken for independently executed benchmark outputs",
      "TP-21 controlled vocabulary could be mistaken for admitted debris benchmark data",
      "source payload presence could be mistaken for release-grade calibration evidence",
    ],
  }

def write_retained_artifacts(
  *,
  retained_dir: Path = DEFAULT_RETAINED_DIR,
  repo_root: Path = REPO_ROOT,
  source_payload_pack_dir: Path = SOURCE_PAYLOAD_PACK_DIR,
) -> dict[str, Any]:
  artifact = generate_mechanism_comparison_hashes(
    repo_root=repo_root,
    source_payload_pack_dir=source_payload_pack_dir,
  )
  artifact_path = retained_dir / MECHANISM_COMPARISON_HASHES_FILENAME
  artifact_sha256 = write_and_hash_json(artifact_path, artifact, ensure_ascii=False)
  manifest = {
    "schema_version": RETAINED_MANIFEST_SCHEMA_VERSION,
    "package_id": PACKAGE_ID,
    "status": artifact["status"],
    "artifact_dir": _rel(retained_dir, repo_root),
    "mechanism_comparison_hashes_artifact": {
      "filename": MECHANISM_COMPARISON_HASHES_FILENAME,
      "relative_path": _rel(artifact_path, repo_root),
      "schema_version": artifact["schema_version"],
      "sha256": artifact_sha256,
    },
    "current_gate_results": artifact["current_gate_results"],
    "comparison_hash_decision": artifact["comparison_hash_decision"],
    "beco_selected_comparison_output_set_sha256": artifact["beco_workbook"].get(
      "selected_comparison_output_set_sha256", ""
    ),
    "tp21_criteria_vocabulary_sha256": artifact["tp21_criteria_vocabulary"][
      "criteria_vocabulary_sha256"
    ],
    "authority_guards_all_false": artifact["authority_guards_all_false"],
    "non_authoritative_guards": artifact["non_authoritative_guards"],
  }
  manifest_path = retained_dir / RETAINED_MANIFEST_FILENAME
  manifest_sha256 = write_and_hash_json(manifest_path, manifest, ensure_ascii=False)
  artifact["retained_artifact_sha256"] = artifact_sha256
  artifact["retained_manifest_sha256"] = manifest_sha256
  return artifact

def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description=(
      "Generate fail-closed A2 RES-005/006 mechanism comparison-output "
      "hash evidence."
    )
  )
  parser.add_argument(
    "--output",
    type=Path,
    help="Optional path for a copy of the generated artifact JSON.",
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
    help="Directory for retained mechanism comparison hash artifacts.",
  )
  parser.add_argument(
    "--write-retained-artifacts",
    action="store_true",
    help="Write mechanism_comparison_hashes.json and manifest.json.",
  )
  args = parser.parse_args(argv)

  if args.write_retained_artifacts:
    artifact = write_retained_artifacts(
      retained_dir=args.retained_dir,
      source_payload_pack_dir=args.source_payload_pack_dir,
    )
  else:
    artifact = generate_mechanism_comparison_hashes(
      source_payload_pack_dir=args.source_payload_pack_dir,
    )
  if args.output:
    _write_json(args.output, artifact)
  return 0

if __name__ == "__main__":
  raise SystemExit(main())
