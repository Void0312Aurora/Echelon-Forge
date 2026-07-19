from __future__ import annotations

from frontend_sources import frontend_text, js_text


def test_unified_scene_layers_are_registered_with_workspace_defaults() -> None:
  symbology = js_text("symbology")
  i18n = js_text("i18n")

  for layer_key, button_id in (
    ("terrain", "btn-layer-terrain"),
    ("water", "btn-layer-water"),
    ("roads", "btn-layer-roads"),
    ("buildings", "btn-layer-buildings"),
  ):
    assert f"{layer_key}: {{" in symbology
    assert f"buttonId: '{button_id}'" in symbology
    assert f"'layer.{layer_key}.label'" in i18n
    assert f"'layer.{layer_key}.short'" in i18n

  # The environment group hosts the unified scene layers.
  assert "layerKeys: ['terrain', 'water', 'roads', 'buildings', 'environment']" in symbology
  # Terrain draws beneath the reference grid; vectors draw above it.
  assert "{ id: 'terrain', layer: 'terrain', order: tacticalLayerCatalog.terrain.drawOrder }" in symbology
  assert "{ id: 'water', layer: 'water', order: tacticalLayerCatalog.water.drawOrder }" in symbology
  assert "{ id: 'roads', layer: 'roads', order: tacticalLayerCatalog.roads.drawOrder }" in symbology
  assert "{ id: 'buildings', layer: 'buildings', order: tacticalLayerCatalog.buildings.drawOrder }" in symbology


def test_unified_scene_geometry_frontend_is_display_only() -> None:
  scene_geometry = js_text("scene-geometry")
  tactical_map = js_text("tactical-map")
  scene3d = js_text("scene3d")
  session = js_text("session")

  assert "fetch('/api/viz/scene_geometry')" in scene_geometry
  assert "function drawSceneTerrain" in scene_geometry
  assert "function drawSceneVectors" in scene_geometry
  assert "held objects arrive as counts and are never rendered" in scene_geometry

  assert "drawSceneTerrain(tacticalCtx, toCanvas);" in tactical_map
  assert "drawSceneVectors(tacticalCtx, toCanvas, scale);" in tactical_map
  assert "sceneGeometryBounds()" in tactical_map

  assert "function buildSceneGeometry3D" in scene3d
  assert "function clearSceneGeometry3D" in scene3d
  assert "buildTerrainMesh" in scene3d

  assert "ensureSceneGeometry(!!appStatus.scene_geometry?.available)" in session

  # Display-only: the frontend never writes environment state back to the
  # session; loading still flows exclusively through profile/scenario events.
  assert "scenario.environment =" not in frontend_text()
  assert "socket.emit('viz_load_profile'" in session
