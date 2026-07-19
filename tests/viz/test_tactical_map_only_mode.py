from __future__ import annotations

from frontend_sources import css_text, frontend_text, index_text, js_text


def test_tactical_map_only_mode_has_explicit_entry_and_escape_exit() -> None:
  html = index_text()
  ui_shell = js_text("ui-shell")
  main = js_text("main")

  assert 'id="btn-map-only"' in html
  assert 'id="btn-map-only-exit"' in html
  assert "window.toggleMapOnlyMode" in ui_shell
  assert "e.key === 'Escape' && vizState.mapOnlyMode" in main
  assert 'html[data-map-only="true"] #viz-menubar' in css_text()


def test_tactical_map_only_mode_is_ui_only_and_preserves_map_workspace() -> None:
  ui_shell = js_text("ui-shell")
  layout = js_text("layout")
  session = js_text("session")

  assert "document.documentElement.dataset.mapOnly" in ui_shell
  assert "layoutState.mode = 'map-only';" in layout
  assert "window.setTacticalWorkspace(vizState.lastMapTacticalWorkspace || 'cop', { skipCapture: true });" in ui_shell
  assert "socket.emit('viz_load_profile'" in session
  assert "socket.emit('viz_load_session'" in session
  assert "scenario.environment =" not in frontend_text()
  assert "profile.ui_defaults =" not in frontend_text()
