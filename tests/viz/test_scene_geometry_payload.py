from __future__ import annotations

from pathlib import Path

import pytest

from examples.viz.runtime.scene_geometry import (
  MAX_TERRAIN_GRID_DIM,
  SceneGeometryError,
  VIZ_SCENE_GEOMETRY_CONTRACT_VERSION,
  load_scene_geometry_payload,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
CHICAGO_BUNDLE = (
  REPO_ROOT
  / "tests"
  / "scenario"
  / "fixtures"
  / "environment_substrate"
  / "arnis_bundle_v1"
  / "chicago_river_phase1"
  / "expected"
)


@pytest.fixture(scope="module")
def payload() -> dict:
  return load_scene_geometry_payload(str(CHICAGO_BUNDLE))


def test_scene_geometry_payload_contract_and_evidence(payload: dict) -> None:
  assert payload["contract_version"] == VIZ_SCENE_GEOMETRY_CONTRACT_VERSION
  assert payload["coordinate_frame"] == "local_enu_m"
  assert payload["bundle"]["static_scene_contract"] == "cmo.static_scene_geometry.v1"

  evidence = payload["evidence"]
  assert evidence["display_only"] is True
  assert evidence["no_runtime_setup_application"] is True
  assert evidence["no_runtime_consumer_release"] is True
  assert evidence["no_movement_release"] is True
  assert evidence["no_los_cover_release"] is True
  assert evidence["no_held_capability_release"] is True


def test_scene_geometry_renders_only_resolved_objects(payload: dict) -> None:
  summary = payload["summary"]["by_feature_class"]
  assert len(payload["buildings"]) == summary["building"]["resolved"]
  assert len(payload["roads"]) == summary["road"]["resolved"]
  assert len(payload["water"]) == summary["hydrology"]["resolved"]

  held = payload["held"]
  assert held["rendered"] is False
  assert held["total"] == payload["summary"]["held"]
  assert held["total"] == sum(held["by_reason"].values())
  assert held["total"] > 0


def test_scene_geometry_terrain_is_downsampled_metric_grid(payload: dict) -> None:
  terrain = payload["terrain"]
  assert terrain["rows"] <= MAX_TERRAIN_GRID_DIM
  assert terrain["cols"] <= MAX_TERRAIN_GRID_DIM
  assert len(terrain["heights"]) == terrain["rows"]
  assert len(terrain["heights"][0]) == terrain["cols"]
  assert terrain["min_m"] <= terrain["max_m"]
  assert terrain["downsample_step"] >= 1
  assert terrain["landcover"]["sampling"] == "nearest_category_only"
  assert len(terrain["landcover"]["values"]) == terrain["rows"]

  extent = payload["region_extent"]
  assert extent["min_x"] < extent["max_x"]
  assert extent["min_y"] < extent["max_y"]


def test_scene_geometry_road_entries_keep_metric_attributes(payload: dict) -> None:
  road = payload["roads"][0]
  assert road["width_m"] > 0
  assert isinstance(road["highway_type"], str)
  assert road["kind"] in {"terrain_draped", "bridge_deck"}
  assert road["parts"], "road entries must carry centerline parts"
  first_point = road["parts"][0][0]
  assert len(first_point) == 3, "centerline points are draped xyz"
  assert road["corridor"], "road entries carry width-bearing corridor polygons"
  assert len(road["corridor"][0][0]) == 3

  building = payload["buildings"][0]
  assert building["top_m"] > building["base_m"]
  assert building["rings"][0]["role"] == "outer"
  assert len(building["rings"][0]["points"][0]) == 2


def test_scene_geometry_resolves_bridge_decks_from_abutment_anchors(payload: dict) -> None:
  bridges = [road for road in payload["roads"] if road["kind"] == "bridge_deck"]
  assert bridges, "chicago fixture must resolve bridge decks"
  for bridge in bridges:
    assert bridge["corridor"], "bridge decks carry corridor polygons"
    deck_z = [point[2] for part in bridge["parts"] for point in part]
    assert all(isinstance(z, float) for z in deck_z)
  # Subsurface roads stay held and are never rendered.
  assert payload["held"]["by_reason"].get("subsurface_profile_unresolved", 0) > 0
  assert "bridge_elevation_profile_unresolved" not in payload["held"]["by_reason"]


def test_scene_geometry_linear_water_keeps_width_and_all_segments(payload: dict) -> None:
  # The Chicago fixture carries two LineString river segments (3-point and
  # 2-point). Both must reach the payload with their authored width so the
  # renderers can stroke/ribbon them instead of fabricating polygons.
  line_entries = [
    entry for entry in payload["water"]
    if any(path["role"] == "line" for path in entry["paths"])
  ]
  assert len(line_entries) == 2, "both fixture river segments must survive"
  for entry in line_entries:
    assert entry["width_m"] > 0, "linear watercourses carry authored width"
    for path in entry["paths"]:
      assert path["role"] == "line"
      assert len(path["points"]) >= 2
  point_counts = sorted(
    len(entry["paths"][0]["points"]) for entry in line_entries
  )
  assert point_counts[0] == 2, "two-point continuation segment must not be dropped"

  polygon_entries = [
    entry for entry in payload["water"]
    if all(path["role"] != "line" for path in entry["paths"])
  ]
  for entry in polygon_entries:
    assert "width_m" not in entry, "polygon surfaces carry no width"


def test_scene_geometry_rejects_missing_bundle(tmp_path: Path) -> None:
  with pytest.raises(SceneGeometryError):
    load_scene_geometry_payload(str(tmp_path / "missing"))
  empty = tmp_path / "empty"
  empty.mkdir()
  with pytest.raises(SceneGeometryError):
    load_scene_geometry_payload(str(empty))
