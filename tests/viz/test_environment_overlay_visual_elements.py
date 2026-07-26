from __future__ import annotations

from frontend_sources import js_text


def test_tactical_environment_overlays_have_small_object_visual_affordances() -> None:
  overlays = js_text("environment-overlays")
  i18n = js_text("i18n")

  assert "function drawEnvironmentOverlayAnchor" in overlays
  assert "function drawEnvironmentOverlayCallout" in overlays
  assert "function environmentOverlayTypeCode" in overlays
  assert "function environmentOverlayDetailText" in overlays
  assert "SURF-IDX" in i18n
  assert "STRUCT" in i18n
  assert "height_m" in overlays
  assert "drawEnvironmentOverlayAnchor(ctx, center, style, bounds, scale);" in overlays
  assert "drawEnvironmentOverlayCallout(ctx, entry, center, style, scale, bounds, labelLod, placedLabelBoxes);" in overlays


def test_tactical_environment_overlay_labels_use_zoom_lod() -> None:
  overlays = js_text("environment-overlays")

  assert "function environmentOverlayLabelPriority" in overlays
  assert "function environmentOverlayLabelLod" in overlays
  assert "const zoom = Math.max(0.35, finiteNumber(vizState.tacticalInteraction.zoom, 1.0) || 1.0);" in overlays
  assert "if (labelScore < 82.0) return { level: 'hidden', alpha: 0.0 };" in overlays
  assert "return { level: 'detail', alpha };" in overlays
  assert "return { level: 'summary', alpha };" in overlays
  assert "if (!lod || lod.level === 'hidden') return;" in overlays
  assert "const lines = lod.level === 'detail'" in overlays
  assert "function environmentLabelBoxesOverlap" in overlays
  assert "const placedLabelBoxes = [];" in overlays
  assert "placedLabelBoxes.some((other) => environmentLabelBoxesOverlap(labelBox, other))" in overlays
