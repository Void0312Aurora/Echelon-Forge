from __future__ import annotations

from types import SimpleNamespace

from python.simulation.air.tasking import make_scripted_c2_task_manager


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
