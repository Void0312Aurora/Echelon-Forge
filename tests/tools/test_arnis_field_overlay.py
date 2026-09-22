from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.environment.arnis.field_overlay import (
    FIELD_OVERLAY_CONTRACT_VERSION,
    FieldOverlayError,
    build_field_overlay,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    REPO_ROOT
    / "tests"
    / "scenario"
    / "fixtures"
    / "environment_substrate"
    / "arnis_bundle_v1"
    / "eastern_plain_infantry_phase1"
    / "input"
    / "osm_extract_synthetic.json"
)
BBOX = {
    "min_lat": 39.4940,
    "min_lon": -98.5100,
    "max_lat": 39.5060,
    "max_lon": -98.4900,
}


def test_field_overlay_preserves_plain_map_semantics_without_runtime_claims() -> None:
    payload = build_field_overlay(SOURCE, BBOX)

    assert payload["contract_version"] == FIELD_OVERLAY_CONTRACT_VERSION
    assert payload["profile_id"] == "eastern_plain_infantry_phase1"
    assert payload["source"]["synthetic"] is True
    assert payload["source"]["path"] == "osm_extract_synthetic.json"
    assert payload["summary"]["counts_by_kind"] == {
        "bridge_crossing": 1,
        "farmland_area": 4,
        "river_corridor": 2,
        "settlement_anchor": 2,
        "settlement_structure": 4,
        "tree_line": 3,
    }
    assert payload["evidence"] == {
        "metadata_only": True,
        "no_runtime_setup_application": True,
        "no_movement_release": True,
        "no_passability_release": True,
        "no_los_cover_release": True,
        "no_fire_control_release": True,
    }
    for entry in payload["entries"]:
        assert entry["evidence"]["metadata_only"] is True
        assert entry["evidence"]["no_passability_release"] is True
        assert entry["geometry"]["geometry_type"] in {"point", "line", "polygon"}


def test_field_overlay_is_deterministic() -> None:
    first = build_field_overlay(SOURCE, BBOX)
    second = build_field_overlay(SOURCE, BBOX)
    assert first == second
    assert json.dumps(first, sort_keys=True, separators=(",", ":")) == json.dumps(
        second, sort_keys=True, separators=(",", ":")
    )


def test_field_overlay_rejects_invalid_bbox() -> None:
    with pytest.raises(FieldOverlayError, match="latitude range"):
        build_field_overlay(SOURCE, {**BBOX, "max_lat": BBOX["min_lat"]})
