"""Working-tree contract for the viz visual assets.

The asset tree is the largest binary surface in the repository, so it carries
two standing rules: every registry entry must resolve to a file that is
actually shipped, and downloaded source packages must not re-land next to the
runtime assets they were extracted from.
"""

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
STATIC_ROOT = REPO_ROOT / "examples" / "viz" / "web_viz" / "static"
ASSETS_DIR = STATIC_ROOT / "assets"
REGISTRY_PATH = REPO_ROOT / "examples" / "viz" / "assets" / "registry" / "default.json"
SOURCE_ARCHIVE_SUFFIXES = {".zip", ".7z", ".rar", ".tar", ".tgz"}


def test_registry_visual_assets_exist_on_disk() -> None:
  registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
  entries = registry["entries"]
  assert entries

  missing = []
  for entry in entries:
    asset_path = str(entry["visual"]["asset_path"])
    assert asset_path.startswith("/static/"), asset_path
    if not (STATIC_ROOT / asset_path[len("/static/") :]).is_file():
      missing.append(f"{entry['id']} -> {asset_path}")

  assert missing == []


def test_asset_tree_carries_no_raw_source_archives() -> None:
  # The downloaded Sketchfab packages were retired to Git history; recovery
  # commands and digests live in the ledger next to the assets.
  assert (ASSETS_DIR / "audit_ledger.md").is_file()

  archives = sorted(
    path.relative_to(ASSETS_DIR).as_posix()
    for path in ASSETS_DIR.rglob("*")
    if path.is_file() and path.suffix.lower() in SOURCE_ARCHIVE_SUFFIXES
  )

  assert archives == []


def test_f16_audit_scene_stays_available_for_geometry_review() -> None:
  # Nothing renders this glTF, but tools/geometry/airframe_review parses it as
  # DEFAULT_AUDIT_SCENE, so it is exempt from the audit-package retirement.
  audit_gltf = ASSETS_DIR / "air" / "audit" / "f16_c_falcon_carlos_maciel" / "gltf"

  assert (audit_gltf / "scene.gltf").is_file()
  assert (audit_gltf / "scene.bin").is_file()
