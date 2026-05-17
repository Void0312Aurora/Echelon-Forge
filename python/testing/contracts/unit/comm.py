from __future__ import annotations

import math
import os
from typing import Any

from python.testing.runtime import resolve_repo_path

from ..common import _check_optional_range, _load_json_file, _materialize_scenario_path, _load_spec
from .common import (
    _air_leader_intent_field_names,
    _air_pilot_report_field_names,
    _air_task_order_field_names,
    _check_fields,
    _common_core_field_names,
    _enum_value_or_default,
    _recovery_approach_enum,
    _task_order_enum_fields,
)


def run_comm_contract(check_kind: str, spec: dict[str, Any]) -> tuple[bool, str] | None:
    if check_kind == "task_order_and_mission_link":
        import ef_py
        from python.rl.tasking.common_core_profile import (
            apply_leader_intent_common_core_defaults,
            apply_leader_intent_common_core_spec,
            apply_pilot_report_common_core_defaults,
            apply_pilot_report_common_core_spec,
            apply_task_order_common_core_defaults,
            apply_task_order_common_core_spec,
        )
        from python.rl.tasking.bridge import normalize_task_order_spec

        def _spawn_aircraft(sim):
            sim.load_database(resolve_repo_path("examples", "config", "database"))
            return sim.spawn_unit(
                ef_py.Side.Blue,
                "F-16C_Block50",
                0.0,
                0.0,
                1200.0,
                90.0,
                0.0,
                0.0,
                90.0,
                0.0,
                0.0,
            )

        sim = ef_py.SimulationKernel()
        entity_id = _spawn_aircraft(sim)

        order_spec = normalize_task_order_spec(dict(spec.get("task_order", {}) or {}))
        order = ef_py.TaskOrder()
        order.task_id = int(order_spec.get("task_id", 77))
        order.task_type = _enum_value_or_default(ef_py.TaskType, order_spec.get("task_type", None), "Idle")
        order.priority = int(order_spec.get("priority", 3))
        order.issuer_id = int(order_spec.get("issuer_id", 1001))
        order.assignee_id = int(order_spec.get("assignee_id", entity_id))
        order.anchor_x_m = float(order_spec.get("anchor_x_m", 12000.0))
        order.anchor_y_m = float(order_spec.get("anchor_y_m", -8000.0))
        order.anchor_z_m = float(order_spec.get("anchor_z_m", 6500.0))
        order.station_type = _enum_value_or_default(ef_py.StationType, order_spec.get("station_type", None), "Racetrack")
        order.station_radius_m = float(order_spec.get("station_radius_m", 18000.0))
        order.station_leg_length_m = float(order_spec.get("station_leg_length_m", 30000.0))
        order.station_heading_deg = float(order_spec.get("station_heading_deg", 45.0))
        order.target_altitude_m = float(order_spec.get("target_altitude_m", 7000.0))
        order.target_speed_mps = float(order_spec.get("target_speed_mps", 210.0))
        order.on_station_time_s = float(order_spec.get("on_station_time_s", 900.0))
        order.recovery_base_id = int(order_spec.get("recovery_base_id", 55))
        order.recovery_runway_id = int(order_spec.get("recovery_runway_id", 7))
        if hasattr(order, "recovery_approach_type"):
            order.recovery_approach_type = _recovery_approach_enum(order_spec.get("recovery_approach_type", "None"))
        apply_task_order_common_core_spec(order, order_spec)
        apply_task_order_common_core_defaults(order)
        sim.set_task_order(entity_id, order)

        stored_order = sim.get_task_order(entity_id)
        if not bool(stored_order.active):
            return False, "stored task order is not active"
        if int(stored_order.task_id) != int(order.task_id):
            return False, f"stored task_id mismatch: {stored_order.task_id} != {order.task_id}"
        if int(stored_order.task_type) != int(order.task_type):
            return False, f"stored task_type mismatch: {stored_order.task_type} != {order.task_type}"
        if int(stored_order.station_type) != int(order.station_type):
            return False, f"stored station_type mismatch: {stored_order.station_type} != {order.station_type}"
        if not math.isclose(float(stored_order.target_speed_mps), float(order.target_speed_mps), rel_tol=1e-6, abs_tol=1e-6):
            return False, f"stored target_speed mismatch: {stored_order.target_speed_mps} != {order.target_speed_mps}"
        ok, detail = _check_fields(
            stored_order,
            order,
            _common_core_field_names("task_order"),
            label="task_order",
        )
        if not ok:
            return False, detail
        ok, detail = _check_fields(
            stored_order,
            order,
            _air_task_order_field_names(),
            label="task_order_air",
        )
        if not ok:
            return False, detail

        intent_spec = dict(spec.get("leader_intent", {}) or {})
        intent = ef_py.LeaderIntent()
        intent.phase_id = _enum_value_or_default(ef_py.LeaderPhase, intent_spec.get("phase_id", None), "TransitToStation")
        intent.command_code = int(intent_spec.get("command_code", 3))
        if hasattr(intent, "route_ref_id"):
            intent.route_ref_id = int(intent_spec.get("route_ref_id", 0))
        if hasattr(intent, "recovery_base_id"):
            intent.recovery_base_id = int(intent_spec.get("recovery_base_id", order.recovery_base_id))
        if hasattr(intent, "recovery_runway_id"):
            intent.recovery_runway_id = int(intent_spec.get("recovery_runway_id", order.recovery_runway_id))
        if hasattr(intent, "recovery_approach_type"):
            intent.recovery_approach_type = _recovery_approach_enum(
                intent_spec.get("recovery_approach_type", order_spec.get("recovery_approach_type", "None"))
            )
        intent.cmd_heading_deg = float(intent_spec.get("cmd_heading_deg", 135.0))
        intent.cmd_altitude_m = float(intent_spec.get("cmd_altitude_m", 6800.0))
        intent.cmd_speed_mps = float(intent_spec.get("cmd_speed_mps", 205.0))
        intent.approach_armed = bool(intent_spec.get("approach_armed", False))
        apply_leader_intent_common_core_spec(intent, intent_spec)
        apply_leader_intent_common_core_defaults(intent, order=order, default_tactical_unit_id=int(entity_id))
        sim.set_leader_intent(entity_id, intent)

        stored_intent = sim.get_leader_intent(entity_id)
        if not bool(stored_intent.active):
            return False, "stored leader intent is not active"
        if int(stored_intent.phase_id) != int(intent.phase_id):
            return False, f"stored phase_id mismatch: {stored_intent.phase_id} != {intent.phase_id}"
        if int(stored_intent.command_code) != int(intent.command_code):
            return False, f"stored command_code mismatch: {stored_intent.command_code} != {intent.command_code}"
        if not math.isclose(float(stored_intent.cmd_heading_deg), float(intent.cmd_heading_deg), rel_tol=1e-6, abs_tol=1e-6):
            return False, f"stored intent heading mismatch: {stored_intent.cmd_heading_deg} != {intent.cmd_heading_deg}"
        ok, detail = _check_fields(
            stored_intent,
            intent,
            _common_core_field_names("leader_intent"),
            label="leader_intent",
        )
        if not ok:
            return False, detail
        ok, detail = _check_fields(
            stored_intent,
            intent,
            _air_leader_intent_field_names(),
            label="leader_intent_air",
        )
        if not ok:
            return False, detail

        report_spec = dict(spec.get("pilot_report", {}) or {})
        report = ef_py.PilotReport()
        report.report_type = _enum_value_or_default(ef_py.CommMsgType, report_spec.get("report_type", None), "REP_ON_STATION")
        report.sender_id = int(report_spec.get("sender_id", entity_id))
        report.task_id = int(report_spec.get("task_id", order.task_id))
        report.phase_id = int(_enum_value_or_default(ef_py.LeaderPhase, report_spec.get("phase_id", None), "OnStation"))
        report.timestamp_s = float(report_spec.get("timestamp_s", 12.5))
        report.status_value = float(report_spec.get("status_value", 1.0))
        report.location_x_m = float(report_spec.get("location_x_m", 12010.0))
        report.location_y_m = float(report_spec.get("location_y_m", -7990.0))
        report.location_z_m = float(report_spec.get("location_z_m", 6980.0))
        apply_pilot_report_common_core_spec(report, report_spec)
        apply_pilot_report_common_core_defaults(report, order=order, default_tactical_unit_id=int(entity_id))
        sim.set_pilot_report(entity_id, report)

        stored_report = sim.get_pilot_report(entity_id)
        if not bool(stored_report.active):
            return False, "stored pilot report is not active"
        if int(stored_report.report_type) != int(report.report_type):
            return False, f"stored report_type mismatch: {stored_report.report_type} != {report.report_type}"
        if int(stored_report.task_id) != int(report.task_id):
            return False, f"stored report task_id mismatch: {stored_report.task_id} != {report.task_id}"
        if not math.isclose(float(stored_report.location_z_m), float(report.location_z_m), rel_tol=1e-6, abs_tol=1e-6):
            return False, f"stored report altitude mismatch: {stored_report.location_z_m} != {report.location_z_m}"
        ok, detail = _check_fields(
            stored_report,
            report,
            _common_core_field_names("pilot_report"),
            label="pilot_report",
        )
        if not ok:
            return False, detail
        ok, detail = _check_fields(
            stored_report,
            report,
            _air_pilot_report_field_names(),
            label="pilot_report_air",
        )
        if not ok:
            return False, detail

        latency_sim = ef_py.SimulationKernel()
        latency_entity_id = _spawn_aircraft(latency_sim)
        command_link = dict(spec.get("command_link", {}) or {})
        latency_sim.set_command_link(
            latency_entity_id,
            float(command_link.get("latency_s", 0.2)),
            float(command_link.get("loss_probability", 0.0)),
        )
        mission_spec = dict(spec.get("mission_command", {}) or {})
        command = ef_py.MissionCommand()
        command.cmd_heading_deg = float(mission_spec.get("cmd_heading_deg", 222.0))
        command.cmd_altitude_m = float(mission_spec.get("cmd_altitude_m", 5000.0))
        command.cmd_speed_mps = float(mission_spec.get("cmd_speed_mps", 190.0))
        command.command_code = int(mission_spec.get("command_code", 4))
        if hasattr(command, "route_ref_id"):
            command.route_ref_id = int(mission_spec.get("route_ref_id", 0))
        if hasattr(command, "recovery_base_id"):
            command.recovery_base_id = int(mission_spec.get("recovery_base_id", order.recovery_base_id))
        if hasattr(command, "recovery_runway_id"):
            command.recovery_runway_id = int(mission_spec.get("recovery_runway_id", order.recovery_runway_id))
        if hasattr(command, "recovery_approach_type"):
            command.recovery_approach_type = _recovery_approach_enum(
                mission_spec.get("recovery_approach_type", order_spec.get("recovery_approach_type", "None"))
            )
        latency_sim.set_mission_command(latency_entity_id, command)

        before = latency_sim.get_mission_command(latency_entity_id)
        if bool(before.active):
            return False, "mission command should still be inactive before command-link latency elapses"
        if int(before.command_code) != int(spec.get("pre_link_command_code", 0)):
            return False, f"unexpected pre-link command_code {before.command_code}"
        for _ in range(int(spec.get("link_settle_steps", 20))):
            latency_sim.step()
        after = latency_sim.get_mission_command(latency_entity_id)
        if not bool(after.active):
            return False, "mission command did not activate after command-link latency"
        if int(after.command_code) != int(command.command_code):
            return False, f"post-link command_code mismatch: {after.command_code} != {command.command_code}"
        if not math.isclose(float(after.cmd_heading_deg), float(command.cmd_heading_deg), rel_tol=1e-6, abs_tol=1e-6):
            return False, f"post-link heading mismatch: {after.cmd_heading_deg} != {command.cmd_heading_deg}"
        if not math.isclose(float(after.cmd_altitude_m), float(command.cmd_altitude_m), rel_tol=1e-6, abs_tol=1e-6):
            return False, f"post-link altitude mismatch: {after.cmd_altitude_m} != {command.cmd_altitude_m}"
        if hasattr(command, "recovery_base_id") and int(getattr(after, "recovery_base_id", 0)) != int(getattr(command, "recovery_base_id", 0)):
            return False, f"post-link recovery_base_id mismatch: {after.recovery_base_id} != {command.recovery_base_id}"
        if hasattr(command, "recovery_runway_id") and int(getattr(after, "recovery_runway_id", 0)) != int(getattr(command, "recovery_runway_id", 0)):
            return False, f"post-link recovery_runway_id mismatch: {after.recovery_runway_id} != {command.recovery_runway_id}"
        if hasattr(command, "recovery_approach_type") and int(getattr(after, "recovery_approach_type", 0)) != int(getattr(command, "recovery_approach_type", 0)):
            return False, f"post-link recovery_approach_type mismatch: {after.recovery_approach_type} != {command.recovery_approach_type}"
        return True, "task order / mission link contract passed"

    if check_kind == "task_order_common_core":
        import ef_py
        from python.rl.tasking.common_core_profile import (
            apply_task_order_common_core_defaults,
            apply_task_order_common_core_spec,
        )
        from python.rl.tasking.bridge import normalize_task_order_spec

        order_spec = normalize_task_order_spec(dict(spec.get("task_order", {}) or {}))
        order = ef_py.TaskOrder()
        apply_task_order_common_core_spec(order, order_spec)
        apply_task_order_common_core_defaults(
            order,
            task_name=str(spec.get("task_name", "") or "").strip().upper() or None,
            phase_name=str(spec.get("phase_name", "") or "").strip().lower() or None,
            force_task_family=bool(spec.get("force_task_family", False)),
            force_coordination_mode=bool(spec.get("force_coordination_mode", False)),
        )

        expected_common = dict(spec.get("expected_common_core", spec.get("expected_task_order", {})) or {})
        if not expected_common:
            expected_common = dict(order_spec)

        expected = ef_py.TaskOrder()
        apply_task_order_common_core_spec(expected, expected_common)
        apply_task_order_common_core_defaults(
            expected,
            task_name=str(spec.get("task_name", "") or "").strip().upper() or None,
            phase_name=str(spec.get("phase_name", "") or "").strip().lower() or None,
            force_task_family=bool(spec.get("force_task_family", False)),
            force_coordination_mode=bool(spec.get("force_coordination_mode", False)),
        )
        ok, detail = _check_fields(order, expected, _common_core_field_names("task_order"), label="task_order_common_core")
        if not ok:
            return False, detail
        return True, "task order common-core contract passed"

    if check_kind == "scenario_loader_mission_semantics":
        import ef_py
        from gym_envs.scenario_loader import ScenarioLoader

        scenario_path, cleanup = _materialize_scenario_path(spec)
        try:
            sim = ef_py.SimulationKernel()
            sim.load_database(resolve_repo_path("examples", "config", "database"))
            loader = ScenarioLoader(sim)
            randomization_overrides = dict(spec.get("randomization_overrides", {}) or {})
            if randomization_overrides:
                loader.set_randomization_overrides(randomization_overrides)
            seed = int(spec.get("seed", 0))
            agent_id = loader.load_scenario(scenario_path, seed=seed)
            if agent_id is None:
                return False, "scenario did not spawn an agent"

            expected_initial = dict(spec.get("expected_initial", {}) or {})
            for key, expected in expected_initial.items():
                got = loader.mission_cmd.get(key, None)
                if got != expected:
                    return False, f"initial mission_cmd[{key!r}] mismatch: {got!r} != {expected!r}"

            expected_task_order_common = dict(
                spec.get("expected_task_order_common_core", spec.get("expected_task_order", {})) or {}
            )
            expected_task_order_air = dict(spec.get("expected_task_order_air", {}) or {})
            if expected_task_order_common or expected_task_order_air:
                task_order_spec = loader._task_order_spec()
                enum_fields = _task_order_enum_fields()
                for key, expected in expected_task_order_common.items():
                    got = task_order_spec.get(key, None)
                    namespace = enum_fields.get(key, None)
                    if namespace is not None and isinstance(expected, str):
                        expected = getattr(namespace, expected, expected)
                    try:
                        same = int(got) == int(expected)
                    except Exception:
                        same = got == expected
                    if not same:
                        return False, f"task_order common-core[{key!r}] mismatch: {got!r} != {expected!r}"
                for key, expected in expected_task_order_air.items():
                    got = task_order_spec.get(key, None)
                    namespace = enum_fields.get(key, None)
                    if namespace is not None and isinstance(expected, str):
                        expected = getattr(namespace, expected, expected)
                    try:
                        same = int(got) == int(expected)
                    except Exception:
                        same = got == expected
                    if not same:
                        return False, f"task_order air[{key!r}] mismatch: {got!r} != {expected!r}"

            expected_post = dict(spec.get("expected_post_transition_air", spec.get("expected_post_transition", {})) or {})
            if expected_post:
                post = getattr(loader, "post_waypoint_transition", None)
                if not isinstance(post, dict):
                    return False, "expected normalized post_waypoint_transition, got none"
                for key, expected in expected_post.items():
                    got = post.get(key, None)
                    if got != expected:
                        return False, f"post transition field {key!r} mismatch: {got!r} != {expected!r}"

            if bool(spec.get("activate_post_transition", True)):
                transitioned = loader._activate_post_waypoint_transition()
                if not isinstance(transitioned, dict):
                    return False, "post_waypoint_transition did not activate"
                expected_activated = dict(spec.get("expected_activated", expected_post) or {})
                for key, expected in expected_activated.items():
                    got = loader.mission_cmd.get(key, None)
                    if got != expected:
                        return False, f"activated mission_cmd[{key!r}] mismatch: {got!r} != {expected!r}"
            return True, "scenario loader mission semantics contract passed"
        finally:
            if cleanup:
                try:
                    os.remove(scenario_path)
                except OSError:
                    pass

    if check_kind == "scenario_loader_common_core_semantics":
        import ef_py
        from gym_envs.scenario_loader import ScenarioLoader

        scenario_path, cleanup = _materialize_scenario_path(spec)
        try:
            sim = ef_py.SimulationKernel()
            sim.load_database(resolve_repo_path("examples", "config", "database"))
            loader = ScenarioLoader(sim)
            randomization_overrides = dict(spec.get("randomization_overrides", {}) or {})
            if randomization_overrides:
                loader.set_randomization_overrides(randomization_overrides)
            seed = int(spec.get("seed", 0))
            agent_id = loader.load_scenario(scenario_path, seed=seed)
            if agent_id is None:
                return False, "scenario did not spawn an agent"

            expected_task_order = dict(spec.get("expected_task_order_common_core", spec.get("expected_task_order", {})) or {})
            if not expected_task_order:
                return False, "scenario_loader_common_core_semantics requires expected_task_order_common_core"
            task_order_spec = loader._task_order_spec()
            enum_fields = _task_order_enum_fields()
            for key, expected in expected_task_order.items():
                got = task_order_spec.get(key, None)
                namespace = enum_fields.get(key, None)
                if namespace is not None and isinstance(expected, str):
                    expected = getattr(namespace, expected, expected)
                try:
                    same = int(got) == int(expected)
                except Exception:
                    same = got == expected
                if not same:
                    return False, f"task_order common-core[{key!r}] mismatch: {got!r} != {expected!r}"
            return True, "scenario loader common-core semantics contract passed"
        finally:
            if cleanup:
                try:
                    os.remove(scenario_path)
                except OSError:
                    pass

    if check_kind == "naval_screen_contact_report":
        import ef_py
        from gym_envs.scenario_loader import ScenarioLoader

        scenario_path, cleanup = _materialize_scenario_path(spec)
        try:
            scenario_data = _load_json_file(scenario_path)
            entities_cfg = scenario_data.get("entities", [])
            if not isinstance(entities_cfg, list):
                return False, "scenario entities must be a list"

            entities_by_name = {
                str(item.get("name", "")).strip(): item
                for item in entities_cfg
                if isinstance(item, dict) and str(item.get("name", "")).strip()
            }

            screen_name = str(spec.get("screen_entity", "")).strip()
            hvu_name = str(spec.get("hvu_entity", "")).strip()
            contact_name = str(spec.get("contact_entity", "")).strip()
            if not screen_name or not hvu_name or not contact_name:
                return False, "naval_screen_contact_report requires screen_entity, hvu_entity, and contact_entity"

            for required_name in (screen_name, hvu_name, contact_name):
                if required_name not in entities_by_name:
                    return False, f"scenario is missing entity {required_name!r}"

            def _entity_position(name: str) -> tuple[float, float, float]:
                pos = entities_by_name[name].get("pos", None)
                if not isinstance(pos, list) or len(pos) < 3:
                    raise ValueError(f"entity {name!r} is missing 3D pos")
                return (float(pos[0]), float(pos[1]), float(pos[2]))

            screen_pos0 = _entity_position(screen_name)
            hvu_pos0 = _entity_position(hvu_name)
            contact_pos0 = _entity_position(contact_name)

            checks = dict(spec.get("checks", {}) or {})
            initial_screen_hvu_m = float(math.dist(screen_pos0, hvu_pos0))
            initial_screen_contact_m = float(math.dist(screen_pos0, contact_pos0))
            initial_hvu_contact_m = float(math.dist(hvu_pos0, contact_pos0))

            for label, value in (
                ("initial_screen_hvu_separation_m", initial_screen_hvu_m),
                ("initial_screen_contact_range_m", initial_screen_contact_m),
                ("initial_hvu_contact_range_m", initial_hvu_contact_m),
            ):
                bounds = checks.get(label, None)
                if isinstance(bounds, dict):
                    message = _check_optional_range(value, bounds, label=label)
                    if message is not None:
                        return False, message

            sim = ef_py.SimulationKernel()
            sim.load_database(resolve_repo_path("examples", "config", "database"))
            loader = ScenarioLoader(sim)
            seed = int(spec.get("seed", 0))
            agent_id = loader.load_scenario(scenario_path, seed=seed)
            if agent_id is None:
                return False, "scenario did not spawn an agent"

            if int(agent_id) != int(loader.entities.get(screen_name, 0)):
                return False, "screen entity was not selected as the active agent"

            screen_id = int(loader.entities[screen_name])
            hvu_id = int(loader.entities[hvu_name])
            contact_id = int(loader.entities[contact_name])

            max_steps = max(1, int(spec.get("max_steps", 80)))
            continue_after_contact_chain = bool(spec.get("continue_after_contact_chain", False))
            screen_required_first_source = int(spec.get("screen_required_first_source", 1))
            hvu_required_shared_source = int(spec.get("hvu_required_shared_source", 3))
            report_msg_type = int(getattr(ef_py.CommMsgType, str(spec.get("report_message_type", "ReportContact"))))
            forbid_hvu_local_source = bool(spec.get("forbid_hvu_local_source", True))

            first_screen_step = None
            first_hvu_shared_step = None
            first_hvu_report_step = None
            first_screen_source = None
            hvu_local_source_seen = False
            min_screen_hvu_m = float("inf")
            max_screen_hvu_m = 0.0
            min_hvu_contact_m = float("inf")

            for step in range(max_steps):
                sim.step()
                screen_obs = sim.get_agent_observation(screen_id)
                hvu_obs = sim.get_agent_observation(hvu_id)

                screen_tracks = {
                    int(getattr(track, "id", 0)): track
                    for track in getattr(screen_obs, "contacts", [])
                }
                hvu_tracks = {
                    int(getattr(track, "id", 0)): track
                    for track in getattr(hvu_obs, "contacts", [])
                }

                screen_pos = sim.get_unit_position(screen_id)
                hvu_pos = sim.get_unit_position(hvu_id)
                contact_pos = sim.get_unit_position(contact_id)

                screen_hvu_m = float(math.dist(screen_pos, hvu_pos))
                hvu_contact_m = float(math.dist(hvu_pos, contact_pos))
                min_screen_hvu_m = min(min_screen_hvu_m, screen_hvu_m)
                max_screen_hvu_m = max(max_screen_hvu_m, screen_hvu_m)
                min_hvu_contact_m = min(min_hvu_contact_m, hvu_contact_m)

                if contact_id in screen_tracks and first_screen_step is None:
                    first_screen_step = step + 1
                    first_screen_source = int(getattr(screen_tracks[contact_id], "source", 0))

                if contact_id in hvu_tracks:
                    track_source = int(getattr(hvu_tracks[contact_id], "source", 0))
                    if track_source == 1:
                        hvu_local_source_seen = True
                    if track_source == hvu_required_shared_source and first_hvu_shared_step is None:
                        first_hvu_shared_step = step + 1

                if first_hvu_report_step is None:
                    for msg in sim.get_unit_messages(hvu_id):
                        if (
                            int(getattr(msg, "type", 0)) == report_msg_type
                            and int(getattr(msg, "entity_ref", 0)) == contact_id
                        ):
                            first_hvu_report_step = step + 1
                            break

                if (
                    first_screen_step is not None
                    and first_hvu_shared_step is not None
                    and first_hvu_report_step is not None
                    and not continue_after_contact_chain
                ):
                    break

            if first_screen_step is None:
                return False, "screen never acquired the contact track"
            if int(first_screen_source or 0) != screen_required_first_source:
                return False, (
                    f"screen first contact source mismatch: {first_screen_source} != {screen_required_first_source}"
                )
            if first_hvu_shared_step is None:
                return False, "HVU never received the shared contact track"
            if first_hvu_report_step is None:
                return False, "HVU never received the contact report message"
            if first_hvu_shared_step < first_screen_step:
                return False, "HVU shared track appeared before the screen detected the contact"
            if first_hvu_report_step < first_screen_step:
                return False, "HVU report arrived before the screen detected the contact"
            if forbid_hvu_local_source and hvu_local_source_seen:
                return False, "HVU unexpectedly acquired a local radar track inside the blind-zone contract"

            runtime_checks = {
                "screen_first_detection_step": float(first_screen_step),
                "hvu_first_shared_track_step": float(first_hvu_shared_step),
                "hvu_first_report_step": float(first_hvu_report_step),
                "screen_hvu_separation_m_min": float(min_screen_hvu_m),
                "screen_hvu_separation_m_max": float(max_screen_hvu_m),
                "hvu_contact_closest_approach_m": float(min_hvu_contact_m),
            }
            for label, value in runtime_checks.items():
                bounds = checks.get(label, None)
                if isinstance(bounds, dict):
                    message = _check_optional_range(value, bounds, label=label)
                    if message is not None:
                        return False, message

            return True, "naval screen/contact reporting contract passed"
        finally:
            if cleanup:
                try:
                    os.remove(scenario_path)
                except OSError:
                    pass

    if check_kind == "mission_command_landing_gear_hold":
        import ef_py
        from gym_envs.scenario_loader import ScenarioLoader

        scenario_path, cleanup = _materialize_scenario_path(spec)
        try:
            sim = ef_py.SimulationKernel()
            sim.load_database(resolve_repo_path("examples", "config", "database"))
            loader = ScenarioLoader(sim)
            randomization_overrides = dict(spec.get("randomization_overrides", {}) or {})
            if randomization_overrides:
                loader.set_randomization_overrides(randomization_overrides)
            seed = int(spec.get("seed", 0))
            agent_id = loader.load_scenario(scenario_path, seed=seed)
            if agent_id is None:
                return False, "scenario did not spawn an agent"

            mission_spec = dict(spec.get("mission_command", {}) or {})
            cmd = ef_py.MissionCommand()
            cmd.active = True
            cmd.command_code = int(mission_spec.get("command_code", 4))
            cmd.cmd_heading_deg = float(mission_spec.get("cmd_heading_deg", 90.0))
            cmd.cmd_altitude_m = float(mission_spec.get("cmd_altitude_m", 0.0))
            cmd.cmd_speed_mps = float(mission_spec.get("cmd_speed_mps", 82.0))
            if hasattr(cmd, "recovery_base_id"):
                cmd.recovery_base_id = int(mission_spec.get("recovery_base_id", 1))
            if hasattr(cmd, "recovery_runway_id"):
                cmd.recovery_runway_id = int(mission_spec.get("recovery_runway_id", 1))
            if hasattr(cmd, "recovery_approach_type") and hasattr(ef_py, "RecoveryApproachType"):
                raw = mission_spec.get("recovery_approach_type", "ILS")
                cmd.recovery_approach_type = (
                    getattr(ef_py.RecoveryApproachType, str(raw), ef_py.RecoveryApproachType.ILS)
                    if isinstance(raw, str)
                    else ef_py.RecoveryApproachType(int(raw))
                )
            sim.set_mission_command(agent_id, cmd)

            min_gear_pos = float("inf")
            step_count = int(spec.get("step_count", 30))
            for _ in range(step_count):
                sim.step()
                truth = sim.get_agent_observation(agent_id)
                if float(getattr(truth, "health", 0.0)) <= 0.0:
                    return False, "aircraft crashed during landing gear hold contract"
                inst = sim.get_instrument_state(agent_id)
                min_gear_pos = min(min_gear_pos, float(getattr(inst, "gear_pos", 0.0)))

            required_min = float(spec.get("min_gear_pos", 0.9))
            if min_gear_pos < required_min:
                return False, f"landing command retracted gear too far: min gear_pos={min_gear_pos:.3f} < {required_min:.3f}"
            return True, f"landing gear hold contract passed with min gear_pos={min_gear_pos:.3f}"
        finally:
            if cleanup:
                try:
                    os.remove(scenario_path)
                except OSError:
                    pass

    if check_kind == "instrument_command_bug_semantics":
        import ef_py
        from gym_envs.scenario_loader import ScenarioLoader

        scenario_path, cleanup = _materialize_scenario_path(spec)
        try:
            sim = ef_py.SimulationKernel()
            sim.load_database(resolve_repo_path("examples", "config", "database"))
            loader = ScenarioLoader(sim)
            randomization_overrides = dict(spec.get("randomization_overrides", {}) or {})
            if randomization_overrides:
                loader.set_randomization_overrides(randomization_overrides)
            seed = int(spec.get("seed", 0))
            agent_id = loader.load_scenario(scenario_path, seed=seed)
            if agent_id is None:
                return False, "scenario did not spawn an agent"

            mission_spec = dict(spec.get("mission_command", {}) or {})
            cmd = ef_py.MissionCommand()
            cmd.active = True
            cmd.command_code = int(mission_spec.get("command_code", 3))
            cmd.cmd_heading_deg = float(mission_spec.get("cmd_heading_deg", 90.0))
            cmd.cmd_altitude_m = float(mission_spec.get("cmd_altitude_m", 1200.0))
            cmd.cmd_speed_mps = float(mission_spec.get("cmd_speed_mps", 180.0))
            if hasattr(cmd, "route_ref_id"):
                cmd.route_ref_id = int(mission_spec.get("route_ref_id", 0))
            if hasattr(cmd, "recovery_base_id"):
                cmd.recovery_base_id = int(mission_spec.get("recovery_base_id", 0))
            if hasattr(cmd, "recovery_runway_id"):
                cmd.recovery_runway_id = int(mission_spec.get("recovery_runway_id", 0))
            if hasattr(cmd, "recovery_approach_type") and hasattr(ef_py, "RecoveryApproachType"):
                raw = mission_spec.get("recovery_approach_type", "None")
                default_recovery = getattr(ef_py.RecoveryApproachType, "None")
                cmd.recovery_approach_type = (
                    getattr(ef_py.RecoveryApproachType, str(raw), default_recovery)
                    if isinstance(raw, str)
                    else ef_py.RecoveryApproachType(int(raw))
                )
            sim.set_mission_command(agent_id, cmd)

            inst = None
            step_count = max(1, int(spec.get("step_count", 1)))
            for _ in range(step_count):
                sim.step()
                truth = sim.get_agent_observation(agent_id)
                if float(getattr(truth, "health", 0.0)) <= 0.0:
                    return False, "aircraft crashed during instrument command bug contract"
                inst = sim.get_instrument_state(agent_id)

            if inst is None:
                inst = sim.get_instrument_state(agent_id)
            expected = dict(spec.get("expected", {}) or {})
            heading_tol = float(expected.get("heading_tol_deg", 1.0e-3))
            scalar_tol = float(expected.get("scalar_tol", 1.0e-3))

            if "cmd_heading_deg" in expected:
                actual_heading = float(
                    getattr(inst, "cmd_heading", getattr(inst, "cmd_heading_deg", 0.0))
                )
                if not math.isclose(actual_heading, float(expected["cmd_heading_deg"]), rel_tol=1.0e-6, abs_tol=heading_tol):
                    return False, (
                        f"instrument cmd_heading mismatch: {actual_heading:.6f} != "
                        f"{float(expected['cmd_heading_deg']):.6f}"
                    )
            if "cmd_alt_m" in expected:
                actual_alt = float(getattr(inst, "cmd_alt", getattr(inst, "cmd_alt_m", 0.0)))
                if not math.isclose(actual_alt, float(expected["cmd_alt_m"]), rel_tol=1.0e-6, abs_tol=scalar_tol):
                    return False, f"instrument cmd_alt mismatch: {actual_alt:.6f} != {float(expected['cmd_alt_m']):.6f}"
            if "cmd_speed_mps" in expected:
                actual_speed = float(getattr(inst, "cmd_speed", getattr(inst, "cmd_speed_mps", 0.0)))
                if not math.isclose(actual_speed, float(expected["cmd_speed_mps"]), rel_tol=1.0e-6, abs_tol=scalar_tol):
                    return False, (
                        f"instrument cmd_speed mismatch: {actual_speed:.6f} != "
                        f"{float(expected['cmd_speed_mps']):.6f}"
                    )
            return True, "instrument command bug semantics contract passed"
        finally:
            if cleanup:
                try:
                    os.remove(scenario_path)
                except OSError:
                    pass

    return None
