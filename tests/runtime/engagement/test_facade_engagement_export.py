from __future__ import annotations

import unittest

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402


_DB_PATH = resolve_repo_path("examples", "config", "database")


def _world_ref(world_index: int, entity_id: int) -> ef_py.WorldEntityRef:
    ref = ef_py.WorldEntityRef()
    ref.world_index = int(world_index)
    ref.entity_id = int(entity_id)
    return ref


def _engagement_ref(world_index: int, entity_id: int) -> ef_py.EngagementEntityRef:
    ref = ef_py.EngagementEntityRef()
    ref.world_index = int(world_index)
    ref.entity_id = int(entity_id)
    return ref


def _spawn_request(
    *,
    world_index: int = 0,
    side: object,
    type_name: str,
    entity_name: str,
    y: float,
    heading: float,
    vy: float,
    is_agent: bool,
) -> ef_py.WorldSpawnRequest:
    spawn = ef_py.WorldSpawnRequest()
    spawn.world_index = world_index
    spawn.side = side
    spawn.type_name = type_name
    spawn.entity_name = entity_name
    spawn.is_agent = is_agent
    spawn.x = 0.0
    spawn.y = y
    spawn.z = 1200.0
    spawn.heading = heading
    spawn.vy = vy
    return spawn


def _make_tracked_facade_fixture() -> tuple[ef_py.RuntimeFacade, int, int]:
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
        _spawn_request(
            side=ef_py.Side.Blue,
            type_name="F-16C_Block50",
            entity_name="Blue",
            y=0.0,
            heading=0.0,
            vy=180.0,
            is_agent=True,
        ),
        _spawn_request(
            side=ef_py.Side.Red,
            type_name="F-16C_Block50",
            entity_name="Red",
            y=8000.0,
            heading=180.0,
            vy=-180.0,
            is_agent=False,
        ),
    ]
    setup.time_steps = [0.05]

    result = facade.apply_world_setup(setup)
    blue_id = int(result.entity_ids[0])
    red_id = int(result.entity_ids[1])

    for _ in range(80):
        facade.step_batch()
        obs = facade.get_agent_observations_batch([_world_ref(0, blue_id)])[0]
        if any(int(track.id) == red_id for track in getattr(obs, "contacts", [])):
            return facade, blue_id, red_id

    raise AssertionError("expected facade observation helper to expose a target contact")


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


def _make_pilot_fire_action() -> ef_py.PilotAction:
    action = ef_py.PilotAction()
    action.active = True
    action.master_arm = True
    action.fire_weapon = True
    action.throttle = 0.8
    return action


def _make_window_launch_packet() -> tuple[ef_py.EngagementEventPacket, int, int, int]:
    facade, shooter_id, target_id = _make_tracked_facade_fixture()

    request = ef_py.RuntimeWindowRequest()
    request.window_id = f"window:engagement_export:{shooter_id}"
    request.world_id = 0
    request.source_time_s = 10.0

    observation_request = ef_py.ObservationBatchRequest()
    observation_request.refs = [_world_ref(0, shooter_id)]
    observation_request.include_agent_observations = True
    observation_request.include_instrument_states = True
    request.observation_request = observation_request

    engagement_request = ef_py.EngagementBatchRequest()
    engagement_request.refs = [_engagement_ref(0, shooter_id)]
    engagement_request.include_track_packets = True
    engagement_request.include_diagnostics_traces = True
    request.engagement_request = engagement_request
    request.export_observation = True
    request.export_engagement = True
    request.export_diagnostics = True

    action_request = ef_py.RuntimeWindowActionRequest()
    action_request.source_layer = "facade_engagement_export_test"
    action_request.input_snapshot_version = f"obs:0:{shooter_id}"
    action_request.action_intent.source_id = f"test:fire:{shooter_id}"
    action_request.action_intent.effective_time_s = request.source_time_s
    action_request.action_intent.valid_until_s = request.source_time_s + 1.0
    action_request.action_intent.target.world_index = 0
    action_request.action_intent.target.entity_id = int(shooter_id)
    action_request.action_intent.action_family = "direct_control"
    action_request.action_intent.merge_policy = "last_write_wins"
    action_request.action_intent.action_interface.kind = "PilotActionAssignmentCompat"
    action_request.action_intent.action_interface.payload_type = "pilot_action"
    action_request.action_intent.has_pilot_action = True
    action_request.action_intent.pilot_action = _make_pilot_fire_action()
    request.action_requests = [action_request]

    result = facade.run_wp10_window(request)
    packet = result.engagement_packet
    launch = next(
        event for event in packet.launch_events if event.producer_node_id == "p7.fire_control_launch.v1"
    )
    missile_id = int(launch.spawned_munition.entity_id)
    if missile_id <= 0:
        raise AssertionError("expected maintained facade window launch to produce a munition")
    return packet, shooter_id, target_id, missile_id


class FacadeEngagementExportTests(unittest.TestCase):
    def test_window_launch_export_proves_wp10_nodes_barriers_and_wp11_provenance_chain(self) -> None:
        packet, _, _target_id, missile_id = _make_window_launch_packet()

        self.assertGreaterEqual(int(packet.snapshot_version), 1)
        self.assertEqual(packet.barrier_id, "export")
        self.assertEqual(int(packet.barrier_sequence), 1)
        self.assertEqual(packet.barrier_detail, "maintained_facade_export")
        self.assertEqual(packet.producer_node_id, "p10.observation_export.v1")
        self.assertGreaterEqual(float(packet.source_time_s), 0.0)

        self.assertEqual(packet.packet_provenance.information_state_layer, "TrackState")
        self.assertEqual(packet.packet_provenance.source_label, "track_state_packet")
        self.assertEqual(packet.packet_provenance.maintained_status, "maintained")
        self.assertEqual(
            list(packet.packet_provenance.observation_packet_ids),
            [f"eng:{int(packet.snapshot_version)}"],
        )
        self.assertEqual(
            list(packet.packet_provenance.source_observation_versions),
            [f"track:{int(packet.snapshot_version)}"],
        )
        self.assertEqual(
            packet.diagnostics_provenance.information_state_layer,
            "DecisionBelief",
        )
        self.assertEqual(
            packet.diagnostics_provenance.source_label,
            "world_truth_diagnostics",
        )
        self.assertEqual(
            packet.diagnostics_provenance.maintained_status,
            "diagnostics_only",
        )
        self.assertEqual(
            list(packet.diagnostics_provenance.observation_packet_ids),
            [f"diag:{int(packet.snapshot_version)}"],
        )
        self.assertEqual(
            list(packet.diagnostics_provenance.source_observation_versions),
            [f"diag:{int(packet.snapshot_version)}"],
        )
        self.assertEqual(
            packet.diagnostics_provenance.diagnostics_reason,
            "diagnostics_trace_surface_not_maintained_decision_path",
        )

        launch = next(
            event for event in packet.launch_events if event.producer_node_id == "p7.fire_control_launch.v1"
        )
        self.assertEqual(int(launch.spawned_munition.entity_id), missile_id)

        launch_trace = next(
            trace for trace in packet.diagnostics_traces if int(trace.launch_event_id) == int(launch.event_id)
        )

        self.assertEqual(launch_trace.source_node_id, "p7.fire_control_launch.v1")
        self.assertEqual(launch_trace.export_node_id, "p10.observation_export.v1")
        self.assertEqual(launch_trace.barrier_id, "export")
        self.assertEqual(launch_trace.barrier_detail, "maintained_facade_export")
        self.assertEqual(int(launch_trace.source_snapshot_version), int(packet.snapshot_version))
        self.assertGreaterEqual(float(launch_trace.source_time_s), 0.0)

    def test_live_snapshot_export_preserves_refs_and_trace_ids_and_does_not_fire_weapons(self) -> None:
        facade, blue_id, red_id = _make_tracked_facade_fixture()
        before = facade.get_agent_observations_batch([_world_ref(0, blue_id)])[0]
        missiles_before = int(getattr(before, "missiles_remaining", -1))
        contact = next(track for track in before.contacts if int(track.id) == red_id)

        request = ef_py.EngagementBatchRequest()
        request.refs = [_engagement_ref(0, blue_id)]
        request.trace_ids = [91001]
        request.include_track_packets = True
        request.include_diagnostics_traces = True

        packet = facade.export_engagement_event_packet(request)
        after = facade.get_agent_observations_batch([_world_ref(0, blue_id)])[0]

        self.assertEqual([(int(ref.world_index), int(ref.entity_id)) for ref in packet.refs], [(0, blue_id)])
        self.assertEqual([int(trace_id) for trace_id in packet.trace_ids], [91001])
        self.assertGreaterEqual(int(packet.snapshot_version), 1)
        self.assertEqual(packet.barrier_id, "export")
        self.assertEqual(int(packet.barrier_sequence), 1)
        self.assertEqual(packet.barrier_detail, "maintained_facade_export")
        self.assertEqual(packet.producer_node_id, "p10.observation_export.v1")
        self.assertEqual(int(getattr(after, "missiles_remaining", -1)), missiles_before)
        self.assertEqual(list(packet.launch_requests), [])
        self.assertEqual(list(packet.launch_events), [])
        self.assertEqual(list(packet.munition_lifecycle_packets), [])
        self.assertEqual(list(packet.effects_events), [])
        self.assertEqual(list(packet.damage_reports), [])

        self.assertGreaterEqual(len(packet.track_packets), 1)
        target_track = next(track for track in packet.track_packets if int(track.track_id) == red_id)
        self.assertEqual(int(target_track.correlated_entity.world_index), 0)
        self.assertEqual(int(target_track.correlated_entity.entity_id), red_id)
        self.assertTrue(bool(target_track.has_correlated_entity))
        self.assertEqual(float(target_track.quality), float(contact.quality))
        self.assertEqual(float(target_track.confidence), float(contact.confidence))
        self.assertEqual(float(target_track.update_age_s), float(contact.time_since_update))
        self.assertNotEqual(str(target_track.source), "")

        self.assertGreaterEqual(len(packet.diagnostics_traces), 1)
        trace = next(trace for trace in packet.diagnostics_traces if int(trace.track_id) == red_id)
        self.assertEqual(int(trace.trace_id), 91001)
        self.assertGreaterEqual(int(trace.observation_packet_version), 1)
        self.assertGreaterEqual(int(trace.source_snapshot_version), 1)
        self.assertEqual(trace.barrier_id, "export")
        self.assertEqual(trace.barrier_detail, "maintained_facade_export")
        self.assertEqual(trace.source_node_id, "p10.observation_export.v1")
        self.assertEqual(trace.export_node_id, "p10.observation_export.v1")
        self.assertGreaterEqual(float(trace.source_time_s), 0.0)
        self.assertEqual(int(trace.launch_request_id), 0)
        self.assertEqual(int(trace.launch_event_id), 0)
        self.assertEqual(int(trace.effects_event_id), 0)
        self.assertEqual(int(trace.damage_report_id), 0)

    def test_live_snapshot_export_honors_include_flags(self) -> None:
        facade, blue_id, _ = _make_tracked_facade_fixture()

        request = ef_py.EngagementBatchRequest()
        request.refs = [_engagement_ref(0, blue_id)]
        request.trace_ids = [91002]
        request.include_track_packets = False
        request.include_launch_requests = False
        request.include_launch_events = False
        request.include_munition_lifecycle_packets = False
        request.include_effects_events = False
        request.include_damage_reports = False
        request.include_diagnostics_traces = False

        packet = facade.export_engagement_event_packet(request)

        self.assertEqual([(int(ref.world_index), int(ref.entity_id)) for ref in packet.refs], [(0, blue_id)])
        self.assertEqual([int(trace_id) for trace_id in packet.trace_ids], [91002])
        self.assertEqual(list(packet.track_packets), [])
        self.assertEqual(list(packet.launch_requests), [])
        self.assertEqual(list(packet.launch_events), [])
        self.assertEqual(list(packet.munition_lifecycle_packets), [])
        self.assertEqual(list(packet.effects_events), [])
        self.assertEqual(list(packet.damage_reports), [])
        self.assertEqual(list(packet.diagnostics_traces), [])
        self.assertEqual(packet.barrier_id, "export")
        self.assertEqual(packet.producer_node_id, "p10.observation_export.v1")

    def test_dedicated_diagnostics_export_surface_does_not_require_engagement_packet(self) -> None:
        facade, blue_id, red_id = _make_tracked_facade_fixture()

        request = ef_py.EngagementBatchRequest()
        request.refs = [_engagement_ref(0, blue_id)]
        request.trace_ids = [93001, 93002]
        request.include_track_packets = False
        request.include_diagnostics_traces = True

        traces = facade.export_diagnostics_traces(request)

        self.assertGreaterEqual(len(traces), 1)
        self.assertTrue(any(int(trace.track_id) == red_id for trace in traces))
        self.assertTrue(all(int(trace.trace_id) in {93001, 93002} for trace in traces))
        self.assertTrue(all(int(trace.observation_packet_version) >= 1 for trace in traces))
        self.assertTrue(all(int(trace.source_snapshot_version) >= 1 for trace in traces))
        self.assertTrue(all(trace.barrier_id == "export" for trace in traces))
        self.assertTrue(all(trace.export_node_id == "p10.observation_export.v1" for trace in traces))
        self.assertTrue(all(int(trace.launch_request_id) == 0 for trace in traces if int(trace.track_id) == red_id))

    def test_recent_live_events_are_retagged_with_requested_world_index(self) -> None:
        facade = ef_py.RuntimeFacade(2)
        if not facade.load_database(resolve_repo_path("examples", "config", "database")):
            raise AssertionError("failed to load runtime database")

        setup = ef_py.BatchWorldSetupRequest()
        setup.seeds = [101, 202]
        setup.spawn_requests = [
            _spawn_request(
                world_index=1,
                side=ef_py.Side.Blue,
                type_name="F-16C_Block50",
                entity_name="World1Blue",
                y=0.0,
                heading=0.0,
                vy=250.0,
                is_agent=True,
            ),
            _spawn_request(
                world_index=1,
                side=ef_py.Side.Red,
                type_name="Aircraft",
                entity_name="World1Red",
                y=30000.0,
                heading=180.0,
                vy=-250.0,
                is_agent=False,
            ),
        ]
        result = facade.apply_world_setup(setup)
        blue_id = int(result.entity_ids[0])
        red_id = int(result.entity_ids[1])

        for _ in range(80):
            facade.step_batch()
            obs = facade.get_agent_observations_batch([_world_ref(1, blue_id)])[0]
            if any(int(track.id) == red_id for track in getattr(obs, "contacts", [])):
                break
        else:
            raise AssertionError("expected facade observation helper to expose a target contact")

        window_request = ef_py.RuntimeWindowRequest()
        window_request.window_id = "window:engagement_export:world1"
        window_request.world_id = 1
        window_request.source_time_s = 10.0
        observation_request = ef_py.ObservationBatchRequest()
        observation_request.refs = [_world_ref(1, blue_id)]
        observation_request.include_agent_observations = True
        window_request.observation_request = observation_request
        request = ef_py.EngagementBatchRequest()
        request.refs = [_engagement_ref(1, blue_id)]
        request.include_track_packets = False
        request.include_diagnostics_traces = True
        window_request.engagement_request = request
        window_request.export_observation = True
        window_request.export_engagement = True
        window_request.export_diagnostics = True
        action_request = ef_py.RuntimeWindowActionRequest()
        action_request.source_layer = "facade_engagement_export_test"
        action_request.input_snapshot_version = f"obs:1:{blue_id}"
        action_request.action_intent.source_id = f"test:fire:1:{blue_id}"
        action_request.action_intent.effective_time_s = window_request.source_time_s
        action_request.action_intent.valid_until_s = window_request.source_time_s + 1.0
        action_request.action_intent.target.world_index = 1
        action_request.action_intent.target.entity_id = int(blue_id)
        action_request.action_intent.action_family = "direct_control"
        action_request.action_intent.merge_policy = "last_write_wins"
        action_request.action_intent.action_interface.kind = "PilotActionAssignmentCompat"
        action_request.action_intent.action_interface.payload_type = "pilot_action"
        action_request.action_intent.has_pilot_action = True
        action_request.action_intent.pilot_action = _make_pilot_fire_action()
        window_request.action_requests = [action_request]

        result = facade.run_wp10_window(window_request)
        packet = result.engagement_packet
        self.assertEqual(len(packet.launch_events), 1)
        missile_id = int(packet.launch_events[0].spawned_munition.entity_id)
        self.assertGreater(missile_id, 0)

        self.assertEqual(packet.launch_events[0].producer_node_id, "p7.fire_control_launch.v1")
        self.assertEqual(int(packet.launch_events[0].spawned_munition.world_index), 1)
        self.assertEqual(int(packet.launch_events[0].spawned_munition.entity_id), missile_id)
        self.assertTrue(
            any(int(trace.munition.world_index) == 1 for trace in packet.diagnostics_traces)
        )

    def test_exported_engagement_packet_uses_stable_time_priority_id_ordering(self) -> None:
        packet, _, _, _ = _make_window_launch_packet()

        launch_keys = [
            (float(event.event_time_s), int(event.event_id))
            for event in packet.launch_events
        ]
        effects_keys = [
            (float(event.detonation_time_s), int(event.event_id))
            for event in packet.effects_events
        ]
        damage_keys = [
            (float(report.report_time_s), int(report.report_id))
            for report in packet.damage_reports
        ]
        trace_keys = [
            (float(trace.source_time_s), int(trace.trace_id))
            for trace in packet.diagnostics_traces
        ]

        self.assertEqual(launch_keys, sorted(launch_keys))
        self.assertEqual(effects_keys, sorted(effects_keys))
        self.assertEqual(damage_keys, sorted(damage_keys))
        self.assertEqual(trace_keys, sorted(trace_keys))


if __name__ == "__main__":
    unittest.main()
