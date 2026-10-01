from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from python.tasking_contracts.air.ew.model import (
    AIR_EW_HYBRID_ACTION_DIM,
    AIR_SCRIPTED_EW_ACTION_MODEL_ID,
    AIR_SCRIPTED_EW_MODEL_ID,
    AirScriptedEWActionModel,
    AirScriptedEWIntent,
    AirScriptedEWModel,
)
from python.tasking_contracts.air.registry import AIR_SCRIPTED_MODEL_REGISTRY
from python.tasking_contracts.common.decision_registry import DecisionModel
try:
    from gym_envs.universal_env_parts import (
        AIR_EW_HYBRID_V1_ACTION_MODE,
        build_pilot_action,
        expected_action_dim,
        make_action_space,
    )
except ModuleNotFoundError:
    AIR_EW_HYBRID_V1_ACTION_MODE = None
    build_pilot_action = None
    expected_action_dim = None
    make_action_space = None


def _observation(*rows: list[float]) -> dict[str, np.ndarray]:
    return {"rwr": np.asarray(rows, dtype=np.float32).reshape(-1, 4)}


def test_ew_model_uses_rwr_only_and_emits_declared_observation_intent() -> None:
    model = AirScriptedEWModel(max_rwr=4)
    assert isinstance(model, DecisionModel)
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


@pytest.mark.skipif(AIR_EW_HYBRID_V1_ACTION_MODE is None, reason="compiled ef_py action surface is unavailable")
def test_ew_action_extension_maps_countermeasure_bits_without_changing_full_indices() -> None:
    assert expected_action_dim(AIR_EW_HYBRID_V1_ACTION_MODE) == AIR_EW_HYBRID_ACTION_DIM
    action_space = make_action_space(AIR_EW_HYBRID_V1_ACTION_MODE)
    action = np.zeros((AIR_EW_HYBRID_ACTION_DIM,), dtype=np.float32)
    action[12] = 1.0
    action[13] = 1.0
    pilot = build_pilot_action(action, action_mode=AIR_EW_HYBRID_V1_ACTION_MODE)
    assert pilot.program_chaff is True
    assert pilot.program_flare is True


def test_ew_action_model_emits_versioned_extension_and_is_registered_as_adapter() -> None:
    model = AirScriptedEWActionModel()
    obs = {
        "instruments": np.zeros((31,), dtype=np.float32),
        "mission": np.asarray([1.0, 90.0, 1000.0, 120.0], dtype=np.float32),
        "rwr": np.asarray([[0.0, 0.8, 1.0, 1.0]], dtype=np.float32),
    }
    model.reset(context={"observation": obs, "phase_name": "stable_flight"})
    action = model.decide(
        observation=obs,
        context={"response_doctrine": "countermeasure_ready", "observation_version": "rwr:1"},
        dt=0.05,
    )
    assert action.shape == (AIR_EW_HYBRID_ACTION_DIM,)
    assert np.all(action[4:12] == 0.0)
    assert action[12] == 1.0
    assert action[13] == 1.0
    model.close()
    entries = AIR_SCRIPTED_MODEL_REGISTRY.resolve(domain="air", role_id="air_ew_action_controller")
    assert [entry.model_id for entry in entries] == [AIR_SCRIPTED_EW_ACTION_MODEL_ID]
    assert entries[0].status == "adapter"


def test_ew_hybrid_routes_combat_prefix_through_both_maintained_consumers() -> None:
    from gym_envs.universal_env_parts.actions import (
        air_combat_hybrid_effective_action,
        is_air_combat_hybrid_action_mode,
    )

    assert is_air_combat_hybrid_action_mode(AIR_EW_HYBRID_V1_ACTION_MODE) is True
    raw = np.zeros((AIR_EW_HYBRID_ACTION_DIM,), dtype=np.float32)
    raw[6] = 1.0
    raw[9] = 1.0
    raw[12] = 1.0
    raw[13] = 1.0
    effective = air_combat_hybrid_effective_action(raw)
    assert effective[6] == 1.0
    assert effective[9] == 1.0
    assert effective[12] == 1.0
    assert effective[13] == 1.0

    repo_root = Path(__file__).resolve().parents[3]
    for relative in (
        "python/rl/runtime/world_batch/vec_env.py",
        "python/rl/runtime/single_world_batch_runtime.py",
    ):
        source = (repo_root / relative).read_text(encoding="utf-8")
        assert "is_air_combat_hybrid_action_mode" in source
        assert "air_combat_hybrid_effective_action" in source
        assert "apply_air_combat_event_action_gate" in source
        assert "finalize_air_combat_event_action_info" in source

def test_ew_action_model_keeps_combat_and_avionics_prefix_zero_owned() -> None:
    model = AirScriptedEWActionModel()
    obs = {
        "instruments": np.zeros((31,), dtype=np.float32),
        "mission": np.asarray([4.0, 90.0, 1000.0, 120.0], dtype=np.float32),
        "rwr": np.asarray([[0.0, 0.8, 1.0, 1.0]], dtype=np.float32),
    }
    model.reset(context={"observation": obs, "phase_name": "landing_final"})
    action = model.decide(
        observation=obs,
        context={"response_doctrine": "countermeasure_ready", "observation_version": "rwr:landing"},
        dt=0.05,
    )
    assert np.allclose(action[4:12], 0.0)
    assert tuple(action[12:14]) == (1.0, 1.0)
    model.close()

def test_ew_model_supports_explicit_single_countermeasure_doctrines() -> None:
    model = AirScriptedEWModel(max_rwr=4)
    observation = _observation([45.0, 0.8, 1.0, 1.0])
    model.reset(context={"observation_version": "rwr:0"})

    chaff = model.decide(
        observation=observation,
        context={"observation_version": "rwr:1", "response_doctrine": "chaff_only"},
        dt=0.05,
    )
    flare = model.decide(
        observation=observation,
        context={"observation_version": "rwr:2", "response_doctrine": "flare_only"},
        dt=0.05,
    )
    assert chaff.countermeasure_plan == "request_chaff"
    assert flare.countermeasure_plan == "request_flare"
    model.close()


def test_ew_action_model_maps_single_countermeasure_doctrine_to_one_tail_bit() -> None:
    model = AirScriptedEWActionModel()
    obs = {
        "instruments": np.zeros((31,), dtype=np.float32),
        "mission": np.asarray([1.0, 90.0, 1000.0, 120.0], dtype=np.float32),
        "rwr": np.asarray([[0.0, 0.8, 1.0, 1.0]], dtype=np.float32),
    }
    model.reset(context={"observation": obs, "phase_name": "stable_flight"})
    chaff = model.decide(
        observation=obs,
        context={"response_doctrine": "chaff_only", "observation_version": "rwr:1"},
        dt=0.05,
    )
    flare = model.decide(
        observation=obs,
        context={"response_doctrine": "flare_only", "observation_version": "rwr:2"},
        dt=0.05,
    )
    assert tuple(chaff[12:14]) == (1.0, 0.0)
    assert tuple(flare[12:14]) == (0.0, 1.0)
    model.close()


def test_ew_model_jammer_doctrine_keys_pod_on_lock_and_holds_emcon_otherwise() -> None:
    model = AirScriptedEWModel(max_rwr=4)
    model.reset(context={})
    context = {"jammer_doctrine": "self_protect_on_lock", "jammer_technique": "deception_drfm"}
    locked = model.decide(observation=_observation([10.0, 0.4, 1.0, 0.0]), context=context, dt=0.05)
    assert locked.jammer_transmit is True
    assert locked.jammer_mode == "deception_drfm"
    assert locked.jammer_technique_code == 2

    # A painting radar without lock or launch keeps the pod in standby.
    painted = model.decide(observation=_observation([10.0, 0.4, 0.0, 0.0]), context=context, dt=0.05)
    assert painted.jammer_transmit is False
    assert painted.jammer_mode == "standby"

    held = model.decide(
        observation=_observation([10.0, 0.4, 1.0, 1.0]), context={"jammer_doctrine": "hold"}, dt=0.05
    )
    assert held.jammer_transmit is False
    assert held.jammer_mode == "unchanged"

    with pytest.raises(ValueError, match="jammer doctrine"):
        model.decide(observation=_observation(), context={"jammer_doctrine": "always"}, dt=0.05)
    with pytest.raises(ValueError, match="jammer technique"):
        model.decide(
            observation=_observation(),
            context={"jammer_doctrine": "self_protect_on_lock", "jammer_technique": "laser"},
            dt=0.05,
        )
    model.close()


@pytest.mark.skipif(AIR_EW_HYBRID_V1_ACTION_MODE is None, reason="compiled ef_py action surface is unavailable")
def test_ew_v2_action_model_projects_jammer_tail_to_pilot_action() -> None:
    from gym_envs.universal_env_parts import AIR_EW_HYBRID_V2_ACTION_MODE
    from python.simulation.air.action import build_pilot_action as build_direct_pilot_action
    from python.tasking_contracts.air.ew.model import AIR_EW_HYBRID_V2_ACTION_DIM

    model = AirScriptedEWActionModel(action_dim=AIR_EW_HYBRID_V2_ACTION_DIM)
    obs = {
        "instruments": np.zeros((31,), dtype=np.float32),
        "mission": np.asarray([1.0, 90.0, 1000.0, 120.0], dtype=np.float32),
        "rwr": np.asarray([[0.0, 0.8, 1.0, 0.0]], dtype=np.float32),
    }
    model.reset(context={"observation": obs, "phase_name": "stable_flight"})
    action = model.decide(
        observation=obs,
        context={"jammer_doctrine": "self_protect_on_lock", "jammer_technique": "noise_spot"},
        dt=0.05,
    )
    model.close()
    assert action.shape == (AIR_EW_HYBRID_V2_ACTION_DIM,)
    assert tuple(action[14:16]) == (1.0, 1.0)
    assert expected_action_dim(AIR_EW_HYBRID_V2_ACTION_MODE) == AIR_EW_HYBRID_V2_ACTION_DIM
    space = make_action_space(AIR_EW_HYBRID_V2_ACTION_MODE)
    assert space.shape == (AIR_EW_HYBRID_V2_ACTION_DIM,)

    for pilot in (
        build_pilot_action(action, action_mode=AIR_EW_HYBRID_V2_ACTION_MODE),
        build_direct_pilot_action(action, action_mode=AIR_EW_HYBRID_V2_ACTION_MODE),
    ):
        assert pilot.jammer_transmit is True
        assert pilot.jammer_mode == 1
    # v1 never carries a jammer request.
    v1 = build_pilot_action(action[:14], action_mode=AIR_EW_HYBRID_V1_ACTION_MODE)
    assert v1.jammer_transmit is False
    assert v1.jammer_mode == 0


def test_ew_burst_program_dispenses_on_onset_and_new_threats_only() -> None:
    model = AirScriptedEWModel(max_rwr=4)
    model.reset(context={})
    context = {
        "response_doctrine": "countermeasure_ready",
        "dispense_program": "burst",
        "dispense_burst_s": 0.5,
        "dispense_bearing_gate_deg": 20.0,
    }
    first_threat = _observation([30.0, 1.0, 0.0, 1.0])
    plans = [model.decide(observation=first_threat, context=context, dt=0.05).countermeasure_plan for _ in range(12)]
    # Onset opens a 0.5 s burst (10 decisions at 0.05 s), then the program holds.
    assert plans[:10] == ["request_chaff_and_flare"] * 10
    assert plans[10:] == ["program_hold"] * 2

    # A second launch from a new bearing re-arms the burst; drift inside the
    # association gate does not.
    drifted = _observation([35.0, 1.0, 0.0, 1.0])
    assert model.decide(observation=drifted, context=context, dt=0.05).countermeasure_plan == "program_hold"
    two_threats = _observation([35.0, 1.0, 0.0, 1.0], [-80.0, 1.0, 0.0, 1.0])
    assert model.decide(observation=two_threats, context=context, dt=0.05).countermeasure_plan == (
        "request_chaff_and_flare"
    )

    # Warning clears, then a fresh onset re-arms.
    assert model.decide(observation=_observation(), context=context, dt=0.05).countermeasure_plan == "hold"
    assert model.decide(observation=first_threat, context=context, dt=0.05).countermeasure_plan == (
        "request_chaff_and_flare"
    )
    model.close()


def test_ew_burst_program_requires_declared_doctrine_parameters() -> None:
    model = AirScriptedEWModel()
    model.reset(context={})
    warned = _observation([0.0, 1.0, 0.0, 1.0])
    with pytest.raises(ValueError, match="dispense_burst_s"):
        model.decide(observation=warned, context={"dispense_program": "burst"}, dt=0.05)
    with pytest.raises(ValueError, match="dispense_bearing_gate_deg"):
        model.decide(
            observation=warned,
            context={"dispense_program": "burst", "dispense_burst_s": 1.0},
            dt=0.05,
        )
    with pytest.raises(ValueError, match="dispense program"):
        model.decide(observation=warned, context={"dispense_program": "ripple"}, dt=0.05)
    model.close()
