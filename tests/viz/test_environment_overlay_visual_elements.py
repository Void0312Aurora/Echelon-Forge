from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INDEX_HTML = REPO_ROOT / "examples" / "viz" / "web_viz" / "templates" / "index.html"


def _index_text() -> str:
  return INDEX_HTML.read_text(encoding="utf-8")


def test_tactical_environment_overlays_have_small_object_visual_affordances() -> None:
  text = _index_text()

  assert "function drawEnvironmentOverlayAnchor" in text
  assert "function drawEnvironmentOverlayCallout" in text
  assert "function environmentOverlayTypeCode" in text
  assert "function environmentOverlayDetailText" in text
  assert "SURF-IDX" in text
  assert "STRUCT" in text
  assert "height_m" in text
  assert "drawEnvironmentOverlayAnchor(center, style, bounds, scale);" in text
  assert "drawEnvironmentOverlayCallout(entry, center, style, scale, bounds, labelLod, placedLabelBoxes);" in text


def test_tactical_environment_overlay_labels_use_zoom_lod() -> None:
  text = _index_text()

  assert "function environmentOverlayLabelPriority" in text
  assert "function environmentOverlayLabelLod" in text
  assert "const zoom = Math.max(0.35, finiteNumber(tacticalInteraction.zoom, 1.0) || 1.0);" in text
  assert "if (labelScore < 82.0) return { level: 'hidden', alpha: 0.0 };" in text
  assert "return { level: 'detail', alpha };" in text
  assert "return { level: 'summary', alpha };" in text
  assert "if (!lod || lod.level === 'hidden') return;" in text
  assert "const lines = lod.level === 'detail'" in text
  assert "function environmentLabelBoxesOverlap" in text
  assert "const placedLabelBoxes = [];" in text
  assert "placedLabelBoxes.some((other) => environmentLabelBoxesOverlap(labelBox, other))" in text
