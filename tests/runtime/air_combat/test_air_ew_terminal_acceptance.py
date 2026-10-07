from __future__ import annotations

import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

from tools.diagnostics import air_ew_terminal_acceptance as acceptance
from tools.diagnostics.air_ew_terminal_acceptance import (
    DEFAULT_MAX_STEPS,
    DEFAULT_SEEDS,
    run_single_demo,
    run_cooperative_demo,
    run_terminal_acceptance,
    SCENARIOS,
    validate_cooperative_report,
    validate_single_report,
    _source_provenance,
)


@pytest.fixture(autouse=True)
def clean_source(monkeypatch) -> None:
    # Scenario/receipt tests isolate provenance; the real Git helper and dirty
    # admission boundary are exercised separately below.
    monkeypatch.setattr(acceptance, "_source_provenance", lambda: ("a" * 40, False))


@pytest.fixture(scope="module")
def matrix_and_reports() -> tuple[dict, dict]:
    reports = {}

    def capture(runner, **kwargs):
        report = runner(**kwargs)
        reports[(kwargs["scenario_path"], kwargs["seed"])] = report
        return report

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(acceptance, "_source_provenance", lambda: ("a" * 40, False))
        matrix = run_terminal_acceptance(
            single_runner=lambda **kwargs: capture(run_single_demo, **kwargs),
            cooperative_runner=lambda **kwargs: capture(run_cooperative_demo, **kwargs),
        )
    return matrix, reports


def test_named_terminal_matrix_closes_and_replays_fixed_seeds(matrix_and_reports) -> None:
    matrix, _reports = matrix_and_reports
    assert matrix["accepted"] is True
    assert matrix["playable_capability_promotion"] is False
    assert matrix["replay_checked"] is True
    assert matrix["source_dirty"] is False
    assert matrix["receipt_reproducible"] is True
    assert len(matrix["source_revision"]) == 40
    assert len(matrix["native_module"]["sha256"]) == 64
    assert len(matrix["scenarios"]) == 2
    for scenario in matrix["scenarios"]:
        assert len(scenario["scenario_sha256"]) == 64
        assert [receipt["seed"] for receipt in scenario["seeds"]] == list(DEFAULT_SEEDS)
        for receipt in scenario["seeds"]:
            assert 0 < receipt["steps"] < DEFAULT_MAX_STEPS
            assert receipt["replay_equal"] is True
            assert len(receipt["trace_sha256"]) == 64
            slots = receipt.get("slot_receipts", [receipt])
            for slot in slots:
                assert slot["terminal_reason"] == "combat_win"
                assert slot["accepted_release_count"] > 0
                assert slot["chaff_consumed"] > 0 and slot["flare_consumed"] > 0
                assert 0 < slot["native_jammer_transmit_steps"] <= slot["jammer_request_steps"]


@pytest.mark.parametrize("cooperative", [False, True])
@pytest.mark.parametrize("failure", ["loss", "timeout", "unfinished", "budget", "resource", "no_tx", "post_reset", "baseline"])
def test_terminal_acceptance_rejects_failed_or_corrupt_evidence(
    matrix_and_reports, cooperative: bool, failure: str
) -> None:
    _matrix, reports = matrix_and_reports
    report = deepcopy(reports[(SCENARIOS[int(cooperative)]["path"], DEFAULT_SEEDS[0])])
    if failure == "loss":
        report["termination_reasons" if cooperative else "termination_reason"] = (
            ["combat_win", "combat_loss"] if cooperative else "combat_loss"
        )
    elif failure == "timeout":
        report["truncated"] = [False, True] if cooperative else True
    elif failure == "unfinished":
        report["terminated"] = [True, False] if cooperative else False
    elif failure == "budget":
        report["steps"] = DEFAULT_MAX_STEPS + 1
    elif failure == "resource":
        samples = report["countermeasure_state_samples"][1] if cooperative else report["countermeasure_state_samples"]
        for sample in samples:
            sample["chaff_remaining"] = 60
    elif failure == "no_tx":
        if cooperative:
            report["jammer_transmit_steps"][1] = []
        else:
            report["jammer_transmit_steps"] = []
    elif failure == "post_reset":
        samples = report["countermeasure_state_samples"][1] if cooperative else report["countermeasure_state_samples"]
        samples.append({"step": report["steps"], "chaff_remaining": 60, "flare_remaining": 30})
    elif failure == "baseline":
        if cooperative:
            report["pre_request_countermeasure_state"][1] = None
        else:
            report["pre_request_countermeasure_state"] = None
    validator = validate_cooperative_report if cooperative else validate_single_report
    with pytest.raises(ValueError):
        validator(report, max_steps=DEFAULT_MAX_STEPS)


def test_consumption_includes_the_first_request(matrix_and_reports) -> None:
    matrix, reports = matrix_and_reports
    source = reports[(SCENARIOS[0]["path"], DEFAULT_SEEDS[0])]
    receipt = matrix["scenarios"][0]["seeds"][0]
    assert receipt["chaff_consumed"] == (
        source["pre_request_countermeasure_state"]["chaff_remaining"]
        - source["countermeasure_state_samples"][-1]["chaff_remaining"]
    )
    assert receipt["chaff_consumed"] > (
        source["countermeasure_state_samples"][0]["chaff_remaining"]
        - source["countermeasure_state_samples"][-1]["chaff_remaining"]
    )


@pytest.mark.parametrize("cooperative", [False, True])
def test_native_timeout_is_reported_and_rejected(tmp_path: Path, cooperative: bool) -> None:
    fixture = json.loads(Path(SCENARIOS[int(cooperative)]["path"]).read_text(encoding="utf-8"))
    # Exhaust the native environment budget before the diagnostic runner's
    # budget, so rejection checks a genuine timeout rather than a cut-off run.
    fixture["environment"]["max_steps"] = 2
    scenario_path = tmp_path / "native_timeout.json"
    scenario_path.write_text(json.dumps(fixture), encoding="utf-8")
    runner = run_cooperative_demo if cooperative else run_single_demo
    report = runner(
        scenario_path=str(scenario_path),
        seed=DEFAULT_SEEDS[1],
        max_steps=3,
        response_doctrine="countermeasure_ready",
        jammer_doctrine="self_protect_on_lock",
    )
    assert report["steps"] == 2
    assert report["truncated"] == ([True, True] if cooperative else True)
    if cooperative:
        assert report["termination_reasons"] == ["combat_timeout", "combat_timeout"]
    else:
        assert report["termination_reason"] == "timeout"
    validator = validate_cooperative_report if cooperative else validate_single_report
    with pytest.raises(ValueError, match="timed out"):
        validator(report, max_steps=3)


@pytest.mark.parametrize("cooperative", [False, True])
def test_terminal_must_precede_the_acceptance_budget(matrix_and_reports, cooperative) -> None:
    _matrix, reports = matrix_and_reports
    report = reports[(SCENARIOS[int(cooperative)]["path"], DEFAULT_SEEDS[0])]
    validator = validate_cooperative_report if cooperative else validate_single_report
    with pytest.raises(ValueError, match="invalid terminal step"):
        validator(report, max_steps=report["steps"])


@pytest.mark.parametrize("corruption", ["owner", "missing_slot"])
def test_cooperative_acceptance_requires_complete_owned_roster(matrix_and_reports, corruption) -> None:
    _matrix, reports = matrix_and_reports
    report = deepcopy(reports[(SCENARIOS[1]["path"], DEFAULT_SEEDS[0])])
    if corruption == "owner":
        report["roster"][1]["target_owner_name"] = "Red_A"
    else:
        report["jammer_transmit_steps"].pop()
    with pytest.raises(ValueError):
        validate_cooperative_report(report, max_steps=DEFAULT_MAX_STEPS)


def test_same_seed_replay_mismatch_is_rejected(matrix_and_reports) -> None:
    _matrix, reports = matrix_and_reports
    calls = 0

    def altered_runner(**kwargs):
        nonlocal calls
        calls += 1
        report = deepcopy(reports[(kwargs["scenario_path"], kwargs["seed"])])
        if calls == 2:
            report["last_info"]["replay_drift"] = True
        return report

    with pytest.raises(ValueError, match="same-seed replay mismatch"):
        run_terminal_acceptance(seeds=(DEFAULT_SEEDS[0],), single_runner=altered_runner)


@pytest.mark.parametrize("seeds,budget", [((), 600), ((11, 11), 600), ((11.5,), 600), ((11,), 0)])
def test_invalid_seed_matrix_or_budget_is_rejected(seeds, budget) -> None:
    with pytest.raises(ValueError):
        run_terminal_acceptance(seeds=seeds, max_steps=budget)


@pytest.mark.parametrize("change", ["tracked", "staged", "untracked"])
def test_source_provenance_detects_committed_and_dirty_source(tmp_path, change) -> None:
    def git(*args):
        return subprocess.run(
            ["git", *args], cwd=tmp_path, check=True, capture_output=True, text=True,
        ).stdout.strip()

    git("init", "--quiet")
    tracked = tmp_path / "source.py"
    tracked.write_text("committed = True\n", encoding="utf-8")
    git("add", "source.py")
    git("-c", "user.name=Provenance Test", "-c", "user.email=provenance@example.invalid",
        "commit", "--quiet", "-m", "baseline")
    revision = git("rev-parse", "HEAD")
    assert _source_provenance(tmp_path) == (revision, False)
    if change == "untracked":
        (tmp_path / "new_source.py").write_text("uncommitted = True\n", encoding="utf-8")
    else:
        tracked.write_text("committed = False\n", encoding="utf-8")
        if change == "staged":
            git("add", "source.py")
    assert _source_provenance(tmp_path) == (revision, True)


def test_dirty_source_is_rejected_before_running_or_publishing(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(acceptance, "_source_provenance", lambda: ("a" * 40, True))
    calls = []

    def runner(**kwargs):
        calls.append(kwargs)
        pytest.fail("dirty source must be rejected before scenario execution")

    with pytest.raises(ValueError, match="requires clean committed source"):
        run_terminal_acceptance(single_runner=runner, cooperative_runner=runner)
    assert calls == []
    output = tmp_path / "receipt.json"
    monkeypatch.setattr(acceptance.sys, "argv", ["acceptance", "--json_out", str(output)])
    with pytest.raises(ValueError, match="requires clean committed source"):
        acceptance.main()
    assert not output.exists()


@pytest.mark.parametrize("final_revision,final_dirty", [("a" * 40, True), ("b" * 40, False)])
def test_source_change_during_execution_is_rejected(
    matrix_and_reports, monkeypatch, final_revision, final_dirty,
) -> None:
    _matrix, reports = matrix_and_reports
    provenance = iter([("a" * 40, False), (final_revision, final_dirty)])
    monkeypatch.setattr(acceptance, "_source_provenance", lambda: next(provenance))

    def runner(**kwargs):
        return deepcopy(reports[(kwargs["scenario_path"], kwargs["seed"])])

    with pytest.raises(ValueError, match="source changed during execution"):
        run_terminal_acceptance(single_runner=runner, cooperative_runner=runner)


def test_frozen_receipt_source_revision_is_an_ancestor_of_current_head() -> None:
    receipt_path = (
        acceptance.REPO_ROOT
        / "docs/domains/air/work/active/ew_completion/artifacts/"
        "ew_named_terminal_acceptance_20261007.json"
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    source_revision = receipt.get("source_revision")

    assert receipt.get("accepted") is True
    assert receipt.get("source_dirty") is False
    assert receipt.get("receipt_reproducible") is True
    assert isinstance(source_revision, str) and len(source_revision) == 40
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", source_revision, "HEAD"],
        cwd=acceptance.REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert ancestor.returncode == 0, (
        f"frozen receipt source {source_revision} must be an ancestor of current HEAD"
    )
