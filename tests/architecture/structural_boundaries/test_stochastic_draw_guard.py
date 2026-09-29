"""Decision 5 guard for the stable-entity-identity package (SI-P3, extended at P5 review S1).

Scans `src/core`, `src/models`, `src/systems` and `src/components` for private
copies of the splitmix64/seed machinery and for raw-id arithmetic feeding a
stochastic draw. Every draw site must go through
`src/core/interfaces/stochastic_draw.h` (`draw_seed`, `uniform01`, `lane`, the
two named stream steps) instead of reimplementing or index-mixing its own.

`src/tests`, `src/gpu` and `stochastic_draw.h` itself are excluded: the first
two are out of the guard's layer (P1 CUDA finding, native test fixtures), and
the header is the one place the constants are allowed to live.

The id-arithmetic rule (S1) is deliberately scoped to identifiers that name an
entity id, not every `\\w*_id` identifier: `attacker_id`, `target_id`,
`entity_id`, `owner_id`, any identifier ending `_entity_id` (the repo's own
naming for a raw Flecs id passed across a boundary -- see
`active_helo_entity_id`, `embarked_helo_entity_id`, `munition_entity_id`,
`partner_entity_id`, `reference_entity_id`), and `.id()`. This is narrower than
"ends with `_id`": it must not flag `grid_id * cell_area`, where `grid_id` is a
spatial grid cell coordinate, not an entity id (S1 false-positive report). It
must fire whether the operator sits to the id's right (`target.id() ^ k`,
`attacker_id + k`) or to its left (`k ^ target.id()`, `k * attacker_id`), on
`^`, `*`, `<<`, `%` or `+` (an id is never legitimately added, XORed, shifted
or multiplied), and on a `static_cast<uint64_t>` wrapping either side (for
example `static_cast<uint64_t>(e.id()) * k`).

The time-quantization rule matches `uint64_t(t * 1000.0)` and
`static_cast<uint64_t>(...)` (both with or without the `std::` qualifier on
the cast keyword or the type), including when the multiplied expression is
itself parenthesised (`static_cast<uint64_t>((t + dt) * 1000.0)`), and matches
`* 1e3`, `* 1000` and `* 1000.0` as the multiplier, not only `* 1000.0`.

Calibration (P1 E4, extended S1): a tmp tree with synthetic violations plus
negative controls -- `.id()` used as a plain event key, `world.entity(x_id)`
id lookups, `it.entity(i).id()` passed as a function argument, and
`grid_id * cell_area` (a non-entity id) -- which must not flag.
"""

from __future__ import annotations

import re
import textwrap
from pathlib import Path

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
# uses the qualified `std::uint64_t` form); the multiplied expression may itself be
# parenthesised (`static_cast<uint64_t>((t + dt) * 1000.0)`, S1), and the multiplier may be
# written as `* 1e3`, `* 1000` or `* 1000.0` (S1: not only the literal `* 1000.0` form).
_TIME_QUANTIZATION_PATTERN = re.compile(
  r"(?:static_cast\s*<\s*(?:std::)?u?int64_t\s*>|(?:std::)?u?int64_t)"
  r"\s*\(\s*\(?[^()]*\)?\s*\*\s*1e3\b|"
  r"(?:static_cast\s*<\s*(?:std::)?u?int64_t\s*>|(?:std::)?u?int64_t)"
  r"\s*\(\s*\(?[^()]*\)?\s*\*\s*1000(?:\.0)?\b"
)

# An identifier that names an entity id, as the repo itself spells one: the fixed names
# `attacker_id`, `target_id`, `entity_id`, `owner_id`, or any identifier ending `_entity_id`
# (the repo's own convention for a raw Flecs id crossing a boundary -- `active_helo_entity_id`,
# `embarked_helo_entity_id`, `munition_entity_id`, `partner_entity_id`,
# `reference_entity_id`). Deliberately narrower than "ends with `_id`": a spatial grid
# coordinate like `grid_id` must not match (S1 false-positive report), so a bare `\w*_id` rule
# is not used.
_ENTITY_ID_NAME_FRAGMENT = (
  r"(?:attacker_id|target_id|entity_id|owner_id|\w*_entity_id)\b"
)
# The same name, optionally wrapped in a `static_cast<uint64_t>(...)` (or the unqualified
# `uint64_t(...)` form), so `static_cast<uint64_t>(e.id()) * k` and
# `static_cast<uint64_t>(attacker_id) ^ k` are covered on either side of the operator.
# An expression that ends in an `.id()` / `->id()` call: `target.id()`, `e.id()`,
# `it.entity(i).id()`. On the left of an operator the call suffix alone is enough to anchor a
# search; on the right the whole receiver has to be spelled out, because the operator comes
# first (`seed_base ^ target.id()`, S1).
_ID_CALL_EXPR_FRAGMENT = (
  r"\w+(?:\s*\([^()]*\))?(?:\s*(?:\.|->)\s*\w+(?:\s*\([^()]*\))?)*\s*(?:\.|->)\s*id\(\)"
)
_CAST_OPEN_FRAGMENT = r"(?:static_cast\s*<\s*(?:std::)?u?int64_t\s*>\s*\(\s*)?"
# Left operand of an operator: an entity-id name or a `.id()` call, optionally inside a cast.
_ID_OPERAND_FRAGMENT = (
  rf"(?:{_CAST_OPEN_FRAGMENT}(?:{_ENTITY_ID_NAME_FRAGMENT}|\.id\(\))\s*\)?)"
)
# Right operand of an operator: an entity-id name or a full `<expr>.id()`, optionally cast.
_ID_RIGHT_OPERAND_FRAGMENT = (
  rf"(?:{_CAST_OPEN_FRAGMENT}(?:{_ENTITY_ID_NAME_FRAGMENT}|{_ID_CALL_EXPR_FRAGMENT}))"
)
_OPERATOR_FRAGMENT = r"(?:\^|\*|<<|%|\+)"

# An operator applied directly to an entity id, on either side (S1: `seed_base ^ target.id()`,
# `attacker_id + k`, `k * attacker_id`, `static_cast<uint64_t>(e.id()) * k`). Deliberately
# narrow: it must fire on `x_id * k`, `x_id ^ k`, `x_id << k`, `x_id % k`, `x_id + k` and the
# `.id()` forms of the same in either operand order, but never on `.id()` or an id name used
# merely as a lookup key or function argument (E4/S1 negative controls), and never on `=`
# (`(?!=)` excludes `^=`, `*=`, `%=`; `+` has no such combined-assignment collision risk here
# but the exclusion is harmless for it too).
_ID_ARITHMETIC_PATTERN = re.compile(
  rf"{_ID_OPERAND_FRAGMENT}\s*{_OPERATOR_FRAGMENT}(?!=)"
  rf"|{_OPERATOR_FRAGMENT}(?!=)\s*{_ID_RIGHT_OPERAND_FRAGMENT}"
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


# SI-P3 landed the guard before the sites were converted (Phase Plan order), first as a strict
# xfail naming the exact files it flagged then. Sites 1-7, the ship-motion phase and the five
# private copies are now all converted (P3 exit), so the guard is green for real; this constant
# is kept as the historical record of what P3 started from.
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


def test_stochastic_draw_guard_flags_no_known_site() -> None:
  offenders = _guard_offending_files(REPO_ROOT)
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

  # P5 review S1: forms the first guard missed. One file per form, so each is proven alone.
  s1_forms = {
    "id_right_of_xor.h": "inline unsigned long long f(unsigned long long seed_base, flecs::entity target) { return seed_base ^ target.id(); }",
    "cast_id_times_k.h": "inline unsigned long long f(flecs::entity e) { return static_cast<uint64_t>(e.id()) * 31ULL; }",
    "id_plus_k.h": "inline unsigned long long f(unsigned long long attacker_id) { return attacker_id + 7ULL; }",
    "k_times_id.h": "inline unsigned long long f(unsigned long long attacker_id) { return 31ULL * attacker_id; }",
    "xor_iter_entity_id.h": "inline unsigned long long f(flecs::iter &it, int i, unsigned long long x) { return x ^ it.entity(i).id(); }",
    "functional_cast_time.h": "inline unsigned long long f(double t) { return uint64_t(t * 1000.0); }",
    "std_functional_cast_time.h": "inline unsigned long long f(double t) { return std::uint64_t(t * 1000.0); }",
    "parenthesised_time.h": "inline unsigned long long f(double t, double dt) { return static_cast<uint64_t>((t + dt) * 1000.0); }",
    "time_1e3.h": "inline unsigned long long f(double t) { return static_cast<uint64_t>(t * 1e3); }",
    "time_1000_int.h": "inline unsigned long long f(double t) { return static_cast<std::uint64_t>(t * 1000); }",
  }
  (tmp_path / "src" / "models").mkdir(parents=True)
  for name, body in s1_forms.items():
    (tmp_path / "src" / "models" / name).write_text("#pragma once" + chr(10) + body + chr(10), encoding="utf-8")

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

      // A non-entity `_id` (a spatial grid cell) in arithmetic: not an entity id (S1).
      inline double cell_mass(int grid_id, double cell_area) {
          return grid_id * cell_area;
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
  } | {f"src/models/{name}" for name in s1_forms}, offenders

  assert "splitmix64/seed constant literal" in offenders["src/core/splitmix_copy.h"]
  assert "2^53 uniform-divisor literal" in offenders["src/core/uniform_copy.h"]
  assert "time quantization outside quantize_time_ms" in offenders["src/core/time_quantize_copy.h"]
  assert "operator applied to a raw entity id" in offenders["src/core/id_arithmetic_copy.h"]
  assert "operator applied to a raw entity id" in offenders["src/systems/ship_motion_copy.h"]
  for name in s1_forms:
    assert offenders[f"src/models/{name}"], name
