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

HOLD = 0
COMMIT = 1
#: Consecutive commit steps before the delayed benefit is paid.
COMMIT_DELAY_STEPS = 3
#: Toy rewards are integer quarter points, so they stay exact in any backend.
REWARD_UNITS_PER_POINT = 4
_HOLD_REWARD = 1
_COMMIT_COST = -2
_MATURED_COMMIT_BENEFIT = 6
_JOINT_SYNERGY = 8


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
        return _evenly_spaced(candidates, budget)
    if strategy == "reward_td":
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


def evenly_spaced_indices(count: int, budget: int) -> tuple[int, ...]:
    """Pick ``budget`` of ``count`` ordered indices spread from first to last.

    Probe ``i`` takes index ``i * (count - 1) / (budget - 1)`` rounded half up,
    so both endpoints are always probed and indices never repeat.
    """

    if budget < 0 or count < 0:
        raise ValueError("count and budget must be non-negative")
    if budget >= count:
        return tuple(range(count))
    if budget == 0:
        return ()
    if budget == 1:
        return (0,)
    span = count - 1
    gaps = budget - 1
    return tuple((2 * index * span + gaps) // (2 * gaps) for index in range(budget))


def _evenly_spaced(
    candidates: tuple[DecisionCandidate, ...], budget: int
) -> tuple[DecisionCandidate, ...]:
    """Evenly spaced probes over the time-ordered candidates (input-order free)."""

    ordered = sorted(candidates, key=lambda item: (item.time_step, item.candidate_id))
    return tuple(ordered[index] for index in evenly_spaced_indices(len(ordered), budget))


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


def agent_step_rewards(actions: tuple[int, ...], commit_ages: tuple[int, ...]) -> tuple[int, ...]:
    """Per-agent reward, in quarter points, for one toy step.

    ``commit_ages`` counts each agent's consecutive commit steps before this
    one. Hold pays ``+1``. Commit costs ``-2`` and, once the agent has committed
    for ``COMMIT_DELAY_STEPS`` steps, also pays ``+6``. When two or more agents
    all hold matured commitments, a joint synergy of ``8`` is split evenly with
    any remainder going to the lowest agent indices.
    """

    if not actions or len(actions) != len(commit_ages):
        raise ValueError("actions and commit_ages must be non-empty and aligned")
    if any(action not in (HOLD, COMMIT) for action in actions):
        raise ValueError("toy actions must be 0 or 1")
    if any(isinstance(age, bool) or not isinstance(age, int) or age < 0 for age in commit_ages):
        raise ValueError("commit ages must be non-negative integers")
    rewards = [
        _HOLD_REWARD
        if action == HOLD
        else _COMMIT_COST + (_MATURED_COMMIT_BENEFIT if age >= COMMIT_DELAY_STEPS else 0)
        for action, age in zip(actions, commit_ages)
    ]
    count = len(actions)
    if count >= 2 and all(
        action == COMMIT and age >= COMMIT_DELAY_STEPS for action, age in zip(actions, commit_ages)
    ):
        share, remainder = divmod(_JOINT_SYNERGY, count)
        for index in range(count):
            rewards[index] += share + (1 if index < remainder else 0)
    return tuple(rewards)


def advance_commit_ages(actions: tuple[int, ...], commit_ages: tuple[int, ...]) -> tuple[int, ...]:
    """Commit extends an agent's streak; hold resets it."""

    return tuple(age + 1 if action == COMMIT else 0 for action, age in zip(actions, commit_ages))


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

    commit_ages = (0,) * len(actions)
    step_returns = []
    for _ in range(horizon):
        rewards = agent_step_rewards(actions, commit_ages)
        step_returns.append(sum(rewards) / REWARD_UNITS_PER_POINT)
        commit_ages = advance_commit_ages(actions, commit_ages)

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
    "COMMIT",
    "COMMIT_DELAY_STEPS",
    "HOLD",
    "REWARD_UNITS_PER_POINT",
    "BranchResult",
    "CandidateStrategy",
    "DecisionCandidate",
    "advance_commit_ages",
    "agent_step_rewards",
    "best_branch",
    "evenly_spaced_indices",
    "candidate_recall",
    "interaction_residual",
    "rollout_branch",
    "select_candidates",
]
