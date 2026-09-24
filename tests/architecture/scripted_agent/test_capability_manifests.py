from __future__ import annotations

import json
from pathlib import Path

import pytest

from python.tasking_contracts.scripted_capability import parse_scripted_capability


REPO_ROOT = Path(__file__).resolve().parents[3]

CASES = {
    "air": (
        REPO_ROOT / "scenarios" / "combined" / "takeoff_to_landing_continuous_eval_v1.json",
        "playable_candidate",
        "air.execution.phase_scripted",
        "autopilot_controller",
    ),
    "naval": (
        REPO_ROOT / "scenarios" / "naval" / "ddg51_take1_screen_contact_report_v1.json",
        "bounded_adapter",
        "naval.station.screen_hold",
        "naval_warfare_commander",
    ),
    "ground": (
        REPO_ROOT / "scenarios" / "ground" / "ground_platoon_native_static_occupy_v1.json",
        "held",
        None,
        "ground_commander",
    ),
}


def _load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_representative_scenarios_declare_scripted_capability_v1() -> None:
    for domain, (path, label, model_id, role_id) in CASES.items():
        manifest = parse_scripted_capability(_load(path))
        assert manifest.version == "scripted_capability.v1", path
        assert manifest.domain == domain, path
        assert manifest.label == label, path
        assert manifest.model_id == model_id, path
        assert manifest.role_id == role_id, path
        assert manifest.lifecycle in {"reset_decide_close", "task_status_shell"}, path
        assert manifest.deferred_claims, path
        assert manifest.evidence_refs, path


def test_current_manifests_do_not_claim_final_playable_acceptance() -> None:
    labels = {parse_scripted_capability(_load(path)).label for path, *_ in CASES.values()}
    assert "playable" not in labels


def test_manifest_evidence_refs_name_existing_repo_files() -> None:
    for path, *_ in CASES.values():
        for ref in parse_scripted_capability(_load(path)).evidence_refs:
            prefix, _, target = str(ref).partition(":")
            if prefix in {"source", "test"}:
                assert target and (REPO_ROOT / target).is_file(), (path, ref)


def test_manifest_parser_fails_closed_on_claim_without_model_or_evidence() -> None:
    with pytest.raises(ValueError, match="requires model_id"):
        parse_scripted_capability(
            {
                "scripted_capability": {
                    "version": "scripted_capability.v1",
                    "domain": "air",
                    "label": "playable_candidate",
                    "model_id": None,
                    "role_id": "autopilot_controller",
                    "lifecycle": "reset_decide_close",
                    "evidence_refs": ["test:x"],
                    "deferred_claims": ["runtime"],
                }
            }
        )

    with pytest.raises(ValueError, match="evidence_refs"):
        parse_scripted_capability(
            {
                "scripted_capability": {
                    "version": "scripted_capability.v1",
                    "domain": "ground",
                    "label": "held",
                    "model_id": None,
                    "role_id": "ground_commander",
                    "lifecycle": "task_status_shell",
                    "evidence_refs": [],
                    "deferred_claims": ["movement"],
                }
            }
        )
