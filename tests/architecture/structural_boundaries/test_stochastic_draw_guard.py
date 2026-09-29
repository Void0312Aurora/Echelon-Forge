"""Decision 5 guard for the stable-entity-identity package (SI-P3).

Scans `src/core`, `src/models`, `src/systems` and `src/components` for private
copies of the splitmix64/seed machinery and for raw-id arithmetic feeding a
stochastic draw. Every draw site must go through
`src/core/interfaces/stochastic_draw.h` (`draw_seed`, `uniform01`, `lane`, the
two named stream steps) instead of reimplementing or index-mixing its own.

`src/tests`, `src/gpu` and `stochastic_draw.h` itself are excluded: the first
two are out of the guard's layer (P1 CUDA finding, native test fixtures), and
the header is the one place the constants are allowed to live.

Calibration (P1 E4): a tmp tree with synthetic violations plus negative
controls -- `.id()` used as a plain event key, `world.entity(x_id)` id
lookups, and `it.entity(i).id()` passed as a function argument -- which must
not flag.
"""

from __future__ import annotations

import re
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]

GUARD_SCAN_ROOTS = ("src/core", "src/models", "src/systems", "src/components")
GUARD_EXCLUDED_DIR_PARTS = ("src/tests", "src/gpu")
GUARD_EXCLUDED_FILES = (
  Path("src/core/interfaces/stochastic_draw.h"),
)
GUARD_SOURCE_SUFFIXES = {".c", ".cc", ".cpp", ".h", ".hpp", ".inc"}

# Decision 5 / helper header comment: the splitmix64 constants and the seed literal.
_SPLITMIX_CONSTANT_PATTERN = re.compile(
  r"0x9e3779b97f4a7c15|0xbf58476d1ce4e5b9|0x94d049bb133111eb|0xd6e8feb86659fd93",
  re.IGNORECASE,
)
_UNIFORM_DIVISOR_PATTERN = re.compile(r"\b9007199254740992\b")

# `static_cast<uint64_t>(<expr> * 1000.0)` or the unqualified `uint64_t(...)` form, with or
# without the std:: qualifier on either the cast keyword or the type (E4: the acoustic site
# uses the qualified `std::uint64_t` form).
_TIME_QUANTIZATION_PATTERN = re.compile(
  r"static_cast\s*<\s*(?:std::)?u?int64_t\s*>\s*\([^()]*\*\s*1000\.0\s*\)"
)

# An operator applied directly to an identifier ending `_id`, or to a `.id()` call result.
# Deliberately narrow: it must fire on `x_id * k`, `x_id ^ k`, `x_id << k`, `x_id % k`, and the
# `.id()` forms of the same, but never on `.id()` or `_id` used merely as a lookup key or
# function argument (E4 negative controls).
_ID_ARITHMETIC_PATTERN = re.compile(
  r"(?:\b\w*_id\b|\.id\(\))\s*(?:\^|\*|<<|%)(?!=)"
)

# The genuine non-draw violation the guard must also catch (P1 E4): the ship-motion phase
# derived from a raw id via `%`. `id() % 1024ULL` already matches _ID_ARITHMETIC_PATTERN above,
# so no separate pattern is needed; this constant documents the known site for the calibration
# test below.
_KNOWN_SHIP_MOTION_VIOLATION_FRAGMENT = "id() % 1024ULL"


def _iter_guard_scanned_files(root: Path) -> list[Path]:
  files: list[Path] = []
  for scan_root_rel in GUARD_SCAN_ROOTS:
    scan_root = root / scan_root_rel
    if not scan_root.exists():
      continue
    for path in scan_root.rglob("*"):
      if not path.is_file() or path.suffix not in GUARD_SOURCE_SUFFIXES:
        continue
      rel = path.relative_to(root)
      rel_posix = rel.as_posix()
      if any(rel_posix.startswith(f"{excluded}/") or rel_posix == excluded
             for excluded in GUARD_EXCLUDED_DIR_PARTS):
        continue
      if rel in GUARD_EXCLUDED_FILES:
        continue
      files.append(path)
  return files


def _strip_comments_and_strings(text: str) -> str:
  """Best-effort removal of comments and string/char literals.

  The guard is a source-shape check, not a compiler; stripping comments and
  literals avoids false positives from prose mentioning the constants (as
  this file, and the helper header's own docstring comments, do) while
  keeping line numbers stable for reporting.
  """
  out = []
  i = 0
  n = len(text)
  while i < n:
    two = text[i:i + 2]
    if two == "//":
      j = text.find("\n", i)
      j = n if j == -1 else j
      out.append(" " * (j - i))
      i = j
    elif two == "/*":
      j = text.find("*/", i + 2)
      j = n if j == -1 else j + 2
      chunk = text[i:j]
      out.append("".join("\n" if c == "\n" else " " for c in chunk))
      i = j
    elif text[i] == '"':
      j = i + 1
      while j < n and text[j] != '"':
        if text[j] == "\\":
          j += 1
        j += 1
      j = min(j + 1, n)
      out.append(" " * (j - i))
      i = j
    elif text[i] == "'":
      j = i + 1
      while j < n and text[j] != "'":
        if text[j] == "\\":
          j += 1
        j += 1
      j = min(j + 1, n)
      out.append(" " * (j - i))
      i = j
    else:
      out.append(text[i])
      i += 1
  return "".join(out)


def _guard_violations_in_text(text: str) -> list[str]:
  scrubbed = _strip_comments_and_strings(text)
  violations: list[str] = []
  if _SPLITMIX_CONSTANT_PATTERN.search(scrubbed):
    violations.append("splitmix64/seed constant literal")
  if _UNIFORM_DIVISOR_PATTERN.search(scrubbed):
    violations.append("2^53 uniform-divisor literal")
  if _TIME_QUANTIZATION_PATTERN.search(scrubbed):
    violations.append("time quantization outside quantize_time_ms")
  if _ID_ARITHMETIC_PATTERN.search(scrubbed):
    violations.append("operator applied to a raw entity id")
  return violations


def _guard_offending_files(root: Path) -> dict[str, list[str]]:
  offenders: dict[str, list[str]] = {}
  for path in _iter_guard_scanned_files(root):
    violations = _guard_violations_in_text(path.read_text(encoding="utf-8"))
    if violations:
      offenders[path.relative_to(root).as_posix()] = violations
  return offenders


# SI-P3 landed the guard before the sites were converted (Phase Plan order): it is committed
# first as a strict xfail naming the exact files it flags today, then the xfail is removed once
# sites 1-7, the ship-motion phase and the five private copies are all converted (P3 exit).
_PRE_CONVERSION_KNOWN_OFFENDERS = frozenset(
  {
    "src/core/engine/simulation_kernel_command_api.cpp",
    "src/core/engine/simulation_kernel_damage_debug_api.cpp",
    "src/core/engine/simulation_kernel_weapon_release_service.cpp",
    "src/models/systems/default_acoustic_model.cpp",
    "src/models/systems/default_sensor_model.cpp",
    "src/models/weapons/detail/default_effects_geometry_detail.h",
    "src/systems/combat/damage_system_common.h",
    "src/systems/domains/naval/ship_motion_system.h",
  }
)


@pytest.mark.xfail(
  strict=True,
  reason=(
    "SI-P3 (docs/architecture/work/active/stable_entity_identity): the guard lands before "
    "the draw sites are converted. It flags exactly the 8 known pre-conversion files "
    f"{sorted(_PRE_CONVERSION_KNOWN_OFFENDERS)}. Remove this xfail once sites 1-7, the "
    "ship-motion phase and the five private splitmix/uniform copies are all converted."
  ),
)
def test_stochastic_draw_guard_flags_no_known_site() -> None:
  offenders = _guard_offending_files(REPO_ROOT)
  assert offenders.keys() == _PRE_CONVERSION_KNOWN_OFFENDERS, (
    "the pre-conversion offender set drifted from the recorded set; update "
    "_PRE_CONVERSION_KNOWN_OFFENDERS only if a real new site appeared, and re-check the xfail "
    f"reason. Offenders now: {sorted(offenders)}"
  )
  assert offenders == {}, (
    "the stochastic-draw guard (Decision 5) still flags maintained source outside "
    f"stochastic_draw.h: {offenders}. Every draw site must go through "
    "core/interfaces/stochastic_draw.h (draw_seed/uniform01/lane/the named stream steps)."
  )


def test_stochastic_draw_guard_calibration_on_synthetic_tree(tmp_path: Path) -> None:
  # Positive controls: one file per violation family, plus the genuine non-draw violation
  # (ship-motion phase from a raw id) the guard must also catch (P1 E4).
  (tmp_path / "src" / "core").mkdir(parents=True)
  (tmp_path / "src" / "core" / "splitmix_copy.h").write_text(
    textwrap.dedent(
      """
      #pragma once
      inline unsigned long long splitmix64(unsigned long long seed) {
          unsigned long long z = seed + 0x9e3779b97f4a7c15ULL;
          z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
          z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
          return z ^ (z >> 31);
      }
      """
    ),
    encoding="utf-8",
  )
  (tmp_path / "src" / "core" / "uniform_copy.h").write_text(
    textwrap.dedent(
      """
      #pragma once
      inline double rand_uniform01(unsigned long long z) {
          return (z >> 11) * (1.0 / 9007199254740992.0);
      }
      """
    ),
    encoding="utf-8",
  )
  (tmp_path / "src" / "core" / "time_quantize_copy.h").write_text(
    textwrap.dedent(
      """
      #pragma once
      inline unsigned long long quantize(double sim_time_s) {
          return static_cast<uint64_t>(sim_time_s * 1000.0);
      }
      """
    ),
    encoding="utf-8",
  )
  (tmp_path / "src" / "core" / "id_arithmetic_copy.h").write_text(
    textwrap.dedent(
      """
      #pragma once
      inline unsigned long long mix(unsigned long long target_id) {
          return target_id ^ 0x1234ULL;
      }
      """
    ),
    encoding="utf-8",
  )
  (tmp_path / "src" / "systems").mkdir(parents=True)
  (tmp_path / "src" / "systems" / "ship_motion_copy.h").write_text(
    textwrap.dedent(
      """
      #pragma once
      inline double phase(unsigned long long entity_id) {
          return static_cast<double>(entity_id % 1024ULL) * 0.137;
      }
      """
    ),
    encoding="utf-8",
  )

  # Negative controls: patterns that must NOT flag (P1 E4).
  (tmp_path / "src" / "core" / "negative_controls.h").write_text(
    textwrap.dedent(
      """
      #pragma once
      // `.id()` used as a plain event key, not mixed with an operator.
      inline unsigned long long event_key(flecs::entity entity) {
          return static_cast<unsigned long long>(entity.id());
      }

      // An entity lookup by an `_id`-suffixed identifier: never an operator target.
      inline flecs::entity resolve(flecs::world &world, unsigned long long target_id) {
          return world.entity(target_id);
      }

      // `it.entity(i).id()` passed as a plain function argument.
      inline void record(unsigned long long id) {}
      inline void call_record(flecs::iter &it, int i) {
          record(static_cast<unsigned long long>(it.entity(i).id()));
      }
      """
    ),
    encoding="utf-8",
  )

  # Excluded-by-layer control: a real violation inside src/tests must not be flagged.
  (tmp_path / "src" / "tests").mkdir(parents=True)
  (tmp_path / "src" / "tests" / "fixture_copy.h").write_text(
    "inline unsigned long long g = 0x9e3779b97f4a7c15ULL;\n",
    encoding="utf-8",
  )

  offenders = _guard_offending_files(tmp_path)

  assert offenders.keys() == {
    "src/core/splitmix_copy.h",
    "src/core/uniform_copy.h",
    "src/core/time_quantize_copy.h",
    "src/core/id_arithmetic_copy.h",
    "src/systems/ship_motion_copy.h",
  }, offenders

  assert "splitmix64/seed constant literal" in offenders["src/core/splitmix_copy.h"]
  assert "2^53 uniform-divisor literal" in offenders["src/core/uniform_copy.h"]
  assert "time quantization outside quantize_time_ms" in offenders["src/core/time_quantize_copy.h"]
  assert "operator applied to a raw entity id" in offenders["src/core/id_arithmetic_copy.h"]
  assert "operator applied to a raw entity id" in offenders["src/systems/ship_motion_copy.h"]
