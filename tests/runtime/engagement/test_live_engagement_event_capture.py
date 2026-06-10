from __future__ import annotations

import re
from pathlib import Path

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402


_DB_PATH = resolve_repo_path("examples", "config", "database")
_EFFECTS_DAMAGE_RECORDER_SIGNATURE_PATTERN = re.compile(
    r"(?:virtual\s+)?(?:std::)?uint64_t\s+"
    r"(?:(?:SimulationKernelEngagementEventStore)::)?"
    r"(?P<name>record_effects_damage_event(?:_legacy)?)\s*"
    r"\((?P<params>[^)]*)\)"
)
_DEBUG_DAMAGE_DTO_BUILDER_SIGNATURE = (
    "build_debug_effects_damage_event_record(const DebugEffectsDamageEventRecordInput &input)"
)
_DEBUG_DAMAGE_DTO_CALLER_SIGNATURES = (
    "bool SimulationKernel::debug_apply_proximity_hit(",
    "bool SimulationKernel::debug_apply_local_proximity_hit(",
    "bool SimulationKernel::debug_apply_profiled_local_proximity_hit_with_velocity_and_attitude(",
)
_EFFECTS_EVENT_REF_PATTERN = re.compile(
    r"EffectsEvent\s*&\s*effects\s*=\s*event_record\.effects;"
)


def _read(path: str) -> str:
    return Path(resolve_repo_path(path)).read_text(encoding="utf-8")


def _normalized_cpp_parameters(parameters: str) -> str:
    return re.sub(r"\s+", " ", parameters).strip()


def _effects_damage_recorder_signatures(text: str) -> list[tuple[str, str]]:
    return [
        (match.group("name"), _normalized_cpp_parameters(match.group("params")))
        for match in _EFFECTS_DAMAGE_RECORDER_SIGNATURE_PATTERN.finditer(text)
    ]


def _recorder_method_parameters(text: str, method_name: str) -> list[str]:
    pattern = re.compile(
        r"(?:virtual\s+)?(?:std::)?uint64_t\s+"
        r"(?:(?:SimulationKernelEngagementEventStore)::)?"
        rf"{re.escape(method_name)}\s*"
        r"\((?P<params>[^)]*)\)"
    )
    return [
        _normalized_cpp_parameters(match.group("params"))
        for match in pattern.finditer(text)
    ]


def _assert_recorder_method_takes_dto(
    source_name: str,
    text: str,
    method_name: str,
    dto_name: str,
) -> None:
    assert _recorder_method_parameters(text, method_name) == [f"{dto_name} record"], (
        f"{source_name} must expose {method_name} as a DTO-shaped recorder "
        f"taking exactly {dto_name} record"
    )


def _assert_effects_damage_recorder_signatures_are_dto_only(
    source_name: str,
    text: str,
) -> None:
    signatures = _effects_damage_recorder_signatures(text)
    assert signatures == [
        ("record_effects_damage_event", "EngagementEffectsDamageEventRecord record")
    ], (
        f"{source_name} must expose exactly one DTO-shaped effects damage recorder "
        "signature and no public or private long-argument compatibility helper"
    )


def _extract_function_block(text: str, signature: str) -> str:
    start = text.rindex(signature)
    brace_start = text.index("{", start)
    depth = 0
    for idx in range(brace_start, len(text)):
        char = text[idx]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:idx + 1]
    raise AssertionError(f"could not extract block for {signature}")


def _assert_debug_damage_paths_use_dto_builder(text: str) -> None:
    assert "build_debug_effects_damage_event_record(" in text, (
        "debug damage paths should build EngagementEffectsDamageEventRecord DTOs "
        "through the named TM06 helper"
    )
    helper_block = _extract_function_block(text, _DEBUG_DAMAGE_DTO_BUILDER_SIGNATURE)
    assert "EngagementEffectsDamageEventRecord event_record{}" in helper_block
    assert _EFFECTS_EVENT_REF_PATTERN.search(helper_block) is not None
    assert "engagement_events::apply_effects_result_fields(effects, input.effects_result);" in helper_block
    assert "return event_record;" in helper_block
    assert text.count("EngagementEffectsDamageEventRecord event_record{}") == 1
    assert len(_EFFECTS_EVENT_REF_PATTERN.findall(text)) == 1
    assert text.count("engagement_events::apply_effects_result_fields(") == 1

    for signature in _DEBUG_DAMAGE_DTO_CALLER_SIGNATURES:
        caller_block = _extract_function_block(text, signature)
        assert "build_debug_effects_damage_event_record({" in caller_block
        assert "record_effects_damage_event(std::move(event_record))" in caller_block
        assert "impact.destruct();" in caller_block
        assert (
            caller_block.index("record_effects_damage_event(std::move(event_record))")
            < caller_block.index("impact.destruct();")
        )
        assert "EngagementEffectsDamageEventRecord event_record{}" not in caller_block
        assert _EFFECTS_EVENT_REF_PATTERN.search(caller_block) is None
        assert "engagement_events::apply_effects_result_fields(" not in caller_block


def test_simulation_kernel_exposes_read_only_recent_engagement_events_getter() -> None:
    header = _read("src/core/engine/simulation_kernel.h")
    observation_api = _read("src/core/engine/simulation_kernel_observation_api.cpp")
    event_types_header = _read("src/core/engine/engagement_event_types.h")
    store_header = _read("src/core/engine/simulation_kernel_engagement_event_store.h")
    store_impl = _read("src/core/engine/simulation_kernel_engagement_event_store.cpp")

    assert "struct RecentEngagementEvents" in event_types_header
    assert "RecentEngagementEvents export_recent_engagement_events() const" in header
    assert "core/engine/engagement_event_types.h" in header
    assert "core/engine/simulation_kernel_engagement_event_store.h" not in header
    assert "core/engine/engagement_event_types.h" in store_header
    assert "core/interfaces/engagement_event_recorder.h" in store_header
    assert "core/interfaces/engagement_launch_recorder.h" in store_header
    assert "public IEngagementLaunchRecorder" in store_header
    assert "SimulationKernel::export_recent_engagement_events() const" in observation_api
    assert "SimulationKernelEngagementEventStore::export_recent_events_sorted() const" in store_impl

    getter_body = re.search(
        r"RecentEngagementEvents SimulationKernel::export_recent_engagement_events\(\) const \{(?P<body>.*?)\n\}",
        observation_api,
        re.DOTALL,
    )
    assert getter_body is not None
    assert "engagement_event_store_->export_recent_events_sorted()" in getter_body.group("body")
    assert "std::sort" not in getter_body.group("body")
    assert "fire_missile" not in getter_body.group("body")
    assert "fire_naval_weapon" not in getter_body.group("body")
    assert "debug_apply_proximity_hit" not in getter_body.group("body")
    assert "lhs.event_id < rhs.event_id" in store_impl
    assert "lhs.trace_id < rhs.trace_id" in store_impl


def test_legacy_fire_and_debug_damage_paths_record_compatible_event_dtos() -> None:
    recorder_header = _read("src/core/interfaces/engagement_event_recorder.h")
    store_header = _read("src/core/engine/simulation_kernel_engagement_event_store.h")
    release_service = _read("src/core/engine/simulation_kernel_weapon_release_service.cpp")
    release_service_header = _read("src/core/engine/simulation_kernel_weapon_release_service.h")
    kernel_header = _read("src/core/engine/simulation_kernel.h")
    kernel_impl = _read("src/core/engine/simulation_kernel.cpp")
    services_header = _read("src/core/engine/simulation_kernel_services.h")
    services_impl = _read("src/core/engine/simulation_kernel_services.cpp")
    damage_api = _read("src/core/engine/simulation_kernel_damage_debug_api.cpp")
    store_impl = _read("src/core/engine/simulation_kernel_engagement_event_store.cpp")
    damage_bridge_header = _read("src/core/interfaces/weapon_release_damage_bridge.h")

    assert "struct EngagementEffectsDamageEventRecord" in recorder_header
    assert "struct EngagementWarheadMechanismEventRecord" in recorder_header
    assert "struct EngagementSpatialCoverageEventRecord" in recorder_header
    assert "struct EngagementComponentLoadEventRecord" in recorder_header
    _assert_recorder_method_takes_dto(
        "engagement_event_recorder.h",
        recorder_header,
        "record_effects_damage_event",
        "EngagementEffectsDamageEventRecord",
    )
    _assert_recorder_method_takes_dto(
        "engagement_event_recorder.h",
        recorder_header,
        "record_warhead_mechanism_event",
        "EngagementWarheadMechanismEventRecord",
    )
    _assert_recorder_method_takes_dto(
        "engagement_event_recorder.h",
        recorder_header,
        "record_spatial_coverage_event",
        "EngagementSpatialCoverageEventRecord",
    )
    _assert_recorder_method_takes_dto(
        "engagement_event_recorder.h",
        recorder_header,
        "record_component_load_event",
        "EngagementComponentLoadEventRecord",
    )
    assert "record_effects_damage_event_legacy(" not in recorder_header
    for source_name, source_text in (
        ("engagement_event_recorder.h", recorder_header),
        ("simulation_kernel_engagement_event_store.h", store_header),
        ("simulation_kernel_engagement_event_store.cpp", store_impl),
    ):
        _assert_effects_damage_recorder_signatures_are_dto_only(source_name, source_text)
        assert "record_effects_damage_event_legacy(" not in source_text
    _assert_recorder_method_takes_dto(
        "simulation_kernel_engagement_event_store.cpp",
        store_impl,
        "record_effects_damage_event",
        "EngagementEffectsDamageEventRecord",
    )
    assert "launch_recorder_.record_legacy_launch_event(" in release_service
    assert "damage_recorder_.record_effects_damage_event(" in release_service
    assert "engagement_event_store_->record_effects_damage_event(" in damage_api
    assert "SimulationKernelEngagementEventStore::record_legacy_launch_event(" in store_impl
    assert "SimulationKernelEngagementEventStore::record_effects_damage_event(" in store_impl
    assert "SimulationKernelEngagementEventStore::record_warhead_mechanism_event(" in store_impl
    assert "SimulationKernelEngagementEventStore::record_spatial_coverage_event(" in store_impl
    assert "SimulationKernelEngagementEventStore::record_component_load_event(" in store_impl
    assert "const std::uint64_t munition_entity_id = record.munition_entity_id;" in store_impl
    assert "const std::uint64_t target_id = record.target_id;" in store_impl
    assert "const double event_time_s = record.effects.detonation_time_s;" in store_impl
    assert "effects = std::move(record.effects);" in store_impl
    assert "LaunchEvent event{}" in store_impl
    assert "EffectsEvent effects{}" in store_impl
    assert "DamageReport report{}" in store_impl
    assert "DiagnosticsTrace trace{}" in store_impl
    assert "launch_recorder_.set_pending_effects_launch_event_id(launch_event_id)" in release_service
    assert "EngagementEffectsDamageEventRecord event_record{}" in release_service
    assert "EngagementEffectsDamageEventRecord event_record{}" in damage_api
    assert "engagement_events::apply_effects_result_fields(" in damage_api
    _assert_debug_damage_paths_use_dto_builder(damage_api)
    assert "std::move(event_record)" in release_service
    assert "engagement_event_store_->capture_engagement_damage_state(target_id)" in damage_api
    assert "class IWeaponReleaseDamageBridge" in damage_bridge_header
    assert "virtual bool apply_proximity_hit(" in damage_bridge_header
    assert "class IWeaponReleaseDamageBridge;" in kernel_header
    assert "std::unique_ptr<IWeaponReleaseDamageBridge> weapon_release_damage_bridge_" in kernel_header
    assert (
        "class SimulationKernelWeaponReleaseDamageBridge final : public IWeaponReleaseDamageBridge"
        in kernel_impl
    )
    assert "std::make_unique<SimulationKernelWeaponReleaseDamageBridge>(*this)" in kernel_impl
    assert "*weapon_release_damage_bridge_" in kernel_impl
    assert "IWeaponReleaseDamageBridge& damage_bridge" in services_header
    assert "IWeaponReleaseDamageBridge& damage_bridge" in services_impl
    assert "IWeaponReleaseDamageBridge& damage_bridge_" in release_service_header
    assert "std::function" not in release_service_header
    assert "apply_proximity_hit_(" not in release_service
    assert "damage_bridge_.apply_proximity_hit(" in release_service


def test_recent_event_storage_uses_shared_monotonic_ids_and_queue_aligned_sorted_exports() -> None:
    header = _read("src/core/engine/simulation_kernel.h")
    store_header = _read("src/core/engine/simulation_kernel_engagement_event_store.h")
    observation_api = _read("src/core/engine/simulation_kernel_observation_api.cpp")
    release_service = _read("src/core/engine/simulation_kernel_weapon_release_service.cpp")
    damage_api = _read("src/core/engine/simulation_kernel_damage_debug_api.cpp")
    store_impl = _read("src/core/engine/simulation_kernel_engagement_event_store.cpp")

    assert "std::uint64_t next_engagement_event_id_ = 1;" in store_header
    assert "static constexpr std::size_t kMaxRecentEngagementEvents = 64;" in store_header
    assert "next_engagement_event_id_" not in header
    assert "const std::uint64_t event_id = next_engagement_event_id_++;" in store_impl
    assert "trace.trace_id = next_engagement_event_id_++;" in store_impl
    assert "const std::uint64_t effects_event_id = next_engagement_event_id_++;" in store_impl
    assert "const std::uint64_t damage_report_id = next_engagement_event_id_++;" in store_impl
    assert "const std::uint64_t trace_id = next_engagement_event_id_++;" in store_impl
    for comparator in (
        "lhs.event_id < rhs.event_id",
        "lhs.header.event_id < rhs.header.event_id",
        "lhs.report_id < rhs.report_id",
        "lhs.trace_id < rhs.trace_id",
    ):
        assert comparator in store_impl
    assert "export_recent_events_sorted()" in observation_api
    assert "record_legacy_launch_event(" in release_service
    assert "SimulationKernelEngagementEventStore::" not in damage_api


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


def _make_research_warhead_profile(
    family: str = "blast_fragmentation",
    *,
    damage: float = 90.0,
    radius: float = 35.0,
) -> ef_py.WarheadProfile:
    profile = ef_py.WarheadProfile()
    profile.family = family
    profile.mass_kg = 12.0
    profile.lethal_radius_m = float(radius)
    profile.damage_scalar = float(damage)
    profile.synthetic = False
    profile.damage_scalar_synthetic = False
    profile.provenance = "test_generic_research_profile"
    return profile


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
    assert len(events.warhead_mechanism_events) == 1
    assert len(events.spatial_coverage_events) == 1
    assert list(events.component_load_events) == []
    assert len(events.damage_reports) == 1
    assert len(events.diagnostics_traces) == 1
    effects = events.effects_events[0]
    warhead = events.warhead_mechanism_events[0]
    spatial = events.spatial_coverage_events[0]
    assert int(effects.target.entity_id) == target_id
    assert str(effects.outcome_state) == "hit"
    assert int(warhead.header.parent_event_id) == int(effects.event_id)
    assert int(spatial.header.parent_event_id) == int(effects.event_id)
    assert str(warhead.header.stage) == "warhead_mechanism"
    assert str(spatial.header.stage) == "spatial_coverage"
    assert str(warhead.header.fidelity_mode) == "research_runtime"
    assert str(warhead.header.evidence_level) == "engineering_assumption"
    assert str(warhead.header.reason).startswith("generic_research_")
    assert str(spatial.header.reason) == "generic_research_spatial_projection"
    assert float(warhead.fragment_energy_j) == float(effects.mechanism_fragment_energy_j)
    assert float(warhead.blast_overpressure_kpa) == float(effects.mechanism_blast_overpressure_kpa)
    assert int(spatial.sample_count) == int(effects.warhead_spatial_sample_count)
    assert int(spatial.projected_hitbox_count) == int(effects.projected_hitbox_count)
    assert int(events.damage_reports[0].target.entity_id) == target_id
    assert int(events.damage_reports[0].source_event_id) == int(effects.event_id)
    assert float(events.damage_reports[0].hp_delta) < 0.0
    assert int(events.diagnostics_traces[0].effects_event_id) == int(effects.event_id)
    assert int(events.diagnostics_traces[0].damage_report_id) == int(events.damage_reports[0].report_id)


def test_profiled_air_hit_records_standard_component_load_events() -> None:
    sim = ef_py.SimulationKernel()
    sim.reset(771)
    if not sim.load_database(_DB_PATH):
        raise AssertionError("failed to load runtime database")

    attacker_id = int(
        sim.spawn_unit(
            ef_py.Side.Blue,
            "Aircraft",
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
    target_id = int(
        sim.spawn_unit(
            ef_py.Side.Red,
            "F-16C_Block50",
            0.0,
            1000.0,
            5000.0,
            180.0,
            0.0,
            0.0,
            0.0,
            -200.0,
            0.0,
        )
    )

    assert sim.debug_apply_profiled_local_proximity_hit_with_velocity(
        attacker_id,
        target_id,
        -0.8,
        4.1,
        0.0,
        _make_research_warhead_profile(),
        900.0,
        -250.0,
        0.0,
    )
    events = sim.export_recent_engagement_events()
    assert len(events.effects_events) == 1
    effects = events.effects_events[0]
    source_rows = [
        row
        for row in effects.component_mechanism_load_rows
        if str(row.component_name) or str(row.component_system)
    ]
    component_loads = list(events.component_load_events)
    assert source_rows
    assert len(component_loads) == len(source_rows)

    first_row = source_rows[0]
    first_load = component_loads[0]
    assert int(first_load.header.parent_event_id) == int(effects.event_id)
    assert int(first_load.header.chain_id) == int(effects.event_id)
    assert str(first_load.header.stage) == "component_load"
    assert str(first_load.header.fidelity_mode) == "research_runtime"
    assert str(first_load.header.evidence_level) == "engineering_assumption"
    assert str(first_load.header.reason) == "generic_research_component_load_projection"
    assert str(first_load.component_name) == str(first_row.component_name)
    assert str(first_load.component_system) == str(first_row.component_system)
    assert bool(first_load.direct_hit) == bool(first_row.direct_hit)
    assert float(first_load.distance_m) == float(first_row.distance_m)
    assert float(first_load.effect_scale) == float(first_row.effect_scale)
    assert float(first_load.fragment_energy_j) == float(first_row.mechanism_fragment_energy_j)
    assert float(first_load.blast_overpressure_kpa) == float(
        first_row.mechanism_blast_overpressure_kpa
    )
    assert str(first_load.load_source) in {"direct_component_hit", "spatial_component_projection"}


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
