from __future__ import annotations

import builtins
import importlib
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_PATH = REPO_ROOT / "python" / "simulation" / "backend.py"
SCRIPTED_ENTRYPOINTS = (
    REPO_ROOT / "tools" / "diagnostics" / "air_combat_scripted_demo.py",
    REPO_ROOT / "tools" / "diagnostics" / "air_combat_ew_scripted_demo.py",
    REPO_ROOT / "tools" / "diagnostics" / "air_ew_scripted_demo.py",
    REPO_ROOT / "tools" / "diagnostics" / "air_cooperative_combat_scripted_demo.py",
    REPO_ROOT / "tools" / "diagnostics" / "air_cooperative_ew_scripted_demo.py",
    REPO_ROOT / "tools" / "eval" / "naval_station_policy_eval.py",
)


class _FakeBackend:
    def seed(self, seed: int) -> int:
        return int(seed)

    def reset(self) -> dict[str, Any]:
        return {"ready": True}

    def step(self, actions: Any) -> tuple[Any, ...]:
        return actions, [], [False], [{}]

    def snapshot(self) -> dict[str, Any]:
        return {"ready": True}

    def close(self) -> None:
        return None


class _FakeExecutionRuntime:
    def reset(self, *, seed: int | None = None, options: dict[str, Any] | None = None) -> dict[str, Any]:
        return {"seed": seed, "options": options}

    def step(self, action: Any) -> tuple[Any, ...]:
        return action, 0.0, False, False, {}

    def close(self) -> None:
        return None


class _FakeCooperativeBackend(_FakeBackend):
    slots_per_world = 2

    def cooperative_slot_metadata(self):
        return (
            {"entity_name": "BlueLead", "formation_role_id": "Lead", "target_owner_name": "RedLead"},
            {"entity_name": "BlueWing", "formation_role_id": "Wingman", "target_owner_name": "RedWing"},
        )


def test_simulation_backend_import_is_dependency_terminal(monkeypatch: pytest.MonkeyPatch) -> None:
    original_import = builtins.__import__

    def reject_simulation_provider(name: str, *args: Any, **kwargs: Any):
        if name == "ef_py" or name == "gymnasium" or name == "python.rl" or name.startswith("python.rl."):
            raise AssertionError(f"simulation backend imported provider eagerly: {name}")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", reject_simulation_provider)
    module = importlib.import_module("python.simulation.backend")
    assert "python.rl" not in module.__dict__
    assert "ef_py" not in module.__dict__


def test_registered_backend_is_constructed_through_neutral_factory() -> None:
    module = importlib.import_module("python.simulation.backend")
    backend_id = "test.fake.simulation"
    registration = module.SimulationBackendRegistration(
        backend_id=backend_id,
        single_factory=_FakeBackend,
        cooperative_factory=_FakeBackend,
        execution_factory=_FakeBackend,
    )
    module.register_backend(registration)
    try:
        backend = module.create_single_backend(backend_id=backend_id)
        assert isinstance(backend, _FakeBackend)
        assert backend.seed(7) == 7
        assert backend.reset() == {"ready": True}
    finally:
        module._REGISTRATIONS.pop(backend_id, None)


def test_scenario_provider_has_an_explicit_setup_snapshot_factory() -> None:
    module = importlib.import_module("python.simulation.backend")
    backend_id = "test.native.scenario"
    module.register_backend(
        module.SimulationBackendRegistration(
            backend_id=backend_id,
            scenario_factory=_FakeBackend,
            implementation_owner="python.simulation.test_provider",
            requires_rl=False,
        )
    )
    try:
        backend = module.create_scenario_backend(backend_id=backend_id)
        assert isinstance(backend, module.SimulationScenarioBackend)
        assert backend.snapshot() == {"ready": True}
    finally:
        module._REGISTRATIONS.pop(backend_id, None)


def test_backend_registration_validates_dependency_ownership_metadata() -> None:
    module = importlib.import_module("python.simulation.backend")
    registration = module.SimulationBackendRegistration(
        backend_id="test.metadata.simulation",
        single_factory=_FakeBackend,
        implementation_owner="python.simulation.test_provider",
        requires_rl=False,
    )
    assert registration.implementation_owner == "python.simulation.test_provider"
    assert registration.requires_rl is False
    with pytest.raises(ValueError, match="implementation_owner"):
        module.SimulationBackendRegistration(
            backend_id="test.empty.owner",
            single_factory=_FakeBackend,
            implementation_owner=" ",
        )
    with pytest.raises(TypeError, match="requires_rl"):
        module.SimulationBackendRegistration(
            backend_id="test.invalid.requires_rl",
            single_factory=_FakeBackend,
            requires_rl=1,
        )


def test_builtin_provider_ownership_is_explicit_and_queryable(monkeypatch: pytest.MonkeyPatch) -> None:
    module = importlib.import_module("python.simulation.backend")
    module._REGISTRATIONS.pop("world_batch", None)
    module._REGISTRATIONS.pop("facade_batch", None)

    class _Provider:
        WorldBatchVecEnv = _FakeBackend
        CooperativeWorldBatchVecEnv = _FakeCooperativeBackend
        build_single_world_batch_execution_runtime = _FakeExecutionRuntime

    class _FacadeProvider:
        FacadeBatchBackend = _FakeBackend

    def load_provider(name: str):
        if name in {
            "python.rl.runtime.world_batch.vec_env",
            "python.rl.runtime.cooperative_world_batch_vec_env",
            "python.rl.runtime.single_world_batch_runtime",
        }:
            return _Provider()
        if name == "python.simulation.facade_batch":
            return _FacadeProvider()
        pytest.fail(name)

    monkeypatch.setattr(module, "import_module", load_provider)
    try:
        world_batch = module.get_backend_registration("world_batch")
        assert world_batch.implementation_owner == "python.rl.runtime"
        assert world_batch.requires_rl is True

        facade = module.get_backend_registration("facade_batch")
        assert facade.implementation_owner == "python.simulation.facade_batch"
        assert facade.requires_rl is False
        assert facade.scenario_factory is _FakeBackend
    finally:
        module._REGISTRATIONS.pop("world_batch", None)
        module._REGISTRATIONS.pop("facade_batch", None)


def test_builtin_backend_ids_cannot_be_shadowed_before_lazy_resolution() -> None:
    module = importlib.import_module("python.simulation.backend")
    registration = module.SimulationBackendRegistration(
        backend_id="world_batch",
        cooperative_factory=_FakeCooperativeBackend,
    )
    with pytest.raises(ValueError, match="reserved"):
        module.register_backend(registration)
    assert "world_batch" not in module._REGISTRATIONS


def test_cooperative_backend_exposes_provider_neutral_slot_metadata() -> None:
    module = importlib.import_module("python.simulation.backend")
    backend_id = "test.fake.cooperative"
    module.register_backend(
        module.SimulationBackendRegistration(
            backend_id=backend_id,
            cooperative_factory=_FakeCooperativeBackend,
        )
    )
    try:
        backend = module.create_cooperative_backend(backend_id=backend_id)
        assert isinstance(backend, module.SimulationCooperativeBatchBackend)
        assert backend.slots_per_world == 2
        assert backend.cooperative_slot_metadata()[1]["target_owner_name"] == "RedWing"
    finally:
        module._REGISTRATIONS.pop(backend_id, None)


def test_execution_only_provider_is_a_valid_backend_registration() -> None:
    module = importlib.import_module("python.simulation.backend")
    backend_id = "test.execution.only"
    module.register_backend(
        module.SimulationBackendRegistration(
            backend_id=backend_id,
            execution_factory=_FakeExecutionRuntime,
        )
    )
    try:
        runtime = module.create_single_execution_runtime(backend_id=backend_id)
        assert isinstance(runtime, _FakeExecutionRuntime)
        assert runtime.reset(seed=3)["seed"] == 3
    finally:
        module._REGISTRATIONS.pop(backend_id, None)


def test_execution_wrapper_spec_is_resolved_lazily_through_boundary(monkeypatch: pytest.MonkeyPatch) -> None:
    module = importlib.import_module("python.simulation.backend")
    calls: list[str] = []

    class _Provider:
        @staticmethod
        def get_action_wrapper_spec(config: dict[str, Any]):
            calls.append(str(config["mode"]))
            return object, {"mode": config["mode"]}

    def load_provider(name: str):
        if name == "python.rl.control.wrappers":
            return _Provider()
        pytest.fail(name)

    monkeypatch.setattr(module, "import_module", load_provider)
    assert module.resolve_execution_wrapper_spec({"mode": "test"}) == (object, {"mode": "test"})
    assert calls == ["test"]


def test_leader_window_runtime_selection_is_provider_lazy(monkeypatch: pytest.MonkeyPatch) -> None:
    module = importlib.import_module("python.simulation.backend")

    class _Local:
        def __init__(self, env: Any):
            self.env = env

    class _WorldBatch(_Local):
        pass

    class _Provider:
        LocalLeaderWindowRuntime = _Local
        WorldBatchLeaderWindowRuntime = _WorldBatch

    class _Env:
        execution_world_batch_runtime = True
        _exec_runtime = object()

    class _BatchEnv(_Env):
        class _Runtime:
            def rollout_window(self):
                return None

        _exec_runtime = _Runtime()

    def load_provider(name: str):
        if name == "python.rl.runtime.leader_window_runtime":
            return _Provider()
        pytest.fail(name)

    monkeypatch.setattr(module, "import_module", load_provider)
    assert isinstance(module.create_leader_window_runtime(_Env()), _Local)
    assert isinstance(module.create_leader_window_runtime(_BatchEnv()), _WorldBatch)


def test_execution_policy_loader_keeps_algorithm_provider_lazy(monkeypatch: pytest.MonkeyPatch) -> None:
    module = importlib.import_module("python.simulation.backend")

    class _Policy:
        @staticmethod
        def load(path: str, *, device: str):
            return ("adaptive", path, device)

    class _AdaptiveProvider:
        AdaptiveKLPPO = _Policy

    class _StableBaselines:
        class PPO:
            @staticmethod
            def load(path: str, *, device: str):
                return ("ppo", path, device)

    def load_provider(name: str):
        if name == "python.rl.policy_algo.ppo_adaptive_kl":
            return _AdaptiveProvider()
        if name == "stable_baselines3":
            return _StableBaselines()
        pytest.fail(name)

    monkeypatch.setattr(module, "import_module", load_provider)
    adaptive_result = module.load_execution_policy("model.zip", device="cpu")
    assert adaptive_result[0] == "adaptive"
    assert adaptive_result[1].endswith("\\model")
    assert adaptive_result[2] == "cpu"
    ppo_result = module.load_execution_policy("model", algo_name="PPO", device="cpu")
    assert ppo_result[0] == "ppo"
    assert ppo_result[1].endswith("\\model")
    assert ppo_result[2] == "cpu"


def test_execution_policy_loader_can_preserve_diagnostic_ppo_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    module = importlib.import_module("python.simulation.backend")

    class _FailingPolicy:
        @staticmethod
        def load(path: str, *, device: str):
            raise RuntimeError("incompatible adaptive checkpoint")

    class _AdaptiveProvider:
        AdaptiveKLPPO = _FailingPolicy

    class _StableBaselines:
        class PPO:
            @staticmethod
            def load(path: str, *, device: str):
                return ("ppo-fallback", path, device)

    def load_provider(name: str):
        if name == "python.rl.policy_algo.ppo_adaptive_kl":
            return _AdaptiveProvider()
        if name == "stable_baselines3":
            return _StableBaselines()
        pytest.fail(name)

    monkeypatch.setattr(module, "import_module", load_provider)
    result = module.load_execution_policy(
        "model.zip",
        algo_name="AdaptiveKLPPO",
        device="cpu",
        fallback_on_error=True,
    )
    assert result[0] == "ppo-fallback"


def test_scenario_runtime_adapter_is_provider_lazy(monkeypatch: pytest.MonkeyPatch) -> None:
    module = importlib.import_module("python.simulation.backend")

    class _Adapter:
        def __init__(self, world_count: int, *, marker: str):
            self.world_count = world_count
            self.marker = marker

    class _Provider:
        RuntimeFacadeAdapter = _Adapter

    def load_provider(name: str):
        if name == "python.rl.runtime.world_batch.adapter":
            return _Provider()
        pytest.fail(name)

    monkeypatch.setattr(module, "import_module", load_provider)
    adapter = module.create_scenario_runtime_adapter(1, marker="csg")
    assert (adapter.world_count, adapter.marker) == (1, "csg")


def test_provider_import_is_lazy_and_scripted_entries_use_backend_boundary() -> None:
    source = BACKEND_PATH.read_text(encoding="utf-8")
    assert 'import_module("python.rl.runtime.world_batch.vec_env")' in source
    assert 'import_module("python.rl.runtime.cooperative_world_batch_vec_env")' in source
    assert 'import_module("python.rl.runtime.single_world_batch_runtime")' in source
    for path in SCRIPTED_ENTRYPOINTS:
        text = path.read_text(encoding="utf-8")
        assert "from python.simulation import" in text
        assert "from python.rl.runtime.world_batch" not in text
        assert "from python.rl.runtime.cooperative_world_batch_vec_env" not in text
    cooperative_demo = (
        REPO_ROOT / "tools" / "diagnostics" / "air_cooperative_combat_scripted_demo.py"
    ).read_text(encoding="utf-8")
    assert "cooperative_slot_metadata()" in cooperative_demo
    assert "vec_env._slots" not in cooperative_demo
    trajectory_text = (
        REPO_ROOT / "tools" / "diagnostics" / "flight_trajectory" / "takeoff_to_landing.py"
    ).read_text(encoding="utf-8")
    assert "create_single_execution_runtime" in trajectory_text
    assert "from python.rl.runtime.single_world_batch_runtime" not in trajectory_text
    policy_runtime_text = (
        REPO_ROOT / "gym_envs" / "leader_env_parts" / "execution_runtime" / "policy_runtime.py"
    ).read_text(encoding="utf-8")
    assert (
        "from python.simulation import create_single_execution_runtime, resolve_execution_wrapper_spec"
        in policy_runtime_text
    )
    assert "from python.rl.runtime.single_world_batch_runtime" not in policy_runtime_text
    assert "from python.rl.control.wrappers" not in policy_runtime_text
    policy_text = (
        REPO_ROOT / "gym_envs" / "leader_env_parts" / "policy.py"
    ).read_text(encoding="utf-8")
    assert "from python.simulation import load_execution_policy" in policy_text
    assert "from python.rl.policy_algo.ppo_adaptive_kl" not in policy_text
    csg_replay_text = (
        REPO_ROOT / "python" / "scenario" / "runtime" / "csg_replay.py"
    ).read_text(encoding="utf-8")
    assert "from python.simulation import create_scenario_runtime_adapter" in csg_replay_text
    assert "from python.rl.runtime.world_batch.adapter" not in csg_replay_text
    runtime_facade_text = (
        REPO_ROOT / "gym_envs" / "leader_env_parts" / "runtime_facade.py"
    ).read_text(encoding="utf-8")
    assert "from python.simulation import create_leader_window_runtime" in runtime_facade_text
    assert "from python.rl.runtime.leader_window_runtime" not in runtime_facade_text


def test_evaluation_and_visualization_entries_use_backend_boundary() -> None:
    """Maintained operator entries must not select RL runtime providers directly."""

    entrypoints = (
        REPO_ROOT / "tools" / "eval" / "eval_utils.py",
        REPO_ROOT / "tools" / "eval" / "policy_execution_eval.py",
        REPO_ROOT / "examples" / "viz" / "runtime" / "viz_session.py",
    )
    for path in entrypoints:
        source = path.read_text(encoding="utf-8")
        assert "from python.rl.runtime" not in source, path
        assert "from python.rl.control.wrappers" not in source, path
        assert "from python.rl.policy_algo" not in source, path
        assert "from python.simulation" in source, path


def test_diagnostic_entries_use_backend_boundary() -> None:
    entrypoints = (
        REPO_ROOT / "tools" / "diagnostics" / "flight_trajectory" / "runway_drift_sweep.py",
        REPO_ROOT / "tools" / "diagnostics" / "flight_trajectory" / "takeoff_to_landing.py",
        REPO_ROOT / "tools" / "diagnostics" / "cooperative_trajectory_base.py",
        REPO_ROOT / "tools" / "diagnostics" / "diagnose_cooperative_trajectory.py",
        REPO_ROOT / "tools" / "diagnostics" / "benchmarks" / "world_batch_vec_env.py",
        REPO_ROOT / "tools" / "diagnostics" / "benchmarks" / "air_combat_post_launch_assessment.py",
        REPO_ROOT / "tools" / "diagnostics" / "air_combat_weapon_employment_process_probe.py",
        REPO_ROOT
        / "tools"
        / "diagnostics"
        / "_air_combat_weapon_employment_process_probe_impl"
        / "probe_env.py",
    )
    for path in entrypoints:
        source = path.read_text(encoding="utf-8")
        assert "from python.rl.runtime" not in source, path
        assert "from python.rl.control.wrappers" not in source, path
        assert "from python.rl.policy_algo" not in source, path
        if path.name != "probe_env.py":
            assert "from python.simulation" in source, path
