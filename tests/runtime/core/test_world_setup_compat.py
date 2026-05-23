from __future__ import annotations

import unittest

from python.testing.runtime import ensure_repo_imports


ensure_repo_imports()

import ef_py  # noqa: E402

from python.scenario_runtime import apply_world_setup_payload_compat  # noqa: E402
from python.scenario_runtime import build_batch_world_setup_request  # noqa: E402
from python.scenario_runtime import extract_batch_world_setup_entity_ids  # noqa: E402
from python.scenario_runtime import normalize_world_setup_terrain_assignments  # noqa: E402


class _FacadeOnlyRuntime:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def apply_world_setup(self, request):
        self.calls.append("apply_world_setup")
        result = ef_py.BatchWorldSetupResult()
        result.entity_ids = [701, 702]
        return result


class _CompatOnlyRuntime:
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


class WorldSetupCompatTests(unittest.TestCase):
    def test_build_batch_world_setup_request_normalizes_seed_and_time_step_payloads(self) -> None:
        request = build_batch_world_setup_request(
            seeds=[-1, 5],
            terrain_assignments=[],
            wind_assignments=[],
            zones=[],
            spawn_requests=[],
            time_steps=[0, 0.05],
        )

        self.assertIsNotNone(request)
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

    def test_apply_world_setup_payload_prefers_facade_result_shape(self) -> None:
        runtime = _FacadeOnlyRuntime()

        entity_ids = apply_world_setup_payload_compat(
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

    def test_apply_world_setup_payload_falls_back_to_batch_runtime_when_facade_api_missing(self) -> None:
        runtime = _CompatOnlyRuntime()

        entity_ids = apply_world_setup_payload_compat(
            runtime,
            seeds=[17, 19],
            terrain_assignments=[],
            wind_assignments=[],
            zones=[],
            spawn_requests=[],
            time_steps=[0.1, 0.2],
        )

        self.assertEqual(runtime.calls, ["apply_world_setup_batch"])
        self.assertEqual(entity_ids, [801, 802, 803])
        self.assertIsNotNone(runtime.last_batch_args)
        self.assertEqual(runtime.last_batch_args[0], [17, 19])
        self.assertEqual(runtime.last_batch_args[5], [0.1, 0.2])

    def test_extract_batch_world_setup_entity_ids_accepts_result_or_plain_sequence(self) -> None:
        result = ef_py.BatchWorldSetupResult()
        result.entity_ids = [901, 902]

        self.assertEqual(extract_batch_world_setup_entity_ids(result), [901, 902])
        self.assertEqual(extract_batch_world_setup_entity_ids([903, 904]), [903, 904])


if __name__ == "__main__":
    unittest.main()
