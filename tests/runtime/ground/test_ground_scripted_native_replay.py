"""Native replay of the Ground scripted infantry model on the compiled kernel.

The harness plays the scenario commander: it spawns one soldier on the
verified Arnis fixture, issues the commander's engagement order, and declares
the hostile contact the native fire gate requires (Ground sensing is held, so
the contact is a scenario fixture, as in the native probe). The scripted model
only sees its own position, operational state, and the commander-issued
assigned-target / fire-authorization fields read back from its own mission
command. Its decisions are projected through the maintained Ground command
projection; a fire request is forwarded to the native
``fire_ground_weapon_from_mission_command`` gate, which stays the release
authority.

The kernel calls used here are the ``native_probe_only`` Ground surface; this
is replay evidence for the bounded slice, not a production WorldBatch path.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pytest

from python.runtime_bootstrap import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402

from python.rl.ground.command import build_ground_infantry_mission_command  # noqa: E402
from python.tasking_contracts.common.decision_runtime import (  # noqa: E402
    DECISION_RUNTIME_ACTION_DECIDED,
    DECISION_RUNTIME_ACTION_HELD,
    DecisionRuntimeAgentSpec,
    DecisionRuntimeRoster,
)
from python.tasking_contracts.ground.execution import (  # noqa: E402
    GROUND_INFANTRY_CONTROLLER_ROLE_ID,
    GROUND_INFANTRY_SCRIPTED_MODEL_ID,
    GROUND_SCRIPTED_MODEL_REGISTRY,
    GroundInfantryDecision,
    GroundInfantryObjectiveTask,
    GroundInfantryObservation,
)


_DATABASE = resolve_repo_path("examples", "config", "database")
_FIXTURE = Path(
    resolve_repo_path(
        "tests",
        "scenario",
        "fixtures",
        "environment_substrate",
        "arnis_bundle_v1",
        "eastern_plain_infantry_phase1",
    )
)
_AGENT_ID = "ground:rifleman"
_START_XY_M = (400.0, 100.0)
_OBJECTIVE_XY_M = (406.0, 100.0)
_TIME_STEP_S = 0.5
_MAX_SPEED_MPS = 1.5
_STEPS = 40


def _new_kernel(seed: int) -> Any:
    sim = ef_py.SimulationKernel()
    assert sim.load_database(str(_DATABASE))
    sim.set_time_step(_TIME_STEP_S)
    assert sim.load_arnis_terrain_bundle(str(_FIXTURE / "expected"))
    assert sim.load_arnis_field_overlay(str(_FIXTURE / "field_overlay.json"))
    sim.reset(int(seed))
    return sim


def _spawn(sim: Any, side: Any, xy: tuple[float, float]) -> int:
    entity_id = int(sim.spawn_unit(side, "Ground_Infantry_Soldier_MVP", xy[0], xy[1], 0.0))
    assert entity_id > 0
    return entity_id


def _declare_fixture_contact(sim: Any, observer_id: int, target_id: int, target_xy: tuple[float, float]) -> None:
    dx = target_xy[0] - _START_XY_M[0]
    dy = target_xy[1] - _START_XY_M[1]
    track = ef_py.Detection()
    track.target_id = target_id
    track.range = math.hypot(dx, dy)
    track.bearing = math.degrees(math.atan2(dx, dy))
    track.elevation = 0.0
    track.closing_speed = 0.0
    track.signal_strength = 1.0
    track.snr_db = 20.0
    track.detection_prob_used = 1.0
    track.measured_vr = 0.0
    track.sensor_type = int(ef_py.SensorType.Visual)
    track.local_sensor_hit = True
    track.timestamp = 0.0
    sim.set_contact_list(observer_id, [track])


def _observe(sim: Any, entity_id: int) -> GroundInfantryObservation:
    position = tuple(float(value) for value in sim.get_unit_position(entity_id))
    health = tuple(float(value) for value in sim.get_unit_health(entity_id))
    command = sim.get_mission_command(entity_id)
    return GroundInfantryObservation(
        position_xy_m=(position[0], position[1]),
        operational=health[0] > 0.0,
        assigned_target_id=int(command.assigned_target_id),
        authorization_to_fire=bool(command.authorization_to_fire),
    )


def _command_for(decision: GroundInfantryDecision, order: dict[str, int | bool]) -> Any:
    """Project the model decision and carry the commander's order unchanged."""

    command = build_ground_infantry_mission_command(
        decision.command_action(),
        max_speed_mps=_MAX_SPEED_MPS,
        ground_task_mode=decision.ground_task_mode,
    )
    command.assigned_target_id = int(order["assigned_target_id"])
    command.engagement_authority_holder_id = int(order["engagement_authority_holder_id"])
    command.authorization_to_fire = bool(order["authorization_to_fire"])
    return command


def _run_episode(
    *,
    seed: int,
    target_xy: tuple[float, float],
    authorize: bool,
    holder: str = "self",
) -> dict[str, Any]:
    sim = _new_kernel(seed)
    soldier_id = _spawn(sim, ef_py.Side.Blue, _START_XY_M)
    target_id = _spawn(sim, ef_py.Side.Red, target_xy)
    _declare_fixture_contact(sim, soldier_id, target_id, target_xy)
    sim.set_command_link(soldier_id, 0.0, 0.0)
    order: dict[str, int | bool] = {
        "assigned_target_id": target_id,
        "engagement_authority_holder_id": soldier_id if holder == "self" else target_id,
        "authorization_to_fire": authorize,
    }
    initial = ef_py.MissionCommand()
    initial.active = True
    initial.ground_task_mode = ef_py.GroundTaskMode.OccupyStatic
    initial.assigned_target_id = int(order["assigned_target_id"])
    initial.engagement_authority_holder_id = int(order["engagement_authority_holder_id"])
    initial.authorization_to_fire = bool(order["authorization_to_fire"])
    sim.set_mission_command(soldier_id, initial)

    spec = DecisionRuntimeAgentSpec(
        agent_id=_AGENT_ID,
        model_id=GROUND_INFANTRY_SCRIPTED_MODEL_ID,
        domain="ground",
        role_id=GROUND_INFANTRY_CONTROLLER_ROLE_ID,
        decision_period_s=2.0 * _TIME_STEP_S,
        authority_scope="platform_control",
    )
    roster = DecisionRuntimeRoster.from_registry(GROUND_SCRIPTED_MODEL_REGISTRY, (spec,))
    task = GroundInfantryObjectiveTask(objective_xy_m=_OBJECTIVE_XY_M, objective_radius_m=1.0)
    records: list[dict[str, Any]] = []
    fire_results: list[dict[str, Any]] = []
    try:
        roster.reset(context_by_agent={_AGENT_ID: {"task": task}}, episode_seed=seed)
        for step_index in range(_STEPS):
            observation = _observe(sim, soldier_id)
            result = roster.step(
                observations={_AGENT_ID: observation},
                clock_s=step_index * _TIME_STEP_S,
                observation_versions={_AGENT_ID: f"ground:{step_index}"},
            )[_AGENT_ID]
            decision = result.action
            assert isinstance(decision, GroundInfantryDecision)
            sim.set_mission_command(soldier_id, _command_for(decision, order))
            if decision.fire_requested and result.report.action_source == DECISION_RUNTIME_ACTION_DECIDED:
                ammo_before = float(sim.get_ground_weapon_state(soldier_id)[2])
                damage_before = tuple(float(v) for v in sim.get_unit_damage_state(target_id))
                accepted = bool(sim.fire_ground_weapon_from_mission_command(soldier_id))
                fire_results.append(
                    {
                        "step_index": step_index,
                        "accepted": accepted,
                        "ammo_before": ammo_before,
                        "ammo_after": float(sim.get_ground_weapon_state(soldier_id)[2]),
                        "target_damage_before": damage_before,
                        "target_damage_after": tuple(
                            float(v) for v in sim.get_unit_damage_state(target_id)
                        ),
                    }
                )
            sim.step()
            records.append(
                {
                    "step_index": step_index,
                    "observation": asdict(observation),
                    "action_source": result.report.action_source,
                    "decision_index": result.report.decision_index,
                    "decision": asdict(decision),
                    "position_after": tuple(float(v) for v in sim.get_unit_position(soldier_id)),
                }
            )
        replay_identity = roster.agent(_AGENT_ID).replay_identity
    finally:
        roster.close()
    return {
        "records": records,
        "fire_results": fire_results,
        "replay_identity": replay_identity,
        "soldier_id": soldier_id,
        "target_id": target_id,
    }


def test_scripted_soldier_moves_to_objective_then_occupies_on_the_native_kernel() -> None:
    episode = _run_episode(seed=17, target_xy=(450.0, 100.0), authorize=False)
    records = episode["records"]
    modes = [record["decision"]["ground_task_mode"] for record in records]
    sources = {record["action_source"] for record in records}

    assert modes[0] == "move_static"
    assert "occupy_static" in modes
    first_hold = modes.index("occupy_static")
    assert set(modes[:first_hold]) == {"move_static"}
    assert set(modes[first_hold:]) == {"occupy_static"}
    assert sources == {DECISION_RUNTIME_ACTION_DECIDED, DECISION_RUNTIME_ACTION_HELD}

    start_x = _START_XY_M[0]
    moved = records[first_hold - 1]["position_after"][0] - start_x
    assert moved > 0.0
    hold_positions = {record["position_after"] for record in records[first_hold + 1 :]}
    assert len(hold_positions) == 1, "OccupyStatic must hold position on the native kernel"
    final_x, final_y, _ = records[-1]["position_after"]
    assert math.hypot(_OBJECTIVE_XY_M[0] - final_x, _OBJECTIVE_XY_M[1] - final_y) <= 1.0 + (
        _MAX_SPEED_MPS * 2.0 * _TIME_STEP_S
    )
    assert episode["fire_results"] == []
    assert all(record["decision"]["fire_requested"] is False for record in records)


def test_scripted_soldier_native_replay_is_deterministic_for_one_seed() -> None:
    first = _run_episode(seed=29, target_xy=(450.0, 100.0), authorize=True)
    second = _run_episode(seed=29, target_xy=(450.0, 100.0), authorize=True)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert first["replay_identity"] == f"{_AGENT_ID}:{GROUND_INFANTRY_SCRIPTED_MODEL_ID}:seed=29:reset=1"


def test_authorized_fire_request_goes_through_the_native_mission_command_gate() -> None:
    episode = _run_episode(seed=29, target_xy=(450.0, 100.0), authorize=True)
    fire_results = episode["fire_results"]
    assert fire_results, "an assigned, authorized target must produce a fire request"
    first = fire_results[0]
    assert first["accepted"] is True
    assert first["ammo_after"] == pytest.approx(first["ammo_before"] - 1.0)
    for record in episode["records"]:
        assert record["decision"]["fire_target_id"] in (0, episode["target_id"])
    # Movement is not altered by the fire request.
    modes = [record["decision"]["ground_task_mode"] for record in episode["records"]]
    assert modes[0] == "move_static" and modes[-1] == "occupy_static"


def test_native_gate_rejects_a_fire_request_when_the_holder_is_another_entity() -> None:
    episode = _run_episode(seed=29, target_xy=(450.0, 100.0), authorize=True, holder="other")
    fire_results = episode["fire_results"]
    # The model only reads assignment + authorization, so it requests fire;
    # the native gate owns the holder check and rejects every release.
    assert fire_results
    assert all(result["accepted"] is False for result in fire_results)
    assert all(result["ammo_after"] == result["ammo_before"] for result in fire_results)
    assert all(
        result["target_damage_after"] == result["target_damage_before"] for result in fire_results
    )


def test_scripted_decisions_do_not_depend_on_hostile_geometry() -> None:
    near = _run_episode(seed=31, target_xy=(450.0, 100.0), authorize=False)
    far = _run_episode(seed=31, target_xy=(450.0, 160.0), authorize=False)

    def decisions(episode: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {key: value for key, value in record["decision"].items() if key != "fire_target_id"}
            for record in episode["records"]
        ]

    assert decisions(near) == decisions(far)
