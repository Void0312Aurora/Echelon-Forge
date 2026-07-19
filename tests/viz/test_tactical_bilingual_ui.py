from __future__ import annotations

from frontend_sources import frontend_text, index_text, js_text


def test_tactical_ui_exposes_english_chinese_language_switch() -> None:
  html = index_text()
  store = js_text("store")
  i18n = js_text("i18n")
  ui_shell = js_text("ui-shell")

  assert 'id="btn-language"' in html
  assert "uiLanguage: 'en'," in store
  assert "const I18N_TEXT = Object.freeze" in i18n
  assert "'ui.tacticalView': 'TACTICAL VIEW'" in i18n
  assert "'ui.tacticalView': '战术视图'" in i18n
  assert "'ui.languageButton': '中文'" in i18n
  assert "'ui.languageButton': 'EN'" in i18n
  assert "window.toggleUiLanguage" in ui_shell
  assert "document.documentElement.lang = vizState.uiLanguage === 'zh' ? 'zh-CN' : 'en';" in i18n
  assert 'data-i18n="ui.tacticalView"' in html
  assert 'data-i18n-aria="ui.tacticalLayers"' in html


def test_tactical_ui_localizes_dynamic_controls_and_map_callouts() -> None:
  i18n = js_text("i18n")
  ui_shell = js_text("ui-shell")
  environment_overlays = js_text("environment-overlays")

  assert "function updateLanguageUi" in ui_shell
  assert "function updateSessionLabelText" in ui_shell
  assert "function localizePresentationMode" in i18n
  assert "function localizeCameraMode" in i18n
  assert "function formatTacticalScaleText" in i18n
  assert "function localizeEnvironmentToken" in i18n
  assert "function localizeMissionLabel" in i18n
  assert "const ENVIRONMENT_LABEL_ZH = Object.freeze" in i18n
  assert "updateSessionLabelText();" in ui_shell
  assert "localizePresentationMode(vizState.presentationMode)" in ui_shell
  assert "localizeCameraMode(vizState.viewMode)" in ui_shell
  assert "100 px = ${kmPer100px.toFixed(1)}公里" in i18n
  assert "const localized = localizeEnvironmentToken(raw);" in environment_overlays
  assert "localizeMissionLabel(status.c2_task_label || status.c2_task || '--')" in ui_shell
  assert "i18n('ui.waypointShort')" in ui_shell


def test_tactical_bilingual_ui_is_display_only() -> None:
  session = js_text("session")
  ui_shell = js_text("ui-shell")

  assert "socket.emit('viz_load_profile'" in session
  assert "socket.emit('viz_load_session'" in session
  assert "scenario.environment =" not in frontend_text()
  assert "profile.ui_defaults =" not in frontend_text()
  assert "vizState.currentScenario = loaded ? String(session.scenario || '') : '';" in session
  assert "option.innerText = scenario;" in ui_shell
