"""Deterministic toy primitives for the adaptive counterfactual canary.

This module deliberately has no runtime, gym, or training dependencies.  It
checks the mathematical shape of the first experiment before a maintained
snapshot/restore contract exists in the simulation facade.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Literal


CandidateStrategy = Literal["uniform", "reward_td", "oracle"]


@dataclass(frozen=True)
class DecisionCandidate:
    """A candidate point with observable proposal signals and a hidden label."""

    candidate_id: str
    time_step: int
    reward_delta: float
    td_surprise: float
    oracle_gain: float

    def __post_init__(self) -> None:
        if not self.candidate_id.strip():
            raise ValueError("candidate_id is required")
        if self.time_step < 0:
            raise ValueError("time_step must be non-negative")
        for name, value in (
            ("reward_delta", self.reward_delta),
            ("td_surprise", self.td_surprise),
            ("oracle_gain", self.oracle_gain),
        ):
            if not isinstance(value, (int, float)):
                raise TypeError(f"{name} must be numeric")


def select_candidates(
    candidates: tuple[DecisionCandidate, ...],
    budget: int,
    strategy: CandidateStrategy,
) -> tuple[DecisionCandidate, ...]:
    """Select at most ``budget`` candidates with a deterministic tie break.

    ``oracle`` is reserved for evaluation.  The proposed ``uniform`` and
    ``reward_td`` selectors use only fields that would be available on a
    baseline rollout; ``oracle_gain`` is never read by those paths.
    """

    if budget < 0:
        raise ValueError("budget must be non-negative")
    if strategy == "uniform":
        key = lambda item: (item.time_step, item.candidate_id)
    elif strategy == "reward_td":
        key = lambda item: (
            -(abs(item.reward_delta) + abs(item.td_surprise)),
            item.time_step,
            item.candidate_id,
        )
    elif strategy == "oracle":
        key = lambda item: (-item.oracle_gain, item.time_step, item.candidate_id)
    else:
        raise ValueError(f"unknown candidate strategy: {strategy!r}")
    return tuple(sorted(candidates, key=key)[:budget])


def candidate_recall(
    selected: tuple[DecisionCandidate, ...],
    candidates: tuple[DecisionCandidate, ...],
    gain_threshold: float,
) -> float:
    """Return recall over candidates whose hidden gain passes the threshold."""

    important = {
        item.candidate_id for item in candidates if item.oracle_gain >= gain_threshold
    }
    if not important:
        return 1.0
    return len(important & {item.candidate_id for item in selected}) / len(important)


@dataclass(frozen=True)
class BranchResult:
    actions: tuple[int, ...]
    horizon: int
    step_returns: tuple[float, ...]
    discounted_return: float


def rollout_branch(
    actions: tuple[int, ...],
    horizon: int,
    gamma: float = 1.0,
) -> BranchResult:
    """Evaluate a small deterministic joint-action branch.

    Action ``0`` is a safe hold and action ``1`` is a delayed commitment.  A
    commitment pays an immediate cost and a later benefit.  Joint commitment
    adds a delayed synergy term, making the interaction residual measurable.
    """

    if not actions:
        raise ValueError("at least one agent action is required")
    if any(action not in (0, 1) for action in actions):
        raise ValueError("toy actions must be 0 or 1")
    if horizon <= 0:
        raise ValueError("horizon must be positive")
    if not 0.0 < gamma <= 1.0:
        raise ValueError("gamma must be in (0, 1]")

    committed = sum(actions)
    joint_commitment = int(len(actions) >= 2 and committed == len(actions))
    step_returns = []
    for step in range(horizon):
        immediate = 0.25 * (len(actions) - committed) - 0.5 * committed
        delayed = 1.5 * float(committed) if step >= 3 else 0.0
        synergy = 2.0 * joint_commitment if step >= 3 else 0.0
        step_returns.append(immediate + delayed + synergy)

    discounted_return = sum(gamma**step * value for step, value in enumerate(step_returns))
    return BranchResult(
        actions=actions,
        horizon=horizon,
        step_returns=tuple(step_returns),
        discounted_return=discounted_return,
    )


def best_branch(agent_count: int, horizon: int, gamma: float = 1.0) -> BranchResult:
    """Return the best branch under the toy model with stable tie breaking."""

    if agent_count <= 0:
        raise ValueError("agent_count must be positive")
    branches = (
        rollout_branch(tuple(actions), horizon, gamma)
        for actions in product((0, 1), repeat=agent_count)
    )
    return max(branches, key=lambda result: (result.discounted_return, result.actions))


def interaction_residual(horizon: int, gamma: float = 1.0) -> float:
    """Measure the pairwise value term with a second finite difference."""

    q00 = rollout_branch((0, 0), horizon, gamma).discounted_return
    q01 = rollout_branch((0, 1), horizon, gamma).discounted_return
    q10 = rollout_branch((1, 0), horizon, gamma).discounted_return
    q11 = rollout_branch((1, 1), horizon, gamma).discounted_return
    return q11 - q10 - q01 + q00


__all__ = [
    "BranchResult",
    "CandidateStrategy",
    "DecisionCandidate",
    "best_branch",
    "candidate_recall",
    "interaction_residual",
    "rollout_branch",
    "select_candidates",
]
