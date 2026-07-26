"""Buildless type-checking seed for the viz frontend.

The frontend stays plain ES modules served by Flask (no bundler), but core
contract modules opt into editor/`tsc --noEmit` type checking via JSDoc:

    npx -y -p typescript tsc --noEmit -p examples/viz/web_viz/jsconfig.json

These tests pin the wiring (jsconfig, central typedefs, opted-in modules)
so the typing seed does not silently rot. They do not run tsc: Node is not
a test dependency; the check runs in editors and on demand.
"""

from __future__ import annotations

import json
from pathlib import Path

from frontend_sources import JS_DIR, js_text

WEB_VIZ_DIR = JS_DIR.parent.parent

# Contract/data modules that must stay under type checking. Rendering-heavy
# modules (scene3d, tactical-map, ui-shell, session) migrate incrementally.
TYPE_CHECKED_MODULES = (
    "types",
    "config",
    "utils",
    "store",
    "illumination",
    "symbology",
)


def test_jsconfig_exists_and_is_buildless() -> None:
    jsconfig_path = WEB_VIZ_DIR / "jsconfig.json"
    assert jsconfig_path.is_file()
    jsconfig = json.loads(jsconfig_path.read_text(encoding="utf-8"))
    options = jsconfig["compilerOptions"]
    assert options["noEmit"] is True
    # Vendored three.js resolves through paths, not a package manager.
    assert "three" in options["paths"]
    assert "static/vendor/**" in jsconfig["exclude"]


def test_central_typedefs_cover_wire_contracts() -> None:
    types = js_text("types")
    for typedef in (
        "UnitData",
        "StateFrame",
        "MapSetupPayload",
        "IlluminationPayload",
        "IlluminationState",
        "SceneGeometryPayload",
        "GeodeticAnchor",
        "TerrainGrid",
        "SunVector",
    ):
        assert f"@typedef {{Object}} {typedef}" in types, typedef


def test_core_modules_opt_into_type_checking() -> None:
    for module in TYPE_CHECKED_MODULES:
        source = js_text(module)
        first_line = source.splitlines()[0].strip()
        assert first_line == "// @ts-check", f"{module}.js must start with // @ts-check"


def test_store_and_consumers_reference_shared_types() -> None:
    assert "import('./types.js').IlluminationState" in js_text("store")
    assert "import('./types.js').IlluminationPayload" in js_text("illumination")
    assert "import('./types.js').UnitData" in js_text("symbology")
    assert "import('./types.js').SunVector" in js_text("utils")
