from __future__ import annotations

import math
import json
import os
from typing import Any

from python.runtime_bootstrap import resolve_repo_path
from python.scenario.runtime.csg_replay import CSG_REPLAY_SCHEMA, capture_csg_replay

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


def _make_facade_loader() -> tuple[Any, Any]:
    """Create the maintained contract-test runtime and its world-indexed loader."""

    from python.rl.runtime.world_batch.adapter import RuntimeFacadeAdapter

    adapter = RuntimeFacadeAdapter(1)
    if not adapter.load_database(resolve_repo_path("examples", "config", "database")):
        raise RuntimeError("failed to load runtime database")
    return adapter, adapter.make_scenario_loader(0)


def _world_ref(ef_py: Any, entity_id: int) -> Any:
    ref = ef_py.WorldEntityRef()
    ref.world_index = 0
    ref.entity_id = int(entity_id)
    return ref




def _check_task_order_and_mission_link(spec: dict[str, Any]) -> tuple[bool, str]:
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

    adapter, loader = _make_facade_loader()
    entity_id = loader.load_scenario(
        resolve_repo_path("scenarios", "takeoff", "takeoff.json"),
        seed=0,
    )
    if entity_id is None:
        return False, "facade setup did not spawn an aircraft"
    sim = loader.sim

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

    ref = _world_ref(ef_py, entity_id)
    stored_order = adapter.get_task_orders_maintained_batch([ref])[0]
    stored_order_core = stored_order.shared_core
    if not bool(stored_order_core.active):
        return False, "stored task order is not active"
    expected_order = ef_py.task_order_maintained_batch_contract(order)
    if int(stored_order_core.task_id) != int(expected_order.shared_core.task_id):
        return False, f"stored task_id mismatch: {stored_order_core.task_id} != {expected_order.shared_core.task_id}"
    if int(stored_order.air_tasking_identity.task_type) != int(expected_order.air_tasking_identity.task_type):
        return False, (
            "stored task_type mismatch: "
            f"{stored_order.air_tasking_identity.task_type} != {expected_order.air_tasking_identity.task_type}"
        )
    if int(stored_order.air_stationing.station_type) != int(expected_order.air_stationing.station_type):
        return False, (
            "stored station_type mismatch: "
            f"{stored_order.air_stationing.station_type} != {expected_order.air_stationing.station_type}"
        )
    if not math.isclose(
        float(stored_order.air_stationing.target_speed_mps),
        float(expected_order.air_stationing.target_speed_mps),
        rel_tol=1e-6,
        abs_tol=1e-6,
    ):
        return False, (
            "stored target_speed mismatch: "
            f"{stored_order.air_stationing.target_speed_mps} != {expected_order.air_stationing.target_speed_mps}"
        )

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

    stored_intent = adapter.get_leader_intents_maintained_batch([ref])[0]
    if not bool(stored_intent.shared_core.active):
        return False, "stored leader intent is not active"
    if int(stored_intent.phase_id) != int(intent.phase_id):
        return False, f"stored phase_id mismatch: {stored_intent.phase_id} != {intent.phase_id}"
    if int(stored_intent.shared_core.command_code) != int(intent.command_code):
        return False, f"stored command_code mismatch: {stored_intent.shared_core.command_code} != {intent.command_code}"
    if not math.isclose(
        float(stored_intent.shared_core.cmd_heading_deg),
        float(intent.cmd_heading_deg),
        rel_tol=1e-6,
        abs_tol=1e-6,
    ):
        return False, (
            "stored intent heading mismatch: "
            f"{stored_intent.shared_core.cmd_heading_deg} != {intent.cmd_heading_deg}"
        )

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

    stored_report = adapter.get_pilot_reports_maintained_batch([ref])[0]
    if not bool(stored_report.shared_core.active):
        return False, "stored pilot report is not active"
    if int(stored_report.shared_core.report_type) != int(report.report_type):
        return False, f"stored report_type mismatch: {stored_report.shared_core.report_type} != {report.report_type}"
    if int(stored_report.shared_core.task_id) != int(report.task_id):
        return False, f"stored report task_id mismatch: {stored_report.shared_core.task_id} != {report.task_id}"
    if not math.isclose(
        float(stored_report.shared_core.location_z_m),
        float(report.location_z_m),
        rel_tol=1e-6,
        abs_tol=1e-6,
    ):
        return False, f"stored report altitude mismatch: {stored_report.shared_core.location_z_m} != {report.location_z_m}"

    latency_adapter, latency_loader = _make_facade_loader()
    latency_setup = ef_py.BatchWorldSetupRequest()
    latency_setup.seeds = [0]
    latency_terrain = ef_py.WorldTerrainAssignment()
    latency_terrain.world_index = 0
    latency_terrain.terrain_type = "flat"
    latency_wind = ef_py.WorldWindAssignment()
    latency_wind.world_index = 0
    latency_spawn = ef_py.WorldSpawnRequest()
    latency_spawn.world_index = 0
    latency_spawn.side = ef_py.Side.Blue
    latency_spawn.type_name = "F-16C_Block50"
    latency_spawn.entity_name = "LatencyAircraft"
    latency_spawn.is_agent = True
    latency_spawn.z = 1200.0
    latency_spawn.heading = 90.0
    latency_spawn.vy = 90.0
    latency_setup.terrain_assignments = [latency_terrain]
    latency_setup.wind_assignments = [latency_wind]
    latency_setup.spawn_requests = [latency_spawn]
    latency_setup.time_steps = [0.05]
    latency_entity_id = int(latency_adapter.apply_world_setup(latency_setup).entity_ids[0])
    latency_sim = latency_loader.sim
    command_link = dict(spec.get("command_link", {}) or {})
    link_assignment = ef_py.WorldCommandLinkAssignment()
    link_assignment.world_index = 0
    link_assignment.entity_id = latency_entity_id
    link_assignment.latency_s = float(command_link.get("latency_s", 0.2))
    link_assignment.drop_probability = float(command_link.get("loss_probability", 0.0))
    latency_adapter.set_command_links_batch([link_assignment])
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

    latency_ref = _world_ref(ef_py, latency_entity_id)
    before_contract = latency_adapter.get_mission_commands_maintained_batch([latency_ref])[0]
    before = before_contract.shared_core
    if bool(before.active):
        return False, "mission command should still be inactive before command-link latency elapses"
    if int(before.command_code) != int(spec.get("pre_link_command_code", 0)):
        return False, f"unexpected pre-link command_code {before.command_code}"
    for _ in range(int(spec.get("link_settle_steps", 20))):
        latency_sim.step()
    after_contract = latency_adapter.get_mission_commands_maintained_batch([latency_ref])[0]
    after = after_contract.shared_core
    if not bool(after.active):
        return False, "mission command did not activate after command-link latency"
    if int(after.command_code) != int(command.command_code):
        return False, f"post-link command_code mismatch: {after.command_code} != {command.command_code}"
    if not math.isclose(float(after.cmd_heading_deg), float(command.cmd_heading_deg), rel_tol=1e-6, abs_tol=1e-6):
        return False, f"post-link heading mismatch: {after.cmd_heading_deg} != {command.cmd_heading_deg}"
    if not math.isclose(float(after.cmd_altitude_m), float(command.cmd_altitude_m), rel_tol=1e-6, abs_tol=1e-6):
        return False, f"post-link altitude mismatch: {after.cmd_altitude_m} != {command.cmd_altitude_m}"
    if hasattr(command, "recovery_base_id") and int(after_contract.air_recovery.recovery_base_id) != int(getattr(command, "recovery_base_id", 0)):
        return False, f"post-link recovery_base_id mismatch: {after_contract.air_recovery.recovery_base_id} != {command.recovery_base_id}"
    if hasattr(command, "recovery_runway_id") and int(after_contract.air_recovery.recovery_runway_id) != int(getattr(command, "recovery_runway_id", 0)):
        return False, f"post-link recovery_runway_id mismatch: {after_contract.air_recovery.recovery_runway_id} != {command.recovery_runway_id}"
    if hasattr(command, "recovery_approach_type") and int(after_contract.air_recovery.recovery_approach_type) != int(getattr(command, "recovery_approach_type", 0)):
        return False, f"post-link recovery_approach_type mismatch: {after_contract.air_recovery.recovery_approach_type} != {command.recovery_approach_type}"
    return True, "task order / mission link contract passed"


def _check_task_order_common_core(spec: dict[str, Any]) -> tuple[bool, str]:
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

    # Expectations are an oracle: explicit enums must never fall back to the
    # production normalizer's defaults. Missing fields may still be inferred.
    enum_fields = _task_order_enum_fields()
    for name, raw in expected_common.items():
        namespace = enum_fields.get(name)
        if namespace is None:
            continue
        try:
            if isinstance(raw, str):
                value = getattr(namespace, raw)
                if not isinstance(value, namespace):
                    raise ValueError('not an enum member')
            elif isinstance(raw, namespace):
                value = raw
            elif isinstance(raw, int) and not isinstance(raw, bool):
                value = namespace(raw)
            else:
                raise ValueError('expected an enum name or integer member')
        except (AttributeError, TypeError, ValueError, RuntimeError):
            return False, f"invalid expected enum {name}: {raw!r}"
        # Compare explicit expectations directly, before any default inference.
        if name in _common_core_field_names('task_order'):
            if int(getattr(order, name)) != int(value):
                return False, f"task_order_common_core {name} mismatch: {getattr(order, name)} != {value}"

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


def _check_scenario_loader_mission_semantics(spec: dict[str, Any]) -> tuple[bool, str]:
    scenario_path, cleanup = _materialize_scenario_path(spec)
    try:
        _adapter, loader = _make_facade_loader()
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


def _check_scenario_loader_common_core_semantics(spec: dict[str, Any]) -> tuple[bool, str]:
    scenario_path, cleanup = _materialize_scenario_path(spec)
    try:
        _adapter, loader = _make_facade_loader()
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


def _run_naval_screen_check(spec: dict[str, Any], *, check_threat_roe: bool) -> tuple[bool, str]:
    import ef_py

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

        adapter, loader = _make_facade_loader()
        sim = loader.sim
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
        expected_mission = dict(spec.get("expected_runtime_mission_command", {}) or {})
        screen_ref = _world_ref(ef_py, screen_id)
        hvu_ref = _world_ref(ef_py, hvu_id)
        initial_contact_observation = adapter.get_agent_observation(0, contact_id)
        initial_screen_observation = adapter.get_agent_observation(0, screen_id)
        initial_contact_health = (
            float(getattr(initial_contact_observation, "health", 0.0)) if check_threat_roe else None
        )
        initial_screen_missiles = (
            int(getattr(initial_screen_observation, "missiles_remaining", -1))
            if check_threat_roe
            else None
        )

        first_screen_step = None
        first_hvu_shared_step = None
        first_hvu_report_step = None
        first_mission_active_step = None
        observed_mission_cmd = None
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
            if check_threat_roe:
                mission_contract = adapter.get_mission_commands_maintained_batch([screen_ref])[0]
                mission_cmd = mission_contract.shared_core
                if bool(getattr(mission_cmd, "active", False)):
                    if first_mission_active_step is None:
                        first_mission_active_step = step + 1
                    observed_mission_cmd = mission_cmd

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
                for msg in adapter.get_unit_messages_batch([hvu_ref])[0]:
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
        if check_threat_roe:
            if observed_mission_cmd is None:
                return False, "screen mission command never became observable/active for threat ROE contract"
            for field_name in (
                "active",
                "roe_state",
                "engagement_authority_holder_id",
                "engagement_authority_grantor_id",
                "authorization_to_fire",
            ):
                if field_name not in expected_mission:
                    continue
                actual_value = getattr(observed_mission_cmd, field_name)
                expected_value = expected_mission[field_name]
                if isinstance(expected_value, bool):
                    same = bool(actual_value) == bool(expected_value)
                else:
                    try:
                        same = int(actual_value) == int(expected_value)
                    except Exception:
                        same = actual_value == expected_value
                if not same:
                    return False, (
                        f"mission command {field_name} mismatch: "
                        f"{actual_value!r} != {expected_value!r}"
                    )
            expected_target_entity = str(expected_mission.get("assigned_target_entity", "") or "").strip()
            if expected_target_entity:
                expected_target_id = int(loader.entities.get(expected_target_entity, 0))
                if expected_target_id <= 0:
                    return False, f"expected assigned target entity is not loaded: {expected_target_entity!r}"
                actual_target_id = int(getattr(observed_mission_cmd, "assigned_target_id", 0))
                if actual_target_id != expected_target_id:
                    return False, (
                        f"mission command assigned_target_id mismatch: "
                        f"{actual_target_id} != {expected_target_id} ({expected_target_entity})"
                    )
            elif "assigned_target_id" in expected_mission:
                actual_target_id = int(getattr(observed_mission_cmd, "assigned_target_id", 0))
                expected_target_id = int(expected_mission["assigned_target_id"])
                if actual_target_id != expected_target_id:
                    return False, (
                        f"mission command assigned_target_id mismatch: "
                        f"{actual_target_id} != {expected_target_id}"
                    )

        runtime_checks = {
            "screen_first_detection_step": float(first_screen_step),
            "hvu_first_shared_track_step": float(first_hvu_shared_step),
            "hvu_first_report_step": float(first_hvu_report_step),
            "screen_hvu_separation_m_min": float(min_screen_hvu_m),
            "screen_hvu_separation_m_max": float(max_screen_hvu_m),
            "hvu_contact_closest_approach_m": float(min_hvu_contact_m),
        }
        if check_threat_roe:
            runtime_checks["mission_command_first_active_step"] = float(first_mission_active_step or max_steps + 1)
            final_contact_observation = adapter.get_agent_observation(0, contact_id)
            final_screen_observation = adapter.get_agent_observation(0, screen_id)
            runtime_checks["contact_health_delta"] = abs(
                float(getattr(final_contact_observation, "health", 0.0)) - float(initial_contact_health)
            )
            damage_request = ef_py.EngagementBatchRequest()
            damage_ref = ef_py.EngagementEntityRef()
            damage_ref.world_index = 0
            damage_ref.entity_id = contact_id
            damage_request.refs = [damage_ref]
            damage_request.include_track_packets = False
            damage_request.include_launch_requests = False
            damage_request.include_launch_events = False
            damage_request.include_munition_lifecycle_packets = False
            damage_request.include_effects_events = False
            damage_request.include_damage_reports = True
            damage_request.include_diagnostics_traces = False
            damage_packet = adapter.facade.export_engagement_event_packet(damage_request)
            runtime_checks["contact_damage_delta"] = float(
                sum(
                    1
                    for report in list(getattr(damage_packet, "damage_reports", []) or [])
                    if int(getattr(report, "target_id", getattr(report, "target_entity_id", 0)) or 0)
                    == contact_id
                )
            )
            runtime_checks["screen_weapon_inventory_delta"] = abs(
                int(getattr(final_screen_observation, "missiles_remaining", -1))
                - int(initial_screen_missiles)
            )
        for label, value in runtime_checks.items():
            bounds = checks.get(label, None)
            if isinstance(bounds, dict):
                message = _check_optional_range(value, bounds, label=label)
                if message is not None:
                    return False, message

        if check_threat_roe:
            return True, "naval screen threat/ROE pre-fire contract passed"
        return True, "naval screen/contact reporting contract passed"
    finally:
        if cleanup:
            try:
                os.remove(scenario_path)
            except OSError:
                pass


def _check_mission_command_landing_gear_hold(spec: dict[str, Any]) -> tuple[bool, str]:
    import ef_py

    scenario_path, cleanup = _materialize_scenario_path(spec)
    try:
        _adapter, loader = _make_facade_loader()
        sim = loader.sim
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


def _check_instrument_command_bug_semantics(spec: dict[str, Any]) -> tuple[bool, str]:
    import ef_py

    scenario_path, cleanup = _materialize_scenario_path(spec)
    try:
        _adapter, loader = _make_facade_loader()
        sim = loader.sim
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


def _check_naval_screen_contact_report(spec: dict[str, Any]) -> tuple[bool, str]:
    return _run_naval_screen_check(spec, check_threat_roe=False)


def _check_naval_screen_threat_roe(spec: dict[str, Any]) -> tuple[bool, str]:
    return _run_naval_screen_check(spec, check_threat_roe=True)


def _check_naval_csg_group_composition(spec: dict[str, Any]) -> tuple[bool, str]:
    import ef_py
    from gym_envs.scenario_loader import ScenarioLoader

    scenarios = list(spec.get("scenarios", []) or [])
    if not scenarios:
        return False, "naval_csg_group_composition requires a non-empty scenarios list"

    database = resolve_repo_path("examples", "config", "database")
    schema = str(spec.get("schema", "csg.group_composition.v2"))
    anchor = tuple(float(value) for value in list(spec.get("geodetic_anchor", []) or []))
    if len(anchor) != 3:
        return False, "geodetic_anchor must contain latitude, longitude, and height"

    for scenario_spec in scenarios:
        scenario_path = resolve_repo_path(str(scenario_spec["scenario"]))
        seed = int(scenario_spec.get("seed", spec.get("seed", 0)))
        sim = ef_py.SimulationKernel()
        sim.reset(1)
        if not sim.load_database(database):
            return False, f"database load failed for {scenario_path}"
        loader = ScenarioLoader(sim)
        if loader.load_scenario(scenario_path, seed=seed) is not None:
            return False, f"CSG S0 must remain agent-free: {scenario_path}"

        csg = loader._compiled_runtime_metadata.meta_config.get("csg")
        if not isinstance(csg, dict):
            return False, f"missing compiled CSG metadata: {scenario_path}"
        if csg.get("schema") != schema:
            return False, f"unexpected CSG schema in {scenario_path}: {csg.get('schema')!r}"
        if csg.get("geometry", {}).get("placement") != "geodetic":
            return False, f"CSG scenario is not geodetic: {scenario_path}"
        actual_anchor = tuple(float(value) for value in sim.get_geodetic_anchor())
        if any(not math.isclose(actual, expected, abs_tol=1.0e-9) for actual, expected in zip(actual_anchor, anchor)):
            return False, f"unexpected geodetic anchor in {scenario_path}: {actual_anchor!r}"

        expected_groups = list(scenario_spec.get("groups", []) or [])
        actual_groups = {str(group.get("group_id")): group for group in csg.get("groups", [])}
        if set(actual_groups) != {str(group["group_id"]) for group in expected_groups}:
            return False, f"unexpected CSG groups in {scenario_path}: {sorted(actual_groups)}"

        units = {int(unit.id): unit for unit in sim.get_all_units()}
        for expected in expected_groups:
            group_id = str(expected["group_id"])
            group = actual_groups[group_id]
            if group.get("side") != expected["side"]:
                return False, f"{scenario_path}: {group_id} side mismatch"
            hull_names = [name for row in group.get("ships", []) for name in row.get("entity_names", [])]
            if len(hull_names) != int(expected["hulls"]):
                return False, f"{scenario_path}: {group_id} hull count mismatch"
            inventory_count = sum(int(row.get("count", 0)) for row in group.get("embarked_inventory", []))
            if inventory_count != int(expected["aircraft"]):
                return False, f"{scenario_path}: {group_id} inventory count mismatch"
            side = int(ef_py.Side.Blue if expected["side"] == "Blue" else ef_py.Side.Red)
            side_units = [unit for unit in units.values() if int(unit.side) == side]
            if len(side_units) != int(expected["hulls"]) + int(expected["stowed_helos"]):
                return False, f"{scenario_path}: {group_id} live entity count mismatch"
            aircraft_count = sum(int(unit.type) == int(ef_py.UnitType.Aircraft) for unit in side_units)
            if aircraft_count != int(expected["stowed_helos"]):
                return False, f"{scenario_path}: {group_id} stowed helicopter count mismatch"
            for name in hull_names:
                if name not in loader.entities:
                    return False, f"{scenario_path}: missing loader entity {name}"
                if int(loader.entities[name]) not in units:
                    return False, f"{scenario_path}: missing runtime entity {name}"

        for _ in range(int(scenario_spec.get("steps", spec.get("steps", 0)))):
            sim.step()
            if not all(math.isfinite(float(value)) for unit in sim.get_all_units() for value in (unit.x, unit.y, unit.z)):
                return False, f"non-finite CSG runtime position: {scenario_path}"

    return True, f"naval CSG group-composition contract passed ({len(scenarios)} variant(s))"




def _check_naval_csg_replay(spec: dict[str, Any]) -> tuple[bool, str]:
    replay_ref = str(spec.get("replay", "")).strip()
    if not replay_ref:
        return False, "naval_csg_replay requires a replay path"
    replay_path = resolve_repo_path(replay_ref)
    try:
        with open(replay_path, "r", encoding="utf-8") as handle:
            artifact = json.load(handle)
    except Exception as exc:
        return False, f"failed to load CSG replay {replay_path}: {exc}"
    if artifact.get("schema") != CSG_REPLAY_SCHEMA:
        return False, f"unexpected CSG replay schema: {artifact.get('schema')!r}"
    scenario_ref = str(spec.get("scenario") or artifact.get("scenario") or "").strip()
    if not scenario_ref:
        return False, "CSG replay has no scenario reference"
    try:
        expected = capture_csg_replay(
            scenario_ref,
            seed=int(spec.get("seed", artifact.get("seed", 0))),
            max_steps=int(spec.get("max_steps", artifact.get("max_steps", 0))),
        )
    except Exception as exc:
        return False, f"native CSG replay regeneration failed: {exc}"
    if artifact.get("scenario_sha256") != expected["scenario_sha256"]:
        return False, "CSG replay scenario hash does not match the checked-in scenario"
    if int(artifact.get("seed", -1)) != int(expected["seed"]):
        return False, "CSG replay seed mismatch"
    frames = artifact.get("frames")
    expected_frames = expected["frames"]
    if not isinstance(frames, list) or len(frames) != len(expected_frames):
        return False, f"CSG replay frame count mismatch: {len(frames) if isinstance(frames, list) else 'invalid'} != {len(expected_frames)}"
    for index, (actual_frame, expected_frame) in enumerate(zip(frames, expected_frames)):
        if int(actual_frame.get("tick", -1)) != int(expected_frame["tick"]):
            return False, f"CSG replay tick mismatch at frame {index}"
        actual_units = actual_frame.get("units")
        expected_units = expected_frame["units"]
        if not isinstance(actual_units, list) or len(actual_units) != len(expected_units):
            return False, f"CSG replay roster mismatch at frame {index}"
        for actual_unit, expected_unit in zip(actual_units, expected_units):
            if int(actual_unit.get("id", -1)) != int(expected_unit["id"]):
                return False, f"CSG replay entity mismatch at frame {index}"
            for field in ("x", "y", "z", "heading"):
                if not math.isclose(float(actual_unit.get(field)), float(expected_unit[field]), rel_tol=1e-9, abs_tol=1e-6):
                    return False, f"CSG replay {field} mismatch at frame {index}, entity {expected_unit['id']}"
    return True, f"naval CSG replay contract passed ({len(frames)} frames)"


_COMM_CONTRACT_CHECKS = {
    "task_order_and_mission_link": _check_task_order_and_mission_link,
    "task_order_common_core": _check_task_order_common_core,
    "scenario_loader_mission_semantics": _check_scenario_loader_mission_semantics,
    "scenario_loader_common_core_semantics": _check_scenario_loader_common_core_semantics,
    "naval_screen_contact_report": _check_naval_screen_contact_report,
    "naval_screen_threat_roe": _check_naval_screen_threat_roe,
    "naval_csg_group_composition": _check_naval_csg_group_composition,
    "naval_csg_replay": _check_naval_csg_replay,
    "mission_command_landing_gear_hold": _check_mission_command_landing_gear_hold,
    "instrument_command_bug_semantics": _check_instrument_command_bug_semantics,
}


def run_comm_contract(check_kind: str, spec: dict[str, Any]) -> tuple[bool, str] | None:
    handler = _COMM_CONTRACT_CHECKS.get(check_kind)
    if handler is None:
        return None
    return handler(spec)
