from __future__ import annotations

from tools.diagnostics.air_cooperative_combat_scripted_demo import run_demo
from python.tasking_contracts.air.engagement.model import (
    AIR_COMBAT_C2_ROE_V2,
    AIR_COMBAT_HYBRID_ACTION_DIM,
    AirScriptedEngagementModel,
)
from python.tasking_contracts.air.strategy.action import AirActionLayoutAdapter
from python.tasking_contracts.air.strategy.contracts import (
    AirActionApplication,
    AirTacticalActionIntent,
    AirTacticalObservation,
)
from python.tasking_contracts.air.strategy.observation import AirMissionContactObservationAdapter


_SCENARIO_PATH = "scenarios/air_combat/cooperative_air_2v1_scripted_c2_roe_engagement_v1.json"
_MULTI_TARGET_SCENARIO_PATH = "scenarios/air_combat/cooperative_air_2v2_scripted_c2_roe_terminal_v1.json"
_FOUR_V_FOUR_SCENARIO_PATH = "scenarios/air_combat/cooperative_air_4v4_scripted_c2_roe_terminal_v1.json"


def test_cooperative_combat_scripted_demo_releases_from_both_aircraft_and_terminates() -> None:
    result = run_demo(scenario_path=_SCENARIO_PATH, seed=20260516, max_steps=2400)

    assert result["action_mode"] == "air_combat_hybrid_v1"
    assert result["terminated"] == [True, True]
    assert result["truncated"] == [False, False]
    assert result["termination_reasons"] == ["combat_win", "combat_win"]
    assert all(result["fire_once_accepted_steps"])
    assert all(result["release_executed_steps"])
    assert all(report["weapon_station_valid"] for report in result["scripted_decision_reports"])
    assert all(report["weapon_station_id"] == 1 for report in result["scripted_decision_reports"])
    assert result["playable_boundary"] == "multi_aircraft_scripted_c2_roe_terminal_demo"


def test_cooperative_combat_scripted_demo_replays_event_trace() -> None:
    first = run_demo(scenario_path=_SCENARIO_PATH, seed=20260516, max_steps=2400)
    second = run_demo(scenario_path=_SCENARIO_PATH, seed=20260516, max_steps=2400)

    for key in (
        "steps",
        "terminated",
        "truncated",
        "termination_reasons",
        "roster",
        "fire_once_accepted_steps",
        "release_executed_steps",
        "scripted_decision_reports",
        "scripted_runtime_decisions",
    ):
        assert first[key] == second[key]
    assert first["scripted_runtime_identity"] == second["scripted_runtime_identity"]


def test_cooperative_combat_scripted_demo_routes_two_roster_targets() -> None:
    first = run_demo(scenario_path=_MULTI_TARGET_SCENARIO_PATH, seed=20260516, max_steps=600)
    second = run_demo(scenario_path=_MULTI_TARGET_SCENARIO_PATH, seed=20260516, max_steps=600)

    assert first["target_owner"] == ["Red_A", "Red_B"]
    assert first["terminated"] == [True, True]
    assert first["truncated"] == [False, False]
    assert first["termination_reasons"] == ["combat_win", "combat_win"]
    assert all(first["fire_once_accepted_steps"])
    assert all(first["release_executed_steps"])
    for key in (
        "steps",
        "terminated",
        "truncated",
        "termination_reasons",
        "target_owner",
        "fire_once_accepted_steps",
        "release_executed_steps",
        "scripted_decision_reports",
        "scripted_runtime_decisions",
    ):
        assert first[key] == second[key]
    assert first["scripted_runtime_identity"] == second["scripted_runtime_identity"]


def test_cooperative_combat_scripted_demo_routes_four_ship_two_element_terminal_trace() -> None:
    first = run_demo(scenario_path=_FOUR_V_FOUR_SCENARIO_PATH, seed=20260516, max_steps=600)
    second = run_demo(scenario_path=_FOUR_V_FOUR_SCENARIO_PATH, seed=20260516, max_steps=600)

    assert first["target_owner"] == ["Red_A", "Red_B", "Red_C", "Red_D"]
    assert first["terminated"] == [True, True, True, True]
    assert first["truncated"] == [False, False, False, False]
    assert first["termination_reasons"] == ["combat_win"] * 4
    assert all(first["fire_once_accepted_steps"])
    assert all(first["release_executed_steps"])
    assert len(first["scripted_runtime_identity"]) == 4
    assert len(set(first["scripted_runtime_identity"])) == 4
    for key in (
        "steps",
        "terminated",
        "truncated",
        "termination_reasons",
        "target_owner",
        "fire_once_accepted_steps",
        "release_executed_steps",
        "scripted_decision_reports",
        "scripted_runtime_decisions",
    ):
        assert first[key] == second[key]
    assert first["scripted_runtime_identity"] == second["scripted_runtime_identity"]


class _RecordingObservationAdapter:
    def __init__(self) -> None:
        self.delegate = AirMissionContactObservationAdapter()
        self.calls = 0

    def decode(self, *, observation: dict, mission_obs_mode: str) -> AirTacticalObservation:
        self.calls += 1
        return self.delegate.decode(observation=observation, mission_obs_mode=mission_obs_mode)


class _RecordingActionAdapter:
    def __init__(self) -> None:
        self.delegate = AirActionLayoutAdapter(action_dim=AIR_COMBAT_HYBRID_ACTION_DIM)
        self.calls = 0

    def reset(self) -> None:
        self.delegate.reset()

    def apply(self, action, *, intent: AirTacticalActionIntent) -> AirActionApplication:
        self.calls += 1
        return self.delegate.apply(action, intent=intent)


def test_cooperative_combat_default_and_recording_adapter_routes_have_terminal_parity() -> None:
    recorders: list[tuple[_RecordingObservationAdapter, _RecordingActionAdapter]] = []

    def build_model(_slot_name: str) -> AirScriptedEngagementModel:
        observation_adapter = _RecordingObservationAdapter()
        action_adapter = _RecordingActionAdapter()
        recorders.append((observation_adapter, action_adapter))
        return AirScriptedEngagementModel(
            action_dim=AIR_COMBAT_HYBRID_ACTION_DIM,
            dt=0.05,
            mission_obs_mode=AIR_COMBAT_C2_ROE_V2,
            observation_adapter=observation_adapter,
            action_adapter=action_adapter,
        )

    baseline = run_demo(scenario_path=_SCENARIO_PATH, seed=20260516, max_steps=600)
    injected = run_demo(
        scenario_path=_SCENARIO_PATH,
        seed=20260516,
        max_steps=600,
        _model_factory=build_model,
    )

    for key in (
        "steps",
        "terminated",
        "truncated",
        "termination_reasons",
        "roster",
        "fire_once_accepted_steps",
        "release_executed_steps",
        "scripted_decision_reports",
        "scripted_runtime_decisions",
    ):
        assert injected[key] == baseline[key]
    assert injected["scripted_runtime_identity"] == baseline["scripted_runtime_identity"]
    assert len(recorders) == 2
    assert all(observation.calls > 0 and action.calls > 0 for observation, action in recorders)
