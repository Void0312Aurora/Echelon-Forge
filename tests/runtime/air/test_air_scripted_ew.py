from __future__ import annotations

import numpy as np

from python.tasking_contracts.air_scripted_ew import (
    AIR_SCRIPTED_EW_MODEL_ID,
    AirScriptedEWIntent,
    AirScriptedEWModel,
)
from python.tasking_contracts.air_scripted_registry import AIR_SCRIPTED_MODEL_REGISTRY
from python.tasking_contracts.scripted_registry import ScriptedDecisionModel


def _observation(*rows: list[float]) -> dict[str, np.ndarray]:
    return {"rwr": np.asarray(rows, dtype=np.float32).reshape(-1, 4)}


def test_ew_model_uses_rwr_only_and_emits_declared_observation_intent() -> None:
    model = AirScriptedEWModel(max_rwr=4)
    assert isinstance(model, ScriptedDecisionModel)
    model.reset(context={"observation_version": "rwr:0"})
    intent = model.decide(
        observation=_observation([45.0, 0.8, 1.0, 1.0], [-30.0, 0.3, 0.0, 0.0]),
        context={"observation_version": "rwr:1", "response_doctrine": "countermeasure_ready"},
        dt=0.05,
    )
    assert isinstance(intent, AirScriptedEWIntent)
    assert intent.threat_detected is True
    assert intent.launch_warning is True
    assert intent.track_locked is True
    assert np.isclose(intent.strongest_signal, 0.8)
    assert np.isclose(intent.strongest_bearing_deg, 45.0)
    assert intent.countermeasure_plan == "request_chaff_and_flare"
    assert intent.jammer_mode == "unchanged"
    assert intent.action_owner_status == "native_action_owner_required"
    assert intent.observation_version == "rwr:1"
    model.close()


def test_ew_model_defers_without_declared_response_doctrine_and_handles_empty_rwr() -> None:
    model = AirScriptedEWModel()
    model.reset(context={})
    intent = model.decide(
        observation=_observation(),
        context={"observation_version": "rwr:empty"},
        dt=0.05,
    )
    assert intent.threat_detected is False
    assert intent.launch_warning is False
    assert intent.countermeasure_plan == "hold"
    model.close()


def test_ew_model_is_registered_in_the_aggregate_air_registry_as_adapter() -> None:
    entries = AIR_SCRIPTED_MODEL_REGISTRY.resolve(domain="air", role_id="air_ew_controller")
    assert [entry.model_id for entry in entries] == [AIR_SCRIPTED_EW_MODEL_ID]
    assert entries[0].status == "adapter"
