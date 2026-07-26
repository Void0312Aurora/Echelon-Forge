from __future__ import annotations

from frontend_sources import frontend_text, index_text, js_text


def test_tactical_map_workspace_surfaces_are_named_and_selectable() -> None:
  symbology = js_text("symbology")
  html = index_text()

  assert "const tacticalWorkspaceDefinitions" in symbology
  for workspace_id, label in (
    ("cop", "COP"),
    ("environment", "ENVIRONMENT"),
    ("tracks", "TRACKS"),
    ("inspect3d", "3D INSPECT"),
  ):
    assert f"{workspace_id}: {{" in symbology
    assert f"label: '{label}'" in symbology
    assert f"id=\"workspace-tab-{workspace_id}\"" in html
    assert f"setTacticalWorkspace('{workspace_id}')" in html


def test_tactical_map_workspace_surfaces_have_default_layer_sets() -> None:
  symbology = js_text("symbology")

  for layer_key in (
    "environment",
    "route",
    "trails",
    "weapons",
    "tracks",
    "sensorRings",
    "datalinks",
  ):
    assert f"{layer_key}:" in symbology

  assert "role: 'COMMON PICTURE'" in symbology
  assert "role: 'ENV / AREAS'" in symbology
  assert "role: 'SENSORS / LINKS'" in symbology
  assert "role: 'MODEL INSPECT'" in symbology
  assert "viewMode: 'MAP'" in symbology
  assert "viewMode: '3D'" in symbology


def test_tactical_map_workspace_is_ui_only_and_preserves_session_paths() -> None:
  ui_shell = js_text("ui-shell")
  session = js_text("session")
  i18n = js_text("i18n")

  assert "window.setTacticalWorkspace" in ui_shell
  assert "socket.emit('viz_load_profile'" in session
  assert "socket.emit('viz_load_session'" in session
  assert "currentProfileUiDefaults" in session
  assert "Scenario only (no profile active)" in i18n
  assert "workspace-layer-summary" in index_text()
  assert "scenario.environment" not in frontend_text()
