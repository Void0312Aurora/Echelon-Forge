from __future__ import annotations

import ast
from dataclasses import dataclass, fields
from pathlib import Path

from python.runtime_bootstrap import ensure_repo_imports


ensure_repo_imports()

from gym_envs.scenario_loader.runtime_state import (
  SCENARIO_LOADER_STATE_SHELL_ATTRS,
  SCENARIO_LOADER_STATE_SHELL_BLOCKED_OWNER_CANDIDATE,
  SCENARIO_LOADER_STATE_SHELL_CLASSIFICATION_BUCKETS,
  SCENARIO_LOADER_STATE_SHELL_CLASSIFICATIONS,
  SCENARIO_LOADER_STATE_SHELL_RUNTIME_MIRROR_ONLY,
  SCENARIO_LOADER_STATE_SHELL_SCENARIO_CONTENT_ADAPTER,
  SCENARIO_LOADER_STATE_SHELL_TRANSITIONAL_BEHAVIOR_MIRROR,
  ScenarioLoaderStateShell,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
WORLD_BATCH_VEC_ENV = REPO_ROOT / "python" / "rl" / "runtime" / "world_batch_vec_env.py"
WORLD_BATCH_VEC_ENV_IMPL = REPO_ROOT / "python" / "rl" / "runtime" / "world_batch"
WORLD_BATCH_VEC_ENV_SOURCE_FILES = (
  WORLD_BATCH_VEC_ENV_IMPL / "_vec_env_support.py",
  WORLD_BATCH_VEC_ENV_IMPL / "_visual_backend_mixin.py",
  WORLD_BATCH_VEC_ENV_IMPL / "_observation_mixin.py",
  WORLD_BATCH_VEC_ENV_IMPL / "_execution_episode_mixin.py",
  WORLD_BATCH_VEC_ENV_IMPL / "_air_combat_post_launch_mixin.py",
  WORLD_BATCH_VEC_ENV_IMPL / "vec_env.py",
  WORLD_BATCH_VEC_ENV,
)
WORLD_BATCH_ADAPTER = REPO_ROOT / "python" / "rl" / "runtime" / "world_batch" / "adapter.py"
WORLD_BATCH_RUNTIME_ACCESS = REPO_ROOT / "python" / "rl" / "runtime" / "world_batch" / "runtime_access.py"
LEADER_WORLD_BATCH_RUNTIME = REPO_ROOT / "python" / "rl" / "runtime" / "leader_world_batch_runtime.py"
TASKING_BRIDGE = REPO_ROOT / "python" / "rl" / "tasking" / "bridge.py"
TASKING_BRIDGE_CANONICAL = REPO_ROOT / "python" / "tasking_contracts" / "bridge_views.py"
RUNTIME_CONTRACTS = REPO_ROOT / "src" / "runtime" / "contracts"
RUNTIME_FACADE = REPO_ROOT / "src" / "runtime" / "facade"
RUNTIME_FACADE_SOURCE_FILES = (
  RUNTIME_FACADE / "runtime_facade_world_setup.cpp",
  RUNTIME_FACADE / "runtime_facade_counterfactual.cpp",
  RUNTIME_FACADE / "runtime_facade_config.cpp",
  RUNTIME_FACADE / "runtime_facade_query.cpp",
  RUNTIME_FACADE / "runtime_facade_command_api.cpp",
  RUNTIME_FACADE / "runtime_facade_execution.cpp",
  RUNTIME_FACADE / "runtime_facade_packet.cpp",
  RUNTIME_FACADE / "runtime_facade.cpp",
  RUNTIME_FACADE / "runtime_facade_internal.h",
)
RUNTIME_BINDINGS = REPO_ROOT / "src" / "interfaces" / "python" / "bindings_runtime.cpp"


def runtime_bindings_source_text() -> str:
  """The decomposed bindings_runtime surface joined in registration order.

  bindings_runtime.cpp is an orchestrator shell since the per-domain split;
  source-shape guards must read the concatenated slices instead.
  """
  from tests.architecture.structural_boundaries.helpers import bindings_runtime_text

  return bindings_runtime_text()
GPU_BINDINGS = REPO_ROOT / "src" / "interfaces" / "python" / "bindings_gpu.cpp"
WORLD_BATCH_RUNTIME_H = REPO_ROOT / "src" / "core" / "engine" / "world_batch_runtime.h"
WORLD_BATCH_RUNTIME_CPP = REPO_ROOT / "src" / "core" / "engine" / "world_batch_runtime.cpp"
CORE_SRC = REPO_ROOT / "src" / "core"
SCENARIO_RUNTIME = REPO_ROOT / "python" / "scenario" / "runtime"
UNIVERSAL_ENV = REPO_ROOT / "gym_envs" / "universal_env.py"


def _source() -> str:
  return world_batch_vec_env_source_text()


def _adapter_source() -> str:
  return WORLD_BATCH_ADAPTER.read_text(encoding="utf-8")


def _leader_source() -> str:
  return LEADER_WORLD_BATCH_RUNTIME.read_text(encoding="utf-8")


def _runtime_access_source() -> str:
  return WORLD_BATCH_RUNTIME_ACCESS.read_text(encoding="utf-8")


def _gpu_bindings_source() -> str:
  return GPU_BINDINGS.read_text(encoding="utf-8")


def runtime_facade_source_text() -> str:
  return "\n".join(
    path.read_text(encoding="utf-8") for path in RUNTIME_FACADE_SOURCE_FILES
  )


def world_batch_vec_env_source_text() -> str:
  return "\n".join(
    path.read_text(encoding="utf-8") for path in WORLD_BATCH_VEC_ENV_SOURCE_FILES
  )


def _maintained_execution_episode_compat_read_allowlist() -> set[str]:
  return {
    "python/rl/runtime/world_batch/adapter.py",
    "python/rl/runtime/world_batch/runtime_support.py",
    "tests/world_batch/test_world_batch_vec_env_command_chain.py",
    "tests/world_batch/test_world_batch_vec_env_execution_and_observation.py",
  }


def _iter_maintained_python_paths() -> list[Path]:
  return [
    *REPO_ROOT.joinpath("python", "rl", "runtime").rglob("*.py"),
    *(
      path
      for path in REPO_ROOT.joinpath("tests").rglob("*.py")
      if "tests/architecture/" not in path.relative_to(REPO_ROOT).as_posix()
    ),
  ]


def _iter_maintained_facade_guard_paths() -> list[Path]:
  return [
    *REPO_ROOT.joinpath("python", "rl", "runtime").rglob("*.py"),
    *REPO_ROOT.joinpath("tests", "runtime").rglob("*.py"),
    *REPO_ROOT.joinpath("tests", "world_batch").rglob("*.py"),
  ]


def _iter_non_test_python_paths() -> list[Path]:
  excluded_prefixes = (".git", ".venv", "__pycache__", "build", "dist", "node_modules", "archive", "temp")
  return [
    path
    for path in sorted(REPO_ROOT.rglob("*.py"))
    if not any(part.startswith(excluded_prefixes) for part in path.parts)
    and not path.relative_to(REPO_ROOT).as_posix().startswith("tests/")
  ]


def _class_stack(tree: ast.AST) -> dict[ast.AST, list[str]]:
  stack: list[str] = []
  out: dict[ast.AST, list[str]] = {}

  class Visitor(ast.NodeVisitor):
    def generic_visit(self, node: ast.AST) -> None:
      out[node] = list(stack)
      super().generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
      out[node] = list(stack)
      stack.append(node.name)
      self.generic_visit(node)
      stack.pop()

  Visitor().visit(tree)
  return out


def _compat_batch_runtime_consumer_allowlist() -> set[str]:
  return set()


def _wp22_loader_sim_guard_scope() -> dict[str, tuple[str, ...]]:
  return {
    "python/rl/runtime/world_batch/vec_env.py": (
      "handle.loader.sim,",
      "handle.loader.sim)",
    ),
    "python/rl/runtime/world_batch_vec_env.py": (
      "handle.loader.sim,",
      "handle.loader.sim)",
    ),
    "python/rl/runtime/cooperative_world_batch_vec_env.py": (
      "slot_state.loader.sim,",
      "slot_state.loader.sim)",
      "loader.sim.get_time_step(",
    ),
    "python/rl/runtime/leader_world_batch_runtime.py": (
      "handle.loader.sim,",
      "handle.loader.sim)",
    ),
    "python/rl/runtime/single_world_batch_runtime.py": (
      "self.access.sim(env_idx),",
      "self.access.sim(env_idx))",
      "handle.loader.sim,",
      "handle.loader.sim)",
    ),
    "python/rl/tasking/bridge.py": (
      "loader.sim.set_mission_command(",
      "loader.sim.set_task_order(",
      "loader.sim.set_leader_intent(",
      "loader.sim.set_pilot_report(",
      "loader.sim.get_agent_observation(",
      "loader.sim.get_instrument_state(",
      "loader.sim.get_time_step(",
    ),
    "gym_envs/scenario_loader/behavior_runtime/naval_screen.py": (
      "loader.sim.get_unit_position(",
      "loader.sim.get_unit_velocity(",
      "loader.sim.is_unit_active(",
    ),
    "gym_envs/scenario_loader/behavior_runtime/command_chain.py": (
      "loader.sim.set_mission_command(",
      "loader.sim.get_time_step(",
    ),
    "gym_envs/scenario_loader/step_evaluation.py": (
      "loader.sim.get_time_step(",
    ),
    "gym_envs/scenario_loader/execution_runtime/shadow.py": (
      "loader.sim.get_time_step(",
    ),
    "gym_envs/scenario_loader/behavior_runtime/post_waypoint_transition.py": (
      "loader.sim.get_time_step(",
    ),
    "gym_envs/scenario_loader/behavior_runtime/scripted_opponents.py": (
      "loader.sim,",
      "loader.sim)",
    ),
    "gym_envs/scenario_loader/loading.py": (
      "loader.sim,",
      "loader.sim)",
    ),
    "gym_envs/scenario_loader/runtime_state.py": (
      "loader.sim,",
      "loader.sim)",
      "loader.sim.",
    ),
    "gym_envs/leader_env_parts/decision_runtime/commands.py": (
      "loader.sim.get_agent_observation(",
      "loader.sim.get_instrument_state(",
      "env.unwrapped.sim.get_time_step(",
    ),
    "gym_envs/leader_env_parts/bridges.py": (
      "loader.sim.set_task_order(",
      "loader.sim.set_leader_intent(",
      "loader.sim.set_pilot_report(",
    ),
  }


def _runtime_escape_hatch_path_allowlist() -> set[str]:
  return {
    path
    for path, allowance in SCOPED_ESCAPE_HATCH_ALLOWLIST.items()
    if allowance.runtime_calls or allowance.runtime_world_calls
  }


def _batch_runtime_attribute_lines(path: Path) -> list[int]:
  tree = ast.parse(path.read_text(encoding="utf-8"))
  return sorted(
    {
      int(getattr(node, "lineno", 0) or 0)
      for node in ast.walk(tree)
      if isinstance(node, ast.Attribute) and node.attr == "batch_runtime"
    }
  )


def _world_call_lines(path: Path) -> list[int]:
  tree = ast.parse(path.read_text(encoding="utf-8"))
  return sorted(
    {
      int(getattr(node, "lineno", 0) or 0)
      for node in ast.walk(tree)
      if isinstance(node, ast.Call)
      and isinstance(node.func, ast.Attribute)
      and node.func.attr in {"world", "world_raw_quarantine"}
    }
  )


@dataclass(frozen=True)
class EscapeHatchAllowance:
  runtime_calls: int
  runtime_world_calls: int
  world_batch_ctor_calls: int
  classification: str
  tier: str


SCOPED_ESCAPE_HATCH_ALLOWLIST = {
  "tests/runtime/engagement/test_facade_engagement_evidence_gates.py": EscapeHatchAllowance(
    runtime_calls=0,
    runtime_world_calls=0,
    world_batch_ctor_calls=1,
    classification="diagnostics_only",
    tier="test_only",
  ),
}


EXPECTED_SCENARIO_LOADER_STATE_SHELL_CLASSIFICATION_BY_BUCKET = {
  SCENARIO_LOADER_STATE_SHELL_SCENARIO_CONTENT_ADAPTER: frozenset(
    {
      "_cached_route_ref_id",
      "waypoints",
    }
  ),
  SCENARIO_LOADER_STATE_SHELL_RUNTIME_MIRROR_ONLY: frozenset(
    {
      "_waypoint_leg_origin_x",
      "_waypoint_leg_origin_y",
      "_waypoint_prev_dist_m",
      "gear_bonus_awarded",
      "last_reward_breakdown",
      "last_termination_reason",
      "liftoff_awarded",
      "off_runway_steps",
      "prev_alt",
      "prev_speed",
      "waypoint_idx",
      "waypoint_total_route_length_m",
    }
  ),
  SCENARIO_LOADER_STATE_SHELL_TRANSITIONAL_BEHAVIOR_MIRROR: frozenset(
    {
      "_approach_prev_dme_m",
      "_approach_prev_gs_abs",
      "_approach_prev_loc_abs",
      "mission_phase_name",
      "post_waypoint_transition",
    }
  ),
  SCENARIO_LOADER_STATE_SHELL_BLOCKED_OWNER_CANDIDATE: frozenset(
    {
      "leader_intent",
      "pilot_report",
      "task_order",
    }
  ),
}


def _runtime_escape_hatch_counts(path: Path) -> tuple[int, int, int]:
  tree = ast.parse(path.read_text(encoding="utf-8"))
  runtime_calls = 0
  runtime_world_calls = 0
  world_batch_ctor_calls = 0

  class Visitor(ast.NodeVisitor):
    def visit_Call(self, node: ast.Call) -> None:
      nonlocal runtime_calls, runtime_world_calls, world_batch_ctor_calls
      func = node.func
      if (
        isinstance(func, ast.Attribute)
        and isinstance(func.value, ast.Name)
        and func.value.id == "ef_py"
        and func.attr == "WorldBatchRuntime"
      ):
        world_batch_ctor_calls += 1
      if isinstance(func, ast.Attribute) and func.attr == "runtime_compatibility_quarantine":
        runtime_calls += 1
      if (
        isinstance(func, ast.Attribute)
        and func.attr == "world_raw_quarantine"
        and isinstance(func.value, ast.Call)
        and isinstance(func.value.func, ast.Attribute)
        and func.value.func.attr == "runtime_compatibility_quarantine"
      ):
        runtime_world_calls += 1
      self.generic_visit(node)

  Visitor().visit(tree)
  return runtime_calls, runtime_world_calls, world_batch_ctor_calls


__all__ = tuple(name for name in globals() if not name.startswith("__"))
