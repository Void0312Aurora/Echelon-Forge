from __future__ import annotations

from types import SimpleNamespace

import pytest

from python.rl.tasking import bridge
from python.rl.profile import naval_profile
from python.simulation.air.tasking import make_scripted_c2_task_manager
from python.simulation.air.tasking_runtime import AirScriptedTaskingRuntime
from python.tasking_contracts.air.tasking.c2_policy import C2TransitionDecision
from python.tasking_contracts.common.task_order import (
    apply_common_task_order_defaults,
    apply_common_task_order_overrides,
)


class _RecordingProjection:
    def __init__(self):
        self.calls = []

    def retask_order(self, loader, *, task_name, sim_time_s):
        self.calls.append((loader, task_name, sim_time_s))


class _FixedPolicy:
    def __init__(self, decision):
        self.decision = decision

    def decide(self, state):
        _ = state
        return self.decision


def _minimal_c2_loader():
    return SimpleNamespace(
        agent_id=7,
        scenario_data={},
        task_order=SimpleNamespace(
            on_station_time_s=0.0,
            anchor_x_m=0.0,
            anchor_y_m=0.0,
            station_radius_m=12000.0,
            altitude_block_min_m=0.0,
            altitude_block_max_m=0.0,
            speed_min_mps=0.0,
            speed_max_mps=0.0,
        ),
        pilot_report=SimpleNamespace(active=False),
        waypoints=[],
        waypoint_idx=0,
        get_policy_agent_observation=lambda agent_id: SimpleNamespace(x=0.0, y=0.0, z=1000.0, heading=0.0),
        get_policy_instrument_state=lambda agent_id: SimpleNamespace(
            alt_radar=1000.0,
            alt_baro=1000.0,
            ground_speed=120.0,
            ias=120.0,
            heading=0.0,
            fuel_internal=1000.0,
            fuel_external=0.0,
        ),
        get_ils_observation=lambda x_m, y_m, alt_m: [0.0, 0.0, 0.0, 99999.0],
        get_runway_local_frame=lambda x_m, y_m: (False, 0.0, 0.0, 0.0, 0.0),
        _nearest_ils_beacon=lambda x_m, y_m: None,
    )


def test_compiled_air_c2_factory_constructs_neutral_manager_without_rl_import() -> None:
    loader = SimpleNamespace(
        agent_id=7,
        scenario_data={},
        mission_cmd={"target_altitude": 1200.0, "target_speed": 180.0},
        waypoints=[{"x": 1000.0, "y": 2000.0, "altitude_m": 1200.0, "speed_mps": 180.0}],
        waypoint_idx=0,
    )

    manager = make_scripted_c2_task_manager()
    state = manager.reset(loader, sim_time_s=3.0)

    assert state["task_name"] == manager.TASK_SCRAMBLE
    assert int(loader.task_order.assignee_id) == 7
    assert str(loader.task_order.service_profile).endswith("AirForce")
    assert str(loader.task_order.task_family).endswith("Transit")


def test_c2_manager_rejects_unknown_policy_task_before_runtime_state_or_projection_mutation() -> None:
    projection = _RecordingProjection()
    manager = make_scripted_c2_task_manager(
        transition_policy=_FixedPolicy(
            C2TransitionDecision(
                task_name="TASK_INTERCEPT",
                transitioned=True,
                reason="custom",
                station_entry_time_s=99.0,
            )
        ),
        task_order_projection=projection,
    )
    manager.current_task_name = manager.TASK_CAP
    manager.station_entry_time_s = 12.0
    loader = _minimal_c2_loader()

    with pytest.raises(ValueError, match="unknown task name"):
        manager.update(loader, sim_time_s=5.0)

    assert manager.current_task_name == manager.TASK_CAP
    assert manager.station_entry_time_s == 12.0
    assert projection.calls == []
    assert not hasattr(loader, "c2_task_name")


def test_c2_manager_refreshes_projection_on_non_transition_updates() -> None:
    projection = _RecordingProjection()
    manager = make_scripted_c2_task_manager(
        transition_policy=_FixedPolicy(
            C2TransitionDecision(
                task_name="TASK_CAP",
                transitioned=False,
                reason="steady",
                station_entry_time_s=None,
            )
        ),
        task_order_projection=projection,
    )
    manager.current_task_name = manager.TASK_CAP
    loader = _minimal_c2_loader()

    state = manager.update(loader, sim_time_s=5.0)

    assert state["task_name"] == manager.TASK_CAP
    assert len(projection.calls) == 1
    assert projection.calls[0][1:] == (manager.TASK_CAP, 5.0)


def test_tasking_bridge_exposes_bound_scripted_c2_factory_without_class_compatibility_helper() -> None:
    assert not hasattr(bridge, "scripted_c2_task_manager_class")
    assert callable(bridge.make_scripted_c2_task_manager)


def test_compiled_air_c2_projection_preserves_route_target_blocks() -> None:
    loader = SimpleNamespace(
        agent_id=9,
        scenario_data={},
        mission_cmd={"target_altitude": 900.0, "target_speed": 160.0},
        waypoints=[{"x": 500.0, "y": 800.0, "altitude_m": 1500.0, "speed_mps": 200.0}],
        waypoint_idx=0,
    )
    manager = make_scripted_c2_task_manager()
    manager.reset(loader)
    manager.task_order_projection.retask_order(loader, task_name=manager.TASK_CAP, sim_time_s=5.0)

    assert float(loader.task_order.target_altitude_m) == 1500.0
    assert float(loader.task_order.target_speed_mps) == 200.0
    assert float(loader.task_order.altitude_block_min_m) <= 1500.0 <= float(loader.task_order.altitude_block_max_m)
    assert float(loader.task_order.speed_min_mps) <= 200.0 <= float(loader.task_order.speed_max_mps)


def test_compiled_air_c2_projection_preserves_common_authored_order_fields() -> None:
    loader = SimpleNamespace(
        agent_id=11,
        scenario_data={
            "task_order": {
                "package_id": 42,
                "task_group_id": 84,
                "formation_contract_id": 7,
                "lead_aircraft_id": 11,
                "recovery_base_id": 3,
                "recovery_runway_id": 5,
                "authority_scope": "Operational",
                "coordination_mode": "Attached",
            }
        },
        mission_cmd={"target_altitude": 1200.0, "target_speed": 180.0},
        waypoints=[],
        waypoint_idx=0,
    )

    manager = make_scripted_c2_task_manager()
    manager.reset(loader)

    assert int(loader.task_order.package_id) == 42
    assert int(loader.task_order.task_group_id) == 84
    assert int(loader.task_order.formation_contract_id) == 7
    assert int(loader.task_order.lead_aircraft_id) == 11
    assert int(loader.task_order.recovery_site_id) == 5
    assert str(loader.task_order.authority_scope).endswith("Operational")
    assert str(loader.task_order.coordination_mode).endswith("Attached")


def test_compiled_air_c2_projection_keeps_live_task_type_over_authored_task_type() -> None:
    loader = SimpleNamespace(
        agent_id=12,
        scenario_data={"task_order": {"task_type": "CAP"}},
        mission_cmd={},
        waypoints=[],
        waypoint_idx=0,
    )

    manager = make_scripted_c2_task_manager()
    manager.reset(loader)

    state_task_type = str(loader.task_order.task_type)
    assert state_task_type.endswith("Scramble")


def test_naval_task_order_adapter_converts_authored_string_enums_at_domain_boundary() -> None:
    import ef_py

    order = ef_py.TaskOrder()
    naval_profile.apply_task_order_overrides(
        order,
        {
            "task_name": "TASK_SCREEN",
            "coordination_mode": "Screen",
            "warfare_role_code": "ScreenCommander",
            "naval_station_type": "Screen",
            "package_id": 5101,
        },
        default_assignee_id=17,
    )

    assert order.coordination_mode == ef_py.CoordinationMode.Screen
    assert order.warfare_role_code == ef_py.NavalWarfareRole.ScreenCommander
    assert order.naval_station_type == ef_py.NavalStationType.Screen
    assert int(order.task_group_id) == 5101


def test_common_task_order_owner_keeps_domain_codes_out_of_common_casting() -> None:
    order = SimpleNamespace(package_id=0, task_group_id=0, warfare_role_code=0)
    apply_common_task_order_overrides(
        order,
        {"package_id": 5101, "warfare_role_code": "ScreenCommander"},
        assignee_id=17,
    )
    apply_common_task_order_defaults(order)

    assert order.warfare_role_code == "ScreenCommander"
    assert order.task_group_id == 5101


def test_air_scripted_tasking_runtime_keeps_reset_and_transition_sequence() -> None:
    class _Manager:
        def reset(self, loader, **_kwargs):
            loader.c2_task_name = "TASK_SCRAMBLE"
            return {"task_name": "TASK_SCRAMBLE", "transitioned": False}

        def update(self, loader, *, sim_time_s, **_kwargs):
            task_name = "TASK_CAP" if float(sim_time_s) > 0.0 else "TASK_SCRAMBLE"
            loader.c2_task_name = task_name
            return {
                "task_name": task_name,
                "transitioned": task_name == "TASK_CAP",
                "transition_reason": "fake_transition",
            }

    loader = SimpleNamespace()
    runtime = AirScriptedTaskingRuntime(manager=_Manager())
    assert runtime.reset(loader)["task_name"] == "TASK_SCRAMBLE"
    runtime.update(loader, sim_time_s=0.05)

    assert runtime.task_sequence == ["TASK_SCRAMBLE", "TASK_CAP"]
    assert runtime.transition_history == [
        {"task_name": "TASK_CAP", "reason": "fake_transition", "sim_time_s": 0.05}
    ]
