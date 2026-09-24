from __future__ import annotations

import numpy as np
import pytest
from pathlib import Path

from python.tasking_contracts.naval_scripted_execution import (
    NAVAL_SCRIPTED_MODEL_REGISTRY,
    NAVAL_STATION_HOLD_MODEL_ID,
)


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_naval_station_adapter_is_registered_with_scoped_status() -> None:
    entry = NAVAL_SCRIPTED_MODEL_REGISTRY.get(NAVAL_STATION_HOLD_MODEL_ID)
    assert entry.domain == "naval"
    assert entry.status == "adapter"
    assert entry.role_ids == ("naval_warfare_commander",)


def test_naval_station_adapter_has_neutral_lifecycle_and_zero_hold_action() -> None:
    model = NAVAL_SCRIPTED_MODEL_REGISTRY.create(NAVAL_STATION_HOLD_MODEL_ID, action_dim=3)
    model.reset(context={"scenario": "n4"})
    action = model.decide(observation=None, context={}, dt=0.05)
    assert action.shape == (3,)
    assert action.dtype == np.float32
    assert np.allclose(action, 0.0)
    model.close()
    with pytest.raises(RuntimeError, match="closed"):
        model.decide(observation=None, context={}, dt=0.05)


def test_naval_station_eval_uses_registered_adapter() -> None:
    source = (REPO_ROOT / "tools" / "eval" / "naval_station_policy_eval.py").read_text(encoding="utf-8")
    assert "NAVAL_SCRIPTED_MODEL_REGISTRY.create" in source
    assert "NAVAL_STATION_HOLD_MODEL_ID" in source
    assert "naval_station_cooperative_zero_action_baseline" in source
