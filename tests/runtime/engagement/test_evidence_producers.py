"""Focused gates for the T10 slice-3 / I54 dedicated evidence producers.

These pin the *new* additive run-global producers added on ``RuntimeFacade``:

* ``allocate_run_snapshot_version`` / ``peek_next_run_snapshot_version`` (VA-2):
  a run-global monotone snapshot-version counter that does not reset per export.
* ``allocate_trace_id`` / ``peek_next_trace_id`` (VA-8): a dedicated trace-id
  allocator that is independent of the kernel's resettable
  ``next_engagement_event_id_`` space.

The producers are built "producer first": this slice does not wire them into any
existing export path, so the last test here proves that exercising them leaves
every existing serialized evidence value unchanged (the additive red line) via a
full recursive DTO normalization (every bound field, nested DTOs and vectors
included) rather than a hand-picked fingerprint. "Run-global" is adjudicated as
the lifetime of a single ``RuntimeFacade`` instance (see
``src/runtime/facade/runtime_facade.h``): the sequences survive exports,
``step_batch``, ``reset_batch`` (episode re-seed),
``clear_execution_episode_batch`` and ``resize``; only a fresh facade restarts
them at 1. Move semantics (run identity transfers on move; the moved-from
facade fail-fasts) are pinned in C++
(``src/tests/test_runtime_facade_evidence_allocators.cpp``) because the Python
surface cannot trigger a C++ move: nanobind holds ``RuntimeFacade`` by pointer
and no binding returns it by value.
"""

from __future__ import annotations

import json

from python.runtime_bootstrap import ensure_repo_imports
from python.runtime_bootstrap import resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402


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


def _make_authorized_release_command(shooter_id: int, target_id: int) -> ef_py.MissionCommand:
  command = ef_py.MissionCommand()
  command.active = True
  command.authorization_to_fire = True
  command.assigned_target_id = int(target_id)
  command.engagement_authority_holder_id = int(shooter_id)
  return command


def _apply_fire_scenario(facade: ef_py.RuntimeFacade) -> tuple[int, int]:
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
    ),
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

  return shooter_id, target_id


def _fire_window_request(shooter_id: int, target_id: int) -> ef_py.RuntimeWindowRequest:
  request = ef_py.RuntimeWindowRequest()
  request.window_id = f"window:evidence_producers:{shooter_id}"
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
  action_request.source_layer = "evidence_producer_test"
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
  action_request.action_intent.has_mission_command = True
  action_request.action_intent.mission_command = _make_authorized_release_command(
    shooter_id,
    target_id,
  )
  request.action_requests = [action_request]
  return request


def _build_launched_facade() -> tuple[ef_py.RuntimeFacade, int, ef_py.EngagementBatchRequest]:
  facade = ef_py.RuntimeFacade(1)
  if not facade.load_database(_DB_PATH):
    raise AssertionError("failed to load runtime database")
  shooter_id, target_id = _apply_fire_scenario(facade)
  window_request = _fire_window_request(shooter_id, target_id)
  packet = facade.run_window(window_request).engagement_packet
  if not any(int(event.spawned_munition.entity_id) > 0 for event in packet.launch_events):
    raise AssertionError("expected the fire window to produce a launch event")
  return facade, shooter_id, window_request.engagement_request


_NORMALIZE_MAX_DEPTH = 24


def _normalize_evidence_dto(value: object, depth: int = 0) -> object:
  """Recursively expand an ``ef_py`` DTO into plain Python data.

  Every public, non-callable attribute is expanded, nested DTOs and vectors
  included, so a deep-equal over the result covers the packet's full bound
  field surface instead of a hand-picked fingerprint.
  """
  if depth > _NORMALIZE_MAX_DEPTH:
    raise AssertionError("evidence DTO nesting exceeded the normalization depth bound")
  if value is None or isinstance(value, (bool, int, float, str, bytes)):
    return value
  if isinstance(value, (list, tuple)):
    return [_normalize_evidence_dto(item, depth + 1) for item in value]
  if isinstance(value, dict):
    return {
      str(key): _normalize_evidence_dto(item, depth + 1) for key, item in sorted(value.items())
    }
  if hasattr(type(value), "__members__"):
    # Bound enums normalize to their integral value.
    return int(value)
  fields = {}
  for name in dir(value):
    if name.startswith("_"):
      continue
    attr = getattr(value, name)
    if callable(attr):
      continue
    fields[name] = _normalize_evidence_dto(attr, depth + 1)
  if not fields:
    raise AssertionError(
      f"evidence DTO of type {type(value).__name__} exposed no normalizable fields"
    )
  return fields


def _canonical_evidence_json(value: object) -> str:
  return json.dumps(_normalize_evidence_dto(value), sort_keys=True)


# --- VA-2 / VA-8 counter semantics -----------------------------------------


def test_run_snapshot_version_allocator_is_monotone_from_one() -> None:
  facade = ef_py.RuntimeFacade(1)
  assert int(facade.peek_next_run_snapshot_version()) == 1
  minted = [int(facade.allocate_run_snapshot_version()) for _ in range(5)]
  assert minted == [1, 2, 3, 4, 5]
  assert int(facade.peek_next_run_snapshot_version()) == 6


def test_trace_id_allocator_is_monotone_from_one() -> None:
  facade = ef_py.RuntimeFacade(1)
  assert int(facade.peek_next_trace_id()) == 1
  minted = [int(facade.allocate_trace_id()) for _ in range(5)]
  assert minted == [1, 2, 3, 4, 5]
  assert int(facade.peek_next_trace_id()) == 6


def test_peek_does_not_advance_either_allocator() -> None:
  facade = ef_py.RuntimeFacade(1)
  for _ in range(3):
    assert int(facade.peek_next_run_snapshot_version()) == 1
    assert int(facade.peek_next_trace_id()) == 1
  assert int(facade.allocate_run_snapshot_version()) == 1
  assert int(facade.allocate_trace_id()) == 1


def test_snapshot_version_and_trace_id_are_independent_counters() -> None:
  facade = ef_py.RuntimeFacade(1)
  assert int(facade.allocate_run_snapshot_version()) == 1
  assert int(facade.allocate_run_snapshot_version()) == 2
  # Draining the snapshot-version counter must not disturb the trace-id counter.
  assert int(facade.peek_next_trace_id()) == 1
  assert int(facade.allocate_trace_id()) == 1
  assert int(facade.allocate_run_snapshot_version()) == 3
  assert int(facade.allocate_trace_id()) == 2


def test_fresh_facade_restarts_sequences_at_one() -> None:
  first = ef_py.RuntimeFacade(1)
  for _ in range(4):
    first.allocate_run_snapshot_version()
    first.allocate_trace_id()
  assert int(first.peek_next_run_snapshot_version()) == 5
  assert int(first.peek_next_trace_id()) == 5

  # A new facade is a new "run": the sequences start over at 1, independent of
  # any other live facade instance.
  second = ef_py.RuntimeFacade(1)
  assert int(second.peek_next_run_snapshot_version()) == 1
  assert int(second.peek_next_trace_id()) == 1
  # The original facade is unaffected by the second facade's existence.
  assert int(first.allocate_run_snapshot_version()) == 5


# --- Run-global boundary: no reset across in-run lifecycle events ------------


def test_allocators_do_not_reset_across_steps_and_exports() -> None:
  facade, shooter_id, engagement_request = _build_launched_facade()
  before_sv = int(facade.allocate_run_snapshot_version())
  before_tid = int(facade.allocate_trace_id())

  # Exercise real in-run activity: exports and further steps.
  facade.export_engagement_event_packet(engagement_request)
  facade.export_observation_packet([_world_ref(0, shooter_id)])
  for _ in range(5):
    facade.step_batch()
  facade.export_engagement_event_packet(engagement_request)

  after_sv = int(facade.allocate_run_snapshot_version())
  after_tid = int(facade.allocate_trace_id())
  assert after_sv == before_sv + 1
  assert after_tid == before_tid + 1


def test_allocators_survive_reset_batch_and_episode_clear() -> None:
  facade = ef_py.RuntimeFacade(1)
  for _ in range(3):
    facade.allocate_run_snapshot_version()
    facade.allocate_trace_id()
  sv_cursor = int(facade.peek_next_run_snapshot_version())
  tid_cursor = int(facade.peek_next_trace_id())
  assert sv_cursor == 4
  assert tid_cursor == 4

  # Episode-level resets must not rewind the run-global counters.
  facade.reset_batch()
  facade.clear_execution_episode_batch()
  facade.resize(2)

  assert int(facade.peek_next_run_snapshot_version()) == sv_cursor
  assert int(facade.peek_next_trace_id()) == tid_cursor
  assert int(facade.allocate_run_snapshot_version()) == sv_cursor
  assert int(facade.allocate_trace_id()) == tid_cursor


# --- VA-8 independence from the kernel engagement-event id space -------------


def test_trace_id_allocator_is_independent_of_kernel_engagement_event_ids() -> None:
  facade, shooter_id, engagement_request = _build_launched_facade()

  # A full launch has been produced -- the kernel advanced its own resettable
  # next_engagement_event_id_ space to mint the recorded trace ids -- yet the
  # facade's dedicated allocator has not been consumed at all. The two id
  # spaces are disjoint (VA-8): sim/kernel activity never draws facade ids.
  assert int(facade.peek_next_trace_id()) == 1

  base_trace_ids = [
    int(trace.trace_id)
    for trace in facade.export_engagement_event_packet(engagement_request).diagnostics_traces
  ]
  assert base_trace_ids
  assert any(trace_id > 0 for trace_id in base_trace_ids)

  # Draining the facade allocator must not perturb the exported trace ids.
  for _ in range(10):
    facade.allocate_trace_id()
  after_trace_ids = [
    int(trace.trace_id)
    for trace in facade.export_engagement_event_packet(engagement_request).diagnostics_traces
  ]
  assert after_trace_ids == base_trace_ids
  assert int(facade.peek_next_trace_id()) == 11


# --- Additive red line: producers perturb no existing serialized value -------


def test_new_producers_do_not_change_existing_serialized_evidence() -> None:
  facade, shooter_id, engagement_request = _build_launched_facade()

  engagement_before = _normalize_evidence_dto(
    facade.export_engagement_event_packet(engagement_request)
  )
  observation_before = _normalize_evidence_dto(
    facade.export_observation_packet([_world_ref(0, shooter_id)])
  )

  # Full-surface coverage guard: the normalization must have expanded every
  # bound packet field (27 on EngagementEventPacket and 7 on
  # ObservationBatchPacket at this baseline; floors rather than exact pins so
  # additive slice-4 fields do not break this gate), including the
  # provenance/refs/trace_ids/nested fields a hand-written fingerprint would
  # skip.
  for required in (
    "snapshot_version",
    "barrier_id",
    "barrier_sequence",
    "barrier_detail",
    "source_time_s",
    "producer_node_id",
    "packet_provenance",
    "diagnostics_provenance",
    "refs",
    "trace_ids",
    "track_packets",
    "launch_requests",
    "launch_events",
    "munition_lifecycle_packets",
    "effects_events",
    "damage_reports",
    "diagnostics_traces",
  ):
    assert required in engagement_before, required
  assert len(engagement_before) >= 27
  for required in (
    "snapshot_version",
    "barrier_id",
    "source_time_s",
    "provenance",
    "refs",
    "agent_observations",
    "instrument_states",
  ):
    assert required in observation_before, required
  assert len(observation_before) >= 7
  # Non-vacuous: the engagement export actually carries evidence rows.
  assert engagement_before["diagnostics_traces"] or engagement_before["track_packets"]

  engagement_before_json = json.dumps(engagement_before, sort_keys=True)
  observation_before_json = json.dumps(observation_before, sort_keys=True)
  assert len(engagement_before_json) > 1000

  # Heavily exercise both new producers between two identical exports.
  for _ in range(11):
    facade.allocate_run_snapshot_version()
    facade.allocate_trace_id()

  engagement_after_json = _canonical_evidence_json(
    facade.export_engagement_event_packet(engagement_request)
  )
  observation_after_json = _canonical_evidence_json(
    facade.export_observation_packet([_world_ref(0, shooter_id)])
  )

  assert engagement_after_json == engagement_before_json
  assert observation_after_json == observation_before_json
