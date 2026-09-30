from types import SimpleNamespace

from gym_envs.scenario_loader.behavior_runtime.post_waypoint_transition import (
    apply_pending_landing_vector,
    landing_post_transition_terminal_ready,
)


def _two_runway_loader():
    calls = []
    truth = SimpleNamespace(x=1000.0, y=-1000.0)
    inst = SimpleNamespace(heading=270.0, alt_baro=800.0)
    loader = SimpleNamespace(
        agent_id=1,
        c2_task_name="TASK_RECOVER_LAND",
        c2_transitioned=False,
        scenario_data={"mission_command": {"post_waypoint_transition": {"recovery_runway_id": 2}}},
        post_waypoint_transition={
            "command_code": 4,
            "recovery_runway_id": 2,
            "terminal_ready_threshold_window_m": 3500.0,
            "terminal_ready_dme_m_max": 18000.0,
            "approach_arm_before_threshold_m": 1000.0,
        },
        mission_cmd={"command_code": 3, "target_heading": 0.0},
        waypoints=[],
        waypoint_idx=0,
        ils_beacons=[
            {"runway_id": 1, "cx": 0.0, "cy": 0.0, "thr_x": -1000.0, "thr_y": 0.0, "heading": 90.0},
            {"runway_id": 2, "cx": 0.0, "cy": 0.0, "thr_x": 0.0, "thr_y": -1000.0, "heading": 270.0},
        ],
    )
    loader.get_policy_agent_observation = lambda _agent_id: truth
    loader.get_policy_instrument_state = lambda _agent_id: inst

    def frame(x, y, *, runway_id=None):
        calls.append(("frame", runway_id))
        assert runway_id == 2
        return True, -500.0, 100.0, 3000.0, 45.0

    def ils(x, y, alt, *, runway_id=None):
        calls.append(("ils", runway_id))
        assert runway_id == 2
        return [1.0, 0.1, 0.1, 5000.0]

    loader.get_runway_local_frame = frame
    loader.get_ils_observation = ils
    loader._sync_kernel_mission_command = lambda: None
    return loader, calls


def test_recovery_readiness_and_vectoring_share_declared_runway_identity():
    loader, calls = _two_runway_loader()

    assert landing_post_transition_terminal_ready(loader) is True
    assert apply_pending_landing_vector(loader, sync_to_kernel=False) is True
    assert calls == [("frame", 2), ("ils", 2)]
    assert float(loader.mission_cmd["target_heading"]) == 270.0
