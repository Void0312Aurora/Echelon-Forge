"""Shared readers for the modular viz frontend sources.

The tactical-map frontend was refactored from a single index.html into ES
modules under examples/viz/web_viz/static/js plus a CSS file. Frontend
contract tests read specific module files (preferred) or the concatenated
frontend text for absence checks that must hold everywhere.
"""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WEB_VIZ_DIR = REPO_ROOT / "examples" / "viz" / "web_viz"
INDEX_HTML = WEB_VIZ_DIR / "templates" / "index.html"
VIZ_CSS = WEB_VIZ_DIR / "static" / "css" / "viz.css"
JS_DIR = WEB_VIZ_DIR / "static" / "js"


def index_text() -> str:
  return INDEX_HTML.read_text(encoding="utf-8")


def css_text() -> str:
  return VIZ_CSS.read_text(encoding="utf-8")


def js_text(module_name: str) -> str:
  """Read one ES module, e.g. js_text("symbology")."""
  return (JS_DIR / f"{module_name}.js").read_text(encoding="utf-8")


def frontend_text() -> str:
  """Concatenate template, stylesheet, and every JS module."""
  parts = [index_text(), css_text()]
  for path in sorted(JS_DIR.glob("*.js")):
    parts.append(path.read_text(encoding="utf-8"))
  return "\n".join(parts)
