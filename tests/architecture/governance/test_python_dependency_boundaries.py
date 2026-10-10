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


def _assert_native_dependency_graphs_acyclic(inventory: Inventory) -> None:
  assert strongly_connected_components(inventory.cpp_edges) == [], "C++ include cycle"
  assert strongly_connected_components_cmake(inventory.cmake_edges) == [], "CMake target cycle"


def test_real_native_dependency_graphs_have_no_cycles(inventory: Inventory) -> None:
  assert inventory.cpp_files and inventory.cpp_edges and inventory.cmake_edges
  _assert_native_dependency_graphs_acyclic(inventory)


def _assert_candidate_targets_unreachable(edges) -> None:
  graph: dict[str, set[str]] = {}
  for edge in edges:
    graph.setdefault(edge.source, set()).add(edge.target)
  candidates = {"ef_runtime_host_candidate", "ef_runtime_kernel_candidate",
                "ef_runtime_state_transfer_candidate", "ef_runtime_state_owner_adapters_candidate"}
  for production in ("ef_py", "ef_facade", "ef_facade_backend"):
    pending, seen = [production], set()
    while pending:
      node = pending.pop()
      if node in seen:
        continue
      seen.add(node)
      assert node not in candidates, f"candidate target reachable from {production}: {node}"
      pending.extend(graph.get(node, ()))


def test_candidate_targets_are_transitively_excluded_from_production(inventory: Inventory) -> None:
  _assert_candidate_targets_unreachable(inventory.cmake_edges)


def test_candidate_link_guard_rejects_a_renamed_intermediate_target(tmp_path: Path) -> None:
  path = tmp_path / "CMakeLists.txt"
  path.write_text("""
add_library(ef_facade STATIC facade.cpp)
add_library(ef_hidden_adapter STATIC helper.cpp)
add_library(ef_runtime_host_candidate STATIC candidate.cpp)
target_link_libraries(ef_facade PRIVATE ef_hidden_adapter)
target_link_libraries(ef_hidden_adapter PRIVATE ef_runtime_host_candidate)
""", encoding="utf-8")
  with pytest.raises(AssertionError, match="candidate target reachable from ef_facade"):
    _assert_candidate_targets_unreachable(build_edges(path))


def test_python_policy_classifies_every_inventory_site_once(inventory: Inventory) -> None:
  states = classify_python_edges(inventory, load_transitions())
  assert sum(states.values()) == len(inventory.python_edges)
  assert states["unclassified"] == 0


def test_cpp_cycle_gate_rejects_injected_back_edge(inventory: Inventory) -> None:
  forward = DependencyEdge("cpp_include", "src/components/a.h", "src/components/b.h", "src/components/a.h", 1)
  reverse = DependencyEdge("cpp_include", "src/components/b.h", "src/components/a.h", "src/components/b.h", 1)
  changed = Inventory(inventory.python_modules, inventory.python_edges, inventory.cpp_files,
                      (*inventory.cpp_edges, forward, reverse), inventory.cmake_edges,
                      inventory.unresolved_python_imports)
  with pytest.raises(AssertionError, match=r"C\+\+ include cycle"):
    _assert_native_dependency_graphs_acyclic(changed)


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


def test_transition_register_is_bounded() -> None:
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
  transitions = load_transitions()
  synthetic_transition = False
  if not transitions:
    synthetic_transition = True
    synthetic_key = (
      "python_import",
      "gym_envs.synthetic",
      "python.rl.policy_algo.ppo_adaptive_kl",
    )
    transitions = {
      synthetic_key: {
        "kind": synthetic_key[0],
        "source": synthetic_key[1],
        "target": synthetic_key[2],
        "owner": "test",
        "reason": "test",
        "exit_condition": "test",
        "max_sites": 1,
      }
    }
  transition = next(iter(transitions.values()))
  injected = DependencyEdge(
    str(transition["kind"]),
    str(transition["source"]),
    str(transition["target"]),
    "gym_envs/synthetic.py",
    1,
  )
  injected_edges = (injected, injected) if synthetic_transition else (injected,)
  changed = Inventory(
    inventory.python_modules,
    (*inventory.python_edges, *injected_edges),
    inventory.cpp_files,
    inventory.cpp_edges,
    inventory.cmake_edges,
    inventory.unresolved_python_imports,
  )

  assert any(
    finding.code == "transition_growth" and finding.source == injected.source
    for finding in check_python_policy(changed, transitions)
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
  with pytest.raises(AssertionError, match="CMake target cycle"):
    _assert_native_dependency_graphs_acyclic(Inventory({}, (), (), (), tuple(edges), ()))


def test_cmake_target_graph_preserves_real_command_line_numbers() -> None:
  edges = build_edges(Path("CMakeLists.txt"))

  assert next(edge for edge in edges if edge.source == "ef_core" and edge.target == "ef_content").line == 552
