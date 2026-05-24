from __future__ import annotations

import re
from pathlib import Path

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402


_DB_PATH = resolve_repo_path("examples", "config", "database")


def _read(path: str) -> str:
    return Path(resolve_repo_path(path)).read_text(encoding="utf-8")


def test_simulation_kernel_exposes_read_only_recent_engagement_events_getter() -> None:
    header = _read("src/core/engine/simulation_kernel.h")
    observation_api = _read("src/core/engine/simulation_kernel_observation_api.cpp")

    assert "struct RecentEngagementEvents" in header
    assert "RecentEngagementEvents export_recent_engagement_events() const" in header
    assert "runtime/contracts/engagement_contracts.h" in header
    assert "SimulationKernel::export_recent_engagement_events() const" in observation_api

    getter_body = re.search(
        r"RecentEngagementEvents SimulationKernel::export_recent_engagement_events\(\) const \{(?P<body>.*?)\n\}",
        observation_api,
        re.DOTALL,
    )
    assert getter_body is not None
    assert "std::sort" in getter_body.group("body")
    assert "fire_missile" not in getter_body.group("body")
    assert "fire_naval_weapon" not in getter_body.group("body")
    assert "debug_apply_proximity_hit" not in getter_body.group("body")
    assert "lhs.event_id < rhs.event_id" in getter_body.group("body")
    assert "lhs.trace_id < rhs.trace_id" in getter_body.group("body")


def test_legacy_fire_and_debug_damage_paths_record_compatible_event_dtos() -> None:
    weapon_api = _read("src/core/engine/simulation_kernel_weapon_api.cpp")
    damage_api = _read("src/core/engine/simulation_kernel_damage_debug_api.cpp")

    assert "record_legacy_launch_event(" in weapon_api
    assert "record_effects_damage_event(" in weapon_api
    assert "record_effects_damage_event(" in damage_api
    assert "LaunchEvent event{}" in weapon_api
    assert "EffectsEvent effects{}" in damage_api
    assert "DamageReport report{}" in damage_api
    assert "DiagnosticsTrace trace{}" in damage_api
    assert "pending_effects_launch_event_id_ = launch_event_id" in weapon_api
    assert "capture_engagement_damage_state(target_id)" in damage_api


def test_recent_event_storage_uses_shared_monotonic_ids_and_queue_aligned_sorted_exports() -> None:
    header = _read("src/core/engine/simulation_kernel.h")
    observation_api = _read("src/core/engine/simulation_kernel_observation_api.cpp")
    weapon_api = _read("src/core/engine/simulation_kernel_weapon_api.cpp")
    damage_api = _read("src/core/engine/simulation_kernel_damage_debug_api.cpp")

    assert "std::uint64_t next_engagement_event_id_ = 1;" in header
    assert "static constexpr std::size_t kMaxRecentEngagementEvents = 64;" in header
    assert "const std::uint64_t event_id = next_engagement_event_id_++;" in weapon_api
    assert "trace.trace_id = next_engagement_event_id_++;" in weapon_api
    assert "const std::uint64_t effects_event_id = next_engagement_event_id_++;" in damage_api
    assert "const std::uint64_t damage_report_id = next_engagement_event_id_++;" in damage_api
    assert "const std::uint64_t trace_id = next_engagement_event_id_++;" in damage_api
    for comparator in (
        "lhs.event_id < rhs.event_id",
        "lhs.report_id < rhs.report_id",
        "lhs.trace_id < rhs.trace_id",
    ):
        assert comparator in observation_api


def _engagement_ref(world_index: int, entity_id: int) -> ef_py.EngagementEntityRef:
    ref = ef_py.EngagementEntityRef()
    ref.world_index = world_index
    ref.entity_id = entity_id
    return ref


def _make_detection(target_id: int, *, range_m: float = 30000.0) -> ef_py.Detection:
    detection = ef_py.Detection()
    detection.target_id = int(target_id)
    detection.range = float(range_m)
    detection.bearing = 0.0
    detection.elevation = 0.0
    detection.closing_speed = 500.0
    detection.signal_strength = 1.0
    detection.detection_prob_used = 0.9
    detection.sensor_type = int(ef_py.SensorType.Radar)
    detection.local_sensor_hit = True
    detection.timestamp = 0.0
    return detection


def _world_ref(world_index: int, entity_id: int) -> ef_py.WorldEntityRef:
    ref = ef_py.WorldEntityRef()
    ref.world_index = int(world_index)
    ref.entity_id = int(entity_id)
    return ref


def _make_spawn_request(
    *,
    world_index: int,
    side: object,
    type_name: str,
    entity_name: str,
    y: float,
    heading: float,
    vy: float,
    is_agent: bool,
) -> ef_py.WorldSpawnRequest:
    spawn = ef_py.WorldSpawnRequest()
    spawn.world_index = int(world_index)
    spawn.side = side
    spawn.type_name = type_name
    spawn.entity_name = entity_name
    spawn.is_agent = bool(is_agent)
    spawn.x = 0.0
    spawn.y = float(y)
    spawn.z = 5000.0
    spawn.heading = float(heading)
    spawn.vy = float(vy)
    spawn.ammo_override_enabled = True
    spawn.missiles_remaining = 4
    spawn.max_missiles = 4
    spawn.weapon_cooldown_override_enabled = True
    spawn.weapon_cooldown_s = 0.0
    spawn.weapon_last_fire_time = -1.0
    return spawn


def _make_pilot_fire_action() -> ef_py.PilotAction:
    action = ef_py.PilotAction()
    action.active = True
    action.master_arm = True
    action.fire_weapon = True
    action.throttle = 0.8
    return action


def _make_facade_window_launch() -> tuple[ef_py.RuntimeFacade, int, int, int]:
    facade = ef_py.RuntimeFacade(1)
    if not facade.load_database(_DB_PATH):
        raise AssertionError("failed to load runtime database")

    setup = ef_py.BatchWorldSetupRequest()
    setup.seeds = [123]
    terrain = ef_py.WorldTerrainAssignment()
    terrain.world_index = 0
    terrain.terrain_type = "flat"
    wind = ef_py.WorldWindAssignment()
    wind.world_index = 0
    setup.terrain_assignments = [terrain]
    setup.wind_assignments = [wind]
    setup.spawn_requests = [
        _make_spawn_request(
            world_index=0,
            side=ef_py.Side.Blue,
            type_name="F-16C_Block50",
            entity_name="Blue",
            y=0.0,
            heading=0.0,
            vy=250.0,
            is_agent=True,
        ),
        _make_spawn_request(
            world_index=0,
            side=ef_py.Side.Red,
            type_name="Aircraft",
            entity_name="Red",
            y=30000.0,
            heading=180.0,
            vy=-250.0,
            is_agent=False,
        ),
    ]
    setup.time_steps = [0.05]
    setup_result = facade.apply_world_setup(setup)
    blue_id = int(setup_result.entity_ids[0])
    red_id = int(setup_result.entity_ids[1])

    for _ in range(80):
        facade.step_batch()
        obs = facade.get_agent_observations_batch([_world_ref(0, blue_id)])[0]
        if any(int(track.id) == red_id for track in getattr(obs, "contacts", [])):
            break
    else:
        raise AssertionError("expected facade observation helper to expose a target contact")

    request = ef_py.RuntimeWindowRequest()
    request.window_id = f"window:live_engagement:{blue_id}"
    request.world_id = 0
    request.source_time_s = 10.0
    observation_request = ef_py.ObservationBatchRequest()
    observation_request.refs = [_world_ref(0, blue_id)]
    observation_request.include_agent_observations = True
    request.observation_request = observation_request
    engagement_request = ef_py.EngagementBatchRequest()
    engagement_request.refs = [_engagement_ref(0, blue_id)]
    engagement_request.trace_ids = [95001, 95002]
    engagement_request.include_track_packets = False
    engagement_request.include_diagnostics_traces = True
    request.engagement_request = engagement_request
    request.export_observation = True
    request.export_engagement = True
    request.export_diagnostics = True

    action_request = ef_py.RuntimeWindowActionRequest()
    action_request.source_layer = "live_engagement_event_capture_test"
    action_request.input_snapshot_version = f"obs:0:{blue_id}"
    action_request.action_intent.source_id = f"test:fire:{blue_id}"
    action_request.action_intent.effective_time_s = request.source_time_s
    action_request.action_intent.valid_until_s = request.source_time_s + 1.0
    action_request.action_intent.target.world_index = 0
    action_request.action_intent.target.entity_id = int(blue_id)
    action_request.action_intent.action_family = "direct_control"
    action_request.action_intent.merge_policy = "last_write_wins"
    action_request.action_intent.action_interface.kind = "PilotActionAssignmentCompat"
    action_request.action_intent.action_interface.payload_type = "pilot_action"
    action_request.action_intent.has_pilot_action = True
    action_request.action_intent.pilot_action = _make_pilot_fire_action()
    request.action_requests = [action_request]

    result = facade.run_wp10_window(request)
    launch = next(
        event for event in result.engagement_packet.launch_events if int(event.spawned_munition.entity_id) > 0
    )
    return facade, blue_id, red_id, int(launch.spawned_munition.entity_id)


def _make_air_fixture() -> tuple[ef_py.SimulationKernel, int, int]:
    sim = ef_py.SimulationKernel()
    if not sim.load_database(_DB_PATH):
        raise AssertionError("failed to load runtime database")
    blue_id = int(
        sim.spawn_unit(
            ef_py.Side.Blue,
            "F-16C_Block50",
            0.0,
            0.0,
            5000.0,
            0.0,
            0.0,
            0.0,
            0.0,
            250.0,
            0.0,
        )
    )
    red_id = int(
        sim.spawn_unit(
            ef_py.Side.Red,
            "Aircraft",
            0.0,
            30000.0,
            5000.0,
            180.0,
            0.0,
            0.0,
            0.0,
            -250.0,
            0.0,
        )
    )
    sim.set_unit_ammo(blue_id, 4, 4)
    sim.set_weapon_cooldown(blue_id, 0.0, -1.0)
    sim.set_contact_list(blue_id, [_make_detection(red_id)])
    return sim, blue_id, red_id


def test_recent_engagement_events_are_exported_and_reset_clears_them() -> None:
    sim, blue_id, red_id = _make_air_fixture()

    missile_id = int(sim.fire_missile(blue_id, red_id))
    assert missile_id > 0

    events = sim.export_recent_engagement_events()
    assert len(events.launch_events) == 1
    assert events.launch_events[0].accepted
    assert int(events.launch_events[0].spawned_munition.entity_id) == missile_id
    assert int(events.launch_events[0].ammo_delta) == -1
    assert len(events.diagnostics_traces) >= 1
    assert int(events.diagnostics_traces[0].launch_event_id) == int(events.launch_events[0].event_id)

    sim.reset(999)
    cleared = sim.export_recent_engagement_events()
    assert list(cleared.launch_events) == []
    assert list(cleared.effects_events) == []
    assert list(cleared.damage_reports) == []
    assert list(cleared.diagnostics_traces) == []


def test_debug_damage_records_effects_damage_and_trace_reports() -> None:
    sim = ef_py.SimulationKernel()
    sim.reset(770)
    if not sim.load_database(_DB_PATH):
        raise AssertionError("failed to load runtime database")

    attacker_id = int(
        sim.spawn_unit(
            ef_py.Side.Blue,
            "Aircraft",
            0.0,
            0.0,
            1000.0,
            0.0,
            0.0,
            0.0,
            0.0,
            100.0,
            0.0,
        )
    )
    target_id = int(
        sim.spawn_unit(
            ef_py.Side.Red,
            "DDG-51_Flight_I_USS_Arleigh_Burke",
            0.0,
            1500.0,
            0.0,
            180.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        )
    )

    assert sim.debug_apply_proximity_hit(attacker_id, target_id, 120.0, 80.0)
    events = sim.export_recent_engagement_events()
    assert len(events.effects_events) == 1
    assert len(events.damage_reports) == 1
    assert len(events.diagnostics_traces) == 1
    assert int(events.effects_events[0].target.entity_id) == target_id
    assert str(events.effects_events[0].outcome_state) == "hit"
    assert int(events.damage_reports[0].target.entity_id) == target_id
    assert int(events.damage_reports[0].source_event_id) == int(events.effects_events[0].event_id)
    assert float(events.damage_reports[0].hp_delta) < 0.0
    assert int(events.diagnostics_traces[0].effects_event_id) == int(events.effects_events[0].event_id)
    assert int(events.diagnostics_traces[0].damage_report_id) == int(events.damage_reports[0].report_id)


def test_facade_exports_recent_live_engagement_events_from_maintained_window_path() -> None:
    facade, blue_id, _, missile_id = _make_facade_window_launch()
    request = ef_py.EngagementBatchRequest()
    request.refs = [_engagement_ref(0, blue_id)]
    request.include_track_packets = False
    request.include_diagnostics_traces = True
    packet = facade.export_engagement_event_packet(request)

    assert len(packet.launch_events) == 1
    assert int(packet.launch_events[0].spawned_munition.entity_id) == missile_id
    assert len(packet.diagnostics_traces) >= 1
    assert any(
        int(trace.launch_event_id) == int(packet.launch_events[0].event_id)
        for trace in packet.diagnostics_traces
    )


def test_facade_dedicated_diagnostics_surface_exports_recent_and_observation_trace_rows() -> None:
    facade, blue_id, red_id, missile_id = _make_facade_window_launch()
    request = ef_py.EngagementBatchRequest()
    request.refs = [_engagement_ref(0, blue_id)]
    request.trace_ids = [95001, 95002]
    request.include_track_packets = False
    request.include_diagnostics_traces = True
    traces = facade.export_diagnostics_traces(request)

    assert len(traces) >= 2
    assert any(int(trace.launch_event_id) > 0 for trace in traces)
    assert any(int(trace.track_id) == red_id for trace in traces)
    assert any(int(trace.munition.entity_id) == missile_id for trace in traces)
