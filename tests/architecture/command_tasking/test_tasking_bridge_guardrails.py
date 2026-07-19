from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PRODUCTION_EF_PY_ROOTS = (
  REPO_ROOT / "python" / "rl",
  REPO_ROOT / "python" / "scenario",
  REPO_ROOT / "gym_envs" / "scenario_loader",
)
EF_PY_ASSIGNMENT_RE = re.compile(r"^\s*ef_py\s*=", re.MULTILINE)


def _read(relative_path: str) -> str:
  return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _production_ef_py_assignment_sites() -> list[str]:
  offenders: list[str] = []
  for root in PRODUCTION_EF_PY_ROOTS:
    for path in root.rglob("*.py"):
      text = path.read_text(encoding="utf-8")
      if EF_PY_ASSIGNMENT_RE.search(text):
        offenders.append(path.relative_to(REPO_ROOT).as_posix())
  return sorted(offenders)


def test_leader_tasking_routes_maintained_kernel_dispatch_through_bridge() -> None:
  text = _read("python/rl/tasking/leader_tasking.py")
  assert "_air_profile.build_kernel_mission_command(loader)" not in text
  assert "return _bridge_build_kernel_mission_command(loader)" in text


def test_leader_tasking_does_not_raw_write_command_chain_entities() -> None:
  text = _read("python/rl/tasking/leader_tasking.py")
  for forbidden in (
    "loader.sim.set_task_order(",
    "loader.sim.set_leader_intent(",
    "loader.sim.set_pilot_report(",
  ):
    assert forbidden not in text
  assert "sync_loader_command_chain(loader)" in text


def test_maintained_tasking_consumes_typed_mission_command_helpers() -> None:
  leader_text = _read("python/rl/tasking/leader_tasking.py")
  runtime_state_text = _read("gym_envs/scenario_loader/runtime_state.py")
  loading_text = _read("gym_envs/scenario_loader/loading.py")

  assert 'getattr(loader, "mission_cmd", {})' not in leader_text
  assert 'getattr(loader, "mission_cmd", None)' not in runtime_state_text
  assert "mission_command_view(loader)" in leader_text
  assert "mission_command_view(loader)" in runtime_state_text
  assert "mission_command_dict(loader)" in loading_text


def test_policy_state_reads_route_maintained_loader_owned_seam() -> None:
  # I24 (W2 critical period) moved the loader-owned policy-state-read seam into the
  # neutral `python.tasking_contracts.bridge_views` module so gym_envs no longer has
  # to import python.rl for it. `python/rl/tasking/bridge.py` re-exports the exact
  # same objects (see the compat-shim assertIs test in tests/architecture/tasking_contracts/),
  # so this gate now checks the canonical definitions there and pins the bridge.py
  # shell import as the compatibility half of the contract.
  leader_text = _read("python/rl/tasking/leader_tasking.py")
  bridge_text = _read("python/rl/tasking/bridge.py")
  bridge_views_text = _read("python/tasking_contracts/bridge_views.py")
  loader_text = _read("gym_envs/scenario_loader/core.py")
  loading_text = _read("gym_envs/scenario_loader/loading.py")

  assert "def get_policy_agent_observation(loader: Any, agent_id: Any | None = None) -> Any:" in bridge_views_text
  assert "def get_policy_instrument_state(loader: Any, agent_id: Any | None = None) -> Any:" in bridge_views_text
  assert "    get_policy_agent_observation," in bridge_text
  assert "    get_policy_instrument_state," in bridge_text
  assert "def get_policy_agent_observation(self, agent_id: int | None = None):" in loader_text
  assert "def get_policy_instrument_state(self, agent_id: int | None = None):" in loader_text
  assert "get_policy_agent_observation(loader)" in leader_text
  assert "get_policy_instrument_state(loader)" in leader_text
  assert "get_policy_agent_observation(loader)" in loading_text
  assert "get_policy_instrument_state(loader)" in loading_text
  assert "read_loader_truth_compat(loader)" not in leader_text
  assert "read_loader_instrument_compat(loader)" not in leader_text
  assert "read_loader_truth_compat(loader)" not in loading_text
  assert "read_loader_instrument_compat(loader)" not in loading_text
  assert "apply_loader_owned_world_layout_to_kernel(loader, world_layout)" in loading_text
  assert "def apply_loader_owned_world_layout_to_kernel(loader: Any, layout: Any) -> Any:" in bridge_views_text
  assert "    apply_loader_owned_world_layout_to_kernel," in bridge_text
  assert "apply_world_layout_to_kernel(loader.sim, world_layout)" not in loading_text


def test_common_core_profile_no_longer_defaults_or_exports_air_only_profile_logic() -> None:
  text = _read("python/rl/tasking/common_core_profile.py")
  resolver_slice = text[text.index("def _profile_name_from_context(") : text.index("def _infer_common_task_family(")]

  assert 'return "air"' not in resolver_slice
  assert "return _COMMON_PROFILE_NAME" in text
  assert 'raise ValueError(f"Unknown tasking profile: {raw!r}")' in text
  assert "def infer_air_task_family(" not in text
  assert "def infer_air_task_type(" not in text
  assert "def resolved_task_family(" not in text
  assert "def is_patrol_task(" not in text
  assert "def is_recover_task(" not in text


def test_bridge_quarantines_legacy_command_chain_raw_writes_to_single_owner_seam() -> None:
  # I24 (W2 critical period) moved the loader-owned runtime view / command-chain sync
  # seam into the neutral `python.tasking_contracts.bridge_views` module (canonical
  # owner below); `python/rl/tasking/bridge.py` keeps re-exporting it as the exact
  # same object (compat-shim assertIs test in tests/architecture/tasking_contracts/).
  text = _read("python/tasking_contracts/bridge_views.py")
  bridge_text = _read("python/rl/tasking/bridge.py")
  assert "class LoaderOwnedRuntimeView:" in text
  assert "def loader_owned_runtime_view(loader: Any) -> LoaderOwnedRuntimeView:" in text
  assert "def _sync_loader_command_chain_via_runtime_view(loader: Any) -> None:" in text
  assert "def sync_loader_command_chain(loader: Any) -> None:" in text
  assert "runtime_view.sync_task_order(loader.agent_id, getattr(loader, \"task_order\", None))" in text
  assert "runtime_view.sync_leader_intent(loader.agent_id, getattr(loader, \"leader_intent\", None))" in text
  assert "runtime_view.sync_pilot_report(loader.agent_id, getattr(loader, \"pilot_report\", None))" in text
  assert "LoaderOwnedRawSimCompatibilityFacade" not in text
  assert "loader_owned_raw_sim_compat" not in text
  assert "loader.sim.set_task_order(" not in text
  assert "loader.sim.set_leader_intent(" not in text
  assert "loader.sim.set_pilot_report(" not in text
  assert "    LoaderOwnedRuntimeView," in bridge_text
  assert "    loader_owned_runtime_view," in bridge_text
  assert "    sync_loader_command_chain," in bridge_text
  assert "LoaderOwnedRawSimCompatibilityFacade" not in bridge_text
  assert "loader_owned_raw_sim_compat" not in bridge_text
  assert "loader.sim.set_task_order(" not in bridge_text
  assert "loader.sim.set_leader_intent(" not in bridge_text
  assert "loader.sim.set_pilot_report(" not in bridge_text


def test_wp22_bans_production_ef_py_assignment_but_allows_test_local_stubs() -> None:
  offenders = _production_ef_py_assignment_sites()
  assert not offenders, (
    "WP22-B keeps `ef_py =` monkey patching out of production tasking/profile "
    "sources; test-local stubs in diagnostics/runtime fixtures are not counted "
    f"as maintained-business blockers: {offenders}"
  )
