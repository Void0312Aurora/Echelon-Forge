from __future__ import annotations

from frontend_sources import frontend_text, index_text, js_text


def test_tactical_layer_catalog_groups_controls_and_button_ids() -> None:
  symbology = js_text("symbology")
  ui_shell = js_text("ui-shell")

  assert "const tacticalLayerCatalog = Object.freeze({" in symbology
  assert "const tacticalLayerGroups = Object.freeze([" in symbology
  assert 'id="tactical-layer-controls"' in index_text()
  assert "button.id = spec.buttonId;" in ui_shell
  assert "button.onclick = () => window.toggleTacticalLayer(key);" in ui_shell

  for group_id, label in (
    ("environment", "ENVIRONMENT"),
    ("maneuver", "MANEUVER"),
    ("sensors", "SENSORS"),
    ("effects", "EFFECTS"),
  ):
    assert f"id: '{group_id}', label: '{label}'" in symbology

  for layer_key, button_id in (
    ("environment", "btn-layer-environment"),
    ("route", "btn-layer-route"),
    ("trails", "btn-layer-trails"),
    ("datalinks", "btn-layer-datalinks"),
    ("sensorRings", "btn-layer-sensor-rings"),
    ("tracks", "btn-layer-tracks"),
    ("weapons", "btn-layer-weapons"),
  ):
    assert f"{layer_key}: {{" in symbology
    assert f"buttonId: '{button_id}'" in symbology


def test_tactical_draw_phases_keep_environment_maneuver_sensor_effect_order() -> None:
  symbology = js_text("symbology")
  layers = js_text("layers")
  tactical_map = js_text("tactical-map")

  phase_tokens = [
    "{ id: 'grid', layer: null, order: 0 }",
    "{ id: 'environment', layer: 'environment', order: tacticalLayerCatalog.environment.drawOrder }",
    "{ id: 'route', layer: 'route', order: tacticalLayerCatalog.route.drawOrder }",
    "{ id: 'trails', layer: 'trails', order: tacticalLayerCatalog.trails.drawOrder }",
    "{ id: 'datalinks', layer: 'datalinks', order: tacticalLayerCatalog.datalinks.drawOrder }",
    "{ id: 'sensorRings', layer: 'sensorRings', order: tacticalLayerCatalog.sensorRings.drawOrder }",
    "{ id: 'tracks', layer: 'tracks', order: tacticalLayerCatalog.tracks.drawOrder }",
    "{ id: 'weapons', layer: 'weapons', order: tacticalLayerCatalog.weapons.drawOrder }",
    "{ id: 'units', layer: null, order: 80 }",
    "{ id: 'missileUnits', layer: 'weapons', order: 90 }",
    "{ id: 'labels', layer: null, order: 100 }",
  ]
  positions = [symbology.index(token) for token in phase_tokens]

  assert positions == sorted(positions)
  assert "const tacticalDrawPhaseById = Object.freeze(Object.fromEntries(" in symbology
  assert "function isTacticalDrawPhaseEnabled(phaseId)" in layers
  assert "isTacticalDrawPhaseEnabled('environment')" in tactical_map
  assert "isTacticalDrawPhaseEnabled('route')" in tactical_map
  assert "isTacticalDrawPhaseEnabled('sensorRings')" in tactical_map
  assert "isTacticalDrawPhaseEnabled('missileUnits')" in tactical_map


def test_tactical_symbology_registry_is_first_pass_not_payload_schema() -> None:
  symbology = js_text("symbology")
  environment_overlays = js_text("environment-overlays")
  tactical_map = js_text("tactical-map")
  session = js_text("session")

  assert "const tacticalSymbology = Object.freeze({" in symbology
  assert "function tacticalAffiliationStyle(side)" in symbology
  assert "tacticalSymbology.environment.occlusionCandidate.vegetation" in environment_overlays
  assert "tacticalSymbology.environment.surfaces[surface]" in environment_overlays
  assert "tacticalSymbology.route.path" in tactical_map
  assert "tacticalSymbology.track.fusedStroke" in tactical_map
  assert "tacticalSymbology.datalink.stroke" in tactical_map

  assert "socket.emit('viz_load_profile'" in session
  assert "socket.emit('viz_load_session'" in session
  assert "scenario.environment =" not in frontend_text()
  assert "profile.ui_defaults =" not in frontend_text()
