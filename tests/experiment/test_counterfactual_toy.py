from __future__ import annotations

import subprocess
import sys

from python.experiment.counterfactual_toy import DecisionCandidate
from python.experiment.counterfactual_toy import best_branch
from python.experiment.counterfactual_toy import candidate_recall
from python.experiment.counterfactual_toy import interaction_residual
from python.experiment.counterfactual_toy import rollout_branch
from python.experiment.counterfactual_toy import select_candidates


def test_toy_import_has_no_runtime_bootstrap_side_effects() -> None:
    probe = (
        "import sys\n"
        "import python.experiment.counterfactual_toy\n"
        "roots = {name.split('.')[0] for name in sys.modules}\n"
        "assert not roots & {'ef_py', 'gymnasium', 'stable_baselines3', 'torch'}\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", probe], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_rollout_is_deterministic_for_identical_branch_inputs() -> None:
    first = rollout_branch((1, 0), horizon=8, gamma=0.95)
    second = rollout_branch((1, 0), horizon=8, gamma=0.95)
    assert first == second


def test_horizon_sensitivity_changes_the_best_single_agent_action() -> None:
    assert best_branch(agent_count=1, horizon=1).actions == (0,)
    assert best_branch(agent_count=1, horizon=8).actions == (1,)


def test_joint_branch_exposes_pairwise_interaction_residual() -> None:
    assert interaction_residual(horizon=1) == 0.0
    assert interaction_residual(horizon=8) > 0.0


def test_candidate_selection_respects_budget_and_keeps_provenance_ties_stable() -> None:
    candidates = tuple(
        DecisionCandidate(
            candidate_id=f"t{time_step}",
            time_step=time_step,
            reward_delta=reward_delta,
            td_surprise=td_surprise,
            oracle_gain=oracle_gain,
        )
        for time_step, reward_delta, td_surprise, oracle_gain in (
            (0, 0.1, 0.1, 0.1),
            (2, 2.0, 1.0, 2.5),
            (4, 0.2, 0.2, 0.2),
            (6, 1.5, 1.0, 2.0),
        )
    )

    selected = select_candidates(candidates, budget=2, strategy="reward_td")
    assert len(selected) == 2
    assert [item.candidate_id for item in selected] == ["t2", "t6"]
    assert candidate_recall(selected, candidates, gain_threshold=1.0) == 1.0


def test_uniform_selector_is_a_baseline_and_does_not_read_oracle_gain() -> None:
    candidates = (
        DecisionCandidate("late", 10, 0.0, 0.0, 100.0),
        DecisionCandidate("early", 1, 0.0, 0.0, 0.0),
    )
    selected = select_candidates(candidates, budget=1, strategy="uniform")
    assert [item.candidate_id for item in selected] == ["early"]
    relabeled = tuple(
        DecisionCandidate(item.candidate_id, item.time_step, 0.0, 0.0, -item.oracle_gain)
        for item in candidates
    )
    assert select_candidates(relabeled, budget=1, strategy="uniform") == tuple(
        item for item in relabeled if item.candidate_id == "early"
    )


def test_uniform_selector_spreads_probes_across_the_whole_timeline() -> None:
    candidates = tuple(
        DecisionCandidate(f"t{time_step}", time_step, 0.0, 0.0, 0.0)
        for time_step in range(0, 100, 10)
    )
    selected = select_candidates(candidates, budget=3, strategy="uniform")
    assert [item.time_step for item in selected] == [0, 50, 90]
    every = select_candidates(candidates, budget=len(candidates), strategy="uniform")
    assert [item.time_step for item in every] == list(range(0, 100, 10))
    assert select_candidates(candidates, budget=0, strategy="uniform") == ()


def test_uniform_selector_is_independent_of_input_order() -> None:
    candidates = tuple(
        DecisionCandidate(f"t{time_step}", time_step, 0.0, 0.0, 0.0)
        for time_step in (7, 3, 9, 1, 5)
    )
    forward = select_candidates(candidates, budget=2, strategy="uniform")
    backward = select_candidates(tuple(reversed(candidates)), budget=2, strategy="uniform")
    assert forward == backward
    assert [item.time_step for item in forward] == [1, 9]


def test_doubling_horizon_stop_on_rank_agreement_misses_the_delayed_payoff() -> None:
    """Pin the hazard any adaptive horizon rule must handle.

    Hold wins at H=1, 2, and 4, so a doubling schedule that stops when two
    consecutive horizons agree stops at H=2 with the wrong action. Commitment
    only wins once its delayed payoff outweighs the accumulated hold reward.
    """
    schedule = (1, 2, 4, 8)
    best = [best_branch(agent_count=1, horizon=horizon).actions for horizon in schedule]
    assert best == [(0,), (0,), (0,), (1,)]
    stop_index = next(
        index for index in range(1, len(schedule)) if best[index] == best[index - 1]
    )
    assert schedule[stop_index] == 2
    assert best[stop_index] != best[-1]
