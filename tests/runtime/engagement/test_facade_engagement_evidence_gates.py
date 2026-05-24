from __future__ import annotations

import re
from pathlib import Path

from python.testing.runtime import ensure_repo_imports
from python.testing.runtime import resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402


def _read_repo_text(*parts: str) -> str:
    return Path(resolve_repo_path(*parts)).read_text(encoding="utf-8")


def _function_body(source: str, signature: str) -> str:
    start = source.index(signature)
    body_start = source.index("{", start)
    depth = 0
    for index in range(body_start, len(source)):
        char = source[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[body_start:index + 1]
    raise AssertionError(f"could not locate function body for {signature}")


def _engagement_ref(world_index: int, entity_id: int) -> ef_py.EngagementEntityRef:
    ref = ef_py.EngagementEntityRef()
    ref.world_index = int(world_index)
    ref.entity_id = int(entity_id)
    return ref


def test_engagement_event_packet_producer_coverage_and_deferred_slots_are_explicit() -> None:
    facade_source = _read_repo_text("src", "runtime", "facade", "runtime_facade.cpp")
    facade_types = _read_repo_text("src", "runtime", "facade", "runtime_facade_types.h")

    packet_block = re.search(
        r"struct EngagementEventPacket \{(?P<body>.*?)\};",
        facade_types,
        flags=re.DOTALL,
    )
    assert packet_block is not None
    packet_body = packet_block.group("body")
    for slot in [
        "snapshot_version",
        "barrier_id",
        "barrier_sequence",
        "barrier_detail",
        "source_time_s",
        "producer_node_id",
        "refs",
        "trace_ids",
        "track_packets",
        "launch_requests",
        "launch_events",
        "munition_lifecycle_packets",
        "effects_events",
        "damage_reports",
        "diagnostics_traces",
    ]:
        assert slot in packet_body

    export_body = _function_body(
        facade_source,
        "EngagementEventPacket RuntimeFacade::export_engagement_event_packet",
    )
    append_body = _function_body(
        facade_source,
        "void append_recent_engagement_events",
    )

    assert "packet.refs = request.refs" in export_body
    assert "packet.trace_ids = request.trace_ids" in export_body
    assert "apply_export_packet_metadata" in export_body
    assert "stable_sort_engagement_packet" in export_body
    assert "packet.track_packets.push_back" in export_body
    assert "packet.diagnostics_traces.push_back" in export_body

    for populated_recent_slot in ["launch_events", "effects_events", "damage_reports"]:
        assert f"request.include_{populated_recent_slot}" in append_body
        assert f"packet.{populated_recent_slot}.insert" in append_body
    assert "request.include_diagnostics_traces" in append_body
    assert "append_recent_diagnostics_traces(packet.diagnostics_traces, recent)" in append_body

    for deferred_slot in ["launch_requests", "munition_lifecycle_packets"]:
        assert f"packet.{deferred_slot}.push_back" not in export_body
        assert f"packet.{deferred_slot}.insert" not in export_body
        assert f"packet.{deferred_slot} =" not in export_body
        assert f"packet.{deferred_slot}.push_back" not in append_body
        assert f"packet.{deferred_slot}.insert" not in append_body


def test_engagement_diagnostics_inside_export_are_piggyback_evidence_not_full_log() -> None:
    facade_source = _read_repo_text("src", "runtime", "facade", "runtime_facade.cpp")

    diagnostics_body = _function_body(
        facade_source,
        "DiagnosticsTrace diagnostics_trace_from_track_packet",
    )
    export_body = _function_body(
        facade_source,
        "EngagementEventPacket RuntimeFacade::export_engagement_event_packet",
    )

    assert ".trace_id = trace_id" in diagnostics_body
    assert ".chain_id = trace_id" in diagnostics_body
    assert ".track_id = track.track_id" in diagnostics_body
    assert ".observation_packet_version = observation_packet_version" in diagnostics_body
    assert ".source_snapshot_version = track.snapshot_version" in diagnostics_body
    assert '.barrier_id = std::string(kWp10ExportBarrierId)' in diagnostics_body
    assert '.source_node_id = std::string(kWp10ObservationExportNodeId)' in diagnostics_body
    for non_track_link in ["launch_request_id", "launch_event_id", "effects_event_id", "damage_report_id"]:
        assert non_track_link not in diagnostics_body

    assert "request.include_diagnostics_traces && !request.trace_ids.empty()" in export_body
    assert "diagnostics_trace_from_track_packet" in export_body


def test_recent_effects_damage_and_trace_refs_are_retagged_for_requested_world_index() -> None:
    facade = ef_py.RuntimeFacade(2)
    assert facade.load_database(resolve_repo_path("examples", "config", "database"))

    world = facade.runtime_compatibility_quarantine().world_compatibility_quarantine(1)
    attacker_id = int(
        world.spawn_unit(
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
        world.spawn_unit(
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
    assert world.debug_apply_proximity_hit(attacker_id, target_id, 120.0, 80.0)

    request = ef_py.EngagementBatchRequest()
    request.refs = [_engagement_ref(1, attacker_id)]
    request.include_track_packets = False
    request.include_diagnostics_traces = True

    packet = facade.export_engagement_event_packet(request)

    assert len(packet.effects_events) == 1
    assert len(packet.damage_reports) == 1
    assert len(packet.diagnostics_traces) == 1
    assert int(packet.effects_events[0].munition.world_index) == 1
    assert int(packet.effects_events[0].target.world_index) == 1
    assert int(packet.effects_events[0].target.entity_id) == target_id
    assert int(packet.damage_reports[0].target.world_index) == 1
    assert int(packet.damage_reports[0].target.entity_id) == target_id
    assert int(packet.diagnostics_traces[0].munition.world_index) == 1
    assert packet.effects_events[0].producer_node_id == "p9.effects_damage.v1"
    assert packet.damage_reports[0].producer_node_id == "p9.effects_damage.v1"
    assert packet.diagnostics_traces[0].source_node_id == "p9.effects_damage.v1"
    assert packet.diagnostics_traces[0].export_node_id == "p10.observation_export.v1"
