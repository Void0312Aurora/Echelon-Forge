"""Robustness sweeps over the Phase 1 candidate-discovery findings.

The regression tests pin which Phase 1 observation survives each sweep at a
reduced configuration (6 training and 4 held-out seeds). They are synthetic
regressions on the benchmark world, not claims about the runtime.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from python.experiment.candidate_discovery import BenchmarkConfig
from python.experiment.candidate_discovery import BenchmarkError
from python.experiment.candidate_discovery import CausalDecisionWorld
from python.experiment.candidate_discovery import evaluate
from python.experiment.candidate_discovery import measure_signals
from python.experiment.candidate_discovery import triggers
from python.experiment.candidate_discovery_sweeps import SweepConfig
from python.experiment.candidate_discovery_sweeps import branch_reward_diffs
from python.experiment.candidate_discovery_sweeps import clear_caches
from python.experiment.candidate_discovery_sweeps import discounted_gain
from python.experiment.candidate_discovery_sweeps import measure_seed
from python.experiment.candidate_discovery_sweeps import run_sweeps
from python.experiment.candidate_discovery_sweeps import trigger_role

SMALL_BASE = BenchmarkConfig(
    train_seeds=tuple(range(101, 107)), eval_seeds=tuple(range(201, 205)), budgets=(16, 32, 64)
)
SMALL = SweepConfig(base=SMALL_BASE)
SEEDS = len(SMALL_BASE.eval_seeds)


@pytest.fixture(scope="module")
def report() -> dict:
    return run_sweeps(SMALL)


def _cell(cells: list, **match: object) -> dict:
    (cell,) = [cell for cell in cells if all(cell[key] == value for key, value in match.items())]
    return cell


def _row(cell: dict, selector: str, lookback: int, budget: int) -> dict:
    (row,) = [
        item
        for item in cell["summary"]
        if (item["selector"], item["lookback"], item["budget"]) == (selector, lookback, budget)
    ]
    return row


def _dominance(cell: dict, signal: str) -> dict:
    (row,) = [item for item in cell["dominance"] if item["signal"] == signal]
    return row


def _by_decoy(report: dict, selector: str, lookback: int, budget: int, key: str) -> dict:
    return {
        cell["decoy_reward"]: _row(cell, selector, lookback, budget)[key]
        for cell in report["decoy_sweep"]
    }


def _tiny_world() -> CausalDecisionWorld:
    return CausalDecisionWorld(
        length=20, hazards=(2,), opportunities=(6,), decoys=(10,), false_cues=(13,), delay=3
    )


def test_discounted_oracle_matches_hand_computed_gain() -> None:
    world = _tiny_world()
    config = BenchmarkConfig(horizon=5, budgets=(4,))
    value = {feature: Fraction(0) for feature in range(world.delay + 2)}
    session, signals = measure_signals(world, config, 0, value)
    diffs = branch_reward_diffs(session)
    # act costs -2 instead of +1 now; the avoided -20 (or earned +20) lands delay = 3 steps later.
    assert diffs[2] == (-3, 0, 0, 20, 0)
    assert diffs[6] == (-3, 0, 0, 20, 0)
    assert diffs[10] == (-3, 0, 0, 0, 0)
    assert diffs[13] == (-3, 0, 0, 0, 0)
    # -3 + (4/5)**3 * 20 and -3 + (19/20)**3 * 20, exact.
    assert discounted_gain(diffs[2], Fraction(4, 5)) == Fraction(181, 25)
    assert discounted_gain(diffs[2], Fraction(19, 20)) == Fraction(5659, 400)
    assert discounted_gain(diffs[10], Fraction(4, 5)) == -3
    for item in signals:
        assert discounted_gain(diffs[item.step], Fraction(1)) == item.oracle_gain


def test_sweep_config_validates_its_grid() -> None:
    with pytest.raises(BenchmarkError, match="gamma"):
        SweepConfig(base=SMALL_BASE, oracle_gammas=(Fraction(4, 5),))
    with pytest.raises(BenchmarkError, match="gamma"):
        SweepConfig(base=SMALL_BASE, oracle_gammas=(Fraction(1), Fraction(0)))
    with pytest.raises(BenchmarkError):
        SweepConfig(base=SMALL_BASE, delays=(8,))
    assert SMALL.delay_config(SMALL_BASE.delay) == SMALL_BASE
    assert SMALL.decoy_config(SMALL_BASE.decoy_reward) == SMALL_BASE


def test_trigger_roles_name_the_causing_event() -> None:
    world = _tiny_world()
    assert [trigger_role(world, step) for step in (10, 1, 2, 5, 12, 7, 19)] == [
        "decoy",
        "pre_cue",
        "cue_window",
        "consequence",
        "pre_cue",
        "opportunity",
        "other",
    ]


def test_base_cell_reproduces_the_phase1_benchmark(report: dict) -> None:
    phase1 = evaluate(SMALL_BASE)
    cell = _cell(report["decoy_sweep"], decoy_reward=SMALL_BASE.decoy_reward)
    assert cell["value_by_cue_feature_milli"] == phase1["value_by_cue_feature_milli"]
    assert cell["manifest_digests"] == [seed["manifest_digest"] for seed in phase1["seeds"]]
    for row in phase1["summary"]:
        mine = _row(cell, row["selector"], row["lookback"], row["budget"])
        assert mine["mean_recall_milli"] == row["mean_recall_milli"]
        assert mine["mean_hazard_recall_milli"] == row["mean_hazard_recall_milli"]
        assert mine["zero_regret_seeds"] == row["zero_regret_seeds"]
        assert mine["total_regret_milli"] == 1000 * row["total_regret"]


def test_decoy_aware_scores_never_trigger_on_decoys() -> None:
    # By construction: decoys carry no observation, and both variants remove the
    # unexplained immediate reward. Plain TD is decoy-led at these magnitudes.
    for reward in (25, 50):
        config = SMALL.decoy_config(reward)
        for seed in config.eval_seeds:
            measurement = measure_seed(config, seed)
            kinds = measurement.kinds
            plain = {item.step: item.td_surprise_milli for item in measurement.signals}
            assert kinds[triggers(plain)[0]] == "decoy"
            for name in ("td_vchange", "td_expected"):
                fired = triggers(measurement.variant_milli[name])
                assert fired and not any(kinds[step] == "decoy" for step in fired)


def test_report_is_deterministic_labelled_synthetic_and_carries_its_grid(report: dict) -> None:
    tiny = SweepConfig(
        base=BenchmarkConfig(train_seeds=(101, 102), eval_seeds=(201,), budgets=(16,)),
        oracle_gammas=(Fraction(1), Fraction(4, 5)),
        decoy_rewards=(0, 25),
        delays=(4,),
    )
    first = run_sweeps(tiny)
    clear_caches()
    assert first["evidence_label"] == "synthetic"
    assert run_sweeps(tiny)["report_digest"] == first["report_digest"]
    assert report["evidence_label"] == "synthetic"
    grid = report["config"]["grid"]
    assert grid["oracle_gammas"] == [[1, 1], [19, 20], [4, 5]]
    assert grid["decoy_rewards"] == [0, 5, 10, 25, 50]
    assert grid["lookbacks_by_delay"] == {"2": [0, 2, 4], "4": [0, 4, 6], "6": [0, 6, 8]}


# --- Finding 1: sparsity ---------------------------------------------------------------


def test_sparsity_is_fixed_by_construction_and_vanishes_under_strong_discounting(
    report: dict,
) -> None:
    sparsity = report["phase1_checks"]["f1_sparsity"]
    # 5 decision events over 280 branchable steps in every cell: 1.7 %, not 2.7 %.
    assert sparsity["density_milli"] == [17]
    # gamma**6 * 20 - 3 = 2.24 < gain_threshold 5: no step is "important" at all.
    assert sparsity["cells_with_empty_important_set"] == [[6, 4, 5]]
    assert sparsity["cells_with_changed_positive_set"] == []


# --- Sweep 1: discounted oracle horizon ------------------------------------------------


def test_discounting_rescales_gains_without_changing_any_ranking(report: dict) -> None:
    cells = report["gamma_sweep"]
    for delay in SMALL.delays:
        for gamma in ([19, 20], [4, 5]):
            cell = _cell(cells, delay=delay, gamma=gamma)
            assert cell["positive_changed_seeds"] == 0
            assert cell["ranking_matches_gamma_one"]["regret"] is True
            if [delay, *gamma] != [6, 4, 5]:
                assert cell["important_changed_seeds"] == 0
                assert cell["ranking_matches_gamma_one"]["recall"] is True
    assert _cell(cells, delay=4, gamma=[4, 5])["min_important_gain_milli"] == 5192
    broken = _cell(cells, delay=6, gamma=[4, 5])
    assert broken["important_empty_seeds"] == SEEDS
    assert broken["oracle_best_gain_milli"] == [2243, 2243]
    assert broken["ranking_matches_gamma_one"]["recall"] is None


# --- Sweep 2: decoy magnitude (finding 2) ------------------------------------------------


def test_decoys_dominate_triggers_only_once_they_outrank_the_hazard_penalty(report: dict) -> None:
    domination = report["phase1_checks"]["f2_decoy_domination"]
    expected = {"0": 0, "5": 0, "10": 0, "25": SEEDS, "50": SEEDS}
    assert domination["reward_all_topk_decoy_seeds"] == expected
    assert domination["td_all_topk_decoy_seeds"] == expected
    # Below the penalty, plain TD is still led by a non-decision: the consequence step.
    roles = domination["td_top1_role_seeds_by_decoy"]
    for reward in ("0", "5", "10"):
        assert roles[reward]["consequence"] == SEEDS
    for reward in ("25", "50"):
        assert roles[reward]["decoy"] == SEEDS
    assert all(roles[reward]["pre_cue"] == 0 for reward in roles)


def test_td_l0_hazard_recall_at_16_is_non_monotone_in_decoy_magnitude(report: dict) -> None:
    assert _by_decoy(report, "td", 0, 16, "mean_hazard_recall_milli") == {
        0: 499,
        5: 499,
        10: 0,
        25: 416,
        50: 416,
    }
    assert set(_by_decoy(report, "td", 0, 32, "mean_hazard_recall_milli").values()) == {1000}
    # Mechanism: once a decoy outranks the first pre-cue trigger, decoy windows are
    # spent before the lead step reaches a cue (at 10 a consequence trigger is also ahead).
    assert report["phase1_checks"]["f2_decoy_domination"]["td_decoy_before_pre_cue_seeds"] == {
        "0": 0,
        "5": 0,
        "10": SEEDS,
        "25": SEEDS,
        "50": SEEDS,
    }


# --- Sweep 3: consequence delay (finding 3) ----------------------------------------------


def test_reward_reaches_hazards_with_any_lookback_covering_the_delay(report: dict) -> None:
    checks = report["phase1_checks"]["f3_reward_hazard_recall"]
    measured = {
        (int(delay), int(lookback)): (row["triggered"]["32"], row["triggered"]["64"])
        for delay, rows in checks.items()
        for lookback, row in rows.items()
    }
    assert measured == {
        (2, 0): (0, 0),
        (2, 2): (1000, 1000),
        (2, 4): (666, 1000),
        (4, 0): (0, 0),
        (4, 4): (666, 1000),
        (4, 6): (0, 1000),
        (6, 0): (0, 0),
        (6, 6): (0, 1000),
        (6, 8): (0, 1000),
    }


def test_reward_lookback_beyond_the_delay_works_once_decoys_stop_leading(report: dict) -> None:
    assert _by_decoy(report, "reward", 6, 32, "mean_hazard_recall_milli") == {
        0: 1000,
        5: 1000,
        10: 1000,
        25: 0,
        50: 0,
    }


def test_td_l0_finds_every_cued_hazard_at_32_for_every_delay(report: dict) -> None:
    checks = report["phase1_checks"]["f3_td_l0_hazard_recall"]
    assert {delay: row["triggered"]["32"] for delay, row in checks.items()} == {
        "2": 1000,
        "4": 1000,
        "6": 1000,
    }
    assert {delay: row["triggered"]["16"] for delay, row in checks.items()} == {
        "2": 416,
        "4": 416,
        "6": 0,
    }


# --- Finding 4: backward lookback under TD -----------------------------------------------


def test_td_backward_lookback_fails_only_when_decoys_outrank_the_hazard_triggers(
    report: dict,
) -> None:
    by_lookback = report["phase1_checks"]["f4_td_recall_by_lookback"]
    assert {reward: rows["4"]["32"] for reward, rows in by_lookback.items()} == {
        "0": 600,
        "5": 600,
        "10": 0,
        "25": 0,
        "50": 0,
    }
    assert {reward: rows["4"]["64"] for reward, rows in by_lookback.items()} == dict.fromkeys(
        by_lookback, 600
    )


# --- Sweep 4: decoy-aware TD -------------------------------------------------------------


def test_decoy_aware_td_removes_decoy_domination(report: dict) -> None:
    for reward in SMALL.decoy_rewards:
        cell = _cell(report["variant_sweep"], decoy_reward=reward)
        for name in ("td_vchange", "td_expected"):
            assert _dominance(cell, name)["decoy_triggers"] == 0
            assert _row(cell, name, 0, 32)["mean_hazard_recall_milli"] == 1000
        # V-change alone is led by the consequence step (the cue feature resets and V
        # jumps): an observation change that is not a decision. Only td_expected leads
        # with the pre-cue step whose lead reaches the decision.
        assert _dominance(cell, "td_vchange")["top1_role_seeds"]["consequence"] == SEEDS
        assert _dominance(cell, "td_expected")["top1_role_seeds"]["pre_cue"] == SEEDS
    hazard16 = {
        name: _by_decoy(report, name, 0, 16, "mean_hazard_recall_milli")
        for name in ("td", "td_vchange", "td_expected")
    }
    assert set(hazard16["td_expected"].values()) == {1000}
    assert set(hazard16["td_vchange"].values()) == {499}
    assert hazard16["td"][10] == 0


def test_silent_opportunities_are_never_proposed_by_any_trigger(report: dict) -> None:
    silent = report["phase1_checks"]["f5_silent_opportunities"]
    assert silent["opportunity_trigger_hits"] == 0
    uniform = silent["uniform_opportunity_recall_by_decoy"]
    assert len({tuple(sorted(row.items())) for row in uniform.values()}) == 1
