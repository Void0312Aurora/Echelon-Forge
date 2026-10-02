"""Executable Python dependency inventory and boundary ratchet for issue #60."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.architecture.cmake_target_graph import (
  build_edges,
  strongly_connected_components as strongly_connected_components_cmake,
)
from tools.architecture.dependency_inventory import (
  DependencyEdge,
  Inventory,
  build_inventory,
  strongly_connected_components,
)
from tools.architecture.dependency_policy import (
  EXCEPTION_PATH,
  check_python_policy,
  classify_python_edges,
  load_transitions,
)


@pytest.fixture(scope="module")
def inventory() -> Inventory:
  return build_inventory()


def test_python_dependency_policy_has_no_unregistered_or_growing_edges(inventory: Inventory) -> None:
  transitions = load_transitions()

  findings = check_python_policy(inventory, transitions)

  assert findings == [], "; ".join(
    f"{finding.code}: {finding.source} -> {finding.target} ({finding.sites})"
    for finding in findings
  )


def test_python_dependency_inventory_has_no_unresolved_internal_imports_or_cycles(inventory: Inventory) -> None:
  assert inventory.unresolved_python_imports == ()
  assert strongly_connected_components(inventory.python_edges) == []
  assert inventory.cmake_edges
  assert classify_python_edges(inventory, load_transitions())[
    "forbidden"
  ] == 0


def test_transition_register_is_nonempty_and_bounded() -> None:
  transitions = load_transitions()

  assert EXCEPTION_PATH.is_file()
  assert all(int(entry["max_sites"]) >= 1 for entry in transitions.values())


def test_scripted_opponent_has_a_scenario_owner_and_legacy_export_is_identity_preserving(
  inventory: Inventory,
) -> None:
  from examples.agents import RedScriptedAgent as legacy_red_scripted_agent
  from python.scenario.runtime import RedScriptedAgent as scenario_red_scripted_agent

  assert legacy_red_scripted_agent is scenario_red_scripted_agent
  assert not any(
    edge.source.startswith("gym_envs") and edge.target.startswith("examples")
    for edge in inventory.python_edges
  )


def test_new_reverse_dependency_is_rejected(inventory: Inventory) -> None:
  injected = DependencyEdge(
    "python_import", "gym_envs.synthetic", "examples.agents", "gym_envs/synthetic.py", 1
  )
  changed = Inventory(
    inventory.python_modules,
    (*inventory.python_edges, injected),
    inventory.cpp_files,
    inventory.cpp_edges,
    inventory.cmake_edges,
    inventory.unresolved_python_imports,
  )

  assert any(
    finding.code == "new_forbidden_edge" and finding.source == "gym_envs.synthetic"
    for finding in check_python_policy(changed, load_transitions())
  )


def test_transition_growth_is_rejected(inventory: Inventory) -> None:
  transition = next(iter(load_transitions().values()))
  injected = DependencyEdge(
    str(transition["kind"]),
    str(transition["source"]),
    str(transition["target"]),
    "gym_envs/synthetic.py",
    1,
  )
  changed = Inventory(
    inventory.python_modules,
    (*inventory.python_edges, injected),
    inventory.cpp_files,
    inventory.cpp_edges,
    inventory.cmake_edges,
    inventory.unresolved_python_imports,
  )

  assert any(
    finding.code == "transition_growth" and finding.source == injected.source
    for finding in check_python_policy(changed, load_transitions())
  )


def test_cmake_target_graph_rejects_a_synthetic_back_edge(tmp_path: Path) -> None:
  cmake = tmp_path / "CMakeLists.txt"
  cmake.write_text(
    "\n".join(
      (
        "add_library(ef_core STATIC core.cpp)",
        "add_library(ef_content STATIC content.cpp)",
        "target_link_libraries(ef_core PUBLIC ef_content)",
        "target_link_libraries(ef_content PRIVATE ef_core)",
      )
    ),
    encoding="utf-8",
  )

  edges = build_edges(cmake)

  assert [(edge.source, edge.target) for edge in edges] == [
    ("ef_content", "ef_core"),
    ("ef_core", "ef_content"),
  ]
  assert strongly_connected_components_cmake(edges) == [["ef_content", "ef_core"]]


def test_cmake_target_graph_preserves_real_command_line_numbers() -> None:
  edges = build_edges(Path("CMakeLists.txt"))

  assert next(edge for edge in edges if edge.source == "ef_core" and edge.target == "ef_content").line == 557
