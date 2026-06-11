from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INDEX_HTML = REPO_ROOT / "examples" / "viz" / "web_viz" / "templates" / "index.html"


def _index_text() -> str:
  return INDEX_HTML.read_text(encoding="utf-8")


def test_tactical_map_workspace_surfaces_are_named_and_selectable() -> None:
  text = _index_text()

  assert "const tacticalWorkspaceDefinitions" in text
  for workspace_id, label in (
    ("cop", "COP"),
    ("environment", "ENVIRONMENT"),
    ("tracks", "TRACKS"),
    ("inspect3d", "3D INSPECT"),
  ):
    assert f"{workspace_id}: {{" in text
    assert f"label: '{label}'" in text
    assert f"id=\"workspace-tab-{workspace_id}\"" in text
    assert f"setTacticalWorkspace('{workspace_id}')" in text


def test_tactical_map_workspace_surfaces_have_default_layer_sets() -> None:
  text = _index_text()

  for layer_key in (
    "environment",
    "route",
    "trails",
    "weapons",
    "tracks",
    "sensorRings",
    "datalinks",
  ):
    assert f"{layer_key}:" in text

  assert "role: 'COMMON PICTURE'" in text
  assert "role: 'ENV / AREAS'" in text
  assert "role: 'SENSORS / LINKS'" in text
  assert "role: 'MODEL INSPECT'" in text
  assert "viewMode: 'MAP'" in text
  assert "viewMode: '3D'" in text


def test_tactical_map_workspace_is_ui_only_and_preserves_session_paths() -> None:
  text = _index_text()

  assert "window.setTacticalWorkspace" in text
  assert "socket.emit('viz_load_profile'" in text
  assert "socket.emit('viz_load_session'" in text
  assert "currentProfileUiDefaults" in text
  assert "Scenario only (no profile active)" in text
  assert "workspace-layer-summary" in text
  assert "scenario.environment" not in text
