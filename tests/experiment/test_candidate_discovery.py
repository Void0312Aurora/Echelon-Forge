"""Candidate-discovery benchmark: world mechanics, selector rules, and findings.

The finding tests pin the observed synthetic behavior at a reduced
configuration (8 training and 8 held-out seeds). They are regressions on the
benchmark, not claims about the runtime; see the issue README for the full
24-seed table and its evidence boundary.
"""

from __future__ import annotations

import pytest

from python.experiment.candidate_discovery import ACT
from python.experiment.candidate_discovery import WAIT
from python.experiment.candidate_discovery import BenchmarkConfig
from python.experiment.candidate_discovery import BenchmarkError
from python.experiment.candidate_discovery import CausalDecisionWorld
from python.experiment.candidate_discovery import evaluate
from python.experiment.candidate_discovery import fit_value
from python.experiment.candidate_discovery import make_world
from python.experiment.candidate_discovery import measure_signals
from python.experiment.candidate_discovery import select
from python.experiment.candidate_discovery import triggers
from python.experiment.reference_session import ReferenceSession

SMALL = BenchmarkConfig(
    train_seeds=tuple(range(101, 109)), eval_seeds=tuple(range(201, 209)), budgets=(16, 32)
)


@pytest.fixture(scope="module")
def report() -> dict:
    return evaluate(SMALL)


def _row(report: dict, selector: str, lookback: int, budget: int) -> dict:
    (row,) = [
        item
        for item in report["summary"]
        if item["selector"] == selector and item["lookback"] == lookback and item["budget"] == budget
    ]
    return row


def _world(**overrides: object) -> CausalDecisionWorld:
    fields = {
        "length": 20,
        "hazards": (2,),
        "opportunities": (6,),
        "decoys": (10,),
        "false_cues": (13,),
        "delay": 3,
    }
    fields.update(overrides)
    return CausalDecisionWorld(**fields)


def _rewards(world: CausalDecisionWorld, actions: dict[int, str]) -> list[int]:
    session = ReferenceSession.open(
        session_id="mechanics", seed=0, agent_ids=("agent_0",), policy_ref="probe", world=world
    )
    rewards = []
    step = 0
    while not session.is_terminated(session.baseline):
        transition = session.step(
            session.baseline,
            {"agent_0": actions.get(step, WAIT)},
            observation_provenance="decision_belief_packet",
        )
        rewards.append(transition.rewards[0][1])
        step += 1
    return rewards


def test_world_consequences_are_delayed_and_action_dependent() -> None:
    world = _world()
    baseline = _rewards(world, {})
    assert baseline[5] == 1 + world.hazard_penalty
    assert baseline[10] == 1 + world.decoy_reward
    avoided = _rewards(world, {2: ACT})
    assert avoided[2] == world.act_cost and avoided[5] == 1
    took = _rewards(world, {6: ACT})
    assert took[9] == 1 + world.opportunity_bonus
    decoy_act = _rewards(world, {10: ACT})
    assert decoy_act[10] == world.act_cost + world.decoy_reward
    assert sum(_rewards(world, {13: ACT})) == sum(baseline) - 3


def test_world_rejects_overlapping_or_out_of_range_events() -> None:
    with pytest.raises(BenchmarkError):
        _world(decoys=(2,))
    with pytest.raises(BenchmarkError):
        _world(hazards=(18,))
    with pytest.raises(BenchmarkError):
        _world(opportunities=(7, 6))


def test_config_rejects_shared_train_and_eval_seeds() -> None:
    with pytest.raises(BenchmarkError, match="disjoint"):
        BenchmarkConfig(train_seeds=(1, 2), eval_seeds=(2, 3))


def test_event_placement_keeps_lookback_windows_disjoint() -> None:
    reach = SMALL.delay + max(SMALL.lookbacks)
    for seed in (*SMALL.train_seeds, *SMALL.eval_seeds):
        world = make_world(SMALL, seed)
        events = sorted(step for kind in ("hazard", "opportunity", "decoy", "false_cue") for step in world.events(kind))
        assert all(later - earlier > reach for earlier, later in zip(events, events[1:]))


def test_oracle_gain_marks_exactly_the_decision_events() -> None:
    value = fit_value(SMALL)
    for seed in SMALL.eval_seeds[:3]:
        world = make_world(SMALL, seed)
        _, signals = measure_signals(world, SMALL, seed, value)
        important = {item.step for item in signals if item.oracle_gain >= SMALL.gain_threshold}
        assert important == set(world.hazards) | set(world.opportunities)


def test_triggers_use_a_robust_threshold_and_ignore_ties() -> None:
    flat = {step: 0 for step in range(10)}
    assert triggers(flat) == []
    spiky = {**flat, 3: 9, 7: 4}
    assert triggers(spiky) == [3, 7]


def test_selectors_respect_budget_and_proposals_never_read_the_oracle() -> None:
    value = fit_value(SMALL)
    world = make_world(SMALL, SMALL.eval_seeds[0])
    _, signals = measure_signals(world, SMALL, SMALL.eval_seeds[0], value)
    blinded = tuple(type(item)(item.step, item.reward, item.td_surprise_milli, 0, "inert") for item in signals)
    for selector in ("uniform", "reward", "td", "td_uniform"):
        for budget in (4, 16, 32):
            picked = select(selector, signals, budget, 4, SMALL.uniform_share_milli)
            assert len(picked.steps) == budget == len(set(picked.steps))
            assert picked == select(selector, blinded, budget, 4, SMALL.uniform_share_milli)


def test_report_is_deterministic_and_labelled_synthetic(report: dict) -> None:
    assert report["evidence_label"] == "synthetic"
    assert evaluate(SMALL)["report_digest"] == report["report_digest"]


def test_decision_points_are_sparse(report: dict) -> None:
    assert all(seed["decision_density_milli"] < 50 for seed in report["seeds"])


def test_exogenous_spikes_dominate_both_reward_and_td_triggers() -> None:
    value = fit_value(SMALL)
    for seed in SMALL.eval_seeds:
        world = make_world(SMALL, seed)
        _, signals = measure_signals(world, SMALL, seed, value)
        kinds = {item.step: item.kind for item in signals}
        for scores in (
            {item.step: abs(item.reward) for item in signals},
            {item.step: item.td_surprise_milli for item in signals},
        ):
            assert [kinds[step] for step in triggers(scores)[:4]] == ["decoy"] * 4


def test_td_finds_cued_hazards_where_uniform_and_reward_do_not(report: dict) -> None:
    td = _row(report, "td", 0, 16)
    assert td["mean_hazard_recall_milli"] >= 400
    for selector, lookback in (("uniform", 0), ("reward", 0), ("reward", 4)):
        assert _row(report, selector, lookback, 16)["mean_hazard_recall_milli"] == 0
    assert _row(report, "td", 0, 32)["mean_hazard_recall_milli"] == 1000


def test_backward_lookback_spends_td_budget_on_decoy_neighborhoods(report: dict) -> None:
    for budget in (16, 32):
        assert _row(report, "td", 4, budget)["mean_recall_milli"] == 0
        assert _row(report, "td", 0, budget)["mean_recall_milli"] > 0


def test_reward_lookback_reaches_hazards_only_through_their_delayed_penalty(report: dict) -> None:
    assert _row(report, "reward", 4, 32)["mean_hazard_recall_milli"] >= 600
    assert _row(report, "reward", 6, 32)["mean_hazard_recall_milli"] == 0


def test_silent_opportunities_are_found_only_by_probing(report: dict) -> None:
    for budget in (16, 32):
        for selector, lookback in (("td", 0), ("reward", 4)):
            assert _row(report, selector, lookback, budget)["mean_opportunity_recall_milli"] == 0
    assert _row(report, "uniform", 0, 32)["mean_opportunity_recall_milli"] > 0
    assert _row(report, "td_uniform", 0, 32)["mean_opportunity_recall_milli"] > 0
    assert _row(report, "td_uniform", 0, 32)["mean_hazard_recall_milli"] == 1000
