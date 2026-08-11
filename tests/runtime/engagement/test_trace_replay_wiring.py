"""Focused gates for the T10 slice-4 maintained-run evidence wiring (I59).

Slice 4 of the T10 evidence-spine census order (see
``docs/plan/archive/unified_architecture_program_completed_20260727/t10_evidence_spine_census_20260721.md``
section 3 step 4) wires the *real* run-global evidence producers built in slice 3
(I54) into the maintained window path
(``RuntimeFacadeAdapter.run_maintained_window``), replacing the placeholder
``trace_ids = [1]`` and the synthetic ``input_snapshot_version``
(``"obs:{world}:{entity}"``; glossary
``t10_evidence_glossary_20260721.md`` rows).

The wiring is additive and opt-in. These gates prove:

* the switch defaults off, and with it off the maintained window keeps the exact
  placeholder evidence values **and never invokes the I54 producers** (the
  facade allocators stay at cursor 1), so the default serialized evidence is
  byte-for-byte the pre-slice-4 baseline -- the existing
  ``test_trace_replay_gates.py`` / ``test_evidence_producers.py`` gates stay
  green unchanged;
* the default window-evidence dump is reproducible across independent adapters
  (same-scenario byte comparison);
* with the switch on, ``trace_ids`` are minted from the VA-8
  ``allocate_trace_id`` allocator (monotone across windows, +1 per window
  regardless of kernel engagement-event id activity) and
  ``input_snapshot_version`` becomes ``"snapshot:{n}"`` from the VA-2
  ``allocate_run_snapshot_version`` producer (monotone), overriding the
  synthetic caller/default string;
* the opt-in fail-fast guard is load-bearing: against a binding surface that
  lacks the four I54 producers (a proxy hiding them from the adapter's
  ``hasattr`` capability probe), the capability bit resolves ``False``, the
  default path keeps working untouched, and opt-in raises the *named*
  ``RuntimeError`` -- not a bare ``AttributeError`` leaking from the missing
  binding.
"""

from __future__ import annotations

import json

import pytest

from python.runtime_bootstrap import ensure_repo_imports
from python.runtime_bootstrap import resolve_repo_path


ensure_repo_imports()

import ef_py  # noqa: E402
from python.rl.runtime.world_batch import RuntimeFacadeAdapter  # noqa: E402


_DB_PATH = resolve_repo_path("examples", "config", "database")

# Node ids whose window-record ``source_snapshot_version`` echoes the action
# request's ``input_snapshot_version`` (the export node uses a distinct
# ``observation_packet:*`` evidence string instead).
_INPUT_SNAPSHOT_NODES = ("fire_control_launch.v1", "effects_damage.v1")


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


def _apply_fire_scenario(adapter: RuntimeFacadeAdapter) -> tuple[int, int, float]:
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
  setup_result = adapter.apply_world_setup(setup)
  shooter_id = int(setup_result.entity_ids[0])
  target_id = int(setup_result.entity_ids[1])

  obs = None
  for _ in range(80):
    adapter.step_batch()
    obs = adapter.get_agent_observations_batch([_world_ref(0, shooter_id)])[0]
    if any(int(track.id) == target_id for track in getattr(obs, "contacts", [])):
      break
  else:
    raise AssertionError("expected facade observation helper to expose a target contact")

  source_time_s = float(getattr(obs, "sim_time", 0.0) or 0.0)
  return shooter_id, target_id, source_time_s


def _primed_adapter(*, use_facade_evidence_producers: bool) -> tuple[RuntimeFacadeAdapter, int, float]:
  adapter = RuntimeFacadeAdapter(1, use_facade_evidence_producers=use_facade_evidence_producers)
  if not adapter.load_database(_DB_PATH):
    raise AssertionError("failed to load runtime database")
  shooter_id, _target_id, source_time_s = _apply_fire_scenario(adapter)
  return adapter, shooter_id, source_time_s


def _run_fire_window(
  adapter: RuntimeFacadeAdapter,
  shooter_id: int,
  source_time_s: float,
  tag: object,
  *,
  input_snapshot_version: str | None = None,
) -> object:
  evidence = adapter.run_maintained_window(
    world_index=0,
    entity_id=shooter_id,
    pilot_action=_make_pilot_fire_action(),
    source_time_s=source_time_s,
    window_id=f"trace_replay_wiring:{tag}",
    input_snapshot_version=input_snapshot_version,
    source_layer="training_policy",
    information_state_label="facade_observation_packet",
    action_family="direct_control",
    include_engagement=True,
    include_diagnostics=True,
  )
  assert evidence is not None, "run_maintained_window requires the RuntimeFacade window API"
  return evidence


def _input_snapshot_versions(evidence: object) -> list[str]:
  return [
    str(node.source_snapshot_version)
    for node in evidence.executed_nodes
    if node.node_id in _INPUT_SNAPSHOT_NODES
  ]


_NORMALIZE_MAX_DEPTH = 24


def _normalize(value: object, depth: int = 0) -> object:
  if depth > _NORMALIZE_MAX_DEPTH:
    raise AssertionError("evidence DTO nesting exceeded the normalization depth bound")
  if value is None or isinstance(value, (bool, int, float, str, bytes)):
    return value
  if isinstance(value, (list, tuple)):
    return [_normalize(item, depth + 1) for item in value]
  if isinstance(value, dict):
    return {str(key): _normalize(item, depth + 1) for key, item in sorted(value.items())}
  if hasattr(type(value), "__members__"):
    return int(value)
  fields = {}
  for name in dir(value):
    if name.startswith("_"):
      continue
    attr = getattr(value, name)
    if callable(attr):
      continue
    fields[name] = _normalize(attr, depth + 1)
  if not fields:
    return repr(value)
  return fields


def _canonical(value: object) -> str:
  return json.dumps(_normalize(value), sort_keys=True)


# --- Switch default + capability -------------------------------------------


def test_evidence_producer_switch_defaults_to_off() -> None:
  adapter = RuntimeFacadeAdapter(1)
  assert adapter.use_facade_evidence_producers is False
  # The I54 run-global producers are available on this build (slice-4 depends on
  # slice-3); the opt-in path is a policy choice, not a capability gap.
  assert adapter.capabilities.has_run_global_evidence_producers is True

  opted_in = RuntimeFacadeAdapter(1, use_facade_evidence_producers=True)
  assert opted_in.use_facade_evidence_producers is True


# --- Default path: placeholder values, producers untouched ------------------


def test_default_path_keeps_placeholder_evidence_and_never_touches_producers() -> None:
  adapter, shooter_id, source_time_s = _primed_adapter(use_facade_evidence_producers=False)

  for k in range(3):
    evidence = _run_fire_window(adapter, shooter_id, source_time_s, k)
    # trace_ids stays the maintained placeholder [1] on every window.
    assert list(evidence.engagement_packet.trace_ids) == [1]
    # input_snapshot_version falls back to the synthetic "obs:{world}:{entity}".
    assert _input_snapshot_versions(evidence) == [f"obs:0:{shooter_id}"] * len(
      _input_snapshot_versions(evidence)
    )
    assert _input_snapshot_versions(evidence)

  # The decisive additive proof: the default path never invoked the I54
  # producers, so both run-global cursors are still at their fresh-facade start
  # (1). Nothing the default path serialized can differ from the pre-slice-4
  # baseline.
  assert int(adapter.facade.peek_next_trace_id()) == 1
  assert int(adapter.facade.peek_next_run_snapshot_version()) == 1


def test_default_path_preserves_caller_supplied_input_snapshot_version() -> None:
  adapter, shooter_id, source_time_s = _primed_adapter(use_facade_evidence_producers=False)
  evidence = _run_fire_window(
    adapter,
    shooter_id,
    source_time_s,
    "caller",
    input_snapshot_version="obs:0:caller_supplied",
  )
  versions = _input_snapshot_versions(evidence)
  assert versions
  assert all(version == "obs:0:caller_supplied" for version in versions)
  assert list(evidence.engagement_packet.trace_ids) == [1]
  assert int(adapter.facade.peek_next_trace_id()) == 1
  assert int(adapter.facade.peek_next_run_snapshot_version()) == 1


def test_default_window_evidence_dump_is_reproducible_across_adapters() -> None:
  adapter_a, shooter_a, time_a = _primed_adapter(use_facade_evidence_producers=False)
  evidence_a = _run_fire_window(adapter_a, shooter_a, time_a, "dump")

  adapter_b, shooter_b, time_b = _primed_adapter(use_facade_evidence_producers=False)
  evidence_b = _run_fire_window(adapter_b, shooter_b, time_b, "dump")

  # Same deterministic scenario (seed 123) through two independent default
  # adapters -> byte-identical serialized engagement + observation evidence.
  dump_a = _canonical(
    {
      "engagement": evidence_a.engagement_packet,
      "observation": evidence_a.observation_packet,
    }
  )
  dump_b = _canonical(
    {
      "engagement": evidence_b.engagement_packet,
      "observation": evidence_b.observation_packet,
    }
  )
  assert dump_a == dump_b
  assert len(dump_a) > 1000
  assert '"trace_ids": [1]' in dump_a


# --- Opt-in path: real facade-minted monotone evidence ----------------------


def test_optin_stamps_real_monotone_trace_ids_independent_of_kernel() -> None:
  adapter, shooter_id, source_time_s = _primed_adapter(use_facade_evidence_producers=True)

  minted: list[int] = []
  for k in range(3):
    evidence = _run_fire_window(adapter, shooter_id, source_time_s, k)
    trace_ids = [int(value) for value in evidence.engagement_packet.trace_ids]
    assert len(trace_ids) == 1
    minted.append(trace_ids[0])
    # The exported observation-export diagnostics trace carries the minted tag.
    diag_trace_ids = [int(trace.trace_id) for trace in evidence.diagnostics_traces]
    assert diag_trace_ids == trace_ids

  # Monotone from 1, exactly +1 per window despite each window driving kernel
  # engagement-event id activity (VA-8: the facade allocator is disjoint from
  # the resettable kernel next_engagement_event_id_ space).
  assert minted == [1, 2, 3]
  assert int(adapter.facade.peek_next_trace_id()) == 4


def test_optin_stamps_real_monotone_input_snapshot_versions() -> None:
  adapter, shooter_id, source_time_s = _primed_adapter(use_facade_evidence_producers=True)

  for k in range(3):
    evidence = _run_fire_window(adapter, shooter_id, source_time_s, k)
    versions = _input_snapshot_versions(evidence)
    assert versions
    expected = f"snapshot:{k + 1}"
    assert all(version == expected for version in versions), (k, versions)

  assert int(adapter.facade.peek_next_run_snapshot_version()) == 4


def test_optin_overrides_synthetic_caller_input_snapshot_version() -> None:
  adapter, shooter_id, source_time_s = _primed_adapter(use_facade_evidence_producers=True)
  evidence = _run_fire_window(
    adapter,
    shooter_id,
    source_time_s,
    "override",
    input_snapshot_version="obs:0:caller_supplied",
  )
  versions = _input_snapshot_versions(evidence)
  assert versions
  # Opt-in mints the real produced version, overriding any synthetic caller str.
  assert all(version == "snapshot:1" for version in versions)
  assert all(not version.startswith("obs:") for version in versions)


# --- Fail-fast contract when the I54 producers are missing ------------------


_PRODUCER_METHOD_NAMES = (
  "allocate_trace_id",
  "peek_next_trace_id",
  "allocate_run_snapshot_version",
  "peek_next_run_snapshot_version",
)


class _ProducerlessFacadeProxy:
  """Wrap a live facade while hiding the four I54 run-global producer methods.

  Simulates a pre-I54 binding surface. The adapter's capability probe is
  ``hasattr``-based, and ``hasattr`` keys on ``AttributeError``: rejecting the
  four producer names from ``__getattr__`` therefore resolves
  ``has_run_global_evidence_producers`` to ``False``. Every other attribute is
  forwarded to the wrapped facade, so the maintained window path itself keeps
  working (``run_window``, exports, observations).
  """

  def __init__(self, facade: object) -> None:
    self._facade = facade

  def __getattr__(self, name: str) -> object:
    if name in _PRODUCER_METHOD_NAMES:
      raise AttributeError(name)
    return getattr(self._facade, name)


def _swap_in_producerless_facade(adapter: RuntimeFacadeAdapter) -> None:
  # Swap after scenario priming so the gate stays focused on the window
  # evidence path. The adapter's capability cache keys on id(self.facade), so
  # the next capabilities access re-resolves against the proxy.
  adapter.facade = _ProducerlessFacadeProxy(adapter.facade)
  assert adapter.capabilities.has_run_global_evidence_producers is False


def test_default_path_works_unchanged_when_producers_are_missing() -> None:
  adapter, shooter_id, source_time_s = _primed_adapter(use_facade_evidence_producers=False)
  _swap_in_producerless_facade(adapter)

  # The default path neither needs nor touches the producers: the window still
  # completes against the producerless surface with the placeholder evidence.
  # (Any default-path producer call would surface as the proxy's
  # AttributeError and fail this window.)
  evidence = _run_fire_window(adapter, shooter_id, source_time_s, "producerless-default")
  assert list(evidence.engagement_packet.trace_ids) == [1]
  versions = _input_snapshot_versions(evidence)
  assert versions
  assert all(version == f"obs:0:{shooter_id}" for version in versions)


def test_optin_fails_fast_with_named_error_when_producers_are_missing() -> None:
  """Negative gate for the opt-in fail-fast guard contract.

  Guard-removal drill (load-bearing proof, re-run at this baseline): replacing
  ``RuntimeFacadeAdapter._require_run_global_evidence_producers`` with a no-op
  in memory makes exactly this test fail -- the window then dies with a bare
  ``AttributeError('allocate_trace_id')`` from the proxy instead of the named
  ``RuntimeError`` pinned below, so neither deleting the guard nor letting it
  degrade to the raw binding error can pass this gate.
  """
  adapter, shooter_id, source_time_s = _primed_adapter(use_facade_evidence_producers=True)
  _swap_in_producerless_facade(adapter)

  with pytest.raises(
    RuntimeError,
    match=r"requires the I54 run-global evidence producers",
  ) as excinfo:
    _run_fire_window(adapter, shooter_id, source_time_s, "producerless-optin")

  message = str(excinfo.value)
  # The named contract: the error points the caller at the opt-in switch and
  # the missing I54 producer bindings.
  assert "use_facade_evidence_producers=True" in message
  assert "allocate_trace_id" in message
  assert "allocate_run_snapshot_version" in message
