#!/usr/bin/env python3
"""Write retained Stage B effect-scale candidate artifacts for A2.

This tool materializes the current author-side Stage B candidate artifacts into
stable files under the candidate package directory. It remains non-authoritative:
the retained pack only preserves current candidate evidence surfaces and does not
grant runtime authority or independent validation status.
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
from tools.maintenance.candidate_artifacts import scope_boundary_probe as scope_probe
from tools.maintenance.candidate_artifacts import effect_scale_snapshot as stage_b_snapshot
from tools.maintenance.candidate_artifacts import effect_scale_result_pack as result_pack
from tools.maintenance.candidate_artifacts import validation_scaffold as scaffold

PACKAGE_ID = (
  "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
  "beam_high_near_miss_0_35m_v0"
)
RETAINED_PACK_SCHEMA_VERSION = "a2.stage_b_retained_artifact_pack.v1"
DEFAULT_OUTPUT_DIR = (
  REPO_ROOT
  / "docs"
  / "task"
  / "air_combat"
  / "archive"
  / "a2_high_fidelity_damage_model"
  / "calibration"
  / "vps_candidate_f16c_aim120c_blastfrag_beam_high_nearmiss_0_35m"
  / "retained_artifacts"
  / "stage_b_effect_scale_20260530"
)

ARTIFACT_FILENAMES = {
  "validation_scaffold_snapshot": "validation_scaffold_snapshot.json",
  "scope_boundary_probe_snapshot": "scope_boundary_probe_snapshot.json",
  "stage_b_effect_scale_snapshot": "stage_b_effect_scale_snapshot.json",
  "stage_b_validation_result_pack": "stage_b_validation_result_pack.json",
}

ARTIFACT_RELEASE_BOUNDARIES = {
  "validation_scaffold_snapshot": {
    "origin_class": "author_side_validation_scaffold_snapshot_only",
    "allowed_claim": "candidate validation scaffold inputs and non-authoritative guards are retained",
    "forbidden_claim": (
      "independent validation, stock runtime authority, component-probability "
      "release, Pk authority, or deterministic-fuze authority"
    ),
  },
  "scope_boundary_probe_snapshot": {
    "origin_class": "author_side_scope_boundary_probe_only",
    "allowed_claim": "candidate near-miss and closure scope probe surface is retained",
    "forbidden_claim": (
      "reviewed closure physics, stock runtime authority, component-probability "
      "release, Pk authority, or deterministic-fuze authority"
    ),
  },
  "stage_b_effect_scale_snapshot": {
    "origin_class": "author_side_stage_b_hard_gate_snapshot_only",
    "allowed_claim": "author-side Stage B hard-gate snapshot is retained",
    "forbidden_claim": (
      "release readiness, stock runtime authority, component-probability "
      "release, Pk authority, or deterministic-fuze authority"
    ),
  },
  "stage_b_validation_result_pack": {
    "origin_class": "author_side_stage_b_result_pack_only",
    "allowed_claim": "author-side Stage B result pack and stable hashes are retained",
    "forbidden_claim": (
      "independent validation result, stock runtime authority, "
      "component-probability release, Pk authority, or deterministic-fuze authority"
    ),
  },
}

def _artifact_status(payload: dict[str, Any]) -> str:
  return str(payload.get("status", payload.get("validation_status", "")))

def _canonical_json(payload: dict[str, Any]) -> str:
  return json.dumps(payload, indent=2, sort_keys=True)

def _display_path(path: Path, repo_root: Path) -> str:
  # Kept local: non-resolving relative_to; differs from manifest_integrity._display_path (resolve).
  try:
    return path.relative_to(repo_root).as_posix()
  except ValueError:
    return str(path)

def load_retained_artifact_pack_manifest(
  *,
  repo_root: Path = REPO_ROOT,
  output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
  manifest_path = output_dir / "manifest.json"
  manifest_ref = _display_path(manifest_path, repo_root)
  if not manifest_path.exists():
    return {
      "package_id": PACKAGE_ID,
      "schema_version": RETAINED_PACK_SCHEMA_VERSION,
      "status": "missing_retained_artifact_pack",
      "artifact_dir": _display_path(output_dir, repo_root),
      "manifest_exists": False,
      "manifest_relative_path": manifest_ref,
      "retained_artifact_count": 0,
      "all_artifacts_exist": False,
      "artifacts": [],
    }

  manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
  manifest["manifest_exists"] = True
  manifest["manifest_relative_path"] = manifest_ref
  manifest["manifest_sha256"] = _sha256_file(manifest_path)
  manifest["retained_artifact_count"] = len(manifest.get("artifacts", []))
  manifest["all_artifacts_exist"] = all(
    Path(row["relative_path"]).exists()
    if Path(row["relative_path"]).is_absolute()
    else (repo_root / row["relative_path"]).exists()
    for row in manifest.get("artifacts", [])
  )
  return manifest

def generate_retained_artifact_pack(
  *,
  repo_root: Path = REPO_ROOT,
  output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
  output_dir.mkdir(parents=True, exist_ok=True)
  artifacts = {
    "validation_scaffold_snapshot": scaffold.generate_validation_scaffold(
      repo_root=repo_root
    ),
    "scope_boundary_probe_snapshot": scope_probe.generate_scope_boundary_probe(
      repo_root=repo_root
    ),
    "stage_b_effect_scale_snapshot": stage_b_snapshot.generate_stage_b_effect_scale_snapshot(
      repo_root=repo_root
    ),
    "stage_b_validation_result_pack": result_pack.generate_stage_b_validation_result_pack(
      repo_root=repo_root
    ),
  }

  rows: list[dict[str, Any]] = []
  for artifact_key, payload in artifacts.items():
    filename = ARTIFACT_FILENAMES[artifact_key]
    path = output_dir / filename
    text = _canonical_json(payload) + "\n"
    path.write_text(text, encoding="utf-8")
    rows.append(
      {
        "artifact_key": artifact_key,
        "filename": filename,
        "relative_path": _display_path(path, repo_root),
        "sha256": _sha256_file(path),
        "status": _artifact_status(payload),
        "schema_version": str(payload["schema_version"]),
        "content_sha256": _sha256_text(text.rstrip("\n")),
        "origin_class": ARTIFACT_RELEASE_BOUNDARIES[artifact_key][
          "origin_class"
        ],
        "allowed_claim": ARTIFACT_RELEASE_BOUNDARIES[artifact_key][
          "allowed_claim"
        ],
        "forbidden_claim": ARTIFACT_RELEASE_BOUNDARIES[artifact_key][
          "forbidden_claim"
        ],
      }
    )

  manifest = {
    "package_id": PACKAGE_ID,
    "schema_version": RETAINED_PACK_SCHEMA_VERSION,
    "status": "author_retained_candidate_artifacts_only",
    "artifact_dir": _display_path(output_dir, repo_root),
    "retention_scope": "stage_b_effect_scale_author_side_candidate_only",
    "retained_origin_summary": {
      "runtime_origin": "no_stock_runtime_descriptor_author_side_artifacts_only",
      "review_surface": "author_side_stage_b_effect_scale_candidate_only",
      "independent_release_artifact_present": False,
      "stock_runtime_authority_present": False,
      "stage_c_component_probability_artifacts_present": False,
    },
    "artifacts": rows,
    "non_authoritative_guards": {
      "stock_runtime_authority_granted": False,
      "effect_scale_authority_granted": False,
      "component_failure_probability_authority_granted": False,
      "pk_authority_granted": False,
      "deterministic_fuze_authority_granted": False,
    },
  }
  manifest_path = output_dir / "manifest.json"
  manifest_path.write_text(_canonical_json(manifest) + "\n", encoding="utf-8")
  manifest["manifest_relative_path"] = _display_path(manifest_path, repo_root)
  manifest["manifest_sha256"] = _sha256_file(manifest_path)
  manifest["retained_artifact_count"] = len(rows)
  return manifest

def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description=(
      "Write retained Stage B effect-scale candidate artifacts for the "
      "current A2 blast-fragmentation package."
    )
  )
  parser.add_argument(
    "--output-dir",
    type=Path,
    default=DEFAULT_OUTPUT_DIR,
    help="Directory where retained JSON artifacts will be written.",
  )
  args = parser.parse_args(argv)

  artifact = generate_retained_artifact_pack(output_dir=args.output_dir)
  print(_canonical_json(artifact))
  return 0

if __name__ == "__main__":
  raise SystemExit(main())
