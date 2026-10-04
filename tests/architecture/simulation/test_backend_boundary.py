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
    assert "from python.simulation import create_single_execution_runtime" in trajectory_text
    assert "from python.rl.runtime.single_world_batch_runtime" not in trajectory_text
    policy_runtime_text = (
        REPO_ROOT / "gym_envs" / "leader_env_parts" / "execution_runtime" / "policy_runtime.py"
    ).read_text(encoding="utf-8")
    assert "from python.simulation import create_single_execution_runtime" in policy_runtime_text
    assert "from python.rl.runtime.single_world_batch_runtime" not in policy_runtime_text
