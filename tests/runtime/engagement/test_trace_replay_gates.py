from __future__ import annotations

from python.testing.runtime import ensure_repo_imports
from python.testing.runtime import resolve_repo_path


ensure_repo_imports()

import ef_py # noqa: E402


_DB_PATH = resolve_repo_path("examples", "config", "database")


def _engagement_ref(world_index: int, entity_id: int) -> ef_py.EngagementEntityRef:
  ref = ef_py.EngagementEntityRef()
  ref.world_index = int(world_index)
  ref.entity_id = int(entity_id)
  return ref


def _world_ref(world_index: int, entity_id: int) -> ef_py.WorldEntityRef:
  ref = ef_py.WorldEntityRef()
  ref.world_index = int(world_index)
  ref.entity_id = int(entity_id)
  return ref


def _make_spawn_request(
  *,
  side: object,
  type_name: str,
  entity_name: str,
  y: float,
  heading: float,
  vy: float,
  is_agent: bool,
) -> ef_py.WorldSpawnRequest:
  spawn = ef_py.WorldSpawnRequest()
  spawn.world_index = 0
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


def _make_window_launch_packet() -> tuple[ef_py.EngagementEventPacket, int, int, int]:
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
      side=ef_py.Side.Blue,
      type_name="F-16C_Block50",
      entity_name="Blue",
      y=0.0,
      heading=0.0,
      vy=250.0,
      is_agent=True,
    ),
    _make_spawn_request(
      side=ef_py.Side.Red,
      type_name="Aircraft",
      entity_name="Red",
      y=30000.0,
      heading=180.0,
      vy=-250.0,
      is_agent=False,
    )
  ]
  setup.time_steps = [0.05]
  setup_result = facade.apply_world_setup(setup)
  shooter_id = int(setup_result.entity_ids[0])
  target_id = int(setup_result.entity_ids[1])

  for _ in range(80):
    facade.step_batch()
    obs = facade.get_agent_observations_batch([_world_ref(0, shooter_id)])[0]
    if any(int(track.id) == target_id for track in getattr(obs, "contacts", [])):
      break
  else:
    raise AssertionError("expected facade observation helper to expose a target contact")

  request = ef_py.RuntimeWindowRequest()
  request.window_id = f"window:trace_replay:{shooter_id}"
  request.world_id = 0
  request.source_time_s = 10.0
  observation_request = ef_py.ObservationBatchRequest()
  observation_request.refs = [_world_ref(0, shooter_id)]
  observation_request.include_agent_observations = True
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
  action_request.source_layer = "trace_replay_gate_test"
  action_request.input_snapshot_version = f"obs:0:{shooter_id}"
  action_request.action_intent.source_id = f"test:fire:{shooter_id}"
  action_request.action_intent.effective_time_s = request.source_time_s
  action_request.action_intent.valid_until_s = request.source_time_s + 1.0
  action_request.action_intent.target.world_index = 0
  action_request.action_intent.target.entity_id = int(shooter_id)
  action_request.action_intent.action_family = "direct_control"
  action_request.action_intent.merge_policy = "last_write_wins"
  action_request.action_intent.action_interface.kind = "PilotActionAssignment"
  action_request.action_intent.action_interface.payload_type = "pilot_action"
  action_request.action_intent.has_pilot_action = True
  action_request.action_intent.pilot_action = _make_pilot_fire_action()
  request.action_requests = [action_request]

  packet = facade.run_wp10_window(request).engagement_packet
  launch = next(event for event in packet.launch_events if int(event.spawned_munition.entity_id) > 0)
  return packet, shooter_id, target_id, int(launch.spawned_munition.entity_id)


def _ids(values: object, attr: str) -> list[int]:
  return [int(getattr(value, attr)) for value in values]


def test_current_trace_ancestry_is_linkable_with_replay_sortable_ids() -> None:
  packet, _, _target_id, missile_id = _make_window_launch_packet()

  launch_ids = _ids(packet.launch_events, "event_id")
  trace_ids = _ids(packet.diagnostics_traces, "trace_id")

  assert launch_ids == sorted(launch_ids)
  assert trace_ids == sorted(trace_ids)

  assert len(packet.launch_events) == 1
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
