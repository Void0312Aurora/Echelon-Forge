from __future__ import annotations

from pathlib import Path

from tools.environment.arnis.field_acceptance import (
    FIELD_ACCEPTANCE_CONTRACT_VERSION,
    evaluate_field_map,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
BUNDLE = (
    REPO_ROOT
    / "tests"
    / "scenario"
    / "fixtures"
    / "environment_substrate"
    / "arnis_bundle_v1"
    / "eastern_plain_infantry_phase1"
    / "expected"
)
OVERLAY = BUNDLE.parent / "field_overlay.json"


def test_flat_field_map_passes_composition_gate() -> None:
    report = evaluate_field_map(BUNDLE, OVERLAY)

    assert report["contract_version"] == FIELD_ACCEPTANCE_CONTRACT_VERSION
    assert report["valid"] is True
    assert report["fail_closed"] is False
    assert report["failures"] == []
    assert report["terrain"]["fraction_below_5deg"] >= 0.85
    assert report["terrain"]["slope_p95_deg"] <= 8.0
    assert report["landcover"]["open_landcover_fraction"] >= 0.65
    assert report["landcover"]["tree_cover_fraction"] <= 0.20
    assert report["overlay_counts"]["farmland_area"] == 4
    assert report["evidence"]["no_passability_release"] is True


def test_flat_field_map_gate_fails_closed_for_stricter_slope_requirement() -> None:
    report = evaluate_field_map(
        BUNDLE,
        OVERLAY,
        thresholds={"max_slope_p95_deg": 0.01},
    )

    assert report["valid"] is False
    assert report["fail_closed"] is True
    assert "flatness_p95_slope" in report["failures"]
