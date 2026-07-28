"""I24 (W2 critical period) compatibility-shell identity gates.

Every symbol I24 moved into `python.tasking_contracts` must remain importable
from its original `python.rl.*` location as the *exact same object*
(`assertIs`, not merely equal), so every pre-existing call site, saved
reference, or `isinstance`/`is` check anywhere in the codebase keeps working
unchanged.
"""

from __future__ import annotations

from tests.architecture.helpers import ensure_repo_root_on_sys_path

ensure_repo_root_on_sys_path()

import python.rl.control as control_pkg
import python.rl.control.base_scripted_controller as legacy_base_scripted_controller
import python.rl.control.mission_defs as legacy_mission_defs
import python.rl.control.scripted_landing as legacy_scripted_landing
import python.rl.control.scripted_stable_flight as legacy_scripted_stable_flight
import python.rl.control.scripted_takeoff as legacy_scripted_takeoff
import python.rl.runtime.execution_runtime as legacy_execution_runtime
import python.rl.runtime.leader_window_runtime as legacy_leader_window_runtime
import python.rl.tasking.bridge as legacy_bridge
import python.tasking_contracts.base_scripted_controller as neutral_base_scripted_controller
import python.tasking_contracts.bridge_views as neutral_bridge_views
import python.tasking_contracts.leader_decision_state as neutral_leader_decision_state
import python.tasking_contracts.mission_defs as neutral_mission_defs
import python.tasking_contracts.scripted_landing as neutral_scripted_landing
import python.tasking_contracts.scripted_stable_flight as neutral_scripted_stable_flight
import python.tasking_contracts.scripted_takeoff as neutral_scripted_takeoff
import python.tasking_contracts.timing_utils as neutral_timing_utils


def test_mission_defs_shell_is_identical_to_the_neutral_layer() -> None:
    assert set(legacy_mission_defs.__all__) == set(neutral_mission_defs.__all__)
    for name in neutral_mission_defs.__all__:
        assert getattr(legacy_mission_defs, name) is getattr(neutral_mission_defs, name), name
        assert getattr(control_pkg, name) is getattr(neutral_mission_defs, name), name


def test_bridge_moved_surface_is_identical_to_the_neutral_layer() -> None:
    for name in neutral_bridge_views.__all__:
        assert hasattr(legacy_bridge, name), f"python.rl.tasking.bridge lost re-export of {name!r}"
        assert getattr(legacy_bridge, name) is getattr(neutral_bridge_views, name), name


def test_bridge_residual_profile_dispatch_surface_stays_bridge_owned() -> None:
    # These dispatch into the python.rl-internal air/ground/naval profile modules and
    # were deliberately left in python.rl.tasking.bridge (see I24 report). Pin their
    # module of definition so a future accidental move is caught here first.
    residual_names = (
        "resolve_tasking_profile",
        "tasking_profile_for_loader",
        "normalize_task_order_spec",
        "build_kernel_mission_command",
        "make_rule_based_leader_phase_manager",
        "make_scripted_c2_task_manager",
        "scripted_c2_task_manager_class",
        "is_patrol_task",
        "is_recover_task",
        "task_observation_codes",
        "infer_route_ref_id",
        "infer_recovery_base_id",
        "infer_recovery_runway_id",
        "infer_recovery_approach_type",
        "has_active_waypoint_leg",
        "landing_reference_heading_deg",
    )
    for name in residual_names:
        member = getattr(legacy_bridge, name)
        assert member.__module__ == "python.rl.tasking.bridge", name
        assert not hasattr(neutral_bridge_views, name), (
            f"{name!r} dispatches through python.rl-internal profile modules and must not "
            "leak into the neutral python.tasking_contracts.bridge_views module"
        )


def test_base_scripted_controller_shell_is_identical_to_the_neutral_layer() -> None:
    for name in neutral_base_scripted_controller.__all__:
        assert getattr(legacy_base_scripted_controller, name) is getattr(neutral_base_scripted_controller, name), name


def test_scripted_landing_shell_is_identical_to_the_neutral_layer() -> None:
    for name in neutral_scripted_landing.__all__:
        assert getattr(legacy_scripted_landing, name) is getattr(neutral_scripted_landing, name), name
    assert control_pkg.ScriptedLandingController is neutral_scripted_landing.ScriptedLandingController


def test_scripted_stable_flight_shell_is_identical_to_the_neutral_layer() -> None:
    for name in neutral_scripted_stable_flight.__all__:
        assert getattr(legacy_scripted_stable_flight, name) is getattr(neutral_scripted_stable_flight, name), name
    assert control_pkg.ScriptedStableFlightController is neutral_scripted_stable_flight.ScriptedStableFlightController


def test_scripted_takeoff_shell_is_identical_to_the_neutral_layer() -> None:
    for name in neutral_scripted_takeoff.__all__:
        assert getattr(legacy_scripted_takeoff, name) is getattr(neutral_scripted_takeoff, name), name
    assert control_pkg.ScriptedTakeoffController is neutral_scripted_takeoff.ScriptedTakeoffController


def test_leader_decision_state_shell_is_identical_to_the_neutral_layer() -> None:
    assert legacy_leader_window_runtime.LeaderDecisionState is neutral_leader_decision_state.LeaderDecisionState


def test_coerce_timing_dict_shell_is_identical_to_the_neutral_layer() -> None:
    assert legacy_execution_runtime.coerce_timing_dict is neutral_timing_utils.coerce_timing_dict
