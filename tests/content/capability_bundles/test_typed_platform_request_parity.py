"""T11 pilot (this iteration): entity-materialization parity fixture.

Reference path: ``WorldSpawnRequest`` (the ``spawn_unit`` compatibility
surface -- ``spawn_from_request`` calls ``SimulationKernel::spawn_unit``
directly). New opt-in path: the content capability-bundle document for the
bounded submarine family, expanded through the registered ``submarine``
family expander into a maintained ``typed_platform_request`` and consumed by
``RuntimeFacade.apply_world_setup``.

Both paths spawn ``Kilo_Class_MVP`` with identical placement into two
same-seeded worlds of one facade batch; the fixture then compares the
materialized entities field-for-field over the public observation surface,
at setup and again after stepping (dynamics parity), with exact equality.
"""

from __future__ import annotations

import json
from pathlib import Path

from python.runtime_bootstrap import ensure_repo_imports, resolve_repo_path


ensure_repo_imports()

import ef_py # noqa: E402

from python.content.capability_bundles import ( # noqa: E402
  SpawnPlacement,
  expand_typed_platform_request,
)
from python.content.capability_bundles.bindings_adapter import ( # noqa: E402
  to_typed_platform_spawn_request,
)
import python.content.capability_bundles.submarine # noqa: E402,F401  (G5 opt-in)


REPO_ROOT = Path(__file__).resolve().parents[3]
BUNDLE_DOCUMENT_PATH = (
  REPO_ROOT
  / "python"
  / "content"
  / "capability_bundles"
  / "data"
  / "submarine"
  / "kilo_class_mvp.bundle.json"
)

_OPEN_WATER_X = 1_000_000.0
_OPEN_WATER_Y = 1_000_000.0
_PLACEMENT = SpawnPlacement(
  world_index=1,
  side="blue",
  entity_name="ContentKilo",
  is_agent=False,
  x=_OPEN_WATER_X,
  y=_OPEN_WATER_Y,
  z=0.0,
  heading=90.0,
  vx=4.5,
)


def _entity_ref(world_index: int, entity_id: int) -> ef_py.WorldEntityRef:
  ref = ef_py.WorldEntityRef()
  ref.world_index = int(world_index)
  ref.entity_id = int(entity_id)
  return ref


def _observation_snapshot(observation: object) -> dict:
  snapshot = {}
  for name in dir(observation):
    if name.startswith("_"):
      continue
    value = getattr(observation, name)
    if callable(value):
      continue
    snapshot[name] = repr(value)
  return snapshot


def _expand_content_typed_request() -> ef_py.TypedPlatformSpawnRequest:
  document = json.loads(BUNDLE_DOCUMENT_PATH.read_text(encoding="utf-8"))
  expansion = expand_typed_platform_request(document, "content-typed:kilo", _PLACEMENT)

  assert expansion.diagnostics.valid, expansion.diagnostics
  assert expansion.diagnostics.schema_version == "t11.content_capability_bundle.v1"
  assert expansion.request is not None
  return to_typed_platform_spawn_request(ef_py, expansion.request)


def _build_parity_setup() -> ef_py.BatchWorldSetupRequest:
  setup = ef_py.BatchWorldSetupRequest()
  setup.seeds = [123, 123]

  terrains = []
  winds = []
  for world_index in range(2):
    terrain = ef_py.WorldTerrainAssignment()
    terrain.world_index = world_index
    terrains.append(terrain)
    wind = ef_py.WorldWindAssignment()
    wind.world_index = world_index
    winds.append(wind)
  setup.terrain_assignments = terrains
  setup.wind_assignments = winds

  reference = ef_py.WorldSpawnRequest()
  reference.world_index = 0
  reference.side = ef_py.Side.Blue
  reference.type_name = "Kilo_Class_MVP"
  reference.entity_name = "ReferenceKilo"
  reference.x = _OPEN_WATER_X
  reference.y = _OPEN_WATER_Y
  reference.z = 0.0
  reference.heading = 90.0
  reference.vx = 4.5

  setup.spawn_requests = [reference]
  setup.typed_platform_spawn_requests = [_expand_content_typed_request()]
  setup.time_steps = [0.05, 0.05]
  return setup


def test_content_bundle_materializes_kilo_with_entity_parity_against_spawn_unit() -> None:
  facade = ef_py.RuntimeFacade(2)
  assert facade.load_database(resolve_repo_path("examples", "config", "database"))

  setup_result = facade.apply_world_setup(_build_parity_setup())

  # Reference spawn_unit path unchanged: exactly one legacy entity.
  assert len(setup_result.entity_ids) == 1
  reference_entity_id = int(setup_result.entity_ids[0])
  assert reference_entity_id > 0

  # New opt-in path: materialized through the maintained typed setup surface,
  # never through the type_name projection bridge evidence.
  assert len(setup_result.typed_platform_spawn_results) == 1
  typed_result = setup_result.typed_platform_spawn_results[0]
  assert bool(typed_result.admitted)
  assert bool(typed_result.materialized)
  assert not bool(typed_result.fail_closed)
  assert typed_result.setup_surface == "maintained_typed_setup"
  assert typed_result.rejection_reason == ""
  assert list(typed_result.errors) == []
  assert typed_result.request_id == "content-typed:kilo"
  assert typed_result.source_type_name == "Kilo_Class_MVP"
  assert typed_result.capability_bundle_id == "platform.bundle.kilo_class_mvp"
  evidence_refs = list(typed_result.evidence_refs)
  assert "RuntimeFacade.apply_world_setup.maintained_typed_setup" in evidence_refs
  assert "RuntimeFacade.apply_world_setup.maintained_typed_materialized" in evidence_refs
  assert (
    "RuntimeFacade.apply_world_setup.type_name_projection_materialization"
    not in evidence_refs
  )

  typed_entity_id = int(typed_result.entity_id)
  assert typed_entity_id > 0

  # Field-for-field parity of the materialized entities at setup...
  refs = [_entity_ref(0, reference_entity_id), _entity_ref(1, typed_entity_id)]
  reference_obs, typed_obs = facade.get_agent_observations_batch(refs)
  reference_snapshot = _observation_snapshot(reference_obs)
  typed_snapshot = _observation_snapshot(typed_obs)
  assert reference_snapshot, "observation surface unexpectedly empty"
  assert typed_snapshot == reference_snapshot

  # ...and after stepping the batch (dynamics parity across the same seeds).
  for _ in range(3):
    facade.step_batch()
  reference_obs, typed_obs = facade.get_agent_observations_batch(refs)
  assert _observation_snapshot(typed_obs) == _observation_snapshot(reference_obs)


def test_content_expansion_fails_closed_before_touching_the_runtime() -> None:
  document = json.loads(BUNDLE_DOCUMENT_PATH.read_text(encoding="utf-8"))
  document.pop("schema_version")

  expansion = expand_typed_platform_request(document, "content-typed:kilo", _PLACEMENT)

  assert expansion.request is None
  assert not expansion.diagnostics.valid
  assert expansion.diagnostics.fail_closed
  assert (
    expansion.diagnostics.rejection_reason
    == "content_capability_bundle_schema_version_unsupported"
  )
  assert expansion.diagnostics.schema_version == "t11.content_capability_bundle.v1"


def test_expanded_request_passes_the_runtime_typed_spawn_dto_round_trip() -> None:
  typed = _expand_content_typed_request()

  assert typed.source_type_name == "Kilo_Class_MVP"
  assert typed.capability_bundle.bundle_id == "platform.bundle.kilo_class_mvp"
  assert typed.resolved_spawn_plan.source_request_kind == "typed_platform_request"
  assert typed.resolved_spawn_plan.materialization_strategy == "resolved_spawn_plan_bridge"
  assert not bool(typed.type_name_projection_preserved)
  assert not bool(typed.capability_bundle.type_name_projection_preserved)
  assert not bool(typed.resolved_spawn_plan.type_name_projection_preserved)
  families = [
    capability.family for capability in typed.capability_bundle.capabilities
  ]
  assert families == [
    "sensing",
    "mobility",
    "survivability",
    "command",
    "doctrine",
    "survivability",
  ]

  # The projection-bridge validator must keep rejecting the maintained typed
  # request (it is not the compatibility bridge); the facade's maintained
  # validator is the admitting surface, proven by the parity test above.
  projection_validation = ef_py.validate_typed_platform_spawn_request(typed)
  assert not bool(projection_validation.valid)
  assert (
    projection_validation.rejection_reason
    == "typed_platform_spawn_requires_type_name_projection_path"
  )
