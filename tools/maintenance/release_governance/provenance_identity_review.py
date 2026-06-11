#!/usr/bin/env python3
"""Evaluate the A2 provenance and surrogate-identity review gate.

This gate is a release-review surface for the remaining RES-001 / RES-002
blockers. It records author-side evidence that can be closed today, narrows the
remaining release-grade blockers, and stays fail-closed: it never creates stock
descriptors or grants effect-scale, component-probability, Pk, or deterministic
fuze authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance.release_governance import provenance_closeout as release_closeout_gate # noqa: E402
from tools.maintenance.candidate_artifacts import effect_scale_retained_pack as stage_b_retained # noqa: E402
from tools.maintenance.candidate_artifacts import component_probability_retained_pack as stage_c_retained # noqa: E402


PACKAGE_ID = (
  "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
  "beam_high_near_miss_0_35m_v0"
)
REVIEW_GATE_SCHEMA_VERSION = "a2.provenance_identity_review_gate.v1"
RETAINED_REVIEW_MANIFEST_SCHEMA_VERSION = (
  "a2.provenance_identity_review_retained_manifest.v1"
)
SOURCE_ARTIFACT_PACK_SCHEMA_VERSION = (
  "a2.provenance_identity_retained_source_artifact_pack.v1"
)

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
DEFAULT_RETAINED_REVIEW_DIR = (
  PACKAGE_DIR / "retained_artifacts" / "provenance_identity_review_20260531"
)
REVIEW_ARTIFACT_FILENAME = "provenance_identity_review_gate.json"
REVIEW_MANIFEST_FILENAME = "manifest.json"
SOURCE_ARTIFACT_PACK_MANIFEST_FILENAME = "source_artifact_pack_manifest.json"
REVIEW_SIGNOFF_MANIFEST_FILENAME = "independent_review_signoff_manifest.json"
CANONICAL_SOURCE_PAYLOAD_PACK_DIR = (
  PACKAGE_DIR / "retained_artifacts" / "source_payload_pack_20260531"
)

DOC_REFS = {
  "artifact_pin_manifest": (
    PACKAGE_DIR / "artifact_pin_manifest_stage_b_effect_scale_20260530.zh.md"
  ),
  "surrogate_identity_manifest": (
    PACKAGE_DIR / "surrogate_identity_manifest_stage_b_effect_scale_20260530.zh.md"
  ),
  "validation_manifest": PACKAGE_DIR / "validation_manifest_draft_blastfrag_20260528.zh.md",
  "validation_report": PACKAGE_DIR / "validation_report_draft.zh.md",
  "release_provenance_closeout_doc": (
    PACKAGE_DIR / "validation_release_provenance_closeout_gate_20260531.zh.md"
  ),
  "stage_b_release_closeout": (
    PACKAGE_DIR
    / "retained_artifacts"
    / "stage_b_effect_scale_20260531"
    / "stage_b_release_closeout.json"
  ),
  "stage_c_fragility_prep": (
    PACKAGE_DIR
    / "retained_artifacts"
    / "stage_c_fragility_validation_prep_20260531"
    / "stage_c_fragility_validation_prep.json"
  ),
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

REQUIRED_FORBIDDEN_OUTPUTS = [
  "effect_scale_authority",
  "component_failure_probability_authority",
  "pk_authority",
  "deterministic_fuze_authority",
]
RELEASE_ALLOWED_OUTPUT_POLICY_STATUSES = {
  "release_grade_frozen",
  "reviewer_frozen_release_grade",
  "independently_reviewed_release_grade",
}
RELEASE_BENCHMARK_CONSUMPTION_STATUSES = {
  "release_retained_benchmark_input",
  "release_grade_benchmark_input",
  "consumed_for_release_benchmark",
}
RELEASE_VALIDATION_STATUSES = {
  "validated",
  "release_validated",
  "independently_validated",
}
RELEASE_SOURCE_RETENTION_STATUSES = {
  "release_retained",
  "reviewer_retained",
  "canonical_release_retained",
}
RELEASE_RIGHTS_REVIEW_STATUSES = {
  "release_reviewed",
  "reviewer_approved_public_retention",
  "independently_reviewed_public_retention",
}
RELEASE_SIGNOFF_STATUSES = {
  "signed_off",
  "independent_review_signed_off",
  "release_review_signed_off",
}


def _read_text(path: Path) -> str:
  return path.read_text(encoding="utf-8")


def _read_text_if_exists(path: Path) -> str:
  return _read_text(path) if path.exists() else ""


def _canonical_json(payload: dict[str, Any]) -> str:
  return json.dumps(payload, indent=2, sort_keys=True)


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


def _display_path(path: Path, repo_root: Path) -> str:
  try:
    return path.relative_to(repo_root).as_posix()
  except ValueError:
    return str(path)


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
      return cells[1].strip()
  return ""


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


def _has_sha256(value: str) -> bool:
  return bool(re.search(r"\b[a-f0-9]{64}\b", value))


def _sha256_values(value: str) -> list[str]:
  return re.findall(r"\b[a-f0-9]{64}\b", value)


def _slug(value: str) -> str:
  return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "artifact"


def _forbidden_outputs(identity_text: str) -> list[str]:
  value = _extract_field(identity_text, "forbidden_outputs")
  normalized = value.replace("`", "")
  return [part.strip() for part in normalized.split(",") if part.strip()]


def _verified_source_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
  return [
    row
    for row in rows
    if "verified_candidate_artifact" in row["artifact_status"]
  ]


def _source_artifact_requirements(
  verified_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
  requirements: list[dict[str, str]] = []
  for row in verified_rows:
    named_hashes = re.findall(
      r"([^:;|]+):\s*([a-f0-9]{64})",
      row["sha256"],
    )
    if named_hashes:
      for label, sha256 in named_hashes:
        requirements.append(
          {
            "requirement_id": f"{row['artifact_id']}:{_slug(label)}",
            "artifact_id": row["artifact_id"],
            "source_id": row["source_id"],
            "source_artifact_label": label.strip(),
            "expected_sha256": sha256,
          }
        )
      continue

    hashes = _sha256_values(row["sha256"])
    if hashes:
      requirements.append(
        {
          "requirement_id": f"{row['artifact_id']}:source-artifact",
          "artifact_id": row["artifact_id"],
          "source_id": row["source_id"],
          "source_artifact_label": row["source_ref"],
          "expected_sha256": hashes[0],
        }
      )
  return requirements


def _check_status(author_side_satisfied: bool, release_grade_satisfied: bool) -> str:
  if release_grade_satisfied:
    return "release_grade_satisfied_by_this_review"
  if author_side_satisfied:
    return "author_side_closed_release_grade_blocked"
  return "blocked_author_side_evidence_missing"


def _load_json_if_exists(path: Path) -> dict[str, Any]:
  if not path.exists():
    return {}
  return json.loads(_read_text(path))


def _resolve_artifact_path(row: dict[str, Any], repo_root: Path) -> Path | None:
  value = row.get("relative_path") or row.get("path")
  if not value:
    return None
  path = Path(str(value))
  return path if path.is_absolute() else repo_root / path


def _source_artifact_pack_manifest_candidates(
  *,
  retained_review_dir: Path,
) -> list[tuple[str, Path]]:
  canonical_path = (
    CANONICAL_SOURCE_PAYLOAD_PACK_DIR / SOURCE_ARTIFACT_PACK_MANIFEST_FILENAME
  )
  fallback_path = retained_review_dir / SOURCE_ARTIFACT_PACK_MANIFEST_FILENAME
  candidates = [("canonical_source_payload_pack", canonical_path)]
  if fallback_path != canonical_path:
    candidates.append(("retained_review_dir_fallback", fallback_path))
  return candidates


def _load_source_artifact_pack_manifest(
  *,
  repo_root: Path,
  retained_review_dir: Path,
) -> dict[str, Any]:
  candidates = _source_artifact_pack_manifest_candidates(
    retained_review_dir=retained_review_dir
  )
  manifest_path = next((path for _, path in candidates if path.exists()), None)
  manifest_source = next(
    (source for source, path in candidates if manifest_path == path),
    "missing",
  )
  lookup_order = [
    {
      "source": source,
      "manifest_relative_path": _display_path(path, repo_root),
      "manifest_exists": path.exists(),
    }
    for source, path in candidates
  ]
  if manifest_path is None or not manifest_path.exists():
    return {
      "manifest_exists": False,
      "manifest_source": "missing",
      "manifest_relative_path": _display_path(candidates[0][1], repo_root),
      "manifest_lookup_order": lookup_order,
      "schema_version": SOURCE_ARTIFACT_PACK_SCHEMA_VERSION,
      "status": "missing_retained_source_artifact_pack",
      "artifacts": [],
      "all_payloads_exist": False,
      "all_payload_hashes_match": False,
      "retained_payload_count": 0,
      "rights_review_status": "missing",
      "source_payloads_retained": False,
    }

  manifest = json.loads(_read_text(manifest_path))
  artifacts = list(manifest.get("artifacts", []))
  payload_results: list[dict[str, Any]] = []
  for row in artifacts:
    path = _resolve_artifact_path(row, repo_root)
    exists = bool(path and path.exists())
    actual_sha256 = _sha256_file(path) if exists and path else ""
    expected_sha256 = str(row.get("sha256", ""))
    payload_results.append(
      {
        "artifact_id": row.get("artifact_id", ""),
        "source_artifact_label": row.get("source_artifact_label", ""),
        "relative_path": row.get("relative_path", ""),
        "payload_exists": exists,
        "expected_sha256": expected_sha256,
        "actual_sha256": actual_sha256,
        "hash_matches": bool(
          expected_sha256 and actual_sha256 == expected_sha256
        ),
      }
    )

  manifest["manifest_exists"] = True
  manifest["manifest_source"] = manifest_source
  manifest["manifest_relative_path"] = _display_path(manifest_path, repo_root)
  manifest["manifest_lookup_order"] = lookup_order
  manifest["manifest_sha256"] = _sha256_file(manifest_path)
  manifest["payload_results"] = payload_results
  manifest["all_payloads_exist"] = all(
    row["payload_exists"] for row in payload_results
  )
  manifest["all_payload_hashes_match"] = all(
    row["hash_matches"] for row in payload_results
  )
  manifest["retained_payload_count"] = sum(
    1 for row in payload_results if row["hash_matches"]
  )
  manifest["source_payloads_retained"] = (
    bool(payload_results)
    and manifest["all_payloads_exist"]
    and manifest["all_payload_hashes_match"]
  )
  return manifest


def _source_pack_payload_retention_summary(
  *,
  source_pack: dict[str, Any],
  requirements: list[dict[str, str]],
) -> dict[str, Any]:
  retained_hashes = {
    str(row.get("sha256", "")) for row in source_pack.get("artifacts", [])
  }
  missing_requirements = [
    req
    for req in requirements
    if req["expected_sha256"] not in retained_hashes
  ]
  payload_retention_satisfied = (
    bool(requirements)
    and source_pack.get("manifest_exists") is True
    and source_pack.get("schema_version") == SOURCE_ARTIFACT_PACK_SCHEMA_VERSION
    and source_pack.get("source_payloads_retained") is True
    and not missing_requirements
    and int(source_pack.get("retained_payload_count", 0)) >= len(requirements)
  )
  return {
    "payload_retention_satisfied": payload_retention_satisfied,
    "retained_payload_count": int(source_pack.get("retained_payload_count", 0)),
    "required_payload_count": len(requirements),
    "missing_required_payload_ids": [
      req["requirement_id"] for req in missing_requirements
    ],
    "missing_required_payload_hashes": [
      req["expected_sha256"] for req in missing_requirements
    ],
  }


def _source_pack_release_grade_blocking_reasons(
  *,
  source_pack: dict[str, Any],
  requirements: list[dict[str, str]],
) -> list[str]:
  if not source_pack.get("manifest_exists"):
    return ["source payload pack manifest missing"]

  reasons: list[str] = []
  retention_summary = _source_pack_payload_retention_summary(
    source_pack=source_pack,
    requirements=requirements,
  )
  if not retention_summary["payload_retention_satisfied"]:
    reasons.append("source payload retention incomplete or sha256 mismatch")
  if source_pack.get("rights_review_status") not in RELEASE_RIGHTS_REVIEW_STATUSES:
    reasons.append("rights review status is not release-reviewed")
  if source_pack.get("status") not in {
    "release_retained_source_artifact_pack",
    "reviewer_retained_source_artifact_pack",
  }:
    reasons.append("source pack status is not release-retained")

  rows = list(source_pack.get("artifacts", []))
  non_release_retained = [
    str(row.get("requirement_id") or row.get("artifact_id", ""))
    for row in rows
    if row.get("retention_status") not in RELEASE_SOURCE_RETENTION_STATUSES
  ]
  if non_release_retained:
    reasons.append(
      "payload retention statuses are candidate-only: "
      + ", ".join(non_release_retained)
    )
  rights_blocked = [
    str(row.get("requirement_id") or row.get("artifact_id", ""))
    for row in rows
    if row.get("rights_status") not in RELEASE_RIGHTS_REVIEW_STATUSES
  ]
  if rights_blocked:
    reasons.append(
      "payload rights statuses are not release-reviewed: "
      + ", ".join(rights_blocked)
    )
  forbidden_allowed_use_tokens = (
    "runtime authority",
    "stock authority",
    "authority_granted",
    "authoritative descriptor",
    "source truth",
  )
  forbidden_allowed_use_rows = [
    str(row.get("requirement_id") or row.get("artifact_id", ""))
    for row in rows
    if any(
      token in str(row.get("allowed_use", "")).lower()
      for token in forbidden_allowed_use_tokens
    )
  ]
  if forbidden_allowed_use_rows:
    reasons.append(
      "allowed_use contains authority-bearing wording: "
      + ", ".join(forbidden_allowed_use_rows)
    )
  return reasons


def _source_pack_release_grade_satisfied(
  *,
  source_pack: dict[str, Any],
  requirements: list[dict[str, str]],
) -> bool:
  retention_summary = _source_pack_payload_retention_summary(
    source_pack=source_pack,
    requirements=requirements,
  )
  if not retention_summary["payload_retention_satisfied"]:
    return False
  if source_pack.get("rights_review_status") not in RELEASE_RIGHTS_REVIEW_STATUSES:
    return False
  if source_pack.get("status") not in {
    "release_retained_source_artifact_pack",
    "reviewer_retained_source_artifact_pack",
  }:
    return False
  if not source_pack.get("all_payloads_exist"):
    return False
  if not source_pack.get("all_payload_hashes_match"):
    return False

  rows = list(source_pack.get("artifacts", []))
  retained_hashes = {str(row.get("sha256", "")) for row in rows}
  if not all(req["expected_sha256"] in retained_hashes for req in requirements):
    return False

  for row in rows:
    if row.get("retention_status") not in RELEASE_SOURCE_RETENTION_STATUSES:
      return False
    if row.get("rights_status") not in RELEASE_RIGHTS_REVIEW_STATUSES:
      return False
    allowed_use = str(row.get("allowed_use", "")).lower()
    forbidden_allowed_use_tokens = (
      "runtime authority",
      "stock authority",
      "authority_granted",
      "authoritative descriptor",
      "source truth",
    )
    if any(token in allowed_use for token in forbidden_allowed_use_tokens):
      return False
  return True


def _retained_source_artifact_pack_check(
  *,
  rows: list[dict[str, str]],
  source_pack: dict[str, Any],
) -> dict[str, Any]:
  verified_rows = _verified_source_rows(rows)
  requirements = _source_artifact_requirements(verified_rows)
  verified_ids = [row["artifact_id"] for row in verified_rows]
  sha256_pinned_ids = [
    row["artifact_id"] for row in verified_rows if _has_sha256(row["sha256"])
  ]
  author_side_satisfied = bool(verified_rows) and len(sha256_pinned_ids) == len(
    verified_rows
  )
  release_grade_satisfied = _source_pack_release_grade_satisfied(
    source_pack=source_pack,
    requirements=requirements,
  )
  missing_source_pack = not source_pack.get("manifest_exists", False)
  retention_summary = _source_pack_payload_retention_summary(
    source_pack=source_pack,
    requirements=requirements,
  )
  release_grade_blockers = _source_pack_release_grade_blocking_reasons(
    source_pack=source_pack,
    requirements=requirements,
  )
  if missing_source_pack:
    blocking_summary = (
      "no retained source artifact pack manifest exists for the verified "
      "DENIX payloads"
    )
    shortest_remaining_path = (
      "create source_artifact_pack_manifest.json with retained TP-20 PDF, "
      "BEC-O-V1.xlsx and TP-21 payloads; verify sha256; record rights review "
      "and non-authority allowed use"
    )
  elif retention_summary["payload_retention_satisfied"]:
    blocking_summary = (
      "canonical source payload pack retains all required TP-20, "
      "BEC-O-V1.xlsx and TP-21 payloads; release-grade rights review and "
      "source-pack status remain blocked"
    )
    shortest_remaining_path = (
      "keep the canonical retained payload pack pinned; complete "
      "release-grade rights review and reviewer-retained source-pack status"
    )
  else:
    blocking_summary = (
      "retained source artifact pack manifest is present, but required "
      "payload retention or sha256 matching is incomplete"
    )
    shortest_remaining_path = (
      "repair retained TP-20 PDF, BEC-O-V1.xlsx and TP-21 payload paths "
      "and sha256 values before rights review"
    )
  return {
    "check_id": "REVIEW-RES001-001",
    "residual_ids": ["RES-001"],
    "review_surface": "retained_source_artifact_pack",
    "author_side_satisfied": author_side_satisfied,
    "release_grade_satisfied": release_grade_satisfied,
    "status": _check_status(author_side_satisfied, release_grade_satisfied),
    "observed_evidence": {
      "verified_source_artifact_ids": verified_ids,
      "sha256_pinned_artifact_ids": sha256_pinned_ids,
      "required_source_artifact_payload_count": len(requirements),
      "required_source_artifacts": requirements,
      "source_pack_manifest_exists": source_pack.get("manifest_exists", False),
      "source_pack_manifest_source": source_pack.get("manifest_source", ""),
      "source_pack_status": source_pack.get("status", "missing"),
      "source_pack_manifest_ref": source_pack.get("manifest_relative_path", ""),
      "source_pack_lookup_order": source_pack.get("manifest_lookup_order", []),
      "rights_review_status": source_pack.get("rights_review_status", "missing"),
      "all_payloads_exist": source_pack.get("all_payloads_exist", False),
      "all_payload_hashes_match": source_pack.get(
        "all_payload_hashes_match",
        False,
      ),
      "retained_payload_count": retention_summary["retained_payload_count"],
      "payload_retention_satisfied": retention_summary[
        "payload_retention_satisfied"
      ],
      "missing_required_payload_ids": retention_summary[
        "missing_required_payload_ids"
      ],
      "release_grade_blocking_reasons": release_grade_blockers,
    },
    "blocking_summary": blocking_summary,
    "shortest_remaining_path": shortest_remaining_path,
  }


def _allowed_output_policy_check(
  *,
  pin_text: str,
  identity_text: str,
  source_pack: dict[str, Any],
) -> dict[str, Any]:
  third_party_policy = _extract_field(pin_text, "third_party_policy")
  forbidden_release_action = _extract_field(pin_text, "forbidden_release_action")
  policy_status = (
    source_pack.get("allowed_output_policy_status")
    or _extract_field(pin_text, "allowed_output_policy_status")
    or "missing"
  )
  forbidden_outputs = _forbidden_outputs(identity_text)
  missing_forbidden_outputs = [
    output for output in REQUIRED_FORBIDDEN_OUTPUTS if output not in forbidden_outputs
  ]
  author_side_satisfied = (
    "never auto-authoritative" in third_party_policy
    and "do not treat" in forbidden_release_action
    and not missing_forbidden_outputs
    and policy_status != "missing"
  )
  release_grade_satisfied = (
    author_side_satisfied
    and policy_status in RELEASE_ALLOWED_OUTPUT_POLICY_STATUSES
  )
  return {
    "check_id": "REVIEW-RES001-002",
    "residual_ids": ["RES-001"],
    "review_surface": "allowed_output_policy",
    "author_side_satisfied": author_side_satisfied,
    "release_grade_satisfied": release_grade_satisfied,
    "status": _check_status(author_side_satisfied, release_grade_satisfied),
    "observed_evidence": {
      "third_party_policy": third_party_policy,
      "forbidden_release_action": forbidden_release_action,
      "policy_status": policy_status,
      "policy_source": (
        "canonical_source_payload_pack"
        if source_pack.get("allowed_output_policy_status")
        else "artifact_pin_manifest"
      ),
      "forbidden_outputs": forbidden_outputs,
      "missing_forbidden_outputs": missing_forbidden_outputs,
    },
    "blocking_summary": (
      "candidate-side forbidden outputs and fail-closed policy are explicit, "
      "but no release-grade allowed-output policy signoff is recorded"
    ),
    "shortest_remaining_path": (
      "add reviewer-frozen allowed_output_policy_status and machine-readable "
      "rule that spreadsheet/tool outputs and comparison outputs cannot "
      "become source truth or runtime authority"
    ),
  }


def _benchmark_consumption_trace_check(
  *,
  rows: list[dict[str, str]],
  validation_manifest_text: str,
  source_pack: dict[str, Any],
) -> dict[str, Any]:
  verified_rows = _verified_source_rows(rows)
  explicit_non_consumed_ids = [
    row["artifact_id"]
    for row in verified_rows
    if row["consumption_status"] == "not_consumed_for_stage_b_release"
  ]
  release_consumed_ids = [
    row["artifact_id"]
    for row in verified_rows
    if row["consumption_status"] in RELEASE_BENCHMARK_CONSUMPTION_STATUSES
  ]
  manifest_records_non_consumption = (
    "not as acquired benchmark artifact" in validation_manifest_text
    or "not_consumed_for_stage_b_release" in validation_manifest_text
    or "不作为 acquired benchmark artifact" in validation_manifest_text
  )
  author_side_satisfied = bool(verified_rows) and (
    (
      len(explicit_non_consumed_ids) == len(verified_rows)
      and manifest_records_non_consumption
    )
    or len(release_consumed_ids) == len(verified_rows)
  )
  source_pack_chain_status = source_pack.get(
    "benchmark_consumption_chain_status",
    "missing",
  )
  release_grade_satisfied = (
    bool(verified_rows)
    and len(release_consumed_ids) == len(verified_rows)
    and source_pack_chain_status
    in {"release_reviewed", "reviewer_signed_off_release_consumption"}
  )
  return {
    "check_id": "REVIEW-RES001-003",
    "residual_ids": ["RES-001"],
    "review_surface": "benchmark_consumption_trace",
    "author_side_satisfied": author_side_satisfied,
    "release_grade_satisfied": release_grade_satisfied,
    "status": _check_status(author_side_satisfied, release_grade_satisfied),
    "observed_evidence": {
      "explicit_non_consumed_artifact_ids": explicit_non_consumed_ids,
      "release_consumed_artifact_ids": release_consumed_ids,
      "manifest_records_non_consumption": manifest_records_non_consumption,
      "source_payload_retention_satisfied": source_pack.get(
        "source_payloads_retained",
        False,
      ),
      "source_pack_chain_status": source_pack_chain_status,
    },
    "blocking_summary": (
      "verified DENIX rows have an author-side non-consumption trace, but "
      "no release-reviewed benchmark-consumption chain exists"
    ),
    "shortest_remaining_path": (
      "either keep DENIX payloads explicitly non-consumed for release, or "
      "promote them through a reviewed retained benchmark input chain with "
      "comparison-output hashes and signoff"
    ),
  }


def _comparison_hash_hits(texts: list[str]) -> list[dict[str, str]]:
  hits: list[dict[str, str]] = []
  pattern = re.compile(
    r"\bcomparison[-_ ]output[-_ ]sha256\b[^a-f0-9]{0,80}([a-f0-9]{64})",
    re.IGNORECASE,
  )
  for index, text in enumerate(texts):
    for match in pattern.finditer(text):
      hits.append(
        {
          "source_index": str(index),
          "comparison_output_sha256": match.group(1),
        }
      )
  return hits


def _artifact_hash_count(pack: dict[str, Any]) -> int:
  return sum(1 for row in pack.get("artifacts", []) if _has_sha256(row.get("sha256", "")))


def _comparison_output_hash_check(
  *,
  comparison_texts: list[str],
  stage_b_pack: dict[str, Any],
  stage_c_pack: dict[str, Any],
  source_pack: dict[str, Any],
) -> dict[str, Any]:
  hits = _comparison_hash_hits(comparison_texts)
  candidate_result_hash_count = _artifact_hash_count(stage_b_pack) + _artifact_hash_count(
    stage_c_pack
  )
  source_pack_hash_status = source_pack.get(
    "comparison_output_hash_status",
    "missing_selected_comparison_output_hashes",
  )
  source_pack_hash_count = int(source_pack.get("selected_beco_cached_output_hash_count", 0))
  source_pack_hash_manifest_present = source_pack_hash_status == (
    "partial_hash_manifest_present_release_review_blocked"
  )
  author_side_satisfied = bool(hits) or source_pack_hash_manifest_present
  release_grade_satisfied = bool(hits) and any(
    "reviewer" in text.lower() and "comparison-output" in text.lower()
    for text in comparison_texts
  )
  return {
    "check_id": "REVIEW-RES001-004",
    "residual_ids": ["RES-001"],
    "review_surface": "comparison_output_hash",
    "author_side_satisfied": author_side_satisfied,
    "release_grade_satisfied": release_grade_satisfied,
    "status": _check_status(author_side_satisfied, release_grade_satisfied),
    "observed_evidence": {
      "comparison_output_hashes": hits,
      "source_pack_comparison_output_hash_status": source_pack_hash_status,
      "source_pack_selected_beco_cached_output_hash_count": source_pack_hash_count,
      "candidate_result_artifact_hash_count": candidate_result_hash_count,
      "candidate_result_hashes_are_not_comparison_output_hashes": True,
    },
    "blocking_summary": (
      "hash-only comparison anchors may exist, but no release-reviewed "
      "selected comparison-output sha256 admission is recorded"
    ),
    "shortest_remaining_path": (
      "pin selected comparison-output sha256 values and reviewer-owned "
      "admission boundaries for any BEC-O or debris comparison outputs"
    ),
  }


def _identity_summary(identity_text: str) -> dict[str, Any]:
  return {
    "model_ref": _extract_field(identity_text, "model_ref"),
    "model_version": _extract_field(identity_text, "model_version"),
    "repo_commit": _extract_field(identity_text, "repo_commit"),
    "worktree_state": _extract_field(identity_text, "worktree_state"),
    "retained_artifact_pack_status": _extract_field(
      identity_text,
      "retained_artifact_pack_status",
    ),
    "current_validation_status": _extract_field(
      identity_text,
      "current_validation_status",
    ),
    "output_anchor_count": len(re.findall(r"/tmp/a2_[^|`]+\.json", identity_text)),
  }


def _clean_release_identity_check(identity_summary: dict[str, Any]) -> dict[str, Any]:
  author_side_satisfied = (
    bool(identity_summary["model_ref"])
    and bool(identity_summary["model_version"])
    and bool(re.fullmatch(r"[a-f0-9]{40}", identity_summary["repo_commit"]))
  )
  release_grade_satisfied = (
    identity_summary["worktree_state"] == "clean_release_candidate"
    and identity_summary["output_anchor_count"] == 0
  )
  blockers = []
  if identity_summary["worktree_state"] != "clean_release_candidate":
    blockers.append("worktree_state is not clean_release_candidate")
  if identity_summary["output_anchor_count"] > 0:
    blockers.append("/tmp author-side output anchors remain")
  return {
    "check_id": "REVIEW-RES002-001",
    "residual_ids": ["RES-002"],
    "review_surface": "clean_release_identity",
    "author_side_satisfied": author_side_satisfied,
    "release_grade_satisfied": release_grade_satisfied,
    "status": _check_status(author_side_satisfied, release_grade_satisfied),
    "observed_evidence": identity_summary,
    "blocking_summary": "; ".join(blockers)
    or "clean release identity is not proven",
    "shortest_remaining_path": (
      "publish a clean release candidate identity state with no /tmp "
      "author-output anchors and with retained outputs referenced from repo artifacts"
    ),
  }


def _release_validation_status_check(
  *,
  identity_summary: dict[str, Any],
  validation_manifest_text: str,
) -> dict[str, Any]:
  calibration_status = _extract_field(validation_manifest_text, "calibration_status")
  current_validation_status = str(identity_summary["current_validation_status"])
  author_side_satisfied = bool(current_validation_status) and bool(calibration_status)
  release_grade_satisfied = (
    current_validation_status in RELEASE_VALIDATION_STATUSES
    and calibration_status in RELEASE_VALIDATION_STATUSES
  )
  return {
    "check_id": "REVIEW-RES002-002",
    "residual_ids": ["RES-002"],
    "review_surface": "release_validation_status",
    "author_side_satisfied": author_side_satisfied,
    "release_grade_satisfied": release_grade_satisfied,
    "status": _check_status(author_side_satisfied, release_grade_satisfied),
    "observed_evidence": {
      "identity_current_validation_status": current_validation_status,
      "validation_manifest_calibration_status": calibration_status,
    },
    "blocking_summary": (
      "surrogate identity and validation manifest remain not_validated / "
      "unvalidated"
    ),
    "shortest_remaining_path": (
      "promote validation status only after formal result table, residual "
      "closeout and independent reviewer signoff exist"
    ),
  }


def _pack_release_grade_identity(pack: dict[str, Any]) -> bool:
  origin = pack.get("retained_origin_summary", {})
  return (
    bool(pack.get("manifest_exists"))
    and bool(pack.get("all_artifacts_exist"))
    and origin.get("independent_release_artifact_present") is True
    and origin.get("stock_runtime_authority_present") is True
    and "author" not in str(pack.get("status", ""))
    and "candidate" not in str(pack.get("status", ""))
  )


def _retained_identity_surface_check(
  *,
  stage_b_pack: dict[str, Any],
  stage_c_pack: dict[str, Any],
) -> dict[str, Any]:
  stage_b_complete = (
    stage_b_pack.get("manifest_exists") is True
    and stage_b_pack.get("all_artifacts_exist") is True
    and stage_b_pack.get("retained_artifact_count") == 4
  )
  stage_c_complete = (
    stage_c_pack.get("manifest_exists") is True
    and stage_c_pack.get("all_artifacts_exist") is True
    and stage_c_pack.get("retained_artifact_count") == 4
  )
  author_side_satisfied = stage_b_complete and stage_c_complete
  release_grade_satisfied = _pack_release_grade_identity(
    stage_b_pack
  ) and _pack_release_grade_identity(stage_c_pack)
  return {
    "check_id": "REVIEW-RES002-003",
    "residual_ids": ["RES-002"],
    "review_surface": "retained_identity_surface",
    "author_side_satisfied": author_side_satisfied,
    "release_grade_satisfied": release_grade_satisfied,
    "status": _check_status(author_side_satisfied, release_grade_satisfied),
    "observed_evidence": {
      "stage_b_status": stage_b_pack.get("status", ""),
      "stage_b_manifest_exists": stage_b_pack.get("manifest_exists", False),
      "stage_b_all_artifacts_exist": stage_b_pack.get("all_artifacts_exist", False),
      "stage_b_retained_artifact_count": stage_b_pack.get(
        "retained_artifact_count",
        0,
      ),
      "stage_b_retained_origin_summary": stage_b_pack.get(
        "retained_origin_summary",
        {},
      ),
      "stage_c_status": stage_c_pack.get("status", ""),
      "stage_c_manifest_exists": stage_c_pack.get("manifest_exists", False),
      "stage_c_all_artifacts_exist": stage_c_pack.get("all_artifacts_exist", False),
      "stage_c_retained_artifact_count": stage_c_pack.get(
        "retained_artifact_count",
        0,
      ),
      "stage_c_retained_origin_summary": stage_c_pack.get(
        "retained_origin_summary",
        {},
      ),
    },
    "blocking_summary": (
      "Stage B and Stage C retained packs are author-side candidate packs, "
      "not independent release identity artifacts"
    ),
    "shortest_remaining_path": (
      "add release identity artifacts and independent-review state distinct "
      "from author-side retained Stage B/C packs"
    ),
  }


def _load_review_signoff_manifest(
  *,
  repo_root: Path,
  retained_review_dir: Path,
) -> dict[str, Any]:
  path = retained_review_dir / REVIEW_SIGNOFF_MANIFEST_FILENAME
  if not path.exists():
    return {
      "manifest_exists": False,
      "manifest_relative_path": _display_path(path, repo_root),
      "reviewer_signoff_status": "missing",
      "signed_residual_ids": [],
    }
  manifest = json.loads(_read_text(path))
  manifest["manifest_exists"] = True
  manifest["manifest_relative_path"] = _display_path(path, repo_root)
  manifest["manifest_sha256"] = _sha256_file(path)
  return manifest


def _review_signoff_check(signoff_manifest: dict[str, Any]) -> dict[str, Any]:
  signed_residual_ids = set(signoff_manifest.get("signed_residual_ids", []))
  reviewer_signoff_status = signoff_manifest.get("reviewer_signoff_status", "missing")
  release_grade_satisfied = (
    reviewer_signoff_status in RELEASE_SIGNOFF_STATUSES
    and {"RES-001", "RES-002"}.issubset(signed_residual_ids)
    and bool(signoff_manifest.get("reviewer_id"))
    and bool(signoff_manifest.get("review_date"))
  )
  return {
    "check_id": "REVIEW-RES001-002-001",
    "residual_ids": ["RES-001", "RES-002"],
    "review_surface": "independent_review_signoff",
    "author_side_satisfied": False,
    "release_grade_satisfied": release_grade_satisfied,
    "status": _check_status(False, release_grade_satisfied),
    "observed_evidence": {
      "signoff_manifest_exists": signoff_manifest.get("manifest_exists", False),
      "signoff_manifest_ref": signoff_manifest.get("manifest_relative_path", ""),
      "reviewer_signoff_status": reviewer_signoff_status,
      "signed_residual_ids": sorted(signed_residual_ids),
      "reviewer_id_present": bool(signoff_manifest.get("reviewer_id")),
      "review_date_present": bool(signoff_manifest.get("review_date")),
    },
    "blocking_summary": (
      "no independent reviewer signoff manifest exists for RES-001/RES-002"
    ),
    "shortest_remaining_path": (
      "obtain independent reviewer signoff that covers retained source "
      "payloads, allowed-output policy, benchmark consumption, comparison "
      "hashes and clean release identity"
    ),
  }


def _mentions_residual(row: dict[str, Any], residual_id: str) -> bool:
  return residual_id in row.get("residual_ids", [])


def _residual_condition_trace(
  review_checks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
  trace: list[dict[str, Any]] = []
  for residual_id in ("RES-001", "RES-002"):
    checks = [row for row in review_checks if _mentions_residual(row, residual_id)]
    trace.append(
      {
        "residual_id": residual_id,
        "author_side_closed_check_ids": [
          row["check_id"] for row in checks if row["author_side_satisfied"]
        ],
        "author_side_blocking_check_ids": [
          row["check_id"] for row in checks if not row["author_side_satisfied"]
        ],
        "release_grade_blocking_check_ids": [
          row["check_id"] for row in checks if not row["release_grade_satisfied"]
        ],
        "gate_result": (
          "blocked"
          if any(not row["release_grade_satisfied"] for row in checks)
          else "release_review_ready_by_this_gate"
        ),
      }
    )
  return trace


def _release_closeout_summary(artifact: dict[str, Any]) -> dict[str, Any]:
  return {
    "status": artifact["status"],
    "schema_version": artifact["schema_version"],
    "release_closeout_ready": artifact["release_closeout_decision"][
      "release_closeout_ready"
    ],
    "release_closeout_blocked": artifact["release_closeout_decision"][
      "release_closeout_blocked"
    ],
    "blocking_residual_ids": list(dict.fromkeys(artifact["blocking_residual_ids"])),
  }


def _non_authoritative_guards() -> dict[str, bool]:
  return {
    "stock_descriptor_created": False,
    "stock_database_authority_granted": False,
    "effect_scale_authority_released": False,
    "effect_scale_authority_in_stock": False,
    "component_failure_probability_authority_released": False,
    "component_failure_probability_authority_in_stock": False,
    "pk_authority_released": False,
    "pk_authority": False,
    "deterministic_fuze_authority_released": False,
    "deterministic_fuze_authority": False,
  }


def _source_payload_pack_consumption_summary(
  *,
  source_pack: dict[str, Any],
  review_checks: list[dict[str, Any]],
) -> dict[str, Any]:
  checks = {row["check_id"]: row for row in review_checks}
  source_evidence = checks["REVIEW-RES001-001"]["observed_evidence"]
  return {
    "manifest_source": source_evidence["source_pack_manifest_source"],
    "manifest_ref": source_evidence["source_pack_manifest_ref"],
    "payload_retention_satisfied": source_evidence[
      "payload_retention_satisfied"
    ],
    "retained_payload_count": source_evidence["retained_payload_count"],
    "required_payload_count": source_evidence[
      "required_source_artifact_payload_count"
    ],
    "rights_review_status": source_evidence["rights_review_status"],
    "rights_review_blocked": source_pack.get("rights_review_status")
    not in RELEASE_RIGHTS_REVIEW_STATUSES,
    "allowed_output_policy_blocked": not checks["REVIEW-RES001-002"][
      "release_grade_satisfied"
    ],
    "benchmark_consumption_review_blocked": not checks["REVIEW-RES001-003"][
      "release_grade_satisfied"
    ],
    "comparison_output_hash_blocked": not checks["REVIEW-RES001-004"][
      "release_grade_satisfied"
    ],
    "independent_review_signoff_blocked": not checks[
      "REVIEW-RES001-002-001"
    ]["release_grade_satisfied"],
    "authority_release_included": False,
  }


def generate_provenance_identity_review_gate(
  *,
  repo_root: Path = REPO_ROOT,
  retained_review_dir: Path = DEFAULT_RETAINED_REVIEW_DIR,
) -> dict[str, Any]:
  pin_text = _read_text(DOC_REFS["artifact_pin_manifest"])
  identity_text = _read_text(DOC_REFS["surrogate_identity_manifest"])
  validation_manifest_text = _read_text(DOC_REFS["validation_manifest"])
  rows = _parse_artifact_pin_rows(pin_text)
  source_pack = _load_source_artifact_pack_manifest(
    repo_root=repo_root,
    retained_review_dir=retained_review_dir,
  )
  signoff_manifest = _load_review_signoff_manifest(
    repo_root=repo_root,
    retained_review_dir=retained_review_dir,
  )
  stage_b_pack = stage_b_retained.load_retained_artifact_pack_manifest(
    repo_root=repo_root
  )
  stage_c_pack = stage_c_retained.load_retained_artifact_pack_manifest(
    repo_root=repo_root
  )
  identity = _identity_summary(identity_text)
  comparison_texts = [
    _read_text_if_exists(path)
    for path in (
      DOC_REFS["validation_manifest"],
      DOC_REFS["validation_report"],
      DOC_REFS["release_provenance_closeout_doc"],
      DOC_REFS["stage_b_release_closeout"],
      DOC_REFS["stage_c_fragility_prep"],
    )
  ]
  closeout_artifact = release_closeout_gate.generate_release_provenance_closeout_gate(
    repo_root=repo_root
  )

  review_checks = [
    _retained_source_artifact_pack_check(rows=rows, source_pack=source_pack),
    _allowed_output_policy_check(
      pin_text=pin_text,
      identity_text=identity_text,
      source_pack=source_pack,
    ),
    _benchmark_consumption_trace_check(
      rows=rows,
      validation_manifest_text=validation_manifest_text,
      source_pack=source_pack,
    ),
    _comparison_output_hash_check(
      comparison_texts=comparison_texts,
      stage_b_pack=stage_b_pack,
      stage_c_pack=stage_c_pack,
      source_pack=source_pack,
    ),
    _clean_release_identity_check(identity),
    _release_validation_status_check(
      identity_summary=identity,
      validation_manifest_text=validation_manifest_text,
    ),
    _retained_identity_surface_check(
      stage_b_pack=stage_b_pack,
      stage_c_pack=stage_c_pack,
    ),
    _review_signoff_check(signoff_manifest),
  ]
  release_ready = all(row["release_grade_satisfied"] for row in review_checks)
  residual_trace = _residual_condition_trace(review_checks)
  guards = _non_authoritative_guards()
  source_payload_consumption = _source_payload_pack_consumption_summary(
    source_pack=source_pack,
    review_checks=review_checks,
  )

  return {
    "package_id": PACKAGE_ID,
    "schema_version": REVIEW_GATE_SCHEMA_VERSION,
    "status": (
      "release_grade_provenance_identity_review_ready_non_authoritative"
      if release_ready
      else "blocked_non_authoritative_provenance_identity_review_gate"
    ),
    "review_target": "res_001_002_provenance_identity_release_review",
    "readiness_level": (
      "author_side_subitems_partly_closed_release_grade_review_blocked"
    ),
    "scope": {
      "target_type": "F-16C_Block50",
      "weapon_class": "AIM-120C-class",
      "weapon_family": "blast_fragmentation",
      "aspect_bucket": "beam",
      "closure_bucket": "high",
      "miss_distance_bucket": "near_miss_0_35m",
    },
    "review_decision": {
      "release_grade_review_ready": release_ready,
      "release_grade_review_blocked": not release_ready,
      "authority_release_included": False,
      "retained_review_artifact_included": True,
      "retained_source_payload_pack_included": bool(
        source_pack.get("source_payloads_retained", False)
      ),
    },
    "release_provenance_closeout_gate_summary": _release_closeout_summary(
      closeout_artifact
    ),
    "source_payload_pack_consumption": source_payload_consumption,
    "review_checks": review_checks,
    "residual_condition_trace": residual_trace,
    "residual_gate_results": {
      row["residual_id"]: row["gate_result"] for row in residual_trace
    },
    "blocking_residual_ids": [
      residual_id
      for row in residual_trace
      if row["gate_result"] == "blocked"
      for residual_id in [row["residual_id"]]
    ]
    + ["RES-013/014-boundary"],
    "author_side_closed_summary": {
      "RES-001": [
        "verified DENIX source artifact rows and sha256 pins are present",
        "canonical source payload pack retains all required payload files",
        "forbidden outputs and forbidden release action are explicit",
        "verified DENIX rows are explicitly marked not consumed for Stage B release",
      ],
      "RES-002": [
        "surrogate model/version/repo anchor is recorded",
        "Stage B and Stage C author-side retained identity surfaces are present",
      ],
    },
    "remaining_release_grade_paths": {
      "RES-001": [
        "release-grade rights review for the canonical retained source payload pack",
        "release-grade allowed-output policy freeze",
        "reviewed benchmark-consumption chain or explicit release non-consumption decision",
        "selected comparison-output sha256 values",
        "independent reviewer signoff",
      ],
      "RES-002": [
        "clean release identity state with no /tmp anchors",
        "release validation status",
        "release identity artifacts distinct from author-side retained packs",
        "independent reviewer signoff",
      ],
    },
    "explicit_boundaries": [
      "do not create a stock descriptor from this review gate",
      "do not promote author-side retained packs to release identity",
      "do not treat comparison-output hashes as source truth",
      "do not grant Pk or deterministic fuze authority from this gate",
    ],
    "non_authoritative_guards": guards,
    "authority_guards_all_false": not any(guards.values()),
  }


def write_retained_review_artifact(
  *,
  repo_root: Path = REPO_ROOT,
  retained_review_dir: Path = DEFAULT_RETAINED_REVIEW_DIR,
) -> dict[str, Any]:
  retained_review_dir.mkdir(parents=True, exist_ok=True)
  artifact = generate_provenance_identity_review_gate(
    repo_root=repo_root,
    retained_review_dir=retained_review_dir,
  )
  artifact_path = retained_review_dir / REVIEW_ARTIFACT_FILENAME
  artifact_text = _canonical_json(artifact) + "\n"
  artifact_path.write_text(artifact_text, encoding="utf-8")
  source_payload_consumption = artifact["source_payload_pack_consumption"]

  manifest = {
    "package_id": PACKAGE_ID,
    "schema_version": RETAINED_REVIEW_MANIFEST_SCHEMA_VERSION,
    "status": "retained_provenance_identity_review_artifact_non_authoritative",
    "artifact_dir": _display_path(retained_review_dir, repo_root),
    "retention_scope": "provenance_identity_review_gate_output_only",
    "source_artifact_pack_manifest_expected": _display_path(
      CANONICAL_SOURCE_PAYLOAD_PACK_DIR
      / SOURCE_ARTIFACT_PACK_MANIFEST_FILENAME,
      repo_root,
    ),
    "source_artifact_pack_manifest_consumed": source_payload_consumption[
      "manifest_ref"
    ],
    "source_artifact_payloads_retained": source_payload_consumption[
      "payload_retention_satisfied"
    ],
    "source_payload_release_blockers": {
      "rights_review_blocked": source_payload_consumption[
        "rights_review_blocked"
      ],
      "allowed_output_policy_blocked": source_payload_consumption[
        "allowed_output_policy_blocked"
      ],
      "benchmark_consumption_review_blocked": source_payload_consumption[
        "benchmark_consumption_review_blocked"
      ],
      "comparison_output_hash_blocked": source_payload_consumption[
        "comparison_output_hash_blocked"
      ],
      "independent_review_signoff_blocked": source_payload_consumption[
        "independent_review_signoff_blocked"
      ],
    },
    "independent_review_signoff_present": False,
    "artifacts": [
      {
        "artifact_key": "provenance_identity_review_gate",
        "filename": REVIEW_ARTIFACT_FILENAME,
        "relative_path": _display_path(artifact_path, repo_root),
        "schema_version": REVIEW_GATE_SCHEMA_VERSION,
        "sha256": _sha256_file(artifact_path),
        "content_sha256": _sha256_text(artifact_text.rstrip("\n")),
        "status": artifact["status"],
        "allowed_claim": (
          "release-review blocker surface for RES-001/RES-002 is retained"
        ),
        "forbidden_claim": (
          "stock descriptor release, source payload rights review, "
          "independent review signoff, effect-scale authority, "
          "component-probability authority, Pk authority, or "
          "deterministic-fuze authority"
        ),
      }
    ],
    "non_authoritative_guards": _non_authoritative_guards(),
  }
  manifest_path = retained_review_dir / REVIEW_MANIFEST_FILENAME
  manifest_path.write_text(_canonical_json(manifest) + "\n", encoding="utf-8")
  manifest["manifest_relative_path"] = _display_path(manifest_path, repo_root)
  manifest["manifest_sha256"] = _sha256_file(manifest_path)
  manifest["retained_artifact_count"] = len(manifest["artifacts"])
  manifest["all_artifacts_exist"] = artifact_path.exists()
  return manifest


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description=(
      "Evaluate the release-grade provenance/identity review gate for the "
      "A2 blast-fragmentation candidate package."
    )
  )
  parser.add_argument(
    "--output",
    type=Path,
    help="Optional JSON output path for the gate artifact. Defaults to stdout.",
  )
  parser.add_argument(
    "--write-retained-artifact",
    action="store_true",
    help=(
      "Write the gate artifact and a retained review manifest under the "
      "provenance_identity_review_20260531 retained-artifacts directory."
    ),
  )
  parser.add_argument(
    "--retained-output-dir",
    type=Path,
    default=DEFAULT_RETAINED_REVIEW_DIR,
    help="Directory used for retained review artifacts and optional manifests.",
  )
  args = parser.parse_args(argv)

  if args.write_retained_artifact:
    payload = write_retained_review_artifact(
      retained_review_dir=args.retained_output_dir
    )
  else:
    payload = generate_provenance_identity_review_gate(
      retained_review_dir=args.retained_output_dir
    )

  text = _canonical_json(payload)
  if args.output:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text + "\n", encoding="utf-8")
  else:
    print(text)
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
