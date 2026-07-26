"""Strategic-scale foundation seeds in the viz contracts.

Operational/strategic views (country-scale, aggregated echelons, geodetic
globe) are a committed long-term target. These tests pin the four cheap
contract seeds planted now so today's data stays usable then:

1. geodetic anchor: every scene-geometry payload binds its local ENU frame
   to WGS84 so local scenes remain placeable on a globe;
2. MIL-STD-2525 SIDC vocabulary: units carry a standard symbology
   identifier instead of only ad-hoc shapes;
3. echelon on the unit contract: aggregation views need organizational
   level, seeded from type naming until the engine models it natively;
4. wire contract versions: state frames and map_setup declare a version so
   future protocol migrations (binary frames, AOI subscriptions) can
   negotiate instead of breaking silently.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from examples.viz.runtime.scene_geometry import load_scene_geometry_payload
from examples.viz.runtime.unit_semantics import infer_echelon

from frontend_sources import js_text

REPO_ROOT = Path(__file__).resolve().parents[2]
CHICAGO_BUNDLE = (
    REPO_ROOT
    / "tests"
    / "scenario"
    / "fixtures"
    / "environment_substrate"
    / "arnis_bundle_v1"
    / "chicago_river_phase1"
    / "expected"
)

VIZ_SESSION_SRC = (
    REPO_ROOT / "examples" / "viz" / "runtime" / "viz_session.py"
).read_text(encoding="utf-8")


# --- Seed 1: geodetic anchor -------------------------------------------------


@pytest.fixture(scope="module")
def payload() -> dict:
    return load_scene_geometry_payload(str(CHICAGO_BUNDLE))


def test_scene_geometry_carries_geodetic_anchor(payload: dict) -> None:
    anchor = payload["geodetic_anchor"]
    assert anchor is not None
    assert anchor["frame"] == "local_enu_m"
    assert anchor["source"] == "arnis_bundle_bbox_wgs84"
    # Chicago river fixture: anchor is the bbox midpoint.
    assert anchor["anchor_lat_deg"] == pytest.approx((41.8865 + 41.8895) / 2.0)
    assert anchor["anchor_lon_deg"] == pytest.approx((-87.6355 + -87.6315) / 2.0)
    bbox = anchor["bbox_wgs84"]
    assert bbox["min_lat"] == pytest.approx(41.8865)
    assert bbox["max_lon"] == pytest.approx(-87.6315)
    # The projection that produced the local frame travels with the anchor.
    assert "web_mercator" in anchor["projection"]


def test_frontend_exposes_geodetic_anchor() -> None:
    scene_geometry = js_text("scene-geometry")
    assert "sceneGeodeticAnchor" in scene_geometry
    assert "geodetic_anchor" in scene_geometry


# --- Seed 2: MIL-STD-2525 SIDC vocabulary ------------------------------------


def test_symbology_defines_sidc_vocabulary() -> None:
    symbology = js_text("symbology")
    assert "sidcForUnit" in symbology
    assert "sidcAffiliation" in symbology
    assert "sidcUnitTypeSkeleton" in symbology
    assert "sidcEchelonCode" in symbology
    # Affiliation letters follow the standard.
    assert "Blue: 'F'" in symbology
    assert "Red: 'H'" in symbology
    # Echelon codes cover the platoon-to-corps ladder.
    for code in ("platoon: 'D'", "battalion: 'F'", "division: 'I'"):
        assert code in symbology


def test_unit_list_surfaces_sidc() -> None:
    ui_shell = js_text("ui-shell")
    assert "sidcForUnit" in ui_shell


# --- Seed 3: echelon on the unit contract ------------------------------------


def test_infer_echelon_from_type_naming() -> None:
    assert infer_echelon("Ground_Platoon_MVP") == "platoon"
    assert infer_echelon("Some_Company_Type") == "company"
    assert infer_echelon(None, "Blue_Squad_Alpha") == "squad"
    assert infer_echelon("F-16C") == ""
    assert infer_echelon("") == ""


def test_unit_payload_carries_echelon() -> None:
    assert '"echelon": infer_echelon(type_name, name)' in VIZ_SESSION_SRC
    # Runtime-spawned munitions carry the field too (empty).
    assert '"echelon": ""' in VIZ_SESSION_SRC


# --- Seed 4: wire contract versions ------------------------------------------


def test_state_frame_and_map_setup_declare_contract_versions() -> None:
    assert 'VIZ_STATE_FRAME_CONTRACT_VERSION = "examples.viz.state_frame.v1"' in VIZ_SESSION_SRC
    assert 'VIZ_MAP_SETUP_CONTRACT_VERSION = "examples.viz.map_setup.v1"' in VIZ_SESSION_SRC
    assert '"contract_version": VIZ_STATE_FRAME_CONTRACT_VERSION' in VIZ_SESSION_SRC
    assert '"contract_version": VIZ_MAP_SETUP_CONTRACT_VERSION' in VIZ_SESSION_SRC


def test_frontend_tolerates_and_reports_version_drift() -> None:
    session = js_text("session")
    assert "checkContractVersion" in session
    assert "examples.viz.state_frame.v1" in session
    assert "examples.viz.map_setup.v1" in session
    # Tolerant: warn, do not throw.
    assert "rendering best-effort" in session
