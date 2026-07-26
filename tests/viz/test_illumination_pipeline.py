"""Illumination truth pipeline: scenario -> viz payload -> frontend consumers.

The sun that drives the engine's sensor glare penalty must be the same sun
the operator sees: the map_setup payload carries the scenario illumination,
the 2D hillshade derives its light vector from it, and the 3D scene points
its shadow-casting directional light along it.
"""

from __future__ import annotations

import math

from examples.viz.runtime.illumination import (
    resolve_scenario_illumination,
    sun_vector_from_angles,
)

from frontend_sources import index_text, js_text


def _scenario(illumination=None):
    environment = {"zones": []}
    if illumination is not None:
        environment["illumination"] = illumination
    return {"environment": environment}


class _SimWithSun:
    def __init__(self, azimuth_deg: float, elevation_deg: float) -> None:
        self._vec = sun_vector_from_angles(azimuth_deg, elevation_deg)

    def get_sun_direction(self):
        return self._vec


def test_payload_defaults_match_engine_defaults():
    payload = resolve_scenario_illumination(_scenario(None))
    assert payload["sun_azimuth_deg"] == 0.0
    assert payload["sun_elevation_deg"] == 45.0
    assert payload["configured"] is False
    assert payload["engine_confirmed"] is False


def test_payload_normalizes_configured_angles():
    payload = resolve_scenario_illumination(
        _scenario({"sun_azimuth_deg": -110.0, "sun_elevation_deg": 400.0})
    )
    assert payload["sun_azimuth_deg"] == 250.0
    assert payload["sun_elevation_deg"] == 90.0
    assert payload["configured"] is True


def test_payload_survives_malformed_config():
    payload = resolve_scenario_illumination(
        _scenario({"sun_azimuth_deg": "not-a-number"})
    )
    assert payload["sun_azimuth_deg"] == 0.0
    assert payload["sun_elevation_deg"] == 45.0


def test_engine_confirmation_cross_checks_kernel_vector():
    confirmed = resolve_scenario_illumination(
        _scenario({"sun_azimuth_deg": 250.0, "sun_elevation_deg": 15.0}),
        sim=_SimWithSun(250.0, 15.0),
    )
    assert confirmed["engine_confirmed"] is True

    mismatched = resolve_scenario_illumination(
        _scenario({"sun_azimuth_deg": 250.0, "sun_elevation_deg": 15.0}),
        sim=_SimWithSun(70.0, 60.0),
    )
    assert mismatched["engine_confirmed"] is False


def test_sun_vector_matches_engine_nav_convention():
    east, north, up = sun_vector_from_angles(0.0, 45.0)
    assert abs(east - 0.0) < 1e-9
    assert abs(north - math.cos(math.radians(45.0))) < 1e-9
    assert abs(up - math.sin(math.radians(45.0))) < 1e-9
    # East-pointing sun at the horizon.
    east, north, up = sun_vector_from_angles(90.0, 0.0)
    assert abs(east - 1.0) < 1e-9
    assert abs(north) < 1e-9
    assert abs(up) < 1e-9


# --- Backend payload wiring ---


def test_viz_session_sends_illumination_in_map_setup():
    from pathlib import Path

    session_src = (
        Path(__file__).resolve().parents[2]
        / "examples" / "viz" / "runtime" / "viz_session.py"
    ).read_text(encoding="utf-8")
    assert "resolve_scenario_illumination" in session_src
    assert '"illumination": illumination' in session_src


# --- Frontend contract: one truth drives every lighting consumer ---


def test_store_holds_illumination_truth():
    store = js_text("store")
    assert "illumination" in store
    assert "sunAzimuthDeg" in store
    assert "sunElevationDeg" in store
    assert "engineConfirmed" in store


def test_session_applies_illumination_from_map_setup():
    session = js_text("session")
    assert "applyIllumination" in session
    assert "data?.illumination" in session


def test_hillshade_derives_from_illumination_not_fixed_light():
    scene_geometry = js_text("scene-geometry")
    assert "sunVectorFromAngles" in scene_geometry
    assert "refreshIlluminationShading" in scene_geometry
    assert "shadeLight" in scene_geometry
    # The old hard-coded northwest light must be gone.
    assert "lx = -0.45" not in scene_geometry


def test_scene3d_sun_light_and_shadows_follow_illumination():
    scene3d = js_text("scene3d")
    assert "updateSceneIllumination" in scene3d
    assert "vizState.illumination" in scene3d
    assert "shadowMap.enabled = true" in scene3d
    assert "castShadow" in scene3d
    assert "receiveShadow" in scene3d
    assert "fitShadowCameraToRadius" in scene3d


def test_illumination_module_fans_out_to_both_views():
    module = js_text("illumination")
    assert "updateSceneIllumination" in module
    assert "refreshIlluminationShading" in module
    assert "sun_azimuth_deg" in module


def test_index_loads_modular_frontend():
    # Illumination module is reached through the ES-module graph.
    assert "main.js" in index_text()
