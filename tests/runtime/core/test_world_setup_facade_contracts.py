from __future__ import annotations

import unittest

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

import ef_py # noqa: E402

from python.scenario.runtime import apply_runtime_world_layout_request_maintained # noqa: E402
from python.scenario.runtime import apply_world_setup_payload_maintained # noqa: E402
from python.scenario.runtime import build_batch_world_setup_request # noqa: E402
from python.scenario.runtime import build_runtime_world_layout_request # noqa: E402
from python.scenario.runtime import extract_runtime_world_layout_entity_ids # noqa: E402
from python.scenario.runtime import extract_batch_world_setup_entity_ids # noqa: E402
from python.scenario.runtime import normalize_world_setup_terrain_assignments # noqa: E402
from python.scenario.runtime.world_setup import apply_world_setup_request_maintained # noqa: E402


class _FacadeOnlyRuntime:
  def __init__(self) -> None:
    self.calls: list[str] = []

  def apply_world_setup(self, request):
    self.calls.append("apply_world_setup")
    result = ef_py.BatchWorldSetupResult()
    result.entity_ids = [701, 702]
    return result


class _FacadeOnlyWorldLayoutRuntime:
  def __init__(self) -> None:
    self.calls: list[str] = []
    self.last_request = None

  def apply_world_layout(self, request):
    self.calls.append("apply_world_layout_request")
    self.last_request = request
    result = ef_py.RuntimeWorldLayoutResult()
    result.world_index = int(request.world_index)
    result.entity_ids = [611, 612]
    return result


class _BatchOnlyRuntime:
  def __init__(self) -> None:
    self.calls: list[str] = []
    self.last_batch_args = None

  def apply_world_setup_batch(
    self,
    seeds,
    terrain_assignments,
    wind_assignments,
    zones,
    spawn_requests,
    time_steps,
  ):
    self.calls.append("apply_world_setup_batch")
    self.last_batch_args = (
      list(seeds),
      list(terrain_assignments),
      list(wind_assignments),
      list(zones),
      list(spawn_requests),
      list(time_steps),
    )
    return [801, 802, 803]


class _RawRuntimeWithFutureFacadeSetupMethod:
  def apply_world_setup(self, request):
    raise AssertionError("raw runtime apply_world_setup must stay quarantined")

  def world_raw_quarantine(self, index):
    raise AssertionError(f"raw world_raw_quarantine({index}) access must stay quarantined")


class _RawSignatureWorldLayoutRuntime:
  def __init__(self) -> None:
    self.calls: list[str] = []
    self.last_layout_args = None

  def apply_world_layout(
    self,
    world_index,
    seed,
    terrain_type,
    wind_speed_mps,
    wind_dir_from_deg,
    wind_shear_mps_per_km,
    maritime_configured,
    sea_state,
    wave_heading_deg,
    wave_period_s,
    zones,
    spawn_requests,
    time_steps,
  ):
    self.calls.append("apply_world_layout_compat")
    self.last_layout_args = (
      int(world_index),
      int(seed),
      str(terrain_type),
      float(wind_speed_mps),
      float(wind_dir_from_deg),
      float(wind_shear_mps_per_km),
      bool(maritime_configured),
      float(sea_state),
      float(wave_heading_deg),
      float(wave_period_s),
      list(zones),
      list(spawn_requests),
      list(time_steps),
    )
    return [911, 912]

  def world(self, index):
    raise AssertionError(f"layout helper should not need raw world({index}) access")


class WorldSetupFacadeContractTests(unittest.TestCase):
  def test_build_batch_world_setup_request_normalizes_seed_and_time_step_payloads(self) -> None:
    request = build_batch_world_setup_request(
      seeds=[-1, 5],
      terrain_assignments=[],
      wind_assignments=[],
      zones=[],
      spawn_requests=[],
      time_steps=[0, 0.05],
    )

    self.assertIsInstance(request, ef_py.BatchWorldSetupRequest)
    self.assertEqual(list(request.seeds), [0xFFFFFFFF, 5])
    self.assertEqual(list(request.time_steps), [0.0, 0.05])
    self.assertEqual(len(list(request.terrain_assignments)), 2)
    self.assertEqual([str(item.terrain_type) for item in list(request.terrain_assignments)], ["flat", "flat"])

  def test_normalize_world_setup_terrain_assignments_marks_default_and_compatibility_sources(self) -> None:
    explicit_legacy = ef_py.WorldTerrainAssignment()
    explicit_legacy.world_index = 1
    explicit_legacy.terrain_type = "legacy"

    normalized, sources = normalize_world_setup_terrain_assignments(
      [explicit_legacy],
      world_count=2,
    )

    self.assertEqual(len(normalized), 2)
    normalized_by_world = {int(item.world_index): str(item.terrain_type) for item in normalized}
    self.assertEqual(normalized_by_world[0], "flat")
    self.assertEqual(normalized_by_world[1], "legacy")
    self.assertEqual(sources, ["default_mainline", "explicit_legacy_compatibility"])

  def test_normalize_world_setup_terrain_assignments_rejects_unknown_terrain_type(self) -> None:
    unknown = ef_py.WorldTerrainAssignment()
    unknown.world_index = 0
    unknown.terrain_type = "desert"

    with self.assertRaisesRegex(ValueError, "Unknown terrain_type"):
      normalize_world_setup_terrain_assignments([unknown], world_count=1)

  def test_simulation_kernel_set_terrain_type_rejects_unknown_profile(self) -> None:
    kernel = ef_py.SimulationKernel()

    with self.assertRaisesRegex(Exception, "Unknown terrain_type"):
      kernel.set_terrain_type("desert")

  def test_apply_world_setup_payload_prefers_facade_result_shape(self) -> None:
    runtime = _FacadeOnlyRuntime()

    entity_ids = apply_world_setup_payload_maintained(
      runtime,
      seeds=[11],
      terrain_assignments=[],
      wind_assignments=[],
      zones=[],
      spawn_requests=[],
      time_steps=[0.05],
    )

    self.assertEqual(runtime.calls, ["apply_world_setup"])
    self.assertEqual(entity_ids, [701, 702])

  def test_apply_world_setup_payload_rejects_batch_only_runtime(self) -> None:
    runtime = _BatchOnlyRuntime()

    with self.assertRaisesRegex(RuntimeError, "requires a maintained facade setup target"):
      apply_world_setup_payload_maintained(
        runtime,
        seeds=[17, 19],
        terrain_assignments=[],
        wind_assignments=[],
        zones=[],
        spawn_requests=[],
        time_steps=[0.1, 0.2],
      )

    self.assertEqual(runtime.calls, [])

  def test_apply_world_setup_request_maintained_rejects_raw_runtime_shape_even_if_future_binding_drifts(self) -> None:
    request = build_batch_world_setup_request(
      seeds=[31],
      terrain_assignments=[],
      wind_assignments=[],
      zones=[],
      spawn_requests=[],
      time_steps=[0.05],
    )

    with self.assertRaisesRegex(RuntimeError, "requires a maintained facade setup target"):
      apply_world_setup_request_maintained(
        _RawRuntimeWithFutureFacadeSetupMethod(),
        request,
      )

  def test_build_runtime_world_layout_request_preserves_maritime_fields(self) -> None:
    request = build_runtime_world_layout_request(
      world_index=3,
      seed=-9,
      terrain_type="legacy",
      wind_speed_mps=4.0,
      wind_dir_from_deg=185.0,
      wind_shear_mps_per_km=0.25,
      maritime_configured=True,
      sea_state=0.0,
      wave_heading_deg=135.0,
      wave_period_s=11.0,
      zones=[],
      spawn_requests=[],
      time_steps=[0.05],
    )

    self.assertIsInstance(request, ef_py.RuntimeWorldLayoutRequest)
    self.assertEqual(int(request.world_index), 3)
    self.assertEqual(int(request.seed), 0xFFFFFFFF - 8)
    self.assertTrue(bool(request.maritime_configured))
    self.assertEqual(float(request.sea_state), 0.0)
    self.assertEqual(float(request.wave_heading_deg), 135.0)
    self.assertEqual(float(request.wave_period_s), 11.0)
    self.assertEqual(list(request.time_steps), [0.05])

  def test_apply_runtime_world_layout_request_prefers_facade_result_shape(self) -> None:
    runtime = _FacadeOnlyWorldLayoutRuntime()
    request = build_runtime_world_layout_request(
      world_index=1,
      seed=21,
      terrain_type="flat",
      wind_speed_mps=1.0,
      wind_dir_from_deg=90.0,
      wind_shear_mps_per_km=0.0,
      maritime_configured=False,
      sea_state=0.0,
      wave_heading_deg=0.0,
      wave_period_s=8.0,
      zones=[],
      spawn_requests=[],
      time_steps=[0.05],
    )

    result = apply_runtime_world_layout_request_maintained(runtime, request)

    self.assertEqual(runtime.calls, ["apply_world_layout_request"])
    self.assertEqual(int(result.world_index), 1)
    self.assertEqual(extract_runtime_world_layout_entity_ids(result), [611, 612])

  def test_apply_runtime_world_layout_request_rejects_untyped_result_shape(self) -> None:
    class _UntypedResultRuntime:
      def apply_world_layout(self, request):
        return [611, 612]

    request = build_runtime_world_layout_request(
      world_index=1,
      seed=21,
      terrain_type="flat",
      wind_speed_mps=1.0,
      wind_dir_from_deg=90.0,
      wind_shear_mps_per_km=0.0,
      maritime_configured=False,
      sea_state=0.0,
      wave_heading_deg=0.0,
      wave_period_s=8.0,
      zones=[],
      spawn_requests=[],
      time_steps=[0.05],
    )

    with self.assertRaisesRegex(RuntimeError, "requires maintained RuntimeWorldLayoutResult bindings"):
      apply_runtime_world_layout_request_maintained(_UntypedResultRuntime(), request)

  def test_apply_runtime_world_layout_request_rejects_raw_signature_runtime(self) -> None:
    runtime = _RawSignatureWorldLayoutRuntime()
    request = build_runtime_world_layout_request(
      world_index=2,
      seed=27,
      terrain_type="legacy",
      wind_speed_mps=3.5,
      wind_dir_from_deg=200.0,
      wind_shear_mps_per_km=0.5,
      maritime_configured=True,
      sea_state=2.0,
      wave_heading_deg=45.0,
      wave_period_s=9.5,
      zones=[],
      spawn_requests=[],
      time_steps=[0.08],
    )

    with self.assertRaisesRegex(RuntimeError, "requires a maintained facade setup target"):
      apply_runtime_world_layout_request_maintained(runtime, request)

    self.assertEqual(runtime.calls, [])

  def test_extract_batch_world_setup_entity_ids_requires_typed_result_shape(self) -> None:
    result = ef_py.BatchWorldSetupResult()
    result.entity_ids = [901, 902]

    self.assertEqual(extract_batch_world_setup_entity_ids(result), [901, 902])
    with self.assertRaisesRegex(RuntimeError, "requires maintained BatchWorldSetupResult bindings"):
      extract_batch_world_setup_entity_ids([903, 904])


if __name__ == "__main__":
  unittest.main()
