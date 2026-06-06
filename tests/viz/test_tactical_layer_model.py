from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INDEX_HTML = REPO_ROOT / "examples" / "viz" / "web_viz" / "templates" / "index.html"


def _index_text() -> str:
    return INDEX_HTML.read_text(encoding="utf-8")


def test_tactical_layer_catalog_groups_controls_and_button_ids() -> None:
    text = _index_text()

    assert "const tacticalLayerCatalog = Object.freeze({" in text
    assert "const tacticalLayerGroups = Object.freeze([" in text
    assert 'id="tactical-layer-controls"' in text
    assert "button.id = spec.buttonId;" in text
    assert "button.onclick = () => window.toggleTacticalLayer(key);" in text

    for group_id, label in (
        ("environment", "ENVIRONMENT"),
        ("maneuver", "MANEUVER"),
        ("sensors", "SENSORS"),
        ("effects", "EFFECTS"),
    ):
        assert f"id: '{group_id}', label: '{label}'" in text

    for layer_key, button_id in (
        ("environment", "btn-layer-environment"),
        ("route", "btn-layer-route"),
        ("trails", "btn-layer-trails"),
        ("datalinks", "btn-layer-datalinks"),
        ("sensorRings", "btn-layer-sensor-rings"),
        ("tracks", "btn-layer-tracks"),
        ("weapons", "btn-layer-weapons"),
    ):
        assert f"{layer_key}: {{" in text
        assert f"buttonId: '{button_id}'" in text


def test_tactical_draw_phases_keep_environment_maneuver_sensor_effect_order() -> None:
    text = _index_text()

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
    positions = [text.index(token) for token in phase_tokens]

    assert positions == sorted(positions)
    assert "const tacticalDrawPhaseById = Object.freeze(Object.fromEntries(" in text
    assert "function isTacticalDrawPhaseEnabled(phaseId)" in text
    assert "isTacticalDrawPhaseEnabled('environment')" in text
    assert "isTacticalDrawPhaseEnabled('route')" in text
    assert "isTacticalDrawPhaseEnabled('sensorRings')" in text
    assert "isTacticalDrawPhaseEnabled('missileUnits')" in text


def test_tactical_symbology_registry_is_first_pass_not_payload_schema() -> None:
    text = _index_text()

    assert "const tacticalSymbology = Object.freeze({" in text
    assert "function tacticalAffiliationStyle(side)" in text
    assert "tacticalSymbology.environment.occlusionCandidate.vegetation" in text
    assert "tacticalSymbology.environment.surfaces[surface]" in text
    assert "tacticalSymbology.route.path" in text
    assert "tacticalSymbology.track.fusedStroke" in text
    assert "tacticalSymbology.datalink.stroke" in text

    assert "socket.emit('viz_load_profile'" in text
    assert "socket.emit('viz_load_session'" in text
    assert "scenario.environment =" not in text
    assert "profile.ui_defaults =" not in text
