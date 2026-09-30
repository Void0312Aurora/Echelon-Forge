from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TASKING_ROOT = REPO_ROOT / "python" / "tasking_contracts" / "air" / "tasking"


def test_air_c2_policy_has_a_physical_domain_layer() -> None:
    assert (TASKING_ROOT / "__init__.py").is_file()
    assert (TASKING_ROOT / "c2_policy.py").is_file()
    assert (TASKING_ROOT / "c2_observation.py").is_file()
    assert (TASKING_ROOT / "task_order_projection.py").is_file()
    assert (TASKING_ROOT / "c2_manager.py").is_file()
    assert (TASKING_ROOT / "leader_phase_policy.py").is_file()
    assert (TASKING_ROOT / "leader_approach_policy.py").is_file()


def test_air_c2_policy_is_independent_of_rl_and_simulation_adapters() -> None:
    for path in TASKING_ROOT.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "python.rl" not in text
        assert "gym_envs" not in text
        assert "ef_py" not in text
        assert "numpy" not in text


def test_air_c2_manager_uses_injected_runtime_ports_and_transition_policy() -> None:
    source = (TASKING_ROOT / "c2_manager.py").read_text(encoding="utf-8")
    assert "transition_policy: C2TransitionPolicy | None = None" in source
    assert "self.transition_policy.decide(" in source
    assert "C2TransitionInput(" in source
    assert "task_order_projection: C2TaskOrderProjection | None = None" in source
    assert "self.task_order_projection.retask_order(" in source
    assert "def _retask_order" not in source


def test_rl_leader_module_no_longer_owns_scripted_c2_manager() -> None:
    source = (REPO_ROOT / "python" / "rl" / "tasking" / "leader_tasking.py").read_text(encoding="utf-8")
    assert "class ScriptedC2TaskManager" not in source
    assert "import ScriptedC2TaskManager as _ScriptedC2TaskManager" in source


def test_rl_leader_phase_manager_delegates_phase_selection_to_neutral_policy() -> None:
    source = (REPO_ROOT / "python" / "rl" / "tasking" / "leader_tasking.py").read_text(encoding="utf-8")
    assert "LeaderPhaseInput(" in source
    assert "self.phase_policy.decide(" in source
    assert "def _infer_phase_name" not in source


def test_rl_leader_phase_manager_delegates_approach_gate_to_neutral_policy() -> None:
    source = (REPO_ROOT / "python" / "rl" / "tasking" / "leader_tasking.py").read_text(encoding="utf-8")
    assert "LeaderApproachInput(" in source
    assert "self.approach_policy.decide(" in source
