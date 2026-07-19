from __future__ import annotations

import csv
import json

from python.runtime_bootstrap import ensure_repo_imports


ensure_repo_imports()

import ef_py  # noqa: E402
from tools.diagnostics import structural_breakup_export as export  # noqa: E402


def _ref(entity_id: int, *, world_index: int = 0) -> ef_py.EngagementEntityRef:
  ref = ef_py.EngagementEntityRef()
  ref.entity_id = int(entity_id)
  ref.world_index = int(world_index)
  return ref


def _structural_event(
  *,
  chain_id: int = 7001,
  event_id: int = 7002,
  parent_event_id: int = 7000,
  target_id: int = 202,
  break_mode: str = "wing_loss",
  breakup_state: str = "partial_detachment",
  detached_part_ref: str = "left_wing",
  detached_part_count: int = 1,
  airframe_breakup: bool = False,
  cause_event_id: int = 6999,
) -> ef_py.StructuralBreakupEvent:
  header = ef_py.LethalityChainHeader()
  header.chain_id = int(chain_id)
  header.event_id = int(event_id)
  header.parent_event_id = int(parent_event_id)
  header.stage = "structural_breakup"
  header.status = "observed"
  header.reason = "generic_research_structural_breakup_projection"
  header.source_time_s = 12.5
  header.source_frame = 44
  header.munition = _ref(303)
  header.shooter = _ref(101)
  header.target = _ref(target_id)
  header.producer_node_id = "damage_system.structural_failure"
  header.fidelity_mode = "research_runtime"
  header.evidence_level = "engineering_assumption"
  header.observation_mode = "sampled_runtime"
  header.consumer_visibility = "diagnostics_and_training"
  header.confidence = 0.875

  event = ef_py.StructuralBreakupEvent()
  event.header = header
  event.breakup_state = breakup_state
  event.break_mode = break_mode
  event.detached_part_ref = detached_part_ref
  event.detached_part_count = int(detached_part_count)
  event.airframe_breakup = bool(airframe_breakup)
  event.cause_event_id = int(cause_event_id)
  return event


def test_structural_breakup_event_row_exports_all_contract_fields() -> None:
  row = export.structural_breakup_event_row(_structural_event())

  assert row["schema_version"] == export.SCHEMA_VERSION
  assert row["chain_id"] == 7001
  assert row["event_id"] == 7002
  assert row["parent_event_id"] == 7000
  assert row["stage"] == "structural_breakup"
  assert row["status"] == "observed"
  assert row["reason"] == "generic_research_structural_breakup_projection"
  assert row["source_time_s"] == 12.5
  assert row["source_frame"] == 44
  assert row["producer_node_id"] == "damage_system.structural_failure"
  assert row["munition_id"] == 303
  assert row["shooter_id"] == 101
  assert row["target_id"] == 202
  assert row["breakup_state"] == "partial_detachment"
  assert row["break_mode"] == "wing_loss"
  assert row["detached_part_ref"] == "left_wing"
  assert row["detached_part_count"] == 1
  assert row["airframe_breakup"] is False
  assert row["cause_event_id"] == 6999
  assert row["confidence"] == 0.875


def test_export_consumes_engagement_event_packet_structural_breakup_vector() -> None:
  packet = ef_py.EngagementEventPacket()
  packet.structural_breakup_events = [
    _structural_event(event_id=7004, detached_part_ref="right_wing"),
    _structural_event(event_id=7003, detached_part_ref="left_wing"),
    _structural_event(
      chain_id=8001,
      event_id=8002,
      parent_event_id=8000,
      break_mode="multi_axis",
      breakup_state="full_breakup",
      detached_part_ref="multi_axis",
      detached_part_count=4,
      airframe_breakup=True,
      cause_event_id=8000,
    ),
  ]

  payload = export.export_structural_breakup_events(packet)

  assert payload["schema_version"] == export.SCHEMA_VERSION
  assert payload["event_count"] == 3
  assert payload["chain_count"] == 2
  assert payload["chain_ids"] == [7001, 8001]
  assert [row["event_id"] for row in payload["rows"]] == [7003, 7004, 8002]
  assert payload["authority_boundary"]["consumes_existing_bindings_only"] is True
  assert payload["authority_boundary"]["new_binding_surface"] is False
  assert payload["authority_boundary"]["aerodynamics_modified"] is False
  assert payload["authority_boundary"]["structural_integrity_modified"] is False

  summary_by_chain = {
    int(summary["chain_id"]): summary for summary in payload["summary_by_chain"]
  }
  assert summary_by_chain[7001]["event_count"] == 2
  assert summary_by_chain[7001]["break_modes"] == ["wing_loss"]
  assert summary_by_chain[7001]["detached_part_refs"] == ["left_wing", "right_wing"]
  assert summary_by_chain[7001]["cause_event_ids"] == [6999]
  assert summary_by_chain[8001]["airframe_breakup"] is True
  assert summary_by_chain[8001]["breakup_states"] == ["full_breakup"]
  assert summary_by_chain[8001]["break_modes"] == ["multi_axis"]


def test_export_accepts_recent_engagement_events_and_chain_filter() -> None:
  recent = ef_py.RecentEngagementEvents()
  recent.structural_breakup_events = [
    _structural_event(chain_id=7001, event_id=7002),
    _structural_event(chain_id=8001, event_id=8002, break_mode="engine_detach"),
  ]

  rows = export.structural_breakup_rows(recent, chain_id=8001)

  assert len(rows) == 1
  assert rows[0]["chain_id"] == 8001
  assert rows[0]["break_mode"] == "engine_detach"


def test_run_export_writes_csv_and_json(tmp_path) -> None:
  packet = ef_py.EngagementEventPacket()
  packet.structural_breakup_events = [_structural_event()]
  csv_out = tmp_path / "structural_breakup.csv"
  json_out = tmp_path / "structural_breakup.json"

  payload = export.run_export(packet, csv_out=str(csv_out), json_out=str(json_out))

  assert payload["csv_out"] == str(csv_out)
  assert payload["json_out"] == str(json_out)

  with csv_out.open("r", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))
  assert len(rows) == 1
  assert rows[0]["schema_version"] == export.SCHEMA_VERSION
  assert rows[0]["chain_id"] == "7001"
  assert rows[0]["break_mode"] == "wing_loss"
  assert rows[0]["detached_part_ref"] == "left_wing"

  payload_from_disk = json.loads(json_out.read_text(encoding="utf-8"))
  assert payload_from_disk["schema_version"] == export.SCHEMA_VERSION
  assert payload_from_disk["event_count"] == 1
  assert payload_from_disk["rows"][0]["cause_event_id"] == 6999
