"""Shared implementation behind the A2 candidate retained-artifact packs.

``effect_scale_retained_pack`` (Stage B) and
``component_probability_retained_pack`` (Stage C) are one tool over two
artifact sets: each writes a fixed group of candidate payloads into a retained
directory, pins every file with a sha256 pair, and emits a manifest carrying
the pack's origin and authority boundary. Everything that actually differs --
which payloads, the schema version, the status and retention-scope labels, the
origin summary, the CLI description -- stays a caller-supplied argument, so
both packs keep their own public surface
(``load_retained_artifact_pack_manifest`` / ``generate_retained_artifact_pack``
/ ``main``) and byte-identical CLI behaviour.

Not an entrypoint: the leading underscore marks package-internal shared code,
the same way ``tools/maintenance/_dispatch.py`` does for the routers.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from tools.maintenance.retained_artifacts.manifest_integrity import _sha256_file, _sha256_text

#: Both packs assert the same five guards, and neither may ever flip one true.
NON_AUTHORITATIVE_GUARDS: dict[str, bool] = {
  "stock_runtime_authority_granted": False,
  "effect_scale_authority_granted": False,
  "component_failure_probability_authority_granted": False,
  "pk_authority_granted": False,
  "deterministic_fuze_authority_granted": False,
}


def artifact_status(payload: dict[str, Any]) -> str:
  return str(payload.get("status", payload.get("validation_status", "")))


def canonical_json(payload: dict[str, Any]) -> str:
  return json.dumps(payload, indent=2, sort_keys=True)


def display_path(path: Path, repo_root: Path) -> str:
  # Non-resolving relative_to; differs from manifest_integrity._display_path (resolve).
  try:
    return path.relative_to(repo_root).as_posix()
  except ValueError:
    return str(path)


def load_pack_manifest(
  *,
  repo_root: Path,
  output_dir: Path,
  package_id: str,
  schema_version: str,
  missing_status: str,
) -> dict[str, Any]:
  """Load a retained pack manifest, or describe its absence with *missing_status*."""
  manifest_path = output_dir / "manifest.json"
  manifest_ref = display_path(manifest_path, repo_root)
  if not manifest_path.exists():
    return {
      "package_id": package_id,
      "schema_version": schema_version,
      "status": missing_status,
      "artifact_dir": display_path(output_dir, repo_root),
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


def write_pack(
  *,
  repo_root: Path,
  output_dir: Path,
  build_artifacts: Callable[[Path], dict[str, dict[str, Any]]],
  artifact_filenames: dict[str, str],
  release_boundaries: dict[str, dict[str, str]],
  package_id: str,
  schema_version: str,
  status: str,
  retention_scope: str,
  retained_origin_summary: dict[str, Any],
) -> dict[str, Any]:
  """Write one retained pack and return its manifest.

  *build_artifacts* is a callable rather than a prepared mapping so the output
  directory is created before any payload is generated, matching the order
  each pack used before it shared this writer.
  """
  output_dir.mkdir(parents=True, exist_ok=True)
  artifacts = build_artifacts(repo_root)

  rows: list[dict[str, Any]] = []
  for artifact_key, payload in artifacts.items():
    filename = artifact_filenames[artifact_key]
    path = output_dir / filename
    text = canonical_json(payload) + "\n"
    path.write_text(text, encoding="utf-8")
    boundary = release_boundaries[artifact_key]
    rows.append(
      {
        "artifact_key": artifact_key,
        "filename": filename,
        "relative_path": display_path(path, repo_root),
        "sha256": _sha256_file(path),
        "status": artifact_status(payload),
        "schema_version": str(payload["schema_version"]),
        "content_sha256": _sha256_text(text.rstrip("\n")),
        "origin_class": boundary["origin_class"],
        "allowed_claim": boundary["allowed_claim"],
        "forbidden_claim": boundary["forbidden_claim"],
      }
    )

  manifest = {
    "package_id": package_id,
    "schema_version": schema_version,
    "status": status,
    "artifact_dir": display_path(output_dir, repo_root),
    "retention_scope": retention_scope,
    "retained_origin_summary": retained_origin_summary,
    "artifacts": rows,
    "non_authoritative_guards": dict(NON_AUTHORITATIVE_GUARDS),
  }
  manifest_path = output_dir / "manifest.json"
  manifest_path.write_text(canonical_json(manifest) + "\n", encoding="utf-8")
  manifest["manifest_relative_path"] = display_path(manifest_path, repo_root)
  manifest["manifest_sha256"] = _sha256_file(manifest_path)
  manifest["retained_artifact_count"] = len(rows)
  return manifest


def run_pack_cli(
  argv: list[str] | None,
  *,
  description: str,
  default_output_dir: Path,
  generate: Callable[..., dict[str, Any]],
) -> int:
  """Run the shared ``--output-dir`` CLI both retained packs expose."""
  parser = argparse.ArgumentParser(description=description)
  parser.add_argument(
    "--output-dir",
    type=Path,
    default=default_output_dir,
    help="Directory where retained JSON artifacts will be written.",
  )
  args = parser.parse_args(argv)

  artifact = generate(output_dir=args.output_dir)
  print(canonical_json(artifact))
  return 0
