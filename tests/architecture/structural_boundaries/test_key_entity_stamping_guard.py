"""Decision 1 guard for the stable-entity-identity package (P5 review S2).

Every entity that can take part in a stochastic draw carries `KeyEntity`, and
Decision 1 makes `stamp_stable_serial` the single creation primitive that
gives such an entity its `StableEntitySerial`. This guard keeps that true
structurally: in maintained source, a `KeyEntity` may only be *written*
(`set`/`emplace`/`ensure`, or a `KeyEntity{...}` value handed to one) inside
an admitted creation path, and every admitted path must also call
`stamp_stable_serial`.

Adding a sixth creation path is therefore a deliberate edit to
`ADMITTED_KEY_ENTITY_CREATION_FILES`, reviewed together with its stamp call.
Without that edit, the new path fails here loudly instead of producing an
unstamped entity that aborts later at `draw_seed`.

Scope follows the stochastic-draw guard: `src/` except `src/tests` (native
fixtures build raw worlds on purpose) and `src/gpu`. Comments and string
literals are ignored.
"""

from __future__ import annotations

import re
import textwrap
from pathlib import Path

from tests.architecture.structural_boundaries.test_stochastic_draw_guard import (
  _strip_comments_and_strings,
)

REPO_ROOT = Path(__file__).resolve().parents[3]

SCAN_ROOT = "src"
EXCLUDED_DIR_PARTS = ("src/tests", "src/gpu")
SOURCE_SUFFIXES = {".c", ".cc", ".cpp", ".h", ".hpp", ".inc"}

# The creation paths that write KeyEntity today (P0 inventory, Decision 1):
# - factory root, station munitions and embarked helo (through the recursive spawn);
# - weapon-release missile;
# - EW chaff and flare.
ADMITTED_KEY_ENTITY_CREATION_FILES = frozenset(
  {
    "src/core/engine/simulation_kernel_weapon_release_service.cpp",
    "src/models/core/default_unit_factory.h",
    "src/systems/systems/ew_system.h",
  }
)

_KEY_ENTITY_WRITE_PATTERN = re.compile(
  r"\b(?:set|emplace|ensure|insert)\s*<\s*KeyEntity\s*>\s*\("
)
_STAMP_CALL_PATTERN = re.compile(r"\bstamp_stable_serial\s*\(")


def _iter_scanned_files(root: Path) -> list[Path]:
  base = root / SCAN_ROOT
  if not base.exists():
    return []
  files: list[Path] = []
  for path in base.rglob("*"):
    if not path.is_file() or path.suffix not in SOURCE_SUFFIXES:
      continue
    rel_posix = path.relative_to(root).as_posix()
    if any(rel_posix.startswith(f"{excluded}/") for excluded in EXCLUDED_DIR_PARTS):
      continue
    files.append(path)
  return files


def _key_entity_writers(root: Path) -> dict[str, bool]:
  """Map each file that writes KeyEntity to whether it also calls stamp_stable_serial."""
  writers: dict[str, bool] = {}
  for path in _iter_scanned_files(root):
    text = _strip_comments_and_strings(path.read_text(encoding="utf-8"))
    if _KEY_ENTITY_WRITE_PATTERN.search(text):
      writers[path.relative_to(root).as_posix()] = bool(_STAMP_CALL_PATTERN.search(text))
  return writers


def test_key_entity_is_written_only_by_admitted_stamped_creation_paths() -> None:
  writers = _key_entity_writers(REPO_ROOT)
  assert set(writers) == ADMITTED_KEY_ENTITY_CREATION_FILES, (
    "KeyEntity is written outside the admitted creation paths (Decision 1). A new creation "
    "path must call stamp_stable_serial and be added to ADMITTED_KEY_ENTITY_CREATION_FILES "
    f"deliberately. writers={sorted(writers)}"
  )
  unstamped = sorted(path for path, stamps in writers.items() if not stamps)
  assert unstamped == [], f"KeyEntity creation paths without stamp_stable_serial: {unstamped}"


def test_key_entity_guard_calibration_on_synthetic_tree(tmp_path: Path) -> None:
  src = tmp_path / "src"
  (src / "systems").mkdir(parents=True)
  (src / "tests").mkdir(parents=True)
  (src / "systems" / "stamped_path.h").write_text(
    textwrap.dedent(
      """
      #pragma once
      inline void spawn(flecs::world &w) {
          auto e = w.entity().set<KeyEntity>({UnitType::Unknown});
          stamp_stable_serial(e);
      }
      """
    ),
    encoding="utf-8",
  )
  (src / "systems" / "sixth_path.h").write_text(
    textwrap.dedent(
      """
      #pragma once
      inline void spawn_decoy(flecs::world &w) {
          w.entity().set < KeyEntity > ({UnitType::Unknown});
      }
      """
    ),
    encoding="utf-8",
  )
  (src / "systems" / "reader_only.h").write_text(
    textwrap.dedent(
      """
      #pragma once
      // set<KeyEntity>(...) in a comment is not a write.
      inline bool is_ground(flecs::entity e) {
          const KeyEntity *key = e.get<KeyEntity>();
          return key && key->type == UnitType::Ground;
      }
      """
    ),
    encoding="utf-8",
  )
  (src / "tests" / "fixture.cpp").write_text(
    "void f(flecs::world &w) { w.entity().set<KeyEntity>({UnitType::Unknown}); }\n",
    encoding="utf-8",
  )

  writers = _key_entity_writers(tmp_path)

  assert writers == {
    "src/systems/stamped_path.h": True,
    "src/systems/sixth_path.h": False,
  }, writers
