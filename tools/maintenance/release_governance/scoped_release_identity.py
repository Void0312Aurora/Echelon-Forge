#!/usr/bin/env python3
"""Build the bounded RES-002 scoped release identity surface for A2.

The gate consumes existing retained Stage B/C artifacts, the provenance identity
review, the source payload pack, and current hashes for relevant files. It is
intentionally narrow: it can pass a repo-contained scoped identity surface while
still refusing validation or authority promotion.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
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
  _sha256_text,
  write_and_hash_json,
)
PACKAGE_ID = (
  "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
  "beam_high_near_miss_0_35m_v0"
)
SCOPED_GATE_SCHEMA_VERSION = "a2.res002_scoped_release_identity_gate.v1"
SCOPED_MANIFEST_SCHEMA_VERSION = "a2.res002_scoped_release_identity_manifest.v1"

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
DEFAULT_RETAINED_OUTPUT_DIR = (
  PACKAGE_DIR / "retained_artifacts" / "res002_scoped_release_identity_20260531"
)
GATE_FILENAME = "res002_scoped_release_identity_gate.json"
MANIFEST_FILENAME = "manifest.json"
TEMP_ANCHOR = "/tmp"

DOC_REFS = {
  "subagent_usage_policy": (
    REPO_ROOT
    / "docs"
    / "engineering"
    / "automation"
    / "standards"
    / "subagent_usage_policy.md"
  ),
  "residual_register": PACKAGE_DIR / "residual_register.zh.md",
  "surrogate_identity_manifest": (
    PACKAGE_DIR / "surrogate_identity_manifest_stage_b_effect_scale_20260530.zh.md"
  ),
  "provenance_identity_review_doc": (
    PACKAGE_DIR / "validation_provenance_identity_review_gate_20260531.zh.md"
  ),
  "source_payload_pack_doc": PACKAGE_DIR / "source_payload_pack_20260531.zh.md",
  "source_rights_output_policy_doc": (
    PACKAGE_DIR / "source_rights_output_policy_20260531.zh.md"
  ),
  "release_provenance_closeout_doc": (
    PACKAGE_DIR / "validation_release_provenance_closeout_gate_20260531.zh.md"
  ),
  "runtime_default_effects": (
    REPO_ROOT / "src" / "models" / "weapons" / "default_effects_model.cpp"
  ),
  "target_input_db": (
    REPO_ROOT
    / "examples"
    / "config"
    / "database"
    / "aircraft"
    / "units"
    / "f16c_block50.json"
  ),
  "weapon_input_db": (
    REPO_ROOT
    / "examples"
    / "config"
    / "database"
    / "weapons"
    / "air_to_air"
    / "aim_120c.json"
  ),
  "validation_scaffold_tool": (
    REPO_ROOT
    / "tools"
    / "maintenance"
    / "candidate_artifacts"
    / "validation_scaffold.py"
  ),
  "scope_boundary_probe_tool": (
    REPO_ROOT
    / "tools"
    / "maintenance"
    / "candidate_artifacts"
    / "scope_boundary_probe.py"
  ),
  "stage_b_snapshot_tool": (
    REPO_ROOT
    / "tools"
    / "maintenance"
    / "candidate_artifacts"
    / "effect_scale_snapshot.py"
  ),
  "stage_c_snapshot_tool": (
    REPO_ROOT
    / "tools"
    / "maintenance"
    / "candidate_artifacts"
    / "component_probability_snapshot.py"
  ),
  "source_payload_pack_tool": (
    REPO_ROOT / "tools" / "maintenance" / "damage_model.py"
  ),
  "provenance_identity_review_tool": (
    REPO_ROOT
    / "tools"
    / "maintenance"
    / "damage_model.py"
  ),
}

REQUIRED_RETAINED_DIRS = {
  "stage_b_effect_scale_20260530": (
    PACKAGE_DIR / "retained_artifacts" / "stage_b_effect_scale_20260530"
  ),
  "stage_b_effect_scale_20260531": (
    PACKAGE_DIR / "retained_artifacts" / "stage_b_effect_scale_20260531"
  ),
  "stage_b_independent_review_20260531": (
    PACKAGE_DIR / "retained_artifacts" / "stage_b_independent_review_20260531"
  ),
  "stage_c_component_probability_20260530": (
    PACKAGE_DIR / "retained_artifacts" / "stage_c_component_probability_20260530"
  ),
  "stage_c_fragility_benchmark_20260531": (
    PACKAGE_DIR / "retained_artifacts" / "stage_c_fragility_benchmark_20260531"
  ),
  "stage_c_fragility_review_20260531": (
    PACKAGE_DIR / "retained_artifacts" / "stage_c_fragility_review_20260531"
  ),
  "source_payload_pack_20260531": (
    PACKAGE_DIR / "retained_artifacts" / "source_payload_pack_20260531"
  ),
  "provenance_identity_review_20260531": (
    PACKAGE_DIR / "retained_artifacts" / "provenance_identity_review_20260531"
  ),
}

REQUIRED_FORBIDDEN_OUTPUTS = [
  "effect_scale_authority",
  "component_failure_probability_authority",
  "pk_authority",
  "deterministic_fuze_authority",
]

def _canonical_json(payload: dict[str, Any]) -> str:
  return json.dumps(payload, indent=2, sort_keys=True)

def _display_path(path: Path, repo_root: Path) -> str:
  # Kept local: non-resolving relative_to; differs from manifest_integrity._display_path (resolve).
  try:
    return path.relative_to(repo_root).as_posix()
  except ValueError:
    return str(path)

def _read_text(path: Path) -> str:
  return path.read_text(encoding="utf-8")

def _run_git(repo_root: Path, *args: str) -> str:
  result = subprocess.run(
    ["git", *args],
    cwd=repo_root,
    check=True,
    text=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
  )
  return result.stdout.strip()

def _repo_commit(repo_root: Path) -> str:
  return _run_git(repo_root, "rev-parse", "HEAD")

def _git_status_rows(repo_root: Path) -> list[str]:
  return _run_git(repo_root, "status", "--porcelain=v1").splitlines()

def _dirty_status_by_path(repo_root: Path) -> dict[str, str]:
  statuses: dict[str, str] = {}
  for row in _git_status_rows(repo_root):
    if not row:
      continue
    status = row[:2]
    path_text = row[3:]
    if " -> " in path_text:
      path_text = path_text.split(" -> ", maxsplit=1)[1]
    statuses[path_text] = status
  return statuses

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

def _forbidden_outputs(identity_text: str) -> list[str]:
  value = _extract_field(identity_text, "forbidden_outputs")
  normalized = value.replace("`", "")
  return [part.strip() for part in normalized.split(",") if part.strip()]

def _relevant_file_hash_inventory(repo_root: Path) -> list[dict[str, Any]]:
  dirty_statuses = _dirty_status_by_path(repo_root)
  rows: list[dict[str, Any]] = []
  for role, path in DOC_REFS.items():
    rel_path = _display_path(path, repo_root)
    exists = path.exists()
    rows.append(
      {
        "role": role,
        "relative_path": rel_path,
        "exists": exists,
        "sha256": _sha256_file(path) if exists else None,
        "git_status": dirty_statuses.get(rel_path, "clean"),
        "identity_binding": "current_file_hash",
      }
    )
  return rows

def _retained_artifact_hash_inventory(repo_root: Path) -> list[dict[str, Any]]:
  rows: list[dict[str, Any]] = []
  for retained_key, retained_dir in REQUIRED_RETAINED_DIRS.items():
    files = sorted(path for path in retained_dir.rglob("*") if path.is_file())
    for path in files:
      rows.append(
        {
          "retained_key": retained_key,
          "relative_path": _display_path(path, repo_root),
          "sha256": _sha256_file(path),
          "size_bytes": path.stat().st_size,
          "under_repo_path": _is_under(path, repo_root),
          "under_candidate_retained_artifacts": _is_under(
            path, PACKAGE_DIR / "retained_artifacts"
          ),
        }
      )
  return rows

def _required_retained_dir_summary(repo_root: Path) -> list[dict[str, Any]]:
  rows: list[dict[str, Any]] = []
  for retained_key, retained_dir in REQUIRED_RETAINED_DIRS.items():
    files = sorted(path for path in retained_dir.rglob("*") if path.is_file())
    rows.append(
      {
        "retained_key": retained_key,
        "relative_path": _display_path(retained_dir, repo_root),
        "exists": retained_dir.is_dir(),
        "file_count": len(files),
        "under_repo_path": _is_under(retained_dir, repo_root),
        "under_candidate_retained_artifacts": _is_under(
          retained_dir, PACKAGE_DIR / "retained_artifacts"
        ),
      }
    )
  return rows

def _is_under(path: Path, parent: Path) -> bool:
  try:
    path.resolve().relative_to(parent.resolve())
  except ValueError:
    return False
  return True

def _status_summary(repo_root: Path, relevant_inventory: list[dict[str, Any]]) -> dict[str, Any]:
  status_rows = _git_status_rows(repo_root)
  relevant_dirty_paths = [
    row["relative_path"]
    for row in relevant_inventory
    if row["git_status"] != "clean"
  ]
  return {
    "global_worktree_dirty": bool(status_rows),
    "global_dirty_path_count": len(status_rows),
    "relevant_dirty_path_count": len(relevant_dirty_paths),
    "relevant_dirty_paths": relevant_dirty_paths,
    "unrelated_dirty_path_count": max(len(status_rows) - len(relevant_dirty_paths), 0),
    "note": (
      "The repository has dirty paths outside this gate. This scoped gate "
      "does not clean or revert them; it binds relevant files by current "
      "sha256 and ignores unrelated dirty paths unless a global-clean "
      "policy is required."
    ),
  }

def _standards_global_clean_policy(repo_root: Path) -> dict[str, Any]:
  policy_text = _read_text(DOC_REFS["subagent_usage_policy"])
  strict_patterns = [
    r"\bMUST\b[^\n]{0,80}\bclean\b[^\n]{0,80}\bworktree\b",
    r"\bglobally clean\b[^\n]{0,80}\brequired\b",
    r"\bglobal\b[^\n]{0,80}\bclean\b[^\n]{0,80}\brepo\b",
  ]
  matching_rules = [
    pattern
    for pattern in strict_patterns
    if re.search(pattern, policy_text, flags=re.IGNORECASE)
  ]
  return {
    "policy_refs": [_display_path(DOC_REFS["subagent_usage_policy"], repo_root)],
    "global_clean_worktree_required": bool(matching_rules),
    "matching_rule_patterns": matching_rules,
    "decision_basis": (
      "No mandatory globally clean worktree rule was found in the "
      "governance policy consumed by this gate."
      if not matching_rules
      else "A mandatory globally clean worktree rule matched the consumed governance policy."
    ),
  }

def _source_payload_summary(repo_root: Path) -> dict[str, Any]:
  path = (
    PACKAGE_DIR
    / "retained_artifacts"
    / "source_payload_pack_20260531"
    / "source_artifact_pack_manifest.json"
  )
  if not path.exists():
    return {
      "manifest_exists": False,
      "manifest_relative_path": _display_path(path, repo_root),
      "source_payloads_retained": False,
      "all_payload_hashes_match": False,
      "retained_payload_count": 0,
      "required_payload_count": 0,
    }
  payload = json.loads(path.read_text(encoding="utf-8"))
  return {
    "manifest_exists": True,
    "manifest_relative_path": _display_path(path, repo_root),
    "manifest_sha256": _sha256_file(path),
    "source_payloads_retained": bool(payload.get("source_payloads_retained")),
    "all_payload_hashes_match": bool(payload.get("all_payload_hashes_match")),
    "retained_payload_count": int(payload.get("retained_payload_count", 0)),
    "required_payload_count": int(payload.get("required_payload_count", 0)),
    "rights_review_status": payload.get("rights_review_status", "missing"),
    "allowed_output_policy_status": payload.get(
      "allowed_output_policy_status", "missing"
    ),
    "benchmark_consumption_chain_status": payload.get(
      "benchmark_consumption_chain_status", "missing"
    ),
  }

def _provenance_review_summary(repo_root: Path) -> dict[str, Any]:
  path = (
    PACKAGE_DIR
    / "retained_artifacts"
    / "provenance_identity_review_20260531"
    / "provenance_identity_review_gate.json"
  )
  if not path.exists():
    return {
      "review_artifact_exists": False,
      "review_artifact_relative_path": _display_path(path, repo_root),
      "res002_prior_gate_result": "missing",
    }
  payload = json.loads(path.read_text(encoding="utf-8"))
  return {
    "review_artifact_exists": True,
    "review_artifact_relative_path": _display_path(path, repo_root),
    "review_artifact_sha256": _sha256_file(path),
    "res002_prior_gate_result": payload.get("residual_gate_results", {}).get(
      "RES-002", "missing"
    ),
    "prior_status": payload.get("status", "missing"),
    "prior_review_target": payload.get("review_target", "missing"),
  }

def _non_authoritative_guards() -> dict[str, bool]:
  return {
    "stock_descriptor_created": False,
    "stock_database_authority_granted": False,
    "runtime_authority_granted": False,
    "effect_scale_authority_released": False,
    "effect_scale_authority_in_stock": False,
    "component_failure_probability_authority_released": False,
    "component_failure_probability_authority_in_stock": False,
    "pk_authority_released": False,
    "pk_authority": False,
    "deterministic_fuze_authority_released": False,
    "deterministic_fuze_authority": False,
    "validation_status_promoted": False,
    "residual_register_edited": False,
  }

def _temporary_anchor_count(value: Any) -> int:
  return _canonical_json(value).count(TEMP_ANCHOR)

def _identity_summary(repo_root: Path) -> dict[str, Any]:
  identity_text = _read_text(DOC_REFS["surrogate_identity_manifest"])
  forbidden_outputs = _forbidden_outputs(identity_text)
  return {
    "model_ref": _extract_field(identity_text, "model_ref"),
    "model_version": _extract_field(identity_text, "model_version"),
    "package_id": _extract_field(identity_text, "package_id") or PACKAGE_ID,
    "identity_manifest_repo_commit": _extract_field(identity_text, "repo_commit"),
    "identity_manifest_worktree_state": _extract_field(identity_text, "worktree_state"),
    "identity_manifest_validation_status": _extract_field(
      identity_text, "current_validation_status"
    ),
    "forbidden_outputs": forbidden_outputs,
    "missing_forbidden_outputs": [
      output for output in REQUIRED_FORBIDDEN_OUTPUTS if output not in forbidden_outputs
    ],
    "legacy_identity_manifest_temp_anchor_count": identity_text.count(TEMP_ANCHOR),
    "surrogate_identity_manifest_ref": _display_path(
      DOC_REFS["surrogate_identity_manifest"], repo_root
    ),
  }

def generate_res002_scoped_release_identity_gate(
  *,
  repo_root: Path = REPO_ROOT,
  force_global_clean_required: bool | None = None,
) -> dict[str, Any]:
  identity = _identity_summary(repo_root)
  relevant_inventory = _relevant_file_hash_inventory(repo_root)
  retained_dir_summary = _required_retained_dir_summary(repo_root)
  retained_inventory = _retained_artifact_hash_inventory(repo_root)
  source_payload = _source_payload_summary(repo_root)
  provenance_review = _provenance_review_summary(repo_root)
  dirty_summary = _status_summary(repo_root, relevant_inventory)
  standards_policy = _standards_global_clean_policy(repo_root)
  if force_global_clean_required is not None:
    standards_policy["global_clean_worktree_required"] = force_global_clean_required
    standards_policy["decision_basis"] = (
      "Forced by caller for fail-closed policy evaluation."
    )

  retained_surface_complete = (
    all(row["exists"] and row["file_count"] > 0 for row in retained_dir_summary)
    and all(row["under_repo_path"] for row in retained_dir_summary)
    and all(row["under_candidate_retained_artifacts"] for row in retained_dir_summary)
    and all(row["under_repo_path"] for row in retained_inventory)
    and all(row["under_candidate_retained_artifacts"] for row in retained_inventory)
  )
  source_payload_retained = (
    source_payload["manifest_exists"]
    and source_payload["source_payloads_retained"]
    and source_payload["all_payload_hashes_match"]
    and source_payload["retained_payload_count"]
    == source_payload["required_payload_count"]
  )
  provenance_review_consumed = provenance_review["review_artifact_exists"]
  missing_relevant_paths = [
    row["relative_path"] for row in relevant_inventory if not row["exists"]
  ]
  authority_guards = _non_authoritative_guards()

  scoped_surface = {
    "package_id": PACKAGE_ID,
    "schema_version": SCOPED_GATE_SCHEMA_VERSION,
    "review_target": "res_002_scoped_package_identity_freeze",
    "scope": {
      "target_type": "F-16C_Block50",
      "weapon_class": "AIM-120C-class",
      "weapon_family": "blast_fragmentation",
      "aspect_bucket": "beam",
      "closure_bucket": "high",
      "miss_distance_bucket": "near_miss_0_35m",
    },
    "model_identity": {
      "model_ref": identity["model_ref"],
      "model_version": identity["model_version"],
      "package_id": identity["package_id"],
      "head_commit": _repo_commit(repo_root),
      "identity_manifest_repo_commit": identity["identity_manifest_repo_commit"],
      "identity_manifest_worktree_state": identity[
        "identity_manifest_worktree_state"
      ],
      "identity_manifest_validation_status": identity[
        "identity_manifest_validation_status"
      ],
    },
    "policy_evaluation": {
      "standards_global_clean_policy": standards_policy,
      "global_worktree_dirty": dirty_summary["global_worktree_dirty"],
      "global_worktree_clean": not dirty_summary["global_worktree_dirty"],
      "global_dirty_policy_required_and_unsatisfied": (
        standards_policy["global_clean_worktree_required"]
        and dirty_summary["global_worktree_dirty"]
      ),
    },
    "dirty_worktree_note": dirty_summary,
    "relevant_file_hash_inventory": relevant_inventory,
    "retained_artifact_directory_summary": retained_dir_summary,
    "retained_artifact_hash_inventory": retained_inventory,
    "source_payload_pack_consumption": source_payload,
    "provenance_identity_review_consumption": provenance_review,
    "identity_surface_checks": {
      "all_relevant_files_exist": not missing_relevant_paths,
      "missing_relevant_paths": missing_relevant_paths,
      "required_retained_artifact_dirs_present": all(
        row["exists"] for row in retained_dir_summary
      ),
      "required_retained_artifacts_under_repo_paths": retained_surface_complete,
      "source_payload_pack_retained_and_hash_verified": source_payload_retained,
      "provenance_identity_review_consumed": provenance_review_consumed,
      "authority_guards_all_false": not any(authority_guards.values()),
      "missing_forbidden_outputs": identity["missing_forbidden_outputs"],
      "legacy_identity_manifest_temp_anchor_count": identity[
        "legacy_identity_manifest_temp_anchor_count"
      ],
      "legacy_temp_anchors_consumed_as_blocker_context_only": True,
    },
    "authority_guards": authority_guards,
    "explicit_boundaries": [
      "scoped package identity only; no validation status promotion",
      "current relevant files are bound by sha256 rather than by a clean global worktree",
      "retained artifacts stay candidate/non-authoritative unless reviewed elsewhere",
      "no stock descriptor, Pk authority, or deterministic-fuze authority is created",
      "RES-001, RES-003 through RES-014 remain outside this scoped RES-002 identity decision",
    ],
  }

  scoped_temp_anchor_count = _temporary_anchor_count(scoped_surface)
  scoped_surface["temporary_anchor_scan"] = {
    "scan_surface": "scoped_identity_json_before_scan_field",
    "absolute_temp_anchor_literal_hex": TEMP_ANCHOR.encode("utf-8").hex(),
    "scoped_surface_anchor_count": scoped_temp_anchor_count,
    "legacy_identity_manifest_anchor_count": identity[
      "legacy_identity_manifest_temp_anchor_count"
    ],
    "scoped_surface_contains_temp_anchors": scoped_temp_anchor_count > 0,
    "pass_condition": (
      "the scoped identity artifact must not carry absolute temporary-output anchors"
    ),
  }

  fail_closed_for_global_clean = scoped_surface["policy_evaluation"][
    "global_dirty_policy_required_and_unsatisfied"
  ]
  scoped_identity_pass = (
    retained_surface_complete
    and source_payload_retained
    and provenance_review_consumed
    and not missing_relevant_paths
    and not identity["missing_forbidden_outputs"]
    and not any(authority_guards.values())
    and scoped_temp_anchor_count == 0
    and not fail_closed_for_global_clean
  )
  if fail_closed_for_global_clean:
    status = "failed_closed_global_clean_worktree_required"
    decision = "fail_closed"
    close_reason = (
      "The consumed standards policy was evaluated as requiring a globally "
      "clean worktree, but git status reports dirty paths."
    )
  elif scoped_identity_pass:
    status = "scoped_res002_identity_pass_non_authoritative"
    decision = "narrow_scoped_identity_pass"
    close_reason = (
      "All required A2 retained artifacts are under repository paths, source "
      "payloads are retained and hash-verified, provenance identity review "
      "is consumed, current relevant files are hashed, and the scoped surface "
      "contains no absolute temporary-output anchors."
    )
  else:
    status = "blocked_non_authoritative_res002_scoped_identity_gate"
    decision = "blocked"
    close_reason = "One or more scoped identity prerequisites are missing."

  scoped_surface.update(
    {
      "status": status,
      "readiness_level": "scoped_package_identity_only_non_authoritative",
      "decision": {
        "res002_scoped_package_identity": decision,
        "res002_residual_register_status_change": "not_applied",
        "release_validation_status_promoted": False,
        "authority_release_included": False,
        "global_release_identity_claimed": False,
        "global_clean_worktree_required": standards_policy[
          "global_clean_worktree_required"
        ],
        "fail_closed_reason": close_reason
        if fail_closed_for_global_clean
        else None,
        "scoped_pass_reason": close_reason if scoped_identity_pass else None,
        "remaining_global_release_identity_blockers": [
          "independent reviewer signoff remains outside this scoped gate",
          "validation status remains unvalidated",
          "the global worktree is dirty and is not claimed as release-clean",
          "RES-001 and non-RES-002 residuals remain open",
        ],
      },
    }
  )
  return scoped_surface

def write_retained_scoped_identity_artifact(
  *,
  repo_root: Path = REPO_ROOT,
  retained_output_dir: Path = DEFAULT_RETAINED_OUTPUT_DIR,
) -> dict[str, Any]:
  retained_output_dir.mkdir(parents=True, exist_ok=True)
  artifact = generate_res002_scoped_release_identity_gate(repo_root=repo_root)
  artifact_path = retained_output_dir / GATE_FILENAME
  artifact_sha256 = write_and_hash_json(artifact_path, artifact)
  artifact_content_sha256 = _sha256_text(_canonical_json(artifact))

  manifest = {
    "package_id": PACKAGE_ID,
    "schema_version": SCOPED_MANIFEST_SCHEMA_VERSION,
    "status": "retained_res002_scoped_release_identity_manifest_non_authoritative",
    "artifact_dir": _display_path(retained_output_dir, repo_root),
    "retention_scope": "res002_scoped_package_identity_freeze_only",
    "scoped_gate_status": artifact["status"],
    "scoped_identity_decision": artifact["decision"][
      "res002_scoped_package_identity"
    ],
    "source_payload_pack_consumed": artifact["source_payload_pack_consumption"][
      "manifest_relative_path"
    ],
    "provenance_identity_review_consumed": artifact[
      "provenance_identity_review_consumption"
    ]["review_artifact_relative_path"],
    "retained_input_directory_count": len(REQUIRED_RETAINED_DIRS),
    "retained_input_artifact_count": len(artifact["retained_artifact_hash_inventory"]),
    "relevant_file_hash_count": len(artifact["relevant_file_hash_inventory"]),
    "temporary_anchor_scan": artifact["temporary_anchor_scan"],
    "authority_guards": _non_authoritative_guards(),
    "artifacts": [
      {
        "artifact_key": "res002_scoped_release_identity_gate",
        "filename": GATE_FILENAME,
        "relative_path": _display_path(artifact_path, repo_root),
        "schema_version": SCOPED_GATE_SCHEMA_VERSION,
        "sha256": artifact_sha256,
        "content_sha256": artifact_content_sha256,
        "status": artifact["status"],
        "allowed_claim": (
          "bounded RES-002 scoped package identity surface is retained"
        ),
        "forbidden_claim": (
          "global clean release identity, validation status promotion, "
          "stock authority, effect-scale authority, component-probability "
          "authority, Pk authority, or deterministic-fuze authority"
        ),
      }
    ],
  }
  manifest_path = retained_output_dir / MANIFEST_FILENAME
  manifest_sha256 = write_and_hash_json(manifest_path, manifest)
  manifest["manifest_relative_path"] = _display_path(manifest_path, repo_root)
  manifest["manifest_sha256"] = manifest_sha256
  manifest["retained_artifact_count"] = len(manifest["artifacts"])
  manifest["all_artifacts_exist"] = artifact_path.exists()
  return manifest

def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description=(
      "Create the bounded RES-002 scoped release identity gate and retained "
      "manifest for the A2 blast-fragmentation candidate package."
    )
  )
  parser.add_argument(
    "--output",
    type=Path,
    help="Optional JSON output path. Defaults to stdout.",
  )
  parser.add_argument(
    "--no-write-retained-artifact",
    action="store_true",
    help="Only evaluate the gate; do not write the retained gate/manifest bundle.",
  )
  parser.add_argument(
    "--retained-output-dir",
    type=Path,
    default=DEFAULT_RETAINED_OUTPUT_DIR,
    help="Directory used for retained scoped identity artifacts.",
  )
  args = parser.parse_args(argv)

  if args.no_write_retained_artifact:
    payload = generate_res002_scoped_release_identity_gate()
  else:
    payload = write_retained_scoped_identity_artifact(
      retained_output_dir=args.retained_output_dir
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
