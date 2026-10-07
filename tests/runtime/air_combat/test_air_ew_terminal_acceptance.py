from __future__ import annotations

from copy import deepcopy

import pytest

from tools.diagnostics.air_ew_terminal_acceptance import (
    DEFAULT_MAX_STEPS,
    DEFAULT_SEEDS,
    run_single_demo,
    run_cooperative_demo,
    run_terminal_acceptance,
    SCENARIOS,
    validate_cooperative_report,
    validate_single_report,
)


@pytest.fixture(scope="module")
def matrix_and_reports() -> tuple[dict, dict]:
    reports = {}

    def capture(runner, **kwargs):
        report = runner(**kwargs)
        reports[(kwargs["scenario_path"], kwargs["seed"])] = report
        return report

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
    assert matrix["receipt_reproducible"] is (not matrix["source_dirty"])
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
