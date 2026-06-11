#!/usr/bin/env python3
"""Write retained Stage C component-probability candidate artifacts for A2.

This tool materializes the current Stage C machine-readable candidate surfaces
into stable JSON files under the candidate package directory. The retained pack
is intentionally bounded to candidate, non-authoritative, author-side review
artifacts with a test-local runtime origin. It does not grant stock runtime
authority, validated fragility truth, Pk authority, or deterministic-fuze
authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance.candidate_artifacts import runtime_authority_exercise as authority_pack
from tools.maintenance import (
    a2_blastfrag_stage_c_component_probability_result_pack as result_pack,
)
from tools.maintenance import (
    a2_blastfrag_stage_c_component_probability_snapshot as snapshot,
)
from tools.maintenance import (
    a2_blastfrag_stage_c_component_probability_surface_probe as surface_probe,
)


PACKAGE_ID = (
    "a2_candidate_vps_f16c_block50_aim120c_blast_fragmentation_"
    "beam_high_near_miss_0_35m_v0"
)
RETAINED_PACK_SCHEMA_VERSION = "a2.stage_c_component_probability_retained_artifact_pack.v1"
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
    / "stage_c_component_probability_20260530"
)

ARTIFACT_FILENAMES = {
    "runtime_aligned_authority_pack": "runtime_aligned_authority_pack.json",
    "stage_c_component_probability_snapshot": "stage_c_component_probability_snapshot.json",
    "stage_c_component_probability_surface_probe": (
        "stage_c_component_probability_surface_probe.json"
    ),
    "stage_c_component_probability_result_pack": (
        "stage_c_component_probability_result_pack.json"
    ),
}

ARTIFACT_RELEASE_BOUNDARIES = {
    "runtime_aligned_authority_pack": {
        "origin_class": "test_local_runtime_exercise_only",
        "allowed_claim": "test-local runtime-aligned component probability exercise exists",
        "forbidden_claim": (
            "validated fragility truth, stock runtime authority, Pk authority, "
            "or deterministic-fuze authority"
        ),
    },
    "stage_c_component_probability_snapshot": {
        "origin_class": "author_side_candidate_snapshot_only",
        "allowed_claim": "author-side candidate Stage C snapshot and provenance surface exist",
        "forbidden_claim": (
            "validated component fragility truth, stock runtime authority, Pk "
            "authority, or deterministic-fuze authority"
        ),
    },
    "stage_c_component_probability_surface_probe": {
        "origin_class": "author_side_candidate_surface_probe_only",
        "allowed_claim": (
            "author-side candidate Stage C fragility-surface and repeatability snapshot exist"
        ),
        "forbidden_claim": (
            "validated fragility curve, stock runtime authority, Pk authority, or "
            "deterministic-fuze authority"
        ),
    },
    "stage_c_component_probability_result_pack": {
        "origin_class": "author_side_candidate_result_pack_only",
        "allowed_claim": "author-side candidate Stage C result pack and stable hashes exist",
        "forbidden_claim": (
            "validated release result, stock runtime authority, Pk authority, or "
            "deterministic-fuze authority"
        ),
    },
}


def _artifact_status(payload: dict[str, Any]) -> str:
    return str(payload.get("status", payload.get("validation_status", "")))


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
            "status": "missing_stage_c_component_probability_retained_artifact_pack",
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
        "runtime_aligned_authority_pack": authority_pack.generate_runtime_aligned_authority_pack(
            repo_root=repo_root
        ),
        "stage_c_component_probability_snapshot": snapshot.generate_stage_c_component_probability_snapshot(
            repo_root=repo_root
        ),
        "stage_c_component_probability_surface_probe": (
            surface_probe.generate_stage_c_component_probability_surface_probe(
                repo_root=repo_root
            )
        ),
        "stage_c_component_probability_result_pack": (
            result_pack.generate_stage_c_component_probability_result_pack(
                repo_root=repo_root
            )
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
                "origin_class": ARTIFACT_RELEASE_BOUNDARIES[artifact_key]["origin_class"],
                "allowed_claim": ARTIFACT_RELEASE_BOUNDARIES[artifact_key]["allowed_claim"],
                "forbidden_claim": ARTIFACT_RELEASE_BOUNDARIES[artifact_key][
                    "forbidden_claim"
                ],
            }
        )

    manifest = {
        "package_id": PACKAGE_ID,
        "schema_version": RETAINED_PACK_SCHEMA_VERSION,
        "status": "author_retained_stage_c_component_probability_candidate_artifacts_only",
        "artifact_dir": _display_path(output_dir, repo_root),
        "retention_scope": "stage_c_component_probability_author_side_candidate_only",
        "retained_origin_summary": {
            "runtime_origin": "test_local_runtime_authority_exercise_only",
            "review_surface": "author_side_candidate_snapshot_and_result_pack_only",
            "independent_release_artifact_present": False,
            "stock_runtime_authority_present": False,
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


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Write retained Stage C component-probability candidate artifacts for "
            "the current A2 blast-fragmentation package."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where retained JSON artifacts will be written.",
    )
    args = parser.parse_args()

    artifact = generate_retained_artifact_pack(output_dir=args.output_dir)
    print(_canonical_json(artifact))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
