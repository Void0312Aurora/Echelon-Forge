from __future__ import annotations

from python.testing.runtime import ensure_repo_imports
from python.testing.runtime import resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402


_DB_PATH = resolve_repo_path("examples", "config", "database")


def _engagement_ref(world_index: int, entity_id: int) -> ef_py.EngagementEntityRef:
    ref = ef_py.EngagementEntityRef()
    ref.world_index = int(world_index)
    ref.entity_id = int(entity_id)
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


def _make_launch_damage_packet() -> tuple[ef_py.EngagementEventPacket, int, int, int]:
    facade = ef_py.RuntimeFacade(1)
    if not facade.load_database(_DB_PATH):
        raise AssertionError("failed to load runtime database")

    world = facade.runtime().world(0)
    shooter_id = int(
        world.spawn_unit(
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
    target_id = int(
        world.spawn_unit(
            ef_py.Side.Red,
            "DDG-51_Flight_I_USS_Arleigh_Burke",
            0.0,
            30000.0,
            0.0,
            180.0,
            0.0,
            0.0,
            0.0,
            -250.0,
            0.0,
        )
    )

    world.set_unit_ammo(shooter_id, 4, 4)
    world.set_weapon_cooldown(shooter_id, 0.0, -1.0)
    world.set_contact_list(shooter_id, [_make_detection(target_id)])

    missile_id = int(world.fire_missile(shooter_id, target_id))
    if missile_id <= 0:
        raise AssertionError("expected legacy missile launch to succeed")
    if not bool(world.debug_apply_proximity_hit(shooter_id, target_id, 120.0, 80.0)):
        raise AssertionError("expected debug proximity damage event to be recorded")

    request = ef_py.EngagementBatchRequest()
    request.refs = [_engagement_ref(0, shooter_id)]
    request.include_track_packets = True
    request.include_diagnostics_traces = True
    return facade.export_engagement_event_packet(request), shooter_id, target_id, missile_id


def _ids(values: object, attr: str) -> list[int]:
    return [int(getattr(value, attr)) for value in values]


def test_current_trace_ancestry_is_linkable_with_replay_sortable_ids() -> None:
    packet, _, target_id, missile_id = _make_launch_damage_packet()

    launch_ids = _ids(packet.launch_events, "event_id")
    effect_ids = _ids(packet.effects_events, "event_id")
    damage_ids = _ids(packet.damage_reports, "report_id")
    trace_ids = _ids(packet.diagnostics_traces, "trace_id")

    assert launch_ids == sorted(launch_ids)
    assert effect_ids == sorted(effect_ids)
    assert damage_ids == sorted(damage_ids)
    assert trace_ids == sorted(trace_ids)

    assert len(packet.launch_events) == 1
    assert len(packet.effects_events) == 1
    assert len(packet.damage_reports) == 1
    assert len(packet.diagnostics_traces) >= 2

    launch = packet.launch_events[0]
    assert int(launch.event_id) > 0
    assert int(launch.request_id) > 0
    assert bool(launch.accepted)
    assert bool(launch.has_spawned_munition)
    assert int(launch.spawned_munition.entity_id) == missile_id
    assert float(launch.event_time_s) >= 0.0

    launch_trace = next(
        trace
        for trace in packet.diagnostics_traces
        if int(trace.launch_event_id) == int(launch.event_id)
    )
    assert int(launch_trace.trace_id) > 0
    assert int(launch_trace.chain_id) == int(launch.event_id)
    assert int(launch_trace.launch_request_id) == int(launch.request_id)
    assert int(launch_trace.munition.entity_id) == missile_id

    effect = packet.effects_events[0]
    damage = packet.damage_reports[0]
    assert int(effect.event_id) > 0
    assert int(effect.munition.entity_id) > 0
    assert int(effect.target.entity_id) == target_id
    assert str(effect.outcome_state) == "hit"
    assert float(effect.detonation_time_s) >= 0.0
    assert int(damage.report_id) > 0
    assert int(damage.target.entity_id) == target_id
    assert int(damage.source_event_id) == int(effect.event_id)
    assert float(damage.report_time_s) >= 0.0

    damage_trace = next(
        trace
        for trace in packet.diagnostics_traces
        if int(trace.effects_event_id) == int(effect.event_id)
    )
    assert int(damage_trace.trace_id) > 0
    assert int(damage_trace.chain_id) > 0
    assert int(damage_trace.munition.entity_id) == int(effect.munition.entity_id)
    assert int(damage_trace.damage_report_id) == int(damage.report_id)
    if int(damage_trace.launch_event_id) != 0:
        assert int(damage_trace.launch_event_id) in launch_ids

    assert packet.track_packets
    assert all(int(track.track_id) > 0 for track in packet.track_packets)
    assert all(int(track.snapshot_version) > 0 for track in packet.track_packets)
    assert all(float(track.source_time_s) >= 0.0 for track in packet.track_packets)


def test_current_trace_replay_gates_observation_packet_metadata_stays_explicit_and_separate() -> None:
    engagement_packet = ef_py.EngagementEventPacket()
    observation_packet = ef_py.ObservationBatchPacket()
    diagnostics_trace = ef_py.DiagnosticsTrace()
    facade = ef_py.RuntimeFacade(1)

    for field in (
        "snapshot_version",
        "barrier_id",
        "barrier_sequence",
        "barrier_detail",
        "source_time_s",
        "producer_node_id",
    ):
        assert hasattr(engagement_packet, field)

    for field in ("snapshot_version", "barrier_id", "source_time_s"):
        assert hasattr(observation_packet, field)

    for field in (
        "observation_packet_version",
        "source_snapshot_version",
        "barrier_id",
        "barrier_detail",
        "source_time_s",
        "source_node_id",
        "export_node_id",
    ):
        assert hasattr(diagnostics_trace, field)

    assert observation_packet.barrier_id == "export"
    assert int(observation_packet.snapshot_version) == 0
    assert float(observation_packet.source_time_s) == 0.0
    assert engagement_packet.barrier_id == "export"
    assert int(engagement_packet.barrier_sequence) == 0
    assert engagement_packet.barrier_detail == "maintained_facade_export"
    assert diagnostics_trace.barrier_id == "export"

    assert hasattr(engagement_packet, "diagnostics_traces")
    for method in (
        "export_diagnostics_packet",
        "export_diagnostics_trace_packet",
        "get_diagnostics_traces",
    ):
        assert not hasattr(facade, method)

    assert hasattr(facade, "export_diagnostics_traces")
