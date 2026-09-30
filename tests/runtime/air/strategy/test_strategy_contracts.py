from __future__ import annotations

import numpy as np
import pytest

from python.mission_obs_taxonomy import mission_observation_dim, mission_observation_field_index
from python.tasking_contracts.air.strategy.assessment import AirPostLaunchAssessment, AirPostLaunchAssessmentReport
from python.tasking_contracts.air.engagement.model import (
    AIR_COMBAT_C2_ROE_V2,
    AirScriptedEngagementModel,
)
from python.tasking_contracts.air.strategy.action import AirActionLayoutAdapter
from python.tasking_contracts.air.strategy.assessment import AirPostLaunchAssessment
from python.tasking_contracts.air.strategy.planning import AirEngagementPlanner
from python.tasking_contracts.air.strategy.contracts import (
    AirActionApplication,
    AirActionAdapter,
    AirAssessmentInput,
    AirObservationAdapter,
    AirPlanningContext,
    AirTacticalActionIntent,
    AirTacticalDecision,
    AirTacticalObservation,
    AirTacticalPlanner,
)
from python.tasking_contracts.air.strategy.observation import AirMissionContactObservationAdapter


def _context(**overrides: object) -> AirPlanningContext:
    values: dict[str, object] = {
        "target_contact_present": True,
        "authorization_to_fire": True,
        "fire_mask_open": True,
        "launch_window_open": True,
        "quality_window_ready": True,
        "pending_assessment": False,
        "shot_budget_remaining": 1.0,
        "target_range_m": 16000.0,
    }
    values.update(overrides)
    return AirPlanningContext(**values)


def test_planner_projects_rich_plan_to_stable_decision_contract() -> None:
    planner = AirEngagementPlanner()
    decision = planner.decide(context=_context())

    assert isinstance(planner, AirTacticalPlanner)
    assert isinstance(decision, AirTacticalDecision)
    assert decision.fire_recommended is True
    assert decision.diagnostics["selected_candidate"] == "hold"
    assert decision.as_dict()["reason_codes"]


def test_planning_context_rejects_non_finite_or_negative_values() -> None:
    with pytest.raises(ValueError, match="target_range_m must be finite"):
        _context(target_range_m=float("nan"))
    with pytest.raises(ValueError, match="shot_budget_remaining must be non-negative"):
        _context(shot_budget_remaining=-1.0)


def test_decision_contract_bounds_guidance_and_freezes_diagnostics() -> None:
    decision = AirTacticalDecision(
        mode="reposition",
        selected_candidate="intercept",
        fire_recommended=False,
        guidance_roll=0.2,
        diagnostics={"source": "test"},
    )

    with pytest.raises(TypeError):
        decision.diagnostics["source"] = "mutated"  # type: ignore[index]
    with pytest.raises(ValueError, match="guidance_pitch"):
        AirTacticalDecision(
            mode="reposition",
            selected_candidate="intercept",
            fire_recommended=False,
            guidance_pitch=1.1,
        )


def test_assessment_input_is_typed_and_rejects_negative_evidence_counts() -> None:
    inputs = AirAssessmentInput(
        release_executed=True,
        pending_assessment=True,
        target_contact_present=True,
        own_missiles_in_flight_count=1.0,
        dt_s=0.05,
    )
    assert inputs.release_executed is True
    with pytest.raises(ValueError, match="dt_s must be non-negative"):
        AirAssessmentInput(
            release_executed=False,
            pending_assessment=False,
            target_contact_present=False,
            dt_s=-0.1,
        )


def test_observation_adapter_decodes_declared_mission_and_contact_fields() -> None:
    mission = np.zeros((mission_observation_dim(AIR_COMBAT_C2_ROE_V2),), dtype=np.float32)
    for name, value in {
        "authorization_to_fire": 1.0,
        "target_contact_present": 1.0,
        "fire_mask_open": 1.0,
        "launch_window_open": 1.0,
        "shot_budget_remaining": 1.0,
    }.items():
        mission[mission_observation_field_index(AIR_COMBAT_C2_ROE_V2, name)] = value
    decoded = AirMissionContactObservationAdapter().decode(
        observation={
            "mission": mission,
            "contacts": np.asarray([[16000.0, 12.0, -3.0, 420.0, 0.2]], dtype=np.float32),
        },
        mission_obs_mode=AIR_COMBAT_C2_ROE_V2,
    )

    assert isinstance(decoded, AirTacticalObservation)
    assert isinstance(AirMissionContactObservationAdapter(), AirObservationAdapter)
    assert decoded.mission_values["target_contact_present"] == 1.0
    assert decoded.contact_bearing_deg == 12.0
    assert decoded.contact_elevation_deg == -3.0
    assert decoded.closing_speed_mps == 420.0


def test_action_adapter_owns_full_layout_and_fire_latch_transport() -> None:
    adapter = AirActionLayoutAdapter(action_dim=17)
    assert isinstance(adapter, AirActionAdapter)
    intent = AirTacticalActionIntent(
        target_contact_present=True,
        authorization_to_fire=True,
        shot_budget_available=True,
        fire_window_open=True,
        assessment_blocked=False,
        request_fire=True,
        station_id=1,
    )
    first = adapter.apply(np.zeros((17,), dtype=np.float32), intent=intent)
    second = adapter.apply(np.zeros((17,), dtype=np.float32), intent=intent)

    assert isinstance(first, AirActionApplication)
    assert first.fire_pulse == 1.0
    assert first.action[9] == 1.0
    assert first.action[12] == 1.0
    assert first.action[13] == 1.0
    assert first.action[14] == 1.0
    assert first.action[16] == pytest.approx(1.0 / 7.0)
    assert second.fire_pulse == 0.0
    adapter.reset()
    reset = adapter.apply(np.zeros((17,), dtype=np.float32), intent=intent)
    assert reset.fire_pulse == 1.0


def test_action_adapter_projects_planner_guidance_before_fire_fields() -> None:
    adapter = AirActionLayoutAdapter(action_dim=17)
    intent = AirTacticalActionIntent(
        target_contact_present=True,
        authorization_to_fire=True,
        shot_budget_available=True,
        fire_window_open=True,
        assessment_blocked=False,
        request_fire=False,
        station_id=1,
        guidance_roll=0.2,
        guidance_pitch=-0.3,
        guidance_throttle=0.1,
    )
    action = adapter.apply(np.zeros((17,), dtype=np.float32), intent=intent).action

    assert action[0] == pytest.approx(-0.3)
    assert action[1] == pytest.approx(0.2)
    assert action[3] == pytest.approx(0.1)


class _DecisionOnlyPlanner:
    def reset(self) -> None:
        pass

    def decide(self, *, context: AirPlanningContext) -> AirTacticalDecision:
        return AirTacticalDecision(
            mode="reposition",
            selected_candidate="intercept",
            fire_recommended=False,
            guidance_roll=0.15,
            guidance_pitch=-0.1,
            guidance_throttle=0.05,
            diagnostics={"observation_version": context.observation_version},
        )


class _RecordingActionAdapter:
    def __init__(self) -> None:
        self.delegate = AirActionLayoutAdapter(action_dim=17)
        self.last_intent: AirTacticalActionIntent | None = None

    def reset(self) -> None:
        self.delegate.reset()

    def apply(self, action: np.ndarray, *, intent: AirTacticalActionIntent) -> AirActionApplication:
        self.last_intent = intent
        return self.delegate.apply(action, intent=intent)


def test_engagement_model_accepts_planner_without_raw_action_mutator() -> None:
    observation = _engagement_observation()
    action_adapter = _RecordingActionAdapter()
    model = AirScriptedEngagementModel(
        planner=_DecisionOnlyPlanner(),
        action_adapter=action_adapter,
    )
    model.reset(context={"observation": observation, "phase_name": "stable_flight"})
    action = model.decide(
        observation=observation,
        context={"phase_name": "stable_flight", "observation_version": "trace-v7"},
        dt=0.05,
    )

    assert action.shape == (17,)
    assert action_adapter.last_intent is not None
    assert action_adapter.last_intent.guidance_pitch == pytest.approx(-0.1)
    assert action_adapter.last_intent.guidance_roll == pytest.approx(0.15)
    assert action_adapter.last_intent.guidance_throttle == pytest.approx(0.05)
    assert model.last_decision_info["tactical_decision"]["diagnostics"]["observation_version"] == "trace-v7"
    model.close()


def test_default_assessor_accepts_typed_input_without_changing_outcome() -> None:
    report = AirPostLaunchAssessment().assess(
        inputs=AirAssessmentInput(
            release_executed=True,
            pending_assessment=False,
            target_contact_present=True,
            shot_budget_remaining=1.0,
        )
    )
    assert report.state == "reattack_ready"
    assert report.outcome == "inconclusive"


def _engagement_observation() -> dict[str, np.ndarray]:
    instruments = np.zeros((31,), dtype=np.float32)
    instruments[0] = 120.0
    mission = np.zeros((mission_observation_dim(AIR_COMBAT_C2_ROE_V2),), dtype=np.float32)
    for name, value in {
        "authorization_to_fire": 1.0,
        "target_contact_present": 1.0,
        "fire_mask_open": 1.0,
        "launch_window_open": 1.0,
        "quality_window_ready": 1.0,
        "shot_budget_remaining": 1.0,
        "pending_assessment": 0.0,
    }.items():
        mission[mission_observation_field_index(AIR_COMBAT_C2_ROE_V2, name)] = value
    return {"instruments": instruments, "mission": mission}


class _NoFirePlanner:
    def reset(self) -> None:
        pass

    def decide(self, *, context: AirPlanningContext) -> AirTacticalDecision:
        return AirTacticalDecision(
            mode="hold_authority",
            selected_candidate="hold",
            fire_recommended=False,
            reason_codes=("test_no_fire",),
        )

    def apply_decision_guidance(self, action: np.ndarray, decision: AirTacticalDecision) -> np.ndarray:
        return np.asarray(action, dtype=np.float32).copy()


class _BlockingAssessor:
    def reset(self) -> None:
        pass

    def assess(self, *, inputs: AirAssessmentInput) -> AirPostLaunchAssessmentReport:
        return AirPostLaunchAssessmentReport(
            state="in_flight",
            outcome="pending",
            confidence=0.0,
            allow_reattack=False,
            blocks_fire=True,
            release_executed=inputs.release_executed,
            pending_assessment=True,
            target_contact_present=inputs.target_contact_present,
            own_missiles_in_flight_count=1.0,
            target_track_age_s=inputs.target_track_age_s,
            reason_codes=("test_assessor_block",),
        )


def test_engagement_model_can_replace_planner_without_changing_flight_transport() -> None:
    observation = _engagement_observation()
    model = AirScriptedEngagementModel(planner=_NoFirePlanner())
    model.reset(context={"observation": observation, "phase_name": "stable_flight"})
    action = model.decide(observation=observation, context={"phase_name": "stable_flight"}, dt=0.05)

    assert action.shape == (17,)
    assert action[9] == 1.0
    assert action[13] == 1.0
    assert action[14] == 0.0
    assert model.last_decision_info["tactical_decision"]["reason_codes"] == ["test_no_fire"]
    model.close()


def test_engagement_model_can_replace_assessor_as_an_independent_fire_block() -> None:
    observation = _engagement_observation()
    model = AirScriptedEngagementModel(assessor=_BlockingAssessor())
    model.reset(context={"observation": observation, "phase_name": "stable_flight"})
    action = model.decide(observation=observation, context={"phase_name": "stable_flight"}, dt=0.05)

    assert action[14] == 0.0
    assert model.last_decision_info["post_launch_assessment"]["reason_codes"] == ["test_assessor_block"]
    model.close()


def test_injected_planner_cannot_silently_combine_with_default_policy_config() -> None:
    with pytest.raises(ValueError, match="planner injection cannot be combined"):
        AirScriptedEngagementModel(planner=_NoFirePlanner(), planner_config=AirEngagementPlanner().config)
