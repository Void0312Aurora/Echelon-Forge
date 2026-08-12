"""T3 C++ layer-boundary include-direction gate (I38 slice 1).

Parses every `#include` edge under `src/**`, classifies both endpoints into
the fine-grained layer groups documented by each `src/**/README.md`, and
fails on any edge whose direction is not sanctioned by
`tools/architecture/cpp_include_graph.FINE_GROUP_ALLOWED_TARGETS` unless the
edge is explicitly ratcheted in
`tests/architecture/fixtures/cpp_include_direction_allowlist_20260720.json`.

This is a ratchet, not a freeze: the allowlist may only shrink (an entry is
removed once its structural coupling is resolved, most likely by the T3
physical link-unit split) and the gate fails loudly if an entry stops
reproducing, so the allowlist cannot silently rot into a stale document.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
  from tools.architecture.cpp_include_graph import IncludeEdge

REPO_ROOT = Path(__file__).resolve().parents[3]
ALLOWLIST_FIXTURE = (
  REPO_ROOT
  / "tests"
  / "architecture"
  / "fixtures"
  / "cpp_include_direction_allowlist_20260720.json"
)

# Outermost consumer groups the src/README and per-directory READMEs document
# as legitimate callers into runtime/facade (the Python binding boundary and
# exempt dev/test/GPU-experiment consumers); everything else must reach the
# facade only indirectly, never by #include.
FACADE_PERMITTED_CALLERS = frozenset(
  {"runtime_facade", "interfaces_python", "gpu", "tools", "tests", "main"}
)

# content/README.md's explicit "Dependency Direction" section.
CONTENT_FORBIDDEN_TARGETS = frozenset(
  {"core_engine", "runtime_facade", "interfaces_python", "core_mission_runtime", "core_mission_episode", "core_mission_episode_detail"}
)


def _load_allowlist_payload() -> dict:
  return json.loads(ALLOWLIST_FIXTURE.read_text(encoding="utf-8"))


def _allowlist_by_fingerprint() -> dict[str, dict]:
  payload = _load_allowlist_payload()
  by_fingerprint: dict[str, dict] = {}
  for entry in payload["entries"]:
    fingerprint = f'{entry["file"]}:{entry["line"]}:{entry["include"]}'
    assert fingerprint not in by_fingerprint, f"duplicate allowlist fingerprint: {fingerprint}"
    by_fingerprint[fingerprint] = entry
  return by_fingerprint


def test_allowlist_fixture_entries_are_well_formed_and_match_current_classification() -> None:
  from tools.architecture.cpp_include_graph import (
    FINE_GROUP_ALLOWED_TARGETS,
    classify_fine_group,
  )

  allowlist = _allowlist_by_fingerprint()
  assert allowlist, "expected at least one ratcheted entry to exercise the allowlist path"

  for fingerprint, entry in allowlist.items():
    for key in ("file", "line", "include", "from_group", "to_group", "owner", "next_gate", "reason"):
      assert str(entry.get(key, "")).strip(), f"{fingerprint} missing/blank required field {key!r}"

    source_path = REPO_ROOT / entry["file"]
    assert source_path.is_file(), f"{fingerprint} references a missing file"

    from_group = classify_fine_group(source_path.relative_to(REPO_ROOT / "src").as_posix())
    assert from_group == entry["from_group"], (
      f"{fingerprint}: recorded from_group {entry['from_group']!r} no longer matches "
      f"current classification {from_group!r}"
    )

    included_path = source_path.parent / entry["include"]
    if not included_path.is_file():
      included_path = REPO_ROOT / "src" / entry["include"]
    assert included_path.is_file(), f"{fingerprint}: include target does not resolve to a real file"
    to_group = classify_fine_group(included_path.relative_to(REPO_ROOT / "src").as_posix())
    assert to_group == entry["to_group"], (
      f"{fingerprint}: recorded to_group {entry['to_group']!r} no longer matches "
      f"current classification {to_group!r}"
    )

    # Every ratcheted entry must be a real, currently-classified violation;
    # an entry that the policy would already allow is either stale or was
    # mis-scoped when it was added.
    assert entry["to_group"] not in FINE_GROUP_ALLOWED_TARGETS.get(entry["from_group"], frozenset()), (
      f"{fingerprint}: {entry['from_group']} -> {entry['to_group']} is already policy-allowed; "
      "remove this now-unnecessary allowlist entry"
    )


def test_include_direction_gate_has_no_new_violations_beyond_the_ratchet_allowlist() -> None:
  from tools.architecture.cpp_include_graph import build_edges, is_violation

  allowlist = _allowlist_by_fingerprint()
  edges = build_edges()
  found_violations = [edge for edge in edges if is_violation(edge)]

  unexpected: list[IncludeEdge] = []
  seen_fingerprints: set[str] = set()
  for edge in found_violations:
    fingerprint = edge.fingerprint()
    if fingerprint in allowlist:
      seen_fingerprints.add(fingerprint)
      continue
    unexpected.append(edge)

  assert unexpected == [], (
    "New include-direction violation(s) not covered by the ratchet allowlist "
    f"({ALLOWLIST_FIXTURE.relative_to(REPO_ROOT).as_posix()}). Either fix the "
    "include direction, or add an attributed allowlist entry if the coupling "
    "is a pre-existing structural one deferred to the T3 physical split: "
    + "; ".join(
      f"{edge.from_path}:{edge.line} [{edge.from_group} -> {edge.to_group}] {edge.raw_include}"
      for edge in unexpected
    )
  )

  stale = sorted(set(allowlist) - seen_fingerprints)
  assert stale == [], (
    "Allowlist entries no longer reproduced by the scan (the violation was "
    f"fixed, or the line/include text moved) -- remove or update them: {stale}"
  )


def test_facade_application_layer_has_no_incoming_edges_outside_its_permitted_callers() -> None:
  """G1: 'facade becomes the only application path.' No engine, mission,
  content, components, models, systems, or contracts code may #include
  runtime/facade; only the Python binding boundary and the exempt
  dev/test/GPU-experiment consumer groups may."""
  from tools.architecture.cpp_include_graph import build_edges

  edges = build_edges()
  offenders = [
    edge
    for edge in edges
    if edge.to_group == "runtime_facade" and edge.from_group not in FACADE_PERMITTED_CALLERS
  ]
  assert offenders == [], (
    "unexpected dependency on runtime/facade from a non-application layer: "
    + "; ".join(f"{edge.from_path}:{edge.line} [{edge.from_group}]" for edge in offenders)
  )


def test_content_layer_never_depends_on_engine_facade_mission_or_python_bindings() -> None:
  """content/README.md: 'content/ does not depend on core/engine,
  runtime/facade, or interfaces/python.'"""
  from tools.architecture.cpp_include_graph import build_edges

  edges = build_edges()
  offenders = [
    edge
    for edge in edges
    if edge.from_group == "content" and edge.to_group in CONTENT_FORBIDDEN_TARGETS
  ]
  assert offenders == [], (
    "content/ took on a forbidden dependency: "
    + "; ".join(f"{edge.from_path}:{edge.line} -> [{edge.to_group}]" for edge in offenders)
  )


def test_nothing_outside_the_tool_or_test_groups_depends_on_tools_or_tests() -> None:
  """tools/README.md: '...Reverse dependency from runtime/facade, core/, or
  interfaces/python' is prohibited -- i.e. tools/ and the C++ test suite are
  consumers only and must never be a maintained #include target."""
  from tools.architecture.cpp_include_graph import (
    NO_INCOMING_MAINTAINED_EDGES,
    build_edges,
  )

  edges = build_edges()
  offenders = [
    edge
    for edge in edges
    if edge.to_group in NO_INCOMING_MAINTAINED_EDGES and edge.from_group not in NO_INCOMING_MAINTAINED_EDGES
  ]
  assert offenders == [], (
    "maintained code must not #include tools/ or the C++ test suite: "
    + "; ".join(f"{edge.from_path}:{edge.line} -> [{edge.to_group}]" for edge in offenders)
  )


def test_gate_rejects_an_injected_violation_not_covered_by_the_allowlist(tmp_path: Path) -> None:
  """Negative self-test (no real source files touched): build a throwaway
  `src/` tree with one new components -> core_engine violation and confirm
  the same allowlist cross-check the real gate runs would fail on it."""
  from tools.architecture.cpp_include_graph import build_edges, is_violation

  fake_repo = tmp_path / "fake_repo"
  fake_src = fake_repo / "src"
  (fake_src / "components").mkdir(parents=True)
  (fake_src / "core" / "engine").mkdir(parents=True)
  (fake_src / "core" / "engine" / "widget.h").write_text("#pragma once\n", encoding="utf-8")
  offending_file = fake_src / "components" / "offender.h"
  offending_file.write_text(
    '#pragma once\n#include "core/engine/widget.h"\n',
    encoding="utf-8",
  )

  edges = build_edges(src_root=fake_src, repo_root=fake_repo)
  injected_violations = [edge for edge in edges if is_violation(edge)]

  assert len(injected_violations) == 1
  injected = injected_violations[0]
  assert (injected.from_group, injected.to_group) == ("components", "core_engine")

  allowlist = _allowlist_by_fingerprint()
  assert injected.fingerprint() not in allowlist, (
    "the injected fingerprint accidentally collided with a real allowlist "
    "entry; rename the synthetic fixture files"
  )

  # Mirror the real gate's pass/fail logic against this synthetic edge list:
  # an injected violation absent from the allowlist must fail the check.
  with pytest.raises(AssertionError):
    unexpected = [edge for edge in injected_violations if edge.fingerprint() not in allowlist]
    assert unexpected == [], "expected the injected violation to be flagged as unexpected"


def test_the_contracts_to_mission_step_request_edge_stays_held_with_its_adjudication() -> None:
  """T1/T3 held-edge pin (re-adjudicated this iteration, 2026-07-27).

  WorldExecutionEpisodeStepRequest (runtime/contracts/world_batch_contracts.h)
  types its config/env_state fields as StepEvaluationBatchConfig/
  StepEvaluationBatchEnvState, owned by core/mission/episode/
  execution_episode_batch_prepare.h. The T1 schema-ownership route (dto_schema
  single-sourcing per the I33 engagement-family contracts-owned-leaf pattern)
  was evaluated and foreclosed: the env-state struct is not leaf-closed (ten
  mission-owned aggregates by value, plus ExecutionEpisodeState's
  core/geometry SpatialRouteWaypoint dependency, both outside
  runtime_contracts' {components} target set), and the scanner counts .inc
  textual includes as edges, so any contracts-located definition re-creates
  the violation. This test pins the ratcheted entry and its binding surface;
  the edge may only be closed by the T1 DTO-family-completion migration
  editing this test explicitly, never by reversing the dependency."""
  payload = _load_allowlist_payload()
  contracts_entries = [
    entry for entry in payload["entries"] if entry["from_group"] == "runtime_contracts"
  ]
  assert len(contracts_entries) == 1, (
    "expected exactly one held runtime_contracts entry; a second contracts "
    "violation must not shelter under the held (f) adjudication"
  )

  entry = contracts_entries[0]
  assert entry["file"] == "src/runtime/contracts/world_batch_contracts.h"
  assert entry["include"] == "core/mission/episode/execution_episode_batch_prepare.h"
  assert entry["to_group"] == "core_mission_episode"
  for marker in (
    "Re-adjudicated 2026-07-27",
    "SpatialRouteWaypoint",
    "T1 DTO-family-completion",
    "do not reverse the dependency",
  ):
    assert marker in entry["reason"], (
      f"the held (f) entry's reason lost its adjudication marker {marker!r}; "
      "re-adjudicate before weakening the record"
    )

  # The include site must carry the matching dated adjudication comment so the
  # held verdict is visible where the coupling physically lives.
  include_site = (REPO_ROOT / entry["file"]).read_text(encoding="utf-8")
  assert "HELD include-direction edge" in include_site
  assert "re-adjudicated this iteration, 2026-07-27" in include_site

  # Binding-surface parity pin: the held verdict was adjudicated against a
  # 57-field def_rw surface (15 config + 42 env-state) in bindings_episode.cpp.
  # If either block drifts, the census underlying the held verdict is stale
  # and the edge must be re-adjudicated, not silently kept.
  bindings_text = (
    REPO_ROOT / "src" / "interfaces" / "python" / "bindings_episode.cpp"
  ).read_text(encoding="utf-8")

  def _def_rw_count(class_token: str) -> int:
    start = bindings_text.index(f"nb::class_<{class_token}>")
    end = bindings_text.index(";", start)
    return bindings_text.count(".def_rw(", start, end)

  assert _def_rw_count("StepEvaluationBatchConfig") == 15
  assert _def_rw_count("StepEvaluationBatchEnvState") == 42


def test_direction_policy_groups_stay_in_sync_with_the_maintained_src_tree() -> None:
  """Every file under src/** must resolve to a known fine-grained group so
  the census/gate cannot silently ignore a newly-added top-level directory."""
  from tools.architecture.cpp_include_graph import classify_fine_group, iter_source_files

  unclassified = [
    path
    for path in iter_source_files()
    if classify_fine_group(path.relative_to(REPO_ROOT / "src").as_posix()) == "unclassified"
  ]
  assert unclassified == [], (
    "add a src/**/README.md-backed group + policy entry in "
    f"tools/architecture/cpp_include_graph.py for: {unclassified}"
  )
