from __future__ import annotations

import json
from pathlib import Path


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
        manifest = _load(path)["scripted_capability"]
        assert manifest["version"] == "scripted_capability.v1", path
        assert manifest["domain"] == domain, path
        assert manifest["label"] == label, path
        assert manifest["model_id"] == model_id, path
        assert manifest["role_id"] == role_id, path
        assert manifest["lifecycle"] in {"reset_decide_close", "task_status_shell"}, path
        assert manifest["deferred_claims"], path
        assert manifest["evidence_refs"], path


def test_current_manifests_do_not_claim_final_playable_acceptance() -> None:
    labels = {_load(path)["scripted_capability"]["label"] for path, *_ in CASES.values()}
    assert "playable" not in labels


def test_manifest_evidence_refs_name_existing_repo_files() -> None:
    for path, *_ in CASES.values():
        for ref in _load(path)["scripted_capability"]["evidence_refs"]:
            prefix, _, target = str(ref).partition(":")
            if prefix in {"source", "test"}:
                assert target and (REPO_ROOT / target).is_file(), (path, ref)
