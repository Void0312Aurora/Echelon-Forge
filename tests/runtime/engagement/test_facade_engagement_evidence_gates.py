from __future__ import annotations

import re
from pathlib import Path

from python.testing.runtime import ensure_repo_imports
from python.testing.runtime import resolve_repo_path


ensure_repo_imports()

import ef_py # noqa: E402


def _read_repo_text(*parts: str) -> str:
  return Path(resolve_repo_path(*parts)).read_text(encoding="utf-8")


def _signature_match(source: str, signature: str) -> re.Match[str]:
  pattern = r"\s+".join(re.escape(part) for part in signature.split())
  match = re.search(pattern, source)
  if match is None:
    raise AssertionError(f"could not locate signature {signature}")
  return match


def _function_body(source: str, signature: str) -> str:
  start = _signature_match(source, signature).start()
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


def _make_detection(target_id: int, *, range_m: float = 1500.0) -> ef_py.Detection:
  detection = ef_py.Detection()
  detection.target_id = int(target_id)
  detection.range = float(range_m)
  detection.bearing = 0.0
  detection.elevation = 0.0
  detection.closing_speed = 0.0
  detection.signal_strength = 1.0
  detection.detection_prob_used = 0.9
  detection.sensor_type = int(ef_py.SensorType.Radar)
  detection.local_sensor_hit = True
  detection.timestamp = 0.0
  return detection


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
    "nearest_approach_events",
    "fuze_evaluation_events",
    "warhead_mechanism_events",
    "spatial_coverage_events",
    "component_load_events",
    "component_damage_events",
    "structural_breakup_events",
    "platform_consequence_events",
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
  assert "packet.component_damage_events.insert" in append_body
  assert "packet.structural_breakup_events.insert" in append_body
  assert "packet.platform_consequence_events.insert" in append_body
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


def test_recent_effects_damage_and_trace_refs_are_diagnostics_runtime_scoped() -> None:
  runtime = ef_py.WorldBatchRuntime(2)
  assert runtime.load_database(resolve_repo_path("examples", "config", "database"))

  world = runtime.world_raw_quarantine(1)
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
  world.set_contact_list(attacker_id, [_make_detection(target_id)])
  assert world.debug_apply_proximity_hit(attacker_id, target_id, 120.0, 80.0)

  recent = world.export_recent_engagement_events()

  assert len(recent.effects_events) == 1
  assert len(recent.damage_reports) == 1
  assert len(recent.diagnostics_traces) == 1
  assert int(recent.effects_events[0].target.entity_id) == target_id
  assert int(recent.damage_reports[0].target.entity_id) == target_id
  assert recent.effects_events[0].producer_node_id == ""
  assert recent.damage_reports[0].producer_node_id == ""
