"""Sun illumination contract: scenario config -> engine truth -> consumers.

Phase A of the unified environment substrate: the sun direction that drives
the sensor glare penalty is a scenario-configurable operational parameter
(``environment.illumination``) instead of a hard-coded constant. These tests
pin the kernel setter/getter, the layout parse path, and the batch DTO.
"""

from __future__ import annotations

import math
import unittest

import numpy as np

from python.testing.runtime import ensure_repo_imports

ensure_repo_imports()

import ef_py  # noqa: E402

from python.scenario.runtime.kernel_apply import (  # noqa: E402
    apply_world_layout_to_kernel,
    prepare_scenario_world_layout,
)


def _expected_sun_vector(azimuth_deg: float, elevation_deg: float) -> tuple[float, float, float]:
    az = math.radians(azimuth_deg)
    el = math.radians(elevation_deg)
    horizontal = math.cos(el)
    return (math.sin(az) * horizontal, math.cos(az) * horizontal, math.sin(el))


def _ground_scenario(illumination: dict | None) -> dict:
    environment: dict = {
        "time_step": 1.0,
        "max_steps": 10,
        "terrain_type": "flat",
        "wind": {"speed_mps": 0.0, "dir_from_deg": 0.0, "shear_mps_per_km": 0.0},
        "zones": [],
    }
    if illumination is not None:
        environment["illumination"] = illumination
    return {
        "scenario_name": "sun_illumination_contract",
        "environment": environment,
        "entities": [],
    }


class KernelSunDirectionTests(unittest.TestCase):
    def test_default_sun_matches_historical_fixed_vector(self) -> None:
        kernel = ef_py.SimulationKernel()
        kernel.reset(7)
        x, y, z = kernel.get_sun_direction()
        self.assertAlmostEqual(x, 0.0, places=6)
        self.assertAlmostEqual(y, 0.7071, places=3)
        self.assertAlmostEqual(z, 0.7071, places=3)

    def test_setter_drives_getter_with_nav_convention(self) -> None:
        kernel = ef_py.SimulationKernel()
        kernel.reset(7)
        kernel.set_sun_direction(250.0, 15.0)
        expected = _expected_sun_vector(250.0, 15.0)
        actual = kernel.get_sun_direction()
        for got, want in zip(actual, expected):
            self.assertAlmostEqual(got, want, places=6)
        # Unit-length invariant.
        self.assertAlmostEqual(sum(v * v for v in actual), 1.0, places=6)

    def test_setter_normalizes_azimuth_and_clamps_elevation(self) -> None:
        kernel = ef_py.SimulationKernel()
        kernel.reset(7)
        kernel.set_sun_direction(-110.0, 400.0)
        # -110 az == 250 az; 400 el clamps to 90 (zenith).
        x, y, z = kernel.get_sun_direction()
        self.assertAlmostEqual(z, 1.0, places=6)
        self.assertAlmostEqual(x, 0.0, places=6)
        self.assertAlmostEqual(y, 0.0, places=6)

    def test_sun_survives_reset_like_wind(self) -> None:
        # Environment configuration is per-layout: kernel.reset() keeps the
        # configured sun (same semantics as set_wind) and the scenario apply
        # path re-asserts it on every layout application.
        kernel = ef_py.SimulationKernel()
        kernel.reset(7)
        kernel.set_sun_direction(250.0, 15.0)
        kernel.reset(8)
        expected = _expected_sun_vector(250.0, 15.0)
        for got, want in zip(kernel.get_sun_direction(), expected):
            self.assertAlmostEqual(got, want, places=6)


class ScenarioLayoutIlluminationTests(unittest.TestCase):
    def _layout(self, illumination: dict | None):
        return prepare_scenario_world_layout(
            _ground_scenario(illumination),
            seed=11,
            rng=np.random.RandomState(11),
        )

    def test_layout_defaults_preserve_historical_sun(self) -> None:
        layout = self._layout(None)
        self.assertEqual(layout.sun_azimuth_deg, 0.0)
        self.assertEqual(layout.sun_elevation_deg, 45.0)

    def test_layout_parses_environment_illumination(self) -> None:
        layout = self._layout({"sun_azimuth_deg": 250.0, "sun_elevation_deg": 15.0})
        self.assertEqual(layout.sun_azimuth_deg, 250.0)
        self.assertEqual(layout.sun_elevation_deg, 15.0)

    def test_apply_world_layout_sets_kernel_sun(self) -> None:
        kernel = ef_py.SimulationKernel()
        kernel.reset(11)
        layout = self._layout({"sun_azimuth_deg": 250.0, "sun_elevation_deg": 15.0})
        apply_world_layout_to_kernel(kernel, layout)
        expected = _expected_sun_vector(250.0, 15.0)
        for got, want in zip(kernel.get_sun_direction(), expected):
            self.assertAlmostEqual(got, want, places=6)


class BatchLayoutRequestIlluminationTests(unittest.TestCase):
    def test_runtime_world_layout_request_carries_sun_fields(self) -> None:
        request = ef_py.RuntimeWorldLayoutRequest()
        # Defaults preserve the historical fixed sun.
        self.assertEqual(request.sun_azimuth_deg, 0.0)
        self.assertEqual(request.sun_elevation_deg, 45.0)
        request.sun_azimuth_deg = 250.0
        request.sun_elevation_deg = 15.0
        self.assertEqual(request.sun_azimuth_deg, 250.0)
        self.assertEqual(request.sun_elevation_deg, 15.0)

    def test_build_runtime_world_layout_request_forwards_sun(self) -> None:
        from python.scenario.runtime.world_setup import build_runtime_world_layout_request

        request = build_runtime_world_layout_request(
            world_index=0,
            seed=3,
            terrain_type="flat",
            wind_speed_mps=0.0,
            wind_dir_from_deg=0.0,
            wind_shear_mps_per_km=0.0,
            maritime_configured=False,
            sea_state=0.0,
            wave_heading_deg=0.0,
            wave_period_s=8.0,
            zones=[],
            spawn_requests=[],
            time_steps=[],
            sun_azimuth_deg=250.0,
            sun_elevation_deg=15.0,
        )
        self.assertEqual(request.sun_azimuth_deg, 250.0)
        self.assertEqual(request.sun_elevation_deg, 15.0)


if __name__ == "__main__":
    unittest.main()
