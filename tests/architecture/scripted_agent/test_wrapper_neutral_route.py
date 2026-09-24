from __future__ import annotations

from types import SimpleNamespace
from pathlib import Path

import numpy as np

from python.rl.control.wrappers import MultiTimescaleActionController


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_combined_wrapper_baseline_consumes_neutral_air_model() -> None:
    action_space = SimpleNamespace(shape=(17,))
    loader = SimpleNamespace(mission_phase_name="departure")
    controller = MultiTimescaleActionController(
        action_space=action_space,
        loader_getter=lambda: loader,
        dt_getter=lambda: 0.05,
        scripted_baseline_mode="takeoff_cruise_landing",
        scripted_blend_indices=(0,),
        scripted_lock_indices=(1,),
    )
    observation = {
        "instruments": np.asarray([0.0, 0.0, 0.0, 0.0], dtype=np.float32),
        "mission": np.asarray([1.0, 0.0, 100.0, 120.0], dtype=np.float32),
    }

    controller.reset_state(observation)
    prepared = controller.prepare_action(np.zeros((17,), dtype=np.float32))

    assert prepared.baseline_action is not None
    assert prepared.baseline_action.shape == (17,)
    assert prepared.scripted_active_mode == "takeoff"
    assert controller._scripted_model is not None
    assert type(controller._scripted_model).__module__ == "python.tasking_contracts.air_scripted_execution"


def test_both_wrapper_consumers_use_role_aware_registry_creation() -> None:
    source = (REPO_ROOT / "python" / "rl" / "control" / "wrappers.py").read_text(encoding="utf-8")
    assert source.count("AIR_SCRIPTED_MODEL_REGISTRY.create_for") >= 2
