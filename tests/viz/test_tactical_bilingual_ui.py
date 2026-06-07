from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INDEX_HTML = REPO_ROOT / "examples" / "viz" / "web_viz" / "templates" / "index.html"


def _index_text() -> str:
    return INDEX_HTML.read_text(encoding="utf-8")


def test_tactical_ui_exposes_english_chinese_language_switch() -> None:
    text = _index_text()

    assert 'id="btn-language"' in text
    assert "let uiLanguage = 'en';" in text
    assert "const I18N_TEXT = Object.freeze" in text
    assert "'ui.tacticalView': 'TACTICAL VIEW'" in text
    assert "'ui.tacticalView': '战术视图'" in text
    assert "'ui.languageButton': '中文'" in text
    assert "'ui.languageButton': 'EN'" in text
    assert "window.toggleUiLanguage" in text
    assert "document.documentElement.lang = uiLanguage === 'zh' ? 'zh-CN' : 'en';" in text
    assert 'data-i18n="ui.tacticalView"' in text
    assert 'data-i18n-aria="ui.tacticalLayers"' in text


def test_tactical_ui_localizes_dynamic_controls_and_map_callouts() -> None:
    text = _index_text()

    assert "function updateLanguageUi" in text
    assert "function updateSessionLabelText" in text
    assert "function localizePresentationMode" in text
    assert "function localizeCameraMode" in text
    assert "function formatTacticalScaleText" in text
    assert "function localizeEnvironmentToken" in text
    assert "function localizeMissionLabel" in text
    assert "const ENVIRONMENT_LABEL_ZH = Object.freeze" in text
    assert "updateSessionLabelText();" in text
    assert "localizePresentationMode(presentationMode)" in text
    assert "localizeCameraMode(viewMode)" in text
    assert "100 px = ${kmPer100px.toFixed(1)}公里" in text
    assert "const localized = localizeEnvironmentToken(raw);" in text
    assert "localizeMissionLabel(status.c2_task_label || status.c2_task || '--')" in text
    assert "i18n('ui.waypointShort')" in text


def test_tactical_bilingual_ui_is_display_only() -> None:
    text = _index_text()

    assert "socket.emit('viz_load_profile'" in text
    assert "socket.emit('viz_load_session'" in text
    assert "scenario.environment =" not in text
    assert "profile.ui_defaults =" not in text
    assert "currentScenario = loaded ? String(session.scenario || '') : '';" in text
    assert "option.innerText = scenario;" in text
