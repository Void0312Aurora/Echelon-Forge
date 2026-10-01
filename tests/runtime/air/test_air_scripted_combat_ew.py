from __future__ import annotations

import numpy as np
import pytest

from python.mission_obs_taxonomy import mission_observation_dim, mission_observation_field_index
from python.tasking_contracts.air.combat_ew.model import (
    AIR_COMBAT_EW_ROLE_ID,
    AIR_SCRIPTED_COMBAT_EW_MODEL_ID,
    AirScriptedCombatEWModel,
)
from python.tasking_contracts.air.engagement.model import (
    AIR_COMBAT_C2_ROE_V2,
    AIR_COMBAT_HYBRID_ACTION_DIM,
    AirScriptedEngagementModel,
)
from python.tasking_contracts.air.ew.model import (
    AIR_EW_HYBRID_ACTION_DIM,
    AIR_EW_HYBRID_V2_ACTION_DIM,
    AIR_EW_JAMMER_TECHNIQUE_CODES,
    AirScriptedEWModel,
    air_ew_action_tail,
)
from python.tasking_contracts.air.registry import AIR_SCRIPTED_MODEL_REGISTRY
from python.tasking_contracts.common.decision_registry import DecisionModel


def _observation(
    *,
    contact: bool,
    fire_window: bool,
    rwr: list[list[float]] | None = None,
    pending: bool = False,
) -> dict[str, np.ndarray]:
    instruments = np.zeros((31,), dtype=np.float32)
    instruments[0] = 230.0
    instruments[2] = 7000.0
    instruments[3] = 7000.0
    mission = np.zeros((mission_observation_dim(AIR_COMBAT_C2_ROE_V2),), dtype=np.float32)
    values = {
        "authorization_to_fire": 1.0,
        "target_contact_present": 1.0 if contact else 0.0,
        "fire_mask_open": 1.0 if fire_window else 0.0,
        "launch_window_open": 1.0 if fire_window else 0.0,
        "quality_window_ready": 1.0 if fire_window else 0.0,
        "shot_budget_remaining": 1.0,
        "pending_assessment": 1.0 if pending else 0.0,
        "target_range_m": 11000.0,
    }
    for name, value in values.items():
        mission[mission_observation_field_index(AIR_COMBAT_C2_ROE_V2, name)] = value
    rows = np.zeros((4, 4), dtype=np.float32)
    for index, row in enumerate(rwr or []):
        rows[index] = row
    return {"instruments": instruments, "mission": mission, "rwr": rows}


# A decision sequence covering hold, the first fire window, a held repeat, a
# post-release assessment, and launch warnings arriving from two bearings.
_SEQUENCE = (
    (_observation(contact=False, fire_window=False), {}),
    (_observation(contact=True, fire_window=True), {}),
    (
        _observation(contact=True, fire_window=True, rwr=[[10.0, 0.4, 1.0, 0.0]]),
        {"last_event_info": {"release_executed": True}},
    ),
    (_observation(contact=True, fire_window=False, rwr=[[10.0, 0.7, 1.0, 1.0]], pending=True), {}),
    (
        _observation(contact=True, fire_window=False, rwr=[[10.0, 0.8, 1.0, 1.0], [-70.0, 0.5, 0.0, 1.0]]),
        {},
    ),
    (_observation(contact=False, fire_window=False), {}),
)
_BASE_CONTEXT = {
    "phase_name": "stable_flight",
    "mission_obs_mode": AIR_COMBAT_C2_ROE_V2,
    "response_doctrine": "countermeasure_ready",
    "jammer_doctrine": "self_protect_on_lock",
    "jammer_technique": "noise_spot",
}


def _run(model, *, context_overrides: dict | None = None) -> list[np.ndarray]:
    base = {**_BASE_CONTEXT, **(context_overrides or {})}
    model.reset(context={"observation": _SEQUENCE[0][0], **base})
    actions = []
    for index, (observation, extra) in enumerate(_SEQUENCE):
        context = {**base, **extra, "observation_version": f"seq:{index}"}
        actions.append(np.asarray(model.decide(observation=observation, context=context, dt=0.05)))
    model.close()
    return actions


@pytest.mark.parametrize("action_dim", (AIR_EW_HYBRID_ACTION_DIM, AIR_EW_HYBRID_V2_ACTION_DIM))
def test_combined_prefix_is_the_standalone_engagement_action_bit_for_bit(action_dim: int) -> None:
    combined = _run(AirScriptedCombatEWModel(action_dim=action_dim, weapon_station_id=1))
    standalone = _run(
        AirScriptedEngagementModel(action_dim=AIR_COMBAT_HYBRID_ACTION_DIM, weapon_station_id=1)
    )
    assert [action.shape for action in combined] == [(action_dim,)] * len(_SEQUENCE)
    for joint, alone in zip(combined, standalone):
        assert joint.dtype == np.float32
        assert joint[:AIR_COMBAT_HYBRID_ACTION_DIM].tobytes() == alone.tobytes()
    # The sequence really exercises the engagement fire pulse.
    assert [float(action[9]) for action in standalone] == [0.0, 1.0, 0.0, 0.0, 0.0, 0.0]


@pytest.mark.parametrize("action_dim", (AIR_EW_HYBRID_ACTION_DIM, AIR_EW_HYBRID_V2_ACTION_DIM))
def test_combined_tail_follows_the_standalone_ew_intent(action_dim: int) -> None:
    combined = _run(AirScriptedCombatEWModel(action_dim=action_dim, weapon_station_id=1))
    ew_model = AirScriptedEWModel(max_rwr=4)
    ew_model.reset(context=dict(_BASE_CONTEXT))
    for index, ((observation, extra), joint) in enumerate(zip(_SEQUENCE, combined)):
        intent = ew_model.decide(
            observation=observation,
            context={**_BASE_CONTEXT, **extra, "observation_version": f"seq:{index}"},
            dt=0.05,
        )
        expected_tail = air_ew_action_tail(intent, action_dim=action_dim)
        assert joint[AIR_COMBAT_HYBRID_ACTION_DIM:].tobytes() == expected_tail.tobytes()
    ew_model.close()
    tails = np.stack([action[AIR_COMBAT_HYBRID_ACTION_DIM:] for action in combined])
    # Launch rows on decisions 3 and 4 request chaff and flare; nothing else does.
    assert tails[:, 0].tolist() == [0.0, 0.0, 0.0, 1.0, 1.0, 0.0]
    assert tails[:, 1].tolist() == [0.0, 0.0, 0.0, 1.0, 1.0, 0.0]
    if action_dim == AIR_EW_HYBRID_V2_ACTION_DIM:
        # The jammer keys on the lock at decision 2 and on both warned frames.
        assert tails[:, 2].tolist() == [0.0, 0.0, 1.0, 1.0, 1.0, 0.0]
        assert set(tails[:, 3].tolist()) == {float(AIR_EW_JAMMER_TECHNIQUE_CODES["noise_spot"])}


def test_ew_doctrine_never_changes_the_engagement_prefix() -> None:
    active = _run(AirScriptedCombatEWModel(action_dim=AIR_EW_HYBRID_V2_ACTION_DIM, weapon_station_id=1))
    passive = _run(
        AirScriptedCombatEWModel(action_dim=AIR_EW_HYBRID_V2_ACTION_DIM, weapon_station_id=1),
        context_overrides={"response_doctrine": "observe_only", "jammer_doctrine": "hold"},
    )
    for loud, quiet in zip(active, passive):
        assert loud[:AIR_COMBAT_HYBRID_ACTION_DIM].tobytes() == quiet[:AIR_COMBAT_HYBRID_ACTION_DIM].tobytes()
        # Chaff, flare and jammer-transmit stay off; [15] is the selected
        # technique code, which the v2 tail carries even while not transmitting.
        assert not np.any(quiet[AIR_COMBAT_HYBRID_ACTION_DIM:15] > 0.5)


def test_combined_model_reports_last_engagement_decision_and_ew_intent() -> None:
    model = AirScriptedCombatEWModel(action_dim=AIR_EW_HYBRID_V2_ACTION_DIM, weapon_station_id=1)
    assert isinstance(model, DecisionModel)
    assert model.model_kind == "scripted"
    assert model.last_decision_info["ew_intent"] is None
    observation, _ = _SEQUENCE[4]
    model.reset(context={"observation": observation, **_BASE_CONTEXT})
    model.decide(observation=observation, context=dict(_BASE_CONTEXT), dt=0.05)
    info = model.last_decision_info
    assert info["role"] == AIR_COMBAT_EW_ROLE_ID
    assert info["engagement"]["role"] == "air_tactical_engagement_controller"
    assert info["engagement"] == model.last_engagement_decision_info
    assert info["ew_intent"]["launch_warning"] is True
    assert info["ew_intent"]["countermeasure_plan"] == "request_chaff_and_flare"
    assert info["ew_intent"]["jammer_transmit"] is True
    assert model.last_intent is not None
    model.close()
    with pytest.raises(RuntimeError, match="closed"):
        model.decide(observation=observation, context=dict(_BASE_CONTEXT), dt=0.05)


@pytest.mark.parametrize("action_dim", (AIR_COMBAT_HYBRID_ACTION_DIM, 17, 15))
def test_combined_model_rejects_non_ew_action_dimensions(action_dim: int) -> None:
    with pytest.raises(ValueError, match="14 \\(air_ew_hybrid_v1\\) or 16 \\(air_ew_hybrid_v2\\)"):
        AirScriptedCombatEWModel(action_dim=action_dim)


def test_combined_model_is_registered_as_an_adapter() -> None:
    entries = AIR_SCRIPTED_MODEL_REGISTRY.resolve(domain="air", role_id=AIR_COMBAT_EW_ROLE_ID)
    assert [entry.model_id for entry in entries] == [AIR_SCRIPTED_COMBAT_EW_MODEL_ID]
    assert entries[0].status == "adapter"
    assert entries[0].model_kind == "scripted"
    model = AIR_SCRIPTED_MODEL_REGISTRY.create_for(
        domain="air",
        role_id=AIR_COMBAT_EW_ROLE_ID,
        model_id=AIR_SCRIPTED_COMBAT_EW_MODEL_ID,
        action_dim=AIR_EW_HYBRID_V2_ACTION_DIM,
        dt=0.05,
        mission_obs_mode=AIR_COMBAT_C2_ROE_V2,
        weapon_station_id=1,
    )
    assert isinstance(model, AirScriptedCombatEWModel)
    assert model.action_dim == AIR_EW_HYBRID_V2_ACTION_DIM
    assert model.engagement_model.action_dim == AIR_COMBAT_HYBRID_ACTION_DIM
    assert model.engagement_model.weapon_station_id == 1
    model.close()
