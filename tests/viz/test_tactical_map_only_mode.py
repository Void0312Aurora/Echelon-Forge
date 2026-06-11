from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INDEX_HTML = REPO_ROOT / "examples" / "viz" / "web_viz" / "templates" / "index.html"


def _index_text() -> str:
  return INDEX_HTML.read_text(encoding="utf-8")


def test_tactical_map_only_mode_has_explicit_entry_and_escape_exit() -> None:
  text = _index_text()

  assert 'id="btn-map-only"' in text
  assert 'id="btn-map-only-exit"' in text
  assert "window.toggleMapOnlyMode" in text
  assert "e.key === 'Escape' && mapOnlyMode" in text
  assert 'html[data-map-only="true"] #viz-menubar' in text


def test_tactical_map_only_mode_is_ui_only_and_preserves_map_workspace() -> None:
  text = _index_text()

  assert "document.documentElement.dataset.mapOnly" in text
  assert "layoutState.mode = 'map-only';" in text
  assert "window.setTacticalWorkspace(lastMapTacticalWorkspace || 'cop', { skipCapture: true });" in text
  assert "socket.emit('viz_load_profile'" in text
  assert "socket.emit('viz_load_session'" in text
  assert "scenario.environment =" not in text
  assert "profile.ui_defaults =" not in text
