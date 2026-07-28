#!/usr/bin/env python3
"""Scan `src/**` C++ `#include` edges and classify them into maintained layers.

This is a pure source-text scanner: it does not require a built `ef_core`/
`ef_py`, and it does not execute any C++ preprocessing. It resolves quoted
`#include "..."` edges the same way the compiler would for this project's
include search path (`target_include_directories(ef_core PUBLIC .../src)`):
first relative to the including file's own directory, then relative to
`src/`. Unresolvable includes (third-party headers such as `<flecs.h>`,
`<spdlog/spdlog.h>`, `<nlohmann/json.hpp>`, and the standard library) are not
project edges and are skipped.

Used by:
- `tests/architecture/governance/test_cpp_include_direction.py` (the I38/T3
  include-direction gate).

Fine-grained groups follow the boundary rules already documented in each
`src/**/README.md` (see `docs/plan/unified_architecture_program/README.md`
T3 and `simulation_system_architecture_design.md` S15 G2 for the program-level
framing). Each fine group rolls up into one of the coarse layers named by the
T3 work order: `engine`, `mission`, `facade`, `content`, or `other` (the
independent/exempt groups such as `components`, `models`, `systems`,
`interfaces_python`, `gpu`, `tools`, `tests`, `main`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"

SOURCE_SUFFIXES = {".h", ".hpp", ".hxx", ".cpp", ".cc", ".cxx", ".inc"}

_INCLUDE_PATTERN = re.compile(
  r'^\s*#\s*include\s*(?:"(?P<quoted>[^"]+)"|<(?P<angled>[^>]+)>)'
)

# Ordered most-specific-prefix-first: the first matching entry wins.
_FINE_GROUP_PREFIXES: tuple[tuple[str, str], ...] = (
  ("core/mission/episode/detail", "core_mission_episode_detail"),
  ("core/mission/episode", "core_mission_episode"),
  ("core/mission/runtime", "core_mission_runtime"),
  ("core/mission", "core_mission_runtime"),  # mission/*.md-documented files outside runtime|episode
  ("core/engine", "core_engine"),
  ("core/geometry", "core_geometry"),
  ("core/interfaces", "core_interfaces"),
  ("runtime/facade", "runtime_facade"),
  ("runtime/contracts", "runtime_contracts"),
  ("content", "content"),
  ("components", "components"),
  ("models", "models"),
  ("systems", "systems"),
  ("interfaces/python", "interfaces_python"),
  ("gpu", "gpu"),
  ("tools", "tools"),
  ("tests", "tests"),
)

# Fine group -> coarse T3 layer (engine/mission/facade/content/other).
COARSE_LAYER_OF_FINE: dict[str, str] = {
  "core_engine": "engine",
  "core_mission_runtime": "mission",
  "core_mission_episode": "mission",
  "core_mission_episode_detail": "mission",
  "runtime_facade": "facade",
  "runtime_contracts": "facade",
  "content": "content",
  "core_geometry": "other",
  "core_interfaces": "other",
  "components": "other",
  "models": "other",
  "systems": "other",
  "interfaces_python": "other",
  "gpu": "other",
  "tools": "other",
  "tests": "other",
  "main": "other",
}

# Fine group -> one-line description used in the census report legend.
FINE_GROUP_DESCRIPTION: dict[str, str] = {
  "core_engine": "src/core/engine (T3 engine layer: SimulationKernel, WorldBatchRuntime)",
  "core_mission_runtime": "src/core/mission/runtime (T3 mission layer: pure runtime kernels)",
  "core_mission_episode": "src/core/mission/episode (T3 mission layer: episode controller/state)",
  "core_mission_episode_detail": "src/core/mission/episode/detail (T3 mission layer: private episode helpers)",
  "runtime_facade": "src/runtime/facade (T3 facade layer: RuntimeFacade application API)",
  "runtime_contracts": "src/runtime/contracts (T3 facade layer per task mapping; shared leaf DTOs in the repo's own boundary docs)",
  "content": "src/content (T3 content layer: unit/scenario content schemas and loaders)",
  "core_geometry": "src/core/geometry (independent leaf: spatial query runtime)",
  "core_interfaces": "src/core/interfaces (independent leaf: abstract model interfaces/contracts)",
  "components": "src/components (independent leaf: ECS components/DTO-like structs)",
  "models": "src/models (independent group: replaceable default model implementations)",
  "systems": "src/systems (independent group: Flecs system registration/tick logic)",
  "interfaces_python": "src/interfaces/python (exempt outermost layer: nanobind Python bindings)",
  "gpu": "src/gpu (exempt group: GPU helper runtime and experimental probes)",
  "tools": "src/tools (exempt group: dev-time/experimental tools)",
  "tests": "src/tests (exempt group: C++ doctest suite)",
  "main": "src/main.cpp (exempt: ef_app standalone entry point)",
}


def classify_fine_group(relative_posix_path: str) -> str:
  """Classify a `src/`-relative posix path into a fine-grained group name."""
  if relative_posix_path == "main.cpp":
    return "main"
  for prefix, group in _FINE_GROUP_PREFIXES:
    if relative_posix_path == prefix or relative_posix_path.startswith(prefix + "/"):
      return group
  return "unclassified"


@dataclass(frozen=True)
class IncludeEdge:
  from_path: str  # POSIX path relative to REPO_ROOT
  line: int
  raw_include: str  # e.g. '#include "core/engine/simulation_kernel.h"'
  included_spelling: str  # e.g. "core/engine/simulation_kernel.h"
  to_path: str  # POSIX path relative to REPO_ROOT (resolved)
  from_group: str
  to_group: str

  @property
  def from_layer(self) -> str:
    return COARSE_LAYER_OF_FINE.get(self.from_group, "other")

  @property
  def to_layer(self) -> str:
    return COARSE_LAYER_OF_FINE.get(self.to_group, "other")

  def fingerprint(self) -> str:
    """Stable (file, line, include-text) identity used by the ratchet allowlist."""
    return f"{self.from_path}:{self.line}:{self.included_spelling}"


def iter_source_files(src_root: Path = SRC_ROOT) -> list[Path]:
  return sorted(
    path
    for path in src_root.rglob("*")
    if path.is_file() and path.suffix in SOURCE_SUFFIXES
  )


def _resolve_include(including_file: Path, spelling: str, src_root: Path) -> Path | None:
  same_dir_candidate = including_file.parent / spelling
  if same_dir_candidate.is_file():
    return same_dir_candidate
  src_root_candidate = src_root / spelling
  if src_root_candidate.is_file():
    return src_root_candidate
  return None


def parse_file_includes(path: Path) -> list[tuple[int, str, str | None]]:
  """Return (line_no, raw_line, quoted_spelling_or_None) for every #include."""
  results: list[tuple[int, str, str | None]] = []
  text = path.read_text(encoding="utf-8", errors="replace")
  for line_no, line in enumerate(text.splitlines(), start=1):
    match = _INCLUDE_PATTERN.match(line)
    if not match:
      continue
    quoted = match.group("quoted")
    results.append((line_no, line.strip(), quoted))
  return results


def build_edges(
  files: list[Path] | None = None,
  *,
  src_root: Path = SRC_ROOT,
  repo_root: Path = REPO_ROOT,
) -> list[IncludeEdge]:
  """Build the full maintained include-edge list for `src/**`.

  Only quoted includes that resolve to a real file under `src_root` are
  counted as project edges; third-party/system includes (angle-bracket, or
  quoted spellings that do not resolve under `src_root`) are skipped.

  `src_root`/`repo_root` default to this repository's real `src/` tree, but
  may be overridden (e.g. with a `tmp_path`-backed throwaway tree rooted the
  same way, `<root>/src/...`) so governance tests can exercise the gate
  against a synthetic violation without touching real source files.
  """
  edges: list[IncludeEdge] = []
  for path in files if files is not None else iter_source_files(src_root):
    from_rel = path.relative_to(src_root).as_posix()
    from_group = classify_fine_group(from_rel)
    for line_no, raw_line, spelling in parse_file_includes(path):
      if spelling is None:
        continue  # angle-bracket system/third-party include
      resolved = _resolve_include(path, spelling, src_root)
      if resolved is None:
        continue  # unresolvable quoted include (third-party or generated)
      to_rel = resolved.relative_to(src_root).as_posix()
      to_group = classify_fine_group(to_rel)
      edges.append(
        IncludeEdge(
          from_path=path.relative_to(repo_root).as_posix(),
          line=line_no,
          raw_include=raw_line,
          included_spelling=spelling,
          to_path=resolved.relative_to(repo_root).as_posix(),
          from_group=from_group,
          to_group=to_group,
        )
      )
  return edges


# --- Direction policy -------------------------------------------------------
#
# Per-fine-group allowed target groups, derived directly from the "Allowed" /
# "Forbidden" / "Dependency Direction" sections already documented in each
# `src/**/README.md` (see the I38 registration for the source citations).
# A group may always include its own group; that is implicit and omitted
# below. Any edge whose `to_group` is not in the `from_group`'s allowed set
# (and is not the same group) is a direction violation.
FINE_GROUP_ALLOWED_TARGETS: dict[str, frozenset[str]] = {
  # Pure leaf DTOs: "must not own runtime orchestration logic"; no documented
  # allowance to depend on anything outside its own tree.
  "components": frozenset(),
  # "core/engine and models/core may consume content/. content/ does not
  # depend on core/engine, runtime/facade, or interfaces/python."
  # (components are used by unit_definition.h; core/interfaces is the
  # abstract-contract leaf content is allowed to describe types against.)
  "content": frozenset({"components", "core_interfaces"}),
  # "Model interfaces ... does not provide default implementations." Pure
  # abstraction leaf; may reference components for shared value types.
  # `runtime/contracts` is the T1 DTO-schema-owned vocabulary
  # ("referenced by the facade, engine, Python bindings, and tests");
  # `IEffectsModel`/event-builder/recorder interfaces here declare methods
  # against those schema-owned DTO shapes rather than duplicating fields.
  # `content` supplies the `UnitDefinition` value type referenced by
  # `IUnitFactory`'s signature (`core/engine`, the boundary that calls
  # through this interface, is separately documented as allowed to consume
  # `content/`).
  "core_interfaces": frozenset({"components", "runtime_contracts", "content"}),
  # "Pure C++ query services callable by core/engine or systems/ ... If a
  # query begins to depend on the lifecycle of a specific world owner,
  # ownership should be kept in core/engine" -> geometry must not depend on
  # engine/mission/facade.
  "core_geometry": frozenset({"components", "core_interfaces"}),
  # "This layer may depend on systems/, models/, components/, content/, and
  # core/interfaces. It does not depend on runtime/facade or
  # interfaces/python." core_geometry is a sibling query service engine may
  # call into; runtime_contracts is an explicitly shared DTO leaf ("Types
  # here may be referenced by the facade, engine, ...").
  "core_engine": frozenset(
    {"systems", "models", "components", "content", "core_interfaces", "core_geometry", "runtime_contracts"}
  ),
  # "This layer may consume components/command, components/tasking, the
  # public API of core/engine, and mission-related DTOs. It should not
  # depend on runtime/facade or interfaces/python." `core/geometry` is a
  # pure query-service leaf explicitly documented as "callable by
  # core/engine or systems/"; mission runtime kernels (e.g. waypoint/
  # approach shaping) call the same spatial-query leaf engine uses.
  "core_mission_runtime": frozenset(
    {"components", "core_engine", "core_interfaces", "runtime_contracts", "core_geometry"}
  ),
  # "episode/ may depend on runtime/." `episode/detail/` is documented as
  # "internal helpers used only by the episode controller" -- i.e. the
  # controller (`episode/`) is expected to #include its own `detail/`
  # helpers; that is the primary direction the split exists for.
  "core_mission_episode": frozenset(
    {
      "components",
      "core_engine",
      "core_interfaces",
      "runtime_contracts",
      "core_mission_runtime",
      "core_mission_episode_detail",
      "core_geometry",
    }
  ),
  # "episode/detail/ may depend on episode/ and runtime/, but should not
  # become a public cross-layer entry point" (the "not a public entry point"
  # half is a caller-side rule, checked separately).
  "core_mission_episode_detail": frozenset(
    {
      "components",
      "core_engine",
      "core_interfaces",
      "runtime_contracts",
      "core_mission_runtime",
      "core_mission_episode",
      "core_geometry",
    }
  ),
  # "provides capabilities ... to systems/ and core/engine"; "Helpers that
  # depend only on component data and contracts from core/interfaces";
  # content's README explicitly carves out "models/core ... may consume
  # content/". `runtime_contracts` supplies schema-owned capability DTOs
  # (e.g. `platform_capability_contracts.h`) that `default_unit_factory.h`
  # projects typed spawn evidence against (T1 DTO-schema pattern).
  "models": frozenset({"core_interfaces", "components", "content", "runtime_contracts"}),
  # "Code here consumes components/ and models/, and is registered and
  # scheduled by core/engine" -> systems must not depend upward on engine.
  # `runtime_contracts` is the same schema-owned DTO leaf engine/mission are
  # allowed to reference (engagement/lifecycle event contracts here).
  "systems": frozenset({"components", "models", "core_interfaces", "runtime_contracts"}),
  # "stores the stable DTOs shared between runtime/facade and lower-level
  # runtime owners ... must not own world state ... Forbidden: ...Pulling in
  # core/engine/* just for include convenience." Pure leaf; may reference
  # components for shared value types.
  "runtime_contracts": frozenset({"components"}),
  # "Combined calls to core/engine and core/mission" (Allowed); contracts is
  # the facade's own DTO vocabulary. "Directly including core/engine/* in
  # *_types.h or facade public headers" is prohibited -- that header-scoped
  # refinement is checked by a dedicated existing gate
  # (test_runtime_facade_contract_boundaries.py) and by the header-vs-impl
  # split enforced in this module's report, not by widening this matrix.
  "runtime_facade": frozenset(
    {"runtime_contracts", "core_engine", "core_mission_runtime", "core_mission_episode", "components", "core_interfaces"}
  ),
  # "exposes runtime/facade, required compatibility APIs from core, and the
  # relevant data types to Python." Documented as the outermost consumer;
  # treated as exempt/permissive for the direction gate (see README citation
  # in the governance test and the I38 registration note).
  "interfaces_python": frozenset(
    {
      "runtime_facade",
      "runtime_contracts",
      "core_engine",
      "core_mission_runtime",
      "core_mission_episode",
      "core_mission_episode_detail",
      "core_geometry",
      "core_interfaces",
      "components",
      "models",
      "systems",
      "content",
      "gpu",
    }
  ),
  # "GPU helpers, batch packet runtime ... must not silently alter the
  # canonical world-step semantics"; links `ef_core` publicly. Treated as an
  # exempt consumer group (like interfaces_python) rather than gated into
  # the engine/mission/facade ring; must not depend on interfaces_python
  # (that direction is never documented and would invert the Python binding
  # boundary).
  "gpu": frozenset(
    {
      "core_engine",
      "core_mission_runtime",
      "core_mission_episode",
      "runtime_facade",
      "runtime_contracts",
      "components",
      "core_interfaces",
      "content",
      "models",
      "systems",
    }
  ),
  # "development-time utilities ... may call runtime APIs for probing."
  # Exempt consumer; the corresponding "no reverse dependency FROM
  # runtime/facade, core/, or interfaces/python" half is enforced by
  # checking that nothing else targets `tools`.
  "tools": frozenset(
    {
      "core_engine",
      "core_mission_runtime",
      "core_mission_episode",
      "core_mission_episode_detail",
      "runtime_facade",
      "runtime_contracts",
      "components",
      "core_interfaces",
      "core_geometry",
      "content",
      "models",
      "systems",
      "interfaces_python",
      "gpu",
    }
  ),
  # C++ doctest suite: exempt consumer, may reach anywhere (diagnostic path,
  # not a maintained application path; mirrors G1's "test paths are counted
  # but do not increase the maintained metric").
  "tests": frozenset(
    {
      "core_engine",
      "core_mission_runtime",
      "core_mission_episode",
      "core_mission_episode_detail",
      "runtime_facade",
      "runtime_contracts",
      "components",
      "core_interfaces",
      "core_geometry",
      "content",
      "models",
      "systems",
      "gpu",
    }
  ),
  # `ef_app` standalone local-testing entry point; documented as needing to
  # "include/use SimulationKernel" directly.
  "main": frozenset({"core_engine", "core_mission_runtime", "runtime_facade", "components", "core_interfaces"}),
}

# Groups that must never be the *target* of an edge from any other group
# (i.e. nothing may depend on them): dev tools and the test suite are
# consumers only, never dependencies of maintained code.
NO_INCOMING_MAINTAINED_EDGES: frozenset[str] = frozenset({"tools", "tests"})


def is_violation(edge: IncludeEdge) -> bool:
  if edge.from_group == edge.to_group:
    return False
  if edge.to_group in NO_INCOMING_MAINTAINED_EDGES and edge.from_group not in NO_INCOMING_MAINTAINED_EDGES:
    return True
  allowed = FINE_GROUP_ALLOWED_TARGETS.get(edge.from_group)
  if allowed is None:
    return True  # unclassified from-group: fail closed
  return edge.to_group not in allowed


def coarse_matrix(edges: list[IncludeEdge]) -> dict[tuple[str, str], int]:
  matrix: dict[tuple[str, str], int] = {}
  for edge in edges:
    key = (edge.from_layer, edge.to_layer)
    matrix[key] = matrix.get(key, 0) + 1
  return matrix


def fine_matrix(edges: list[IncludeEdge]) -> dict[tuple[str, str], int]:
  matrix: dict[tuple[str, str], int] = {}
  for edge in edges:
    key = (edge.from_group, edge.to_group)
    matrix[key] = matrix.get(key, 0) + 1
  return matrix


def violations(edges: list[IncludeEdge]) -> list[IncludeEdge]:
  return [edge for edge in edges if is_violation(edge)]


__all__ = tuple(name for name in globals() if not name.startswith("_"))
