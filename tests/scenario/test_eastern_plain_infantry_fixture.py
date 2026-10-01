from __future__ import annotations

import json
from pathlib import Path

from python.scenario.environment_substrate import import_arnis_environment_bundle
from tools.environment.arnis.cli import _verify_bundle, _verify_request_expectations
from tools.environment.arnis.field_acceptance import evaluate_field_map


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = (
    REPO_ROOT
    / "tests"
    / "scenario"
    / "fixtures"
    / "environment_substrate"
    / "arnis_bundle_v1"
    / "eastern_plain_infantry_phase1"
)
BUNDLE = FIXTURE / "expected"


def test_eastern_plain_fixture_imports_and_matches_request() -> None:
    result = import_arnis_environment_bundle(BUNDLE)
    assert result.valid is True
    assert result.fail_closed is False
    assert result.manifest is not None

    verification = _verify_bundle(BUNDLE)
    _verify_request_expectations(FIXTURE / "request.json", BUNDLE, verification)
    assert verification["bundle_digest_sha256"] == (
        "eea7c8bcb37baa31ede236276b390fb01657c3cb8b1564e30467ac83d51f51e2"
    )
    assert verification["catalog_counts"]["catalog:arnis_road"] == 5
    assert verification["catalog_counts"]["catalog:arnis_hydrology"] == 2


def test_eastern_plain_fixture_retains_metadata_overlay_and_acceptance_report() -> None:
    overlay = json.loads((FIXTURE / "field_overlay.json").read_text(encoding="utf-8"))
    report = json.loads((FIXTURE / "field_acceptance.json").read_text(encoding="utf-8"))

    assert overlay["contract_version"] == "field_overlay.v1"
    assert overlay["evidence"]["metadata_only"] is True
    assert report == evaluate_field_map(BUNDLE, FIXTURE / "field_overlay.json")
    assert report["valid"] is True
    assert report["evidence"]["no_passability_release"] is True
