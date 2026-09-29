"""Geodetic anchor contract: scenario config -> engine anchor -> EGI (Geodetic Frame P3-B).

A scenario declares ``environment.geodetic_anchor`` or inherits the documented
default anchor. These tests pin the kernel setter/getter and its validation, the
EGI projection about the anchor, the scenario layout parse path (fail closed on
malformed anchors), the single-world and batch apply paths, and the viz payload.

Expected geodetic values come from closed forms on the IUGG mean sphere
(R = 6371009 m): one degree of arc is R * pi / 180 = 111195.08 m, and a point
due north of the anchor keeps the anchor's longitude.
"""

from __future__ import annotations

import math
import unittest

import numpy as np

from python.runtime_bootstrap import ensure_repo_imports, resolve_repo_path

ensure_repo_imports()

import ef_py  # noqa: E402

from python.scenario.compiler import (  # noqa: E402
    DEFAULT_GEODETIC_ANCHOR,
    resolve_environment_geodetic_anchor,
)
from python.scenario.runtime.kernel_apply import (  # noqa: E402
    apply_world_layout_to_kernel,
    prepare_scenario_world_layout,
)

_MEAN_EARTH_RADIUS_M = 6_371_009.0
_METRES_PER_DEGREE = _MEAN_EARTH_RADIUS_M * math.pi / 180.0


def _scenario(anchor: dict | None, *, entities: list | None = None) -> dict:
    environment: dict = {
        "time_step": 0.1,
        "max_steps": 10,
        "terrain_type": "flat",
        "wind": {"speed_mps": 0.0, "dir_from_deg": 0.0, "shear_mps_per_km": 0.0},
        "zones": [],
    }
    if anchor is not None:
        environment["geodetic_anchor"] = anchor
    return {
        "scenario_name": "geodetic_anchor_contract",
        "environment": environment,
        "entities": entities or [],
    }


def _aircraft_entity(x: float, y: float) -> dict:
    return {
        "name": "blue_lead",
        "side": "Blue",
        "type": "F-16C_Block50",
        "is_agent": True,
        "pos": [x, y, 3000.0],
        "vel": [0.0, 200.0, 0.0],
        "heading": 0.0,
    }


class KernelGeodeticAnchorTests(unittest.TestCase):
    def test_default_anchor_is_the_documented_reference(self) -> None:
        kernel = ef_py.SimulationKernel()
        kernel.reset(7)
        self.assertEqual(kernel.get_geodetic_anchor(), DEFAULT_GEODETIC_ANCHOR)

    def test_setter_drives_getter_and_survives_reset(self) -> None:
        kernel = ef_py.SimulationKernel()
        kernel.reset(7)
        kernel.set_geodetic_anchor(18.2, 109.5, 0.0)
        kernel.reset(8)
        self.assertEqual(kernel.get_geodetic_anchor(), (18.2, 109.5, 0.0))

    def test_setter_rejects_polar_and_non_finite_anchors(self) -> None:
        kernel = ef_py.SimulationKernel()
        kernel.reset(7)
        for bad in ((90.0, 0.0), (-90.0, 0.0), (float("nan"), 0.0), (0.0, float("inf"))):
            with self.assertRaises(ValueError):
                kernel.set_geodetic_anchor(bad[0], bad[1])
        self.assertEqual(kernel.get_geodetic_anchor(), DEFAULT_GEODETIC_ANCHOR)


class EgiProjectionTests(unittest.TestCase):
    def _instrument_after_spawn(self, anchor: tuple[float, float] | None, x: float, y: float):
        kernel = ef_py.SimulationKernel()
        kernel.reset(11)
        self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))
        if anchor is not None:
            kernel.set_geodetic_anchor(anchor[0], anchor[1], 0.0)
        kernel.set_time_step(0.01)
        entity = kernel.spawn_unit(
            ef_py.Side.Blue, "F-16C_Block50", x, y, 3000.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        )
        kernel.step()
        return kernel.get_instrument_state(int(entity))

    def test_egi_reads_the_anchor_at_the_origin(self) -> None:
        inst = self._instrument_after_spawn((18.2, 109.5), 0.0, 0.0)
        self.assertAlmostEqual(float(inst.lat), 18.2, places=6)
        self.assertAlmostEqual(float(inst.lon), 109.5, places=6)

    def test_egi_moves_one_degree_per_mean_sphere_arc_due_north(self) -> None:
        inst = self._instrument_after_spawn((18.2, 109.5), 0.0, _METRES_PER_DEGREE)
        # 0.01 s of zero velocity moves nothing; the fix is exact to the step.
        self.assertAlmostEqual(float(inst.lat), 19.2, places=4)
        self.assertAlmostEqual(float(inst.lon), 109.5, places=6)

    def test_default_anchor_replaces_the_equirectangular_approximation(self) -> None:
        # 250 km east of the default anchor: the retired equirectangular rule
        # used 90 km per degree of longitude and gave -112.2722 deg; the
        # azimuthal-equidistant inverse on the sphere gives -112.2632 deg and
        # lat 36.2077 deg.
        inst = self._instrument_after_spawn(None, 250_000.0, 0.0)
        expected_dlon = math.degrees(
            math.atan2(
                math.sin(250_000.0 / _MEAN_EARTH_RADIUS_M),
                math.cos(math.radians(36.24)) * math.cos(250_000.0 / _MEAN_EARTH_RADIUS_M),
            )
        )
        self.assertAlmostEqual(float(inst.lon), -115.05 + expected_dlon, places=4)
        # A straight east line curves toward the equator on the sphere.
        self.assertAlmostEqual(float(inst.lat), 36.2077, places=3)


class ScenarioAnchorParseTests(unittest.TestCase):
    def test_undeclared_anchor_inherits_the_default(self) -> None:
        layout = prepare_scenario_world_layout(_scenario(None), seed=1, rng=np.random.RandomState(1))
        self.assertEqual(layout.geodetic_anchor, DEFAULT_GEODETIC_ANCHOR)
        self.assertEqual(layout.geodetic_anchor_source, "default")

    def test_declared_anchor_is_parsed(self) -> None:
        layout = prepare_scenario_world_layout(
            _scenario({"latitude_deg": 18.2, "longitude_deg": 109.5}),
            seed=1,
            rng=np.random.RandomState(1),
        )
        self.assertEqual(layout.geodetic_anchor, (18.2, 109.5, 0.0))
        self.assertEqual(layout.geodetic_anchor_source, "explicit")

    def test_malformed_anchors_fail_closed(self) -> None:
        bad_anchors = [
            [18.2, 109.5],
            {"latitude_deg": 18.2},
            {"latitude_deg": 95.0, "longitude_deg": 0.0},
            {"latitude_deg": "18.2", "longitude_deg": 109.5},
            {"latitude_deg": True, "longitude_deg": 109.5},
            {"latitude_deg": 18.2, "longitude_deg": float("nan")},
            {"latitude_deg": 18.2, "longitude_deg": 109.5, "datum": "WGS84"},
        ]
        for bad in bad_anchors:
            with self.subTest(anchor=bad), self.assertRaises(ValueError):
                resolve_environment_geodetic_anchor({"geodetic_anchor": bad})


class ScenarioAnchorApplyTests(unittest.TestCase):
    def test_single_world_apply_sets_the_kernel_anchor(self) -> None:
        kernel = ef_py.SimulationKernel()
        kernel.reset(3)
        self.assertTrue(kernel.load_database(resolve_repo_path("examples", "config", "database")))
        layout = prepare_scenario_world_layout(
            _scenario(
                {"latitude_deg": 18.2, "longitude_deg": 109.5},
                entities=[_aircraft_entity(0.0, 0.0)],
            ),
            seed=3,
            rng=np.random.RandomState(3),
        )
        applied = apply_world_layout_to_kernel(kernel, layout)
        self.assertEqual(kernel.get_geodetic_anchor(), (18.2, 109.5, 0.0))
        kernel.step()
        inst = kernel.get_instrument_state(int(applied.agent_id))
        self.assertAlmostEqual(float(inst.lat), 18.2, places=3)

    def test_reapplying_an_undeclared_scenario_restores_the_default(self) -> None:
        kernel = ef_py.SimulationKernel()
        kernel.reset(3)
        kernel.set_geodetic_anchor(18.2, 109.5, 0.0)
        layout = prepare_scenario_world_layout(_scenario(None), seed=3, rng=np.random.RandomState(3))
        apply_world_layout_to_kernel(kernel, layout)
        self.assertEqual(kernel.get_geodetic_anchor(), DEFAULT_GEODETIC_ANCHOR)

    def test_batch_setup_applies_per_world_anchors_and_resets_undeclared_worlds(self) -> None:
        from python.scenario.runtime.batch_apply import apply_world_layouts_to_setup_target

        facade = ef_py.RuntimeFacade(2)
        self.assertTrue(facade.load_database(resolve_repo_path("examples", "config", "database")))
        declared = prepare_scenario_world_layout(
            _scenario(
                {"latitude_deg": 18.2, "longitude_deg": 109.5},
                entities=[_aircraft_entity(0.0, 0.0)],
            ),
            seed=5,
            rng=np.random.RandomState(5),
        )
        undeclared = prepare_scenario_world_layout(
            _scenario(None, entities=[_aircraft_entity(0.0, 0.0)]),
            seed=6,
            rng=np.random.RandomState(6),
        )
        # Run twice in swapped order: a re-setup must not inherit the other
        # world's anchor from the previous application.
        for layouts, expected in (
            ([declared, undeclared], (18.2, 36.24)),
            ([undeclared, declared], (36.24, 18.2)),
        ):
            applied = apply_world_layouts_to_setup_target(facade, layouts)
            facade.step_batch()
            refs = []
            for world_index, world in enumerate(applied):
                ref = ef_py.WorldEntityRef()
                ref.world_index = int(world_index)
                ref.entity_id = int(world.agent_id)
                refs.append(ref)
            latitudes = tuple(float(inst.lat) for inst in facade.get_instrument_states_batch(refs))
            self.assertAlmostEqual(latitudes[0], expected[0], places=3)
            self.assertAlmostEqual(latitudes[1], expected[1], places=3)

    def test_single_world_layout_request_applies_the_anchor(self) -> None:
        from python.rl.runtime.world_batch.adapter import RuntimeFacadeAdapter

        adapter = RuntimeFacadeAdapter(1)
        facade = adapter.facade
        self.assertTrue(facade.load_database(resolve_repo_path("examples", "config", "database")))
        layout = prepare_scenario_world_layout(
            _scenario(
                {"latitude_deg": 18.2, "longitude_deg": 109.5},
                entities=[_aircraft_entity(0.0, 0.0)],
            ),
            seed=7,
            rng=np.random.RandomState(7),
        )
        applied = adapter.apply_world_layout(0, layout)
        facade.step_batch()
        ref = ef_py.WorldEntityRef()
        ref.world_index = 0
        ref.entity_id = int(applied.agent_id)
        inst = facade.get_instrument_states_batch([ref])[0]
        self.assertAlmostEqual(float(inst.lat), 18.2, places=3)
        self.assertAlmostEqual(float(inst.lon), 109.5, places=3)

    def test_runtime_world_layout_request_carries_anchor_fields(self) -> None:
        request = ef_py.RuntimeWorldLayoutRequest()
        self.assertEqual(
            (request.anchor_latitude_deg, request.anchor_longitude_deg, request.anchor_height_m),
            DEFAULT_GEODETIC_ANCHOR,
        )
        assignment = ef_py.WorldGeodeticAnchorAssignment()
        self.assertEqual(
            (assignment.latitude_deg, assignment.longitude_deg, assignment.height_m),
            DEFAULT_GEODETIC_ANCHOR,
        )


class VizGeodeticFramePayloadTests(unittest.TestCase):
    def test_payload_reports_declared_anchor_and_engine_confirmation(self) -> None:
        from examples.viz.runtime.geodetic_frame import resolve_scenario_geodetic_frame

        kernel = ef_py.SimulationKernel()
        kernel.reset(9)
        kernel.set_geodetic_anchor(18.2, 109.5, 0.0)
        payload = resolve_scenario_geodetic_frame(
            _scenario({"latitude_deg": 18.2, "longitude_deg": 109.5}), sim=kernel
        )
        self.assertEqual(payload["anchor_lat_deg"], 18.2)
        self.assertEqual(payload["source"], "explicit")
        self.assertTrue(payload["engine_confirmed"])

        mismatched = resolve_scenario_geodetic_frame(_scenario(None), sim=kernel)
        self.assertEqual(mismatched["source"], "default")
        self.assertFalse(mismatched["engine_confirmed"])


if __name__ == "__main__":
    unittest.main()
