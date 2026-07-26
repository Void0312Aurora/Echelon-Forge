"""Gates for the typed ``ScenarioLoader.sim`` seam (this iteration).

The seam contract lives in ``python/tasking_contracts/runtime_contract.py``
(a pure-stdlib ``typing.Protocol`` named ``ScenarioLoaderRuntime``). This
module enforces, in order:

1. **Census drift gate** — the module-docstring census in
   ``runtime_contract.py`` is mirrored here as a fixture of stable text
   needles (method -> caller file + exact source text). If a maintained
   caller's access through the ``sim`` handle changes, the fixture (and the
   census docstring) must be updated with it.
2. **Proxy conformance** — the maintained facade-backed
   ``_ScenarioLoaderRuntimeProxy`` structurally implements the protocol:
   member-for-member presence, exact ``inspect.signature`` equality, a
   ``runtime_checkable`` ``isinstance`` check, and deliberate *omission* of
   the absence-tolerated optional methods.
3. **Maintained-injection gate** — the maintained business trees construct
   ``ScenarioLoader`` only through the facade proxy
   (``ScenarioLoader(self._scenario_loader_runtime(int(index)))`` in
   ``python/rl/runtime/world_batch/adapter.py``). Raw-kernel injection stays
   confined to ``tests/**`` and the test-contract harness ``python/testing/**``
   (plus offline diagnostics under ``tools/``, which are outside the
   maintained scope by the same convention as the WP22 batch-runtime gates).
4. **Neutral-layer import gate** — ``runtime_contract.py`` imports stdlib
   ``typing``/``__future__`` only: no ``ef_py``, ``numpy``, ``gym_envs`` or
   ``python.rl``, keeping the neutral layer dependency-terminal (G2) and
   adding no ``gym_envs -> python.rl`` edge.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

from tests.architecture.helpers import ensure_repo_root_on_sys_path
from tests.support.paths import REPO_ROOT

ensure_repo_root_on_sys_path()

RUNTIME_CONTRACT_PATH = REPO_ROOT / "python" / "tasking_contracts" / "runtime_contract.py"
WORLD_BATCH_ADAPTER_PATH = REPO_ROOT / "python" / "rl" / "runtime" / "world_batch" / "adapter.py"


# --- 1. Census fixture: method -> [(repo-relative file, exact text needle)] ---
# Mirrors the census section of python/tasking_contracts/runtime_contract.py's
# module docstring by stable source text instead of line numbers.
REQUIRED_METHOD_CALLER_CENSUS: dict[str, list[tuple[str, str]]] = {
    "get_agent_observation": [
        ("gym_envs/scenario_loader/core.py", "return self.sim.get_agent_observation(resolved_agent_id)"),
        ("gym_envs/scenario_loader/execution_runtime/mainline.py", "truth = sim.get_agent_observation(loader.agent_id)"),
        ("gym_envs/universal_env_parts/info.py", "sim.get_agent_observation(agent_id)"),
        ("python/tasking_contracts/bridge_views.py", 'return self.call_optional("get_agent_observation", int(entity_id))'),
        ("python/tasking_contracts/bridge_views.py", 'return self._call("get_agent_observation", int(entity_id))'),
        ("gym_envs/observation_view.py", "return reader.get_agent_observation(entity_id)"),
        (
            "gym_envs/leader_env_parts/execution_runtime/policy_runtime.py",
            "truth_now = env.unwrapped.sim.get_agent_observation(env.unwrapped.agent_id)",
        ),
    ],
    "get_instrument_state": [
        ("gym_envs/scenario_loader/core.py", "return self.sim.get_instrument_state(resolved_agent_id)"),
        ("gym_envs/scenario_loader/execution_runtime/mainline.py", "sim.get_instrument_state(loader.agent_id)"),
        ("gym_envs/universal_env_parts/info.py", "sim.get_instrument_state(agent_id)"),
        ("python/tasking_contracts/bridge_views.py", 'return self.call_optional("get_instrument_state", int(entity_id))'),
        (
            "gym_envs/leader_env_parts/execution_runtime/policy_runtime.py",
            "inst_now = env.unwrapped.sim.get_instrument_state(env.unwrapped.agent_id)",
        ),
    ],
    "get_time_step": [
        ("python/tasking_contracts/bridge_views.py", 'self.call_optional("get_time_step", default=float(default))'),
        ("python/rl/control/wrappers.py", 'getattr(self.unwrapped.sim, "get_time_step", lambda: 0.05)()'),
        ("gym_envs/leader_env_parts/runtime_facade.py", "float(self.unwrapped.sim.get_time_step())"),
        ("gym_envs/leader_env_parts/scripted_exec.py", 'getattr(self.env.unwrapped.sim, "get_time_step", lambda: 0.05)()'),
        ("gym_envs/leader_env_parts/decision_runtime/observations.py", "float(env.unwrapped.sim.get_time_step())"),
    ],
    "is_unit_active": [
        ("python/tasking_contracts/bridge_views.py", 'return bool(self.call_optional("is_unit_active", int(entity_id), default=False))'),
        ("python/tasking_contracts/bridge_views.py", 'return bool(self._call("is_unit_active", int(entity_id), default=False))'),
        ("gym_envs/scenario_loader/behavior_runtime/naval_screen.py", "runtime_view.is_unit_active(last_reference_entity_id)"),
        ("gym_envs/scenario_loader/reward_runtime/air_combat.py", 'hasattr(sim, "is_unit_active")'),
    ],
    "get_unit_position": [
        ("python/tasking_contracts/bridge_views.py", 'return self.call_optional("get_unit_position", int(entity_id))'),
        ("python/tasking_contracts/bridge_views.py", 'return self._call("get_unit_position", int(entity_id))'),
        ("gym_envs/scenario_loader/behavior_runtime/naval_screen.py", "ref_pos = runtime_view.get_unit_position(int(entity_id))"),
        ("gym_envs/observation_view.py", "return reader.get_unit_position(entity_id)"),
    ],
    "set_command": [
        ("python/tasking_contracts/bridge_views.py", '"set_command",'),
    ],
    "fire_missile": [
        ("python/tasking_contracts/bridge_views.py", 'self.call_optional("fire_missile", int(entity_id), int(target_id), default=0)'),
        ("python/tasking_contracts/bridge_views.py", 'self._call("fire_missile", int(entity_id), int(target_id), default=0)'),
    ],
    "set_mission_command": [
        ("python/tasking_contracts/bridge_views.py", 'self.call_optional("set_mission_command", agent_id, cmd)'),
        ("gym_envs/scenario_loader/behavior_runtime/command_chain.py", 'loader_owned_runtime_view(loader).supports("set_mission_command")'),
    ],
    "set_task_order": [
        ("python/tasking_contracts/bridge_views.py", 'self.call_optional("set_task_order", agent_id, task_order)'),
    ],
    "set_leader_intent": [
        ("python/tasking_contracts/bridge_views.py", 'self.call_optional("set_leader_intent", agent_id, leader_intent)'),
    ],
    "set_pilot_report": [
        ("python/tasking_contracts/bridge_views.py", 'self.call_optional("set_pilot_report", agent_id, pilot_report)'),
    ],
}

OPTIONAL_METHOD_CALLER_CENSUS: dict[str, list[tuple[str, str]]] = {
    "get_unit_velocity": [
        ("python/tasking_contracts/bridge_views.py", 'return self.call_optional("get_unit_velocity", int(entity_id))'),
        ("gym_envs/scenario_loader/behavior_runtime/naval_screen.py", "ref_vel = runtime_view.get_unit_velocity(int(entity_id))"),
    ],
    "get_unit_messages": [
        ("gym_envs/scenario_loader/reward_runtime/naval.py", 'hasattr(sim, "get_unit_messages")'),
        ("gym_envs/observation_view.py", 'runtime_view.call_optional("get_unit_messages", entity_id, default=[])'),
    ],
    "export_recent_engagement_events": [
        ("gym_envs/scenario_loader/reward_runtime/air_combat.py", 'hasattr(sim, "export_recent_engagement_events")'),
    ],
    "get_unit_health": [
        ("gym_envs/scenario_loader/reward_runtime/objectives.py", 'hasattr(sim, "get_unit_health")'),
    ],
    "debug_get_aircraft_damage_state": [
        ("gym_envs/scenario_loader/reward_runtime/air_combat.py", 'hasattr(sim, "debug_get_aircraft_damage_state")'),
    ],
    "debug_get_ground_contact_state": [
        ("gym_envs/scenario_loader/reward_runtime/air_combat.py", 'hasattr(sim, "debug_get_ground_contact_state")'),
    ],
}

# Named re-exposure routes of the same handle (census section "Access routes").
SIM_HANDLE_ROUTE_CENSUS: list[tuple[str, str]] = [
    ("python/rl/runtime/world_batch/runtime_support.py", 'return getattr(loader, "sim")'),
    ("python/rl/runtime/leader_world_batch_runtime.py", "return self.loader.sim"),
    ("python/rl/runtime/world_batch/runtime_access.py", "return self.loader(env_idx).sim"),
    ("python/tasking_contracts/bridge_views.py", 'return getattr(self._loader, "sim", None)'),
]


def _assert_needles_present(census: dict[str, list[tuple[str, str]]]) -> None:
    missing: list[tuple[str, str, str]] = []
    for method, callers in census.items():
        for rel, needle in callers:
            text = (REPO_ROOT / rel).read_text(encoding="utf-8")
            if needle not in text:
                missing.append((method, rel, needle))
    assert not missing, (
        "ScenarioLoader.sim seam census drifted; update the fixture AND the census "
        f"docstring in python/tasking_contracts/runtime_contract.py: {missing}"
    )


def test_sim_seam_required_method_census_needles_are_current() -> None:
    _assert_needles_present(REQUIRED_METHOD_CALLER_CENSUS)


def test_sim_seam_optional_method_census_needles_are_current() -> None:
    _assert_needles_present(OPTIONAL_METHOD_CALLER_CENSUS)


def test_sim_seam_handle_route_census_needles_are_current() -> None:
    missing = [
        (rel, needle)
        for rel, needle in SIM_HANDLE_ROUTE_CENSUS
        if needle not in (REPO_ROOT / rel).read_text(encoding="utf-8")
    ]
    assert not missing, f"sim-handle re-exposure routes drifted; update the census: {missing}"


def test_census_fixture_matches_contract_method_sets() -> None:
    from python.tasking_contracts.runtime_contract import (
        SCENARIO_LOADER_RUNTIME_OPTIONAL_METHODS,
        SCENARIO_LOADER_RUNTIME_REQUIRED_METHODS,
    )

    assert set(REQUIRED_METHOD_CALLER_CENSUS) == set(SCENARIO_LOADER_RUNTIME_REQUIRED_METHODS)
    assert set(OPTIONAL_METHOD_CALLER_CENSUS) == set(SCENARIO_LOADER_RUNTIME_OPTIONAL_METHODS)
    assert not (
        SCENARIO_LOADER_RUNTIME_REQUIRED_METHODS & SCENARIO_LOADER_RUNTIME_OPTIONAL_METHODS
    )


# --- 2. Proxy conformance -----------------------------------------------------


def _protocol_members() -> set[str]:
    from python.tasking_contracts.runtime_contract import ScenarioLoaderRuntime

    return {
        name
        for name, member in vars(ScenarioLoaderRuntime).items()
        if not name.startswith("_") and callable(member)
    }


def test_protocol_members_match_required_method_set() -> None:
    from python.tasking_contracts.runtime_contract import (
        SCENARIO_LOADER_RUNTIME_REQUIRED_METHODS,
    )

    assert _protocol_members() == set(SCENARIO_LOADER_RUNTIME_REQUIRED_METHODS)


def test_scenario_loader_runtime_proxy_defines_every_protocol_method_directly() -> None:
    from python.rl.runtime.world_batch.adapter import _ScenarioLoaderRuntimeProxy

    proxy_class_members = vars(_ScenarioLoaderRuntimeProxy)
    missing = [name for name in sorted(_protocol_members()) if name not in proxy_class_members]
    assert not missing, (
        "_ScenarioLoaderRuntimeProxy must implement the maintained sim-seam protocol "
        f"as real class methods (its __getattr__ raises): missing {missing}"
    )


def test_scenario_loader_runtime_proxy_signatures_match_protocol_exactly() -> None:
    from python.rl.runtime.world_batch.adapter import _ScenarioLoaderRuntimeProxy
    from python.tasking_contracts.runtime_contract import ScenarioLoaderRuntime

    mismatched: list[tuple[str, str, str]] = []
    for name in sorted(_protocol_members()):
        protocol_sig = inspect.signature(getattr(ScenarioLoaderRuntime, name))
        proxy_sig = inspect.signature(getattr(_ScenarioLoaderRuntimeProxy, name))
        if protocol_sig != proxy_sig:
            mismatched.append((name, str(protocol_sig), str(proxy_sig)))
    assert not mismatched, f"proxy/protocol signature drift: {mismatched}"


def test_scenario_loader_runtime_proxy_satisfies_runtime_checkable_protocol() -> None:
    from python.rl.runtime.world_batch.adapter import _ScenarioLoaderRuntimeProxy
    from python.tasking_contracts.runtime_contract import ScenarioLoaderRuntime

    proxy = _ScenarioLoaderRuntimeProxy(object(), 0)
    assert isinstance(proxy, ScenarioLoaderRuntime)
    # Sanity: the runtime check actually discriminates.
    assert not isinstance(object(), ScenarioLoaderRuntime)


def test_scenario_loader_runtime_proxy_deliberately_omits_optional_methods() -> None:
    from python.rl.runtime.world_batch.adapter import _ScenarioLoaderRuntimeProxy
    from python.tasking_contracts.runtime_contract import (
        SCENARIO_LOADER_RUNTIME_OPTIONAL_METHODS,
    )

    proxy = _ScenarioLoaderRuntimeProxy(object(), 0)
    present = [
        name
        for name in sorted(SCENARIO_LOADER_RUNTIME_OPTIONAL_METHODS)
        if hasattr(proxy, name)
    ]
    assert not present, (
        "optional sim-seam methods are absence-tolerated by every caller and the "
        "maintained proxy deliberately omits them; growing one is a reviewed, "
        f"opt-in decision, not a drive-by: {present}"
    )


# --- 3. Maintained-injection gate --------------------------------------------

_MAINTAINED_PROXY_CONSTRUCTION = "ScenarioLoader(self._scenario_loader_runtime(int(index)))"


def _count_scenario_loader_constructions(path: Path) -> int:
    """AST count of ``ScenarioLoader(...)`` / ``*.ScenarioLoader(...)`` calls.

    AST-based so docstring/comment mentions (e.g. the census in
    runtime_contract.py) never count as construction sites.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    count = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id == "ScenarioLoader":
            count += 1
        elif isinstance(func, ast.Attribute) and func.attr == "ScenarioLoader":
            count += 1
    return count


def _iter_maintained_business_python_files() -> list[Path]:
    roots = [REPO_ROOT / "gym_envs", REPO_ROOT / "python", REPO_ROOT / "scripts"]
    files = [
        REPO_ROOT / "train.py",
        REPO_ROOT / "evaluate.py",
        REPO_ROOT / "world_model_train.py",
    ]
    testing_root = REPO_ROOT / "python" / "testing"
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            if path.is_relative_to(testing_root):
                # python/testing/** is the test-contract harness: raw-kernel
                # ScenarioLoader(sim) injection is explicitly test-only there.
                continue
            files.append(path)
    return [path for path in files if path.is_file()]


def test_maintained_paths_construct_scenario_loader_only_through_the_facade_proxy() -> None:
    construction_sites: dict[str, int] = {}
    for path in _iter_maintained_business_python_files():
        count = _count_scenario_loader_constructions(path)
        if count:
            construction_sites[path.relative_to(REPO_ROOT).as_posix()] = count

    assert construction_sites == {"python/rl/runtime/world_batch/adapter.py": 1}, (
        "maintained business paths must inject ScenarioLoader.sim only via the "
        "facade-backed _ScenarioLoaderRuntimeProxy; raw-kernel injection belongs "
        f"under tests/ or python/testing/ only. found: {construction_sites}"
    )

    adapter_source = WORLD_BATCH_ADAPTER_PATH.read_text(encoding="utf-8")
    assert _MAINTAINED_PROXY_CONSTRUCTION in adapter_source


# --- 4. Neutral-layer import gate --------------------------------------------

_ALLOWED_CONTRACT_IMPORT_ROOTS = {"__future__", "typing"}


def test_runtime_contract_module_imports_stdlib_typing_only() -> None:
    tree = ast.parse(RUNTIME_CONTRACT_PATH.read_text(encoding="utf-8"))
    offenders: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root not in _ALLOWED_CONTRACT_IMPORT_ROOTS:
                    offenders.append((node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            root = module.split(".", 1)[0]
            if node.level > 0 or root not in _ALLOWED_CONTRACT_IMPORT_ROOTS:
                offenders.append((node.lineno, f"from {'.' * node.level}{module}"))
    assert not offenders, (
        "python/tasking_contracts/runtime_contract.py must stay dependency-terminal "
        "(stdlib typing only; no ef_py/numpy/gym_envs/python.rl, no relative imports): "
        f"{offenders}"
    )


def test_runtime_contract_module_never_mentions_ef_py_or_side_packages_in_code() -> None:
    tree = ast.parse(RUNTIME_CONTRACT_PATH.read_text(encoding="utf-8"))
    names: set[str] = {
        node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
    }
    forbidden = {"ef_py", "gym_envs", "numpy", "np"}
    assert not (names & forbidden), (
        f"runtime_contract.py references forbidden runtime packages: {sorted(names & forbidden)}"
    )
