from __future__ import annotations

import unittest

from python.testing.runtime import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402


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
    if not facade.load_database(resolve_repo_path("examples", "config", "database")):
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


class FacadeEngagementExportTests(unittest.TestCase):
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

        world = facade.runtime().world(1)
        world.set_unit_ammo(blue_id, 4, 4)
        world.set_weapon_cooldown(blue_id, 0.0, -1.0)
        detection = ef_py.Detection()
        detection.target_id = red_id
        detection.range = 30000.0
        detection.bearing = 0.0
        detection.elevation = 0.0
        detection.closing_speed = 500.0
        detection.signal_strength = 1.0
        detection.detection_prob_used = 0.9
        detection.sensor_type = int(ef_py.SensorType.Radar)
        detection.local_sensor_hit = True
        detection.timestamp = 0.0
        world.set_contact_list(blue_id, [detection])

        missile_id = int(world.fire_missile(blue_id, red_id))
        self.assertGreater(missile_id, 0)

        request = ef_py.EngagementBatchRequest()
        request.refs = [_engagement_ref(1, blue_id)]
        request.include_track_packets = False
        request.include_diagnostics_traces = True
        packet = facade.export_engagement_event_packet(request)

        self.assertEqual(len(packet.launch_events), 1)
        self.assertEqual(int(packet.launch_events[0].spawned_munition.world_index), 1)
        self.assertEqual(int(packet.launch_events[0].spawned_munition.entity_id), missile_id)
        self.assertTrue(
            any(int(trace.munition.world_index) == 1 for trace in packet.diagnostics_traces)
        )


if __name__ == "__main__":
    unittest.main()
