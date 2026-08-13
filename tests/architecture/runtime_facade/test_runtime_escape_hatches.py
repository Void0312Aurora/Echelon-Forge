from __future__ import annotations

from tests.architecture.runtime_facade.helpers import *


def test_world_batch_adapter_removes_direct_runtime_fallback() -> None:
  runtime_calls, runtime_world_calls, world_batch_ctor_calls = _runtime_escape_hatch_counts(WORLD_BATCH_ADAPTER)
  assert runtime_calls == 0
  assert runtime_world_calls == 0
  assert world_batch_ctor_calls == 0

def test_world_batch_adapter_keeps_runtime_escape_hatch_deleted() -> None:
  source = _adapter_source()
  assert "self.facade.runtime_compatibility_quarantine() if self.facade is not None" not in source
  assert "runtime_compatibility_quarantine()" not in source
  assert "self._compat_runtime = ef_py.WorldBatchRuntime" not in source
  assert "ef_py.WorldBatchRuntime(" not in source
  assert "self.facade = None" not in source
  assert "self.facade = ef_py.RuntimeFacade(self._world_count)" in source
  assert "def _compat_runtime_handle(self):" not in source
  assert "def _compat_world(self, index: int):" not in source
  assert "def world(self, index: int):" not in source
  assert "def world_raw_quarantine(self, index: int):" not in source
  assert "class _WorldAccessProxy:" not in source
  assert "def _scenario_loader_runtime(self, index: int) -> _ScenarioLoaderRuntimeProxy:" in source
  assert "def _build_runtime_world_layout_request(self, world_index: int, layout: Any):" in source
  assert "def _apply_runtime_world_layout_request(self, request: Any) -> Any:" in source
  assert "def _materialize_applied_world(self, world_index: int, layout: Any, entity_ids: Sequence[Any]) -> AppliedScenarioWorld:" in source
  assert "self._compat_runtime = self.facade.runtime_compatibility_quarantine()" not in source
  assert "self._compat_runtime = None" not in source
  assert "self._compat_runtime_handle().world_raw_quarantine(int(index))" not in source
  assert "return _WorldAccessProxy(self, int(index))" not in source
  assert "apply_world_layout_to_kernel(self.world_raw_quarantine(int(world_index)), layout)" not in source
  assert "ScenarioLoader(self.world_raw_quarantine(int(index)))" not in source
  assert "ScenarioLoader(self._compat_world(int(index)))" not in source
  assert "ScenarioLoader(self._scenario_loader_runtime(int(index)))" in source
  assert "self.world_raw_quarantine(int(world_index)).get_time_step()" not in source
  assert "self.world_raw_quarantine(int(world_index)).get_visual_observation(" not in source
  assert 'hasattr(self.world_raw_quarantine(int(world_index)), "get_visual_observation_downsampled")' not in source
  assert "def get_visual_observation(" not in source
  assert "def get_visual_observation_downsampled(" not in source
  assert "def supports_visual_observation_downsampled(" not in source
  assert "RuntimeFacadeAdapter.legacy_visual_observation" not in source
  assert "return build_runtime_world_layout_request(" in source
  assert "return apply_runtime_world_layout_request_maintained(self.facade, request)" in source
  assert "apply_runtime_world_layout_request_compatibility_quarantine(" not in source
  assert "runtime_compatibility_required_message(" not in source
  assert "result = self._apply_runtime_world_layout_request(request)" in source
  assert "self.facade.world_time_step(int(world_index))" in source
  assert "batch_target = self.facade if self.facade is not None else self._compat_runtime_handle()" not in source
  assert "self.facade," in source
  assert "compute_world_batch_visual_observation_batch_numpy(" in source
  assert "compute_world_batch_visual_observation_batch_export(" in source
  step_worlds_section = source.split("def step_worlds(self, world_indices: Sequence[int]) -> None:", 1)[1].split(
    "def set_mission_commands_maintained_batch",
    1,
  )[0]
  assert "self.facade.step_batch()" in step_worlds_section
  assert "runtime_compatibility_required_message(" not in step_worlds_section
  assert "self._compat_runtime_handle().step_worlds(indices)" not in step_worlds_section
  assert "requires a full facade-owned batch step" in step_worlds_section

def test_runtime_facade_escape_hatch_allowlist_stays_explicit() -> None:
  actual = {}
  for path in [
    WORLD_BATCH_ADAPTER,
    REPO_ROOT / "tests" / "runtime" / "facade" / "test_runtime_facade_core.py",
    REPO_ROOT / "tests" / "runtime" / "engagement" / "test_facade_engagement_export.py",
    REPO_ROOT / "tests" / "runtime" / "engagement" / "test_live_engagement_event_capture.py",
    REPO_ROOT / "tests" / "runtime" / "engagement" / "test_facade_engagement_evidence_gates.py",
    REPO_ROOT / "tests" / "runtime" / "engagement" / "test_trace_replay_gates.py",
  ]:
    counts = _runtime_escape_hatch_counts(path)
    if any(counts):
      allowlist_key = path.relative_to(REPO_ROOT).as_posix()
      actual[allowlist_key] = EscapeHatchAllowance(
        runtime_calls=counts[0],
        runtime_world_calls=counts[1],
        world_batch_ctor_calls=counts[2],
        classification=SCOPED_ESCAPE_HATCH_ALLOWLIST[allowlist_key].classification,
        tier=SCOPED_ESCAPE_HATCH_ALLOWLIST[allowlist_key].tier,
      )

  assert actual == SCOPED_ESCAPE_HATCH_ALLOWLIST, f"scoped escape hatch allowlist drifted: {actual}"

def test_world_batch_adapter_is_only_maintained_escape_hatch_in_scope() -> None:
  maintained = {
    path: allowance
    for path, allowance in SCOPED_ESCAPE_HATCH_ALLOWLIST.items()
    if allowance.tier == "maintained_training_path"
  }
  assert maintained == {}

def test_world_batch_vec_env_does_not_branch_on_facade_presence_in_main_class() -> None:
  source = _source()
  main_class = source.split("class WorldBatchVecEnv", 1)[1]
  assert "_runtime_facade is not None" not in main_class
  assert "_runtime_facade is None" not in main_class

def test_world_batch_vec_env_main_class_does_not_cache_raw_runtime_handles() -> None:
  source = _source()
  main_class = source.split("class WorldBatchVecEnv", 1)[1]
  assert "_batch_runtime" not in main_class
  assert "_runtime_facade" not in main_class
  assert ".compat_runtime" not in main_class

def test_world_batch_vec_env_access_stays_thin_forwarder_without_raw_runtime_ownership() -> None:
  source = _runtime_access_source()
  assert ".batch_runtime." not in source
  assert ".runtime_compatibility_quarantine()" not in source
  assert ".world_raw_quarantine(" not in source
  assert "WorldBatchRuntime" not in source
  assert "RuntimeFacade" not in source

def test_leader_world_batch_runtime_does_not_reach_raw_world_handles() -> None:
  source = _leader_source()
  assert ".batch_runtime.world_raw_quarantine(" not in source
  assert ".world_vec.batch_runtime.world_raw_quarantine(" not in source

def test_leader_world_batch_runtime_keeps_batch_runtime_surface_removed() -> None:
  source = _leader_source()
  assert "def batch_runtime(self):" not in source
  assert ".batch_runtime" not in source

def test_world_batch_vec_env_batch_runtime_surface_is_removed_at_source() -> None:
  source = _source()
  cooperative_source = (REPO_ROOT / "python" / "rl" / "runtime" / "cooperative_world_batch_vec_env.py").read_text(
    encoding="utf-8"
  )
  assert "def batch_runtime(self):" not in source
  assert "def batch_runtime(self):" not in cooperative_source
  assert "_runtime_compat =" not in source
  assert "_runtime_compat =" not in cooperative_source
  assert "self._runtime_compat" not in source
  assert "self._runtime_compat" not in cooperative_source
  assert "RuntimeCompatibilityView" not in source
  assert "RuntimeCompatibilityView" not in cooperative_source

def test_maintained_paths_do_not_add_new_execution_episode_batch_runtime_reads() -> None:
  forbidden_markers = (
    ".batch_runtime.export_execution_episode_states_batch(",
    ".batch_runtime.execution_episode_controller_ready(",
  )
  violations: list[tuple[str, int, str]] = []
  allowlist = _maintained_execution_episode_compat_read_allowlist()

  for path in _iter_maintained_python_paths():
    rel = path.relative_to(REPO_ROOT).as_posix()
    if rel in allowlist:
      continue
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
      stripped = line.strip()
      if any(marker in stripped for marker in forbidden_markers):
        violations.append((rel, lineno, stripped))

  assert not violations, (
    "maintained paths must use vec-env/runtime facade execution-episode helpers instead of "
    f"compat batch_runtime reads: {violations}"
  )

def test_maintained_paths_do_not_add_new_batch_runtime_consumers_outside_compatibility_tests() -> None:
  violations: list[tuple[str, int, str]] = []
  allowlist = _compat_batch_runtime_consumer_allowlist()

  for path in _iter_maintained_facade_guard_paths():
    rel = path.relative_to(REPO_ROOT).as_posix()
    if rel in allowlist:
      continue
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
      stripped = line.strip()
      if ".batch_runtime." in stripped:
        violations.append((rel, lineno, stripped))

  assert not violations, (
    "maintained facade-layer paths must keep vec_env.batch_runtime consumers inside explicit "
    f"compatibility tests only: {violations}"
  )

def test_wp22_public_batch_runtime_consumers_stay_explicit_and_localized() -> None:
  allowlist = {
    "python/rl/runtime/cooperative_world_batch_vec_env.py",
    "python/rl/runtime/leader_world_batch_runtime.py",
    "python/rl/runtime/single_world_batch_runtime.py",
    "python/rl/runtime/world_batch/runtime_support.py",
    "python/rl/runtime/world_batch_vec_env.py",
    "tools/diagnostics/benchmarks/world_batch_vec_env.py",
    "train.py",
  }
  violations: list[tuple[str, int]] = []

  for path in _iter_non_test_python_paths():
    rel = path.relative_to(REPO_ROOT).as_posix()
    if rel in allowlist:
      continue
    for lineno in _batch_runtime_attribute_lines(path):
      violations.append((rel, lineno))

  assert not violations, (
    "WP22 maintained non-test Python paths must keep vec_env.batch_runtime inside the explicit "
    f"raw/diagnostics allowlist only: {violations}"
  )

def test_wp22_public_world_escape_hatch_consumers_stay_explicit_and_localized() -> None:
  allowlist = {
    "python/rl/runtime/world_batch/adapter.py",
  }
  violations: list[tuple[str, int]] = []

  for path in _iter_non_test_python_paths():
    rel = path.relative_to(REPO_ROOT).as_posix()
    if rel in allowlist:
      continue
    for lineno in _world_call_lines(path):
      violations.append((rel, lineno))

  assert not violations, (
    "WP22 maintained non-test Python paths must keep public `.world_raw_quarantine()` escape-hatch calls inside the explicit "
    f"raw escape-hatch allowlist only: {violations}"
  )

def test_maintained_paths_do_not_add_new_runtime_facade_runtime_consumers() -> None:
  allowlist = _runtime_escape_hatch_path_allowlist()
  violations: list[tuple[str, int, int]] = []

  for path in _iter_maintained_facade_guard_paths():
    rel = path.relative_to(REPO_ROOT).as_posix()
    runtime_calls, runtime_world_calls, _ = _runtime_escape_hatch_counts(path)
    if rel in allowlist:
      continue
    if runtime_calls or runtime_world_calls:
      violations.append((rel, runtime_calls, runtime_world_calls))

  assert not violations, (
    "maintained facade-layer paths must keep RuntimeFacade.runtime_compatibility_quarantine() escape hatches inside the "
    f"explicit raw/diagnostics allowlist only: {violations}"
  )

def test_wp22_loader_owned_runtime_paths_do_not_reintroduce_scattered_raw_sim_seams() -> None:
  scope = _wp22_loader_sim_guard_scope()
  violations: list[tuple[str, str]] = []

  for rel, markers in scope.items():
    text = (REPO_ROOT / rel).read_text(encoding="utf-8")
    for marker in markers:
      if marker in text:
        violations.append((rel, marker))

  assert not violations, (
    "WP22 maintained loader/runtime paths must use loader-owned seams or "
    f"explicit tasking compatibility helpers instead of scattered raw loader.sim access: {violations}"
  )

def test_wp22_naval_screen_raw_unit_state_seam_stays_named_and_localized() -> None:
  text = (REPO_ROOT / "gym_envs" / "scenario_loader" / "behavior_runtime" / "naval_screen.py").read_text(encoding="utf-8")
  bridge_text = TASKING_BRIDGE.read_text(encoding="utf-8")
  canonical_bridge_text = TASKING_BRIDGE_CANONICAL.read_text(encoding="utf-8")

  assert "def _read_naval_screen_reference_motion(" in text
  assert "def _prefer_last_active_naval_screen_reference(" in text
  assert "loader_owned_runtime_view(loader)" in text
  assert "loader_owned_raw_sim_compat" not in text
  assert "loader.sim.get_unit_position(" not in text
  assert "loader.sim.get_unit_velocity(" not in text
  assert "loader.sim.is_unit_active(" not in text
  for canonical_definition in (
    "class LoaderOwnedRuntimeView:",
    "def get_unit_position(self, entity_id: int) -> Any:",
    "def get_unit_velocity(self, entity_id: int) -> Any:",
    "def is_unit_active(self, entity_id: int) -> bool:",
  ):
    assert canonical_definition in canonical_bridge_text
    assert canonical_definition not in bridge_text
  for retired_marker in (
    "class LoaderOwnedRawSimCompatibilityFacade:",
    "def loader_owned_raw_sim_compat(",
  ):
    assert retired_marker not in canonical_bridge_text
    assert retired_marker not in bridge_text

def test_wp22_tasking_bridge_quarantines_raw_mission_and_command_chain_sync_helpers() -> None:
  text = TASKING_BRIDGE.read_text(encoding="utf-8")
  canonical_bridge_text = TASKING_BRIDGE_CANONICAL.read_text(encoding="utf-8")

  for canonical_definition in (
    "class LoaderOwnedRuntimeView:",
    "def loader_owned_runtime_view(loader: Any) -> LoaderOwnedRuntimeView:",
    "def sync_loader_mission_command(loader: Any, cmd: Any) -> None:",
    "def sync_loader_command_chain_reentrant(loader: Any) -> None:",
    "def sync_task_order(self, agent_id: Any, task_order: Any) -> None:",
    "def sync_leader_intent(self, agent_id: Any, leader_intent: Any) -> None:",
    "def sync_pilot_report(self, agent_id: Any, pilot_report: Any) -> None:",
    "def sync_mission_command(self, agent_id: Any, cmd: Any) -> None:",
  ):
    assert canonical_definition in canonical_bridge_text
    assert canonical_definition not in text
  for retired_marker in (
    "LoaderOwnedRawSimCompatibilityFacade",
    "loader_owned_raw_sim_compat",
    "sync_loader_command_chain_compat",
    "read_loader_truth_compat",
    "read_loader_instrument_compat",
    "loader.sim.set_mission_command(",
    "loader.sim.set_task_order(",
    "loader.sim.set_leader_intent(",
    "loader.sim.set_pilot_report(",
  ):
    assert retired_marker not in canonical_bridge_text
    assert retired_marker not in text

def test_wp22_scripted_opponent_kernel_access_stays_named_and_localized() -> None:
  text = (REPO_ROOT / "gym_envs" / "scenario_loader" / "behavior_runtime" / "scripted_opponents.py").read_text(
    encoding="utf-8"
  )
  bridge_text = TASKING_BRIDGE.read_text(encoding="utf-8")
  canonical_bridge_text = TASKING_BRIDGE_CANONICAL.read_text(encoding="utf-8")

  assert "loader_owned_scripted_opponent_kernel_view(loader)" in text
  assert "loader_owned_scripted_opponent_kernel_compat" not in text
  assert "loader.sim," not in text
  for canonical_definition in (
    "class LoaderOwnedScriptedOpponentKernelView:",
    "def loader_owned_scripted_opponent_kernel_view(loader: Any) -> LoaderOwnedScriptedOpponentKernelView:",
  ):
    assert canonical_definition in canonical_bridge_text
    assert canonical_definition not in bridge_text
  for retired_marker in (
    "class LoaderOwnedScriptedOpponentKernelCompat:",
    "def loader_owned_scripted_opponent_kernel_compat(",
  ):
    assert retired_marker not in canonical_bridge_text
    assert retired_marker not in bridge_text

def test_wp22_loading_world_layout_kernel_apply_stays_named_and_localized() -> None:
  text = (REPO_ROOT / "gym_envs" / "scenario_loader" / "loading.py").read_text(encoding="utf-8")
  bridge_text = TASKING_BRIDGE.read_text(encoding="utf-8")
  canonical_bridge_text = TASKING_BRIDGE_CANONICAL.read_text(encoding="utf-8")

  assert "apply_loader_owned_world_layout_to_kernel(loader, world_layout)" in text
  assert "apply_world_layout_to_kernel(loader.sim, world_layout)" not in text
  assert "loader.sim," not in text
  for canonical_definition in (
    "def apply_loader_owned_world_layout_to_kernel(loader: Any, layout: Any) -> Any:",
    "loader-owned world-layout kernel-apply seam",
  ):
    assert canonical_definition in canonical_bridge_text
    assert canonical_definition not in bridge_text
  for retired_marker in (
    "apply_world_layout_to_kernel(loader.sim",
    "loader.sim,",
  ):
    assert retired_marker not in canonical_bridge_text
    assert retired_marker not in bridge_text

def test_wp22_runtime_state_execution_episode_export_drops_empty_raw_loader_guard() -> None:
  text = (REPO_ROOT / "gym_envs" / "scenario_loader" / "runtime_state.py").read_text(encoding="utf-8")

  assert 'hasattr(loader.sim, "__class__")' not in text
  assert 'if not hasattr(__import__("ef_py"), "ExecutionEpisodeState"):' in text
  assert 'raise RuntimeError("ef_py.ExecutionEpisodeState is not available")' in text

def test_world_batch_runtime_support_names_loader_owned_reward_and_info_runtime_helpers() -> None:
  text = (REPO_ROOT / "python" / "rl" / "runtime" / "world_batch" / "runtime_support.py").read_text(encoding="utf-8")

  assert "def resolve_loader_runtime_sim(loader: Any) -> Any:" in text
  assert "def compute_loader_step_outcome(" in text
  assert "def build_loader_step_info(" in text
  assert "runtime_compatibility_enabled" not in text
  assert "runtime_compatibility_required_message" not in text

def test_leader_world_batch_runtime_does_not_call_runtime_facade_compatibility_quarantine() -> None:
  tree = ast.parse(_leader_source())
  violations: list[tuple[int, str]] = []

  class Visitor(ast.NodeVisitor):
    def visit_Call(self, node: ast.Call) -> None:
      func = node.func
      if isinstance(func, ast.Attribute) and func.attr == "runtime_compatibility_quarantine":
        violations.append((node.lineno, "runtime_compatibility_quarantine()"))
      self.generic_visit(node)

  Visitor().visit(tree)
  assert not violations, f"leader runtime escaped facade adapter layering: {violations}"

def test_runtime_facade_cpp_maintained_paths_do_not_drill_through_raw_runtime_or_world() -> None:
  source = runtime_facade_source_text()

  assert "runtime_->world_raw_quarantine(" not in source
  assert "runtime_compatibility_quarantine().world_raw_quarantine(" not in source
  assert "runtime()->world_raw_quarantine(" not in source
  assert "facade->runtime_compatibility_quarantine().world_raw_quarantine(" not in source
  assert ".kind = runtime::backend::SetupKind::Layout" in source
  assert ".include_world_time_step = true" in source
  assert "require_compatibility_port(*runtime_)" in source
  assert "collect_visual_binding_compatibility_scenes_from_candidate_ids_batch(" in source
  assert ".get_visual_candidate_ids_batch(" in source
  assert "runtime_->collect_visual_binding_compatibility_scenes_batch(" not in source

def test_wp22_gpu_visual_binding_routes_through_named_world_batch_compatibility_helper() -> None:
  source = _gpu_bindings_source()

  assert ".world_raw_quarantine(" not in source
  assert "RuntimeFacade" in source
  assert "compute_runtime_facade_visual_binding_outputs(" in source
  assert "compute_compat_world_batch_visual_binding_outputs(" in source
  assert "collect_visual_binding_compatibility_scenes_batch(" in source
  assert "render_scenes_batch(" in source

def test_wp22_world_batch_runtime_quarantines_visual_binding_raw_world_access() -> None:
  header = WORLD_BATCH_RUNTIME_H.read_text(encoding="utf-8")
  impl = WORLD_BATCH_RUNTIME_CPP.read_text(encoding="utf-8")
  helper = (
    REPO_ROOT / "src" / "core" / "engine" / "world_batch_visual_binding_compatibility_helper.h"
  ).read_text(encoding="utf-8")

  assert "collect_visual_binding_compatibility_scenes_from_candidate_ids_batch(" in header
  assert "collect_visual_binding_compatibility_scenes_batch(" in header
  assert "Raw escape hatch only." in header
  assert "own candidate-id assembly" in header
  assert "WorldBatchRuntime::collect_visual_binding_compatibility_scenes_from_candidate_ids_batch(" in impl
  assert "WorldBatchRuntime::collect_visual_binding_compatibility_scenes_batch(" in impl
  assert "failed to collect visual scene for world batch visual compatibility helper" in impl
  assert "collect_scene_from_candidate_ids(" in helper

def test_wp22_world_batch_runtime_routes_setup_orchestration_through_named_helper() -> None:
  impl = WORLD_BATCH_RUNTIME_CPP.read_text(encoding="utf-8")
  helper = (REPO_ROOT / "src" / "core" / "engine" / "world_batch_setup_helper.h").read_text(encoding="utf-8")

  assert '#include "core/engine/world_batch_setup_helper.h"' in impl
  assert "world_batch_setup::apply_world_setup(" in impl
  # 2026-08-13 dead-binding sweep: the standalone set_terrain_types_batch /
  # set_winds_batch / set_suns_batch / add_zones_batch entry points were removed
  # (zero python consumers), so the named-helper routing fact now lives in the
  # apply_world_setup orchestration chain inside the helper header itself.
  assert "apply_setup_wind_assignments(world, wind_assignments, wind_grouped_indices);" in helper
  assert "apply_setup_sun_assignments(world, sun_assignments, sun_grouped_indices);" in helper
  assert "replace_zones(world, zones, zone_grouped_indices);" in helper
  assert "inline void apply_setup_terrain_assignments(" in helper
  assert "world.set_terrain_type(WorldTerrainAssignment{}.terrain_type);" in helper
  assert "apply_setup_terrain_assignments(world, terrain_assignments, terrain_grouped_indices);" in helper
  apply_terrain_body = helper.split("inline void apply_terrain_assignments(", 1)[1].split(
    "inline void apply_setup_terrain_assignments(",
    1,
  )[0]
  assert "grouped_indices.empty()" not in apply_terrain_body

def test_runtime_facade_escape_hatch_is_documented() -> None:
  header = (REPO_ROOT / "src" / "runtime" / "facade" / "runtime_facade.h").read_text(encoding="utf-8")
  readme = (REPO_ROOT / "src" / "runtime" / "facade" / "README.md").read_text(encoding="utf-8")
  assert "runtime_compatibility_quarantine" not in header
  assert "no longer exposes a raw `WorldBatchRuntime` escape hatch" in readme
  assert "不得重新引入 `RuntimeFacade.runtime_compatibility_quarantine()`" in readme
  assert "must not cache raw `WorldBatchRuntime`" in readme
