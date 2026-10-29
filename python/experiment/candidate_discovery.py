"""Phase 1 candidate-discovery benchmark over a synthetic causal world.

First algorithm experiment of the adaptive counterfactual search plan
(``docs/learning/work/issues/adaptive_counterfactual_search/README.md``). It
measures ``H1`` (high-value decision points are sparse) and ``H2`` (uniform,
reward, and TD signals find most of them cheaply) on a world whose ground truth
is known, using real branches through the reference session.

The world
---------
:class:`CausalDecisionWorld` is a single-agent timeline. The baseline policy
always waits. Four kinds of placed event:

- **hazard**: a cue is observable at step ``h``; waiting there costs
  ``hazard_penalty`` ``delay`` steps later, acting avoids it. Its consequence
  is visible in the baseline reward, after a delay.
- **opportunity**: acting at ``o`` pays ``opportunity_bonus`` ``delay`` steps
  later; waiting changes nothing. No cue, and nothing in the baseline reward
  reveals it.
- **decoy**: an exogenous reward spike ``decoy_reward`` that no action affects.
- **false cue**: the hazard cue without a hazard.

Signals and selectors
---------------------
- ``reward``: score ``|r_t - mean(r)|`` on the baseline.
- ``td``: score the TD surprise ``|r_t + gamma V(x_{t+1}) - V(x_t)|``, where
  ``V`` is a tabular value over the observable feature "steps since last cue",
  fit as the Monte Carlo return on *training* seeds and applied to held-out
  evaluation seeds.

A step is a *trigger* when its score exceeds ``median + 3 * MAD`` of that
seed's scores (strictly above the median when the MAD is zero). Each trigger,
strongest first, proposes the window ``[t - lookback, t]``, because a reward
event is a proposal source, not a decision point. A TD trigger also proposes
``t + 1`` first: ``delta_t`` contains ``V(x_{t+1})``, so when an observation
changes the outlook the surprise lands on the step *before* the agent can act
on it, and a purely backward window would miss that step. Whatever budget the
triggered windows leave is filled with evenly spaced probes over the remaining
steps, and the report records how many branches came from triggers. Low-score
ties therefore never fall back to step order.

- ``uniform``: evenly spaced probes only.
- ``td_uniform``: reserves a fixed share of the budget for uniform probes even
  when triggers would use all of it; the note's "never remove uniform
  exploration".
- ``oracle``: exhaustive branch gains, an upper bound only.

The oracle gain of step ``t`` is the return over ``horizon`` steps of a branch
that acts at ``t`` and then waits, minus the baseline return over the same
steps. No proposal selector reads it.

Events sit on a grid of slots with a seeded jitter inside each slot. Any two
events are more than ``delay + max(lookbacks)`` steps apart, so a lookback
window can only reach the event that caused its trigger, and the jitter keeps
event positions from aliasing with the uniform probe stride.

Evidence boundary: everything here is ``synthetic``. It characterizes the
selectors on a world built with these causal shapes; it says nothing about the
maintained runtime or any combat scenario.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from functools import lru_cache
from fractions import Fraction
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from python.experiment.contracts import content_digest
from python.experiment.counterfactual_toy import evenly_spaced_indices
from python.experiment.reference_session import ReferenceSession

WAIT = "wait"
ACT = "act"
OBSERVATION = "decision_belief_packet"
POLICY_REF = "synthetic_policy:always_wait"
AGENT = "agent_0"
EVENT_KINDS: tuple[str, ...] = ("hazard", "opportunity", "decoy", "false_cue")
DECISION_KINDS: tuple[str, ...] = ("hazard", "opportunity")


class BenchmarkError(ValueError):
    """Raised when a benchmark configuration is not admissible."""


@dataclass(frozen=True)
class CausalDecisionWorld:
    """Synthetic world with delayed hazards, silent opportunities, and decoys."""

    length: int
    hazards: tuple[int, ...]
    opportunities: tuple[int, ...]
    decoys: tuple[int, ...]
    false_cues: tuple[int, ...]
    delay: int
    base_reward: int = 1
    act_cost: int = -2
    hazard_penalty: int = -20
    opportunity_bonus: int = 20
    decoy_reward: int = 25
    scenario_ref: str = "synthetic:causal_decision"
    actions: tuple[str, ...] = (WAIT, ACT)
    evidence_label: str = "synthetic"
    reward_units_per_point: int = 1

    def __post_init__(self) -> None:
        if self.length < 2 or self.delay < 1:
            raise BenchmarkError("length must be >= 2 and delay >= 1")
        seen: set[int] = set()
        for kind in EVENT_KINDS:
            steps = self.events(kind)
            if list(steps) != sorted(set(steps)) or any(
                not 0 <= step < self.length - self.delay for step in steps
            ):
                raise BenchmarkError(f"{kind} steps must be sorted, unique, and leave room for the delay")
            if seen & set(steps):
                raise BenchmarkError("event steps must be distinct across kinds")
            seen |= set(steps)

    def events(self, kind: str) -> tuple[int, ...]:
        return {
            "hazard": self.hazards,
            "opportunity": self.opportunities,
            "decoy": self.decoys,
            "false_cue": self.false_cues,
        }[kind]

    @property
    def cue_steps(self) -> frozenset[int]:
        return frozenset(self.hazards) | frozenset(self.false_cues)

    def config_payload(self) -> Mapping[str, Any]:
        payload: dict[str, Any] = {kind: list(self.events(kind)) for kind in EVENT_KINDS}
        payload.update(
            length=self.length,
            delay=self.delay,
            base_reward=self.base_reward,
            act_cost=self.act_cost,
            hazard_penalty=self.hazard_penalty,
            opportunity_bonus=self.opportunity_bonus,
            decoy_reward=self.decoy_reward,
        )
        return payload

    def initial_state(self, seed: int, agent_count: int) -> tuple[int, tuple[tuple[int, int], ...]]:
        if agent_count != 1:
            raise BenchmarkError("the causal-decision world is single-agent")
        return (0, ())

    def encode_state(self, state: tuple[int, tuple[tuple[int, int], ...]]) -> Mapping[str, Any]:
        step, scheduled = state
        return {"step": step, "scheduled": [list(item) for item in scheduled]}

    def step(
        self, state: tuple[int, tuple[tuple[int, int], ...]], actions: tuple[str, ...]
    ) -> tuple[tuple[int, tuple[tuple[int, int], ...]], tuple[int, ...], bool]:
        step, scheduled = state
        (action,) = actions
        reward = self.base_reward if action == WAIT else self.act_cost
        if step in self.decoys:
            reward += self.decoy_reward
        reward += sum(amount for due, amount in scheduled if due == step)
        pending = [item for item in scheduled if item[0] > step]
        if step in self.hazards and action == WAIT:
            pending.append((step + self.delay, self.hazard_penalty))
        if step in self.opportunities and action == ACT:
            pending.append((step + self.delay, self.opportunity_bonus))
        return (step + 1, tuple(sorted(pending))), (reward,), step + 1 >= self.length


@dataclass(frozen=True)
class BenchmarkConfig:
    """Fixed protocol for one run; every field is part of the report identity."""

    train_seeds: tuple[int, ...] = tuple(range(101, 117))
    eval_seeds: tuple[int, ...] = tuple(range(201, 225))
    length: int = 288
    delay: int = 4
    hazard_count: int = 3
    opportunity_count: int = 2
    decoy_count: int = 4
    false_cue_count: int = 2
    decoy_reward: int = 25
    horizon: int = 8
    lookbacks: tuple[int, ...] = (0, 4, 6)
    budgets: tuple[int, ...] = (4, 8, 16, 32, 64)
    uniform_share_milli: int = 250
    gain_threshold: int = 5
    gamma: Fraction = Fraction(9, 10)
    jitter: int = 7

    def __post_init__(self) -> None:
        for name in ("train_seeds", "eval_seeds"):
            seeds = getattr(self, name)
            if not seeds or list(seeds) != sorted(set(seeds)):
                raise BenchmarkError(f"{name} must be sorted and unique")
        if set(self.train_seeds) & set(self.eval_seeds):
            raise BenchmarkError("training and evaluation seeds must be disjoint")
        if self.horizon <= self.delay:
            raise BenchmarkError("the evaluation horizon must cover the consequence delay")
        if not self.budgets or any(budget < 1 for budget in self.budgets):
            raise BenchmarkError("budgets must be positive")
        if not 0 <= self.uniform_share_milli <= 1000:
            raise BenchmarkError("uniform_share_milli must be within [0, 1000]")
        if not 0 < self.gamma < 1:
            raise BenchmarkError("gamma must be in (0, 1)")
        if self.jitter < 0:
            raise BenchmarkError("jitter must be non-negative")
        if len(self.slots()) < self.event_count:
            raise BenchmarkError("not enough non-overlapping slots for the requested events")

    @property
    def event_count(self) -> int:
        return self.hazard_count + self.opportunity_count + self.decoy_count + self.false_cue_count

    @property
    def spacing(self) -> int:
        return self.delay + max(self.lookbacks) + 2 + self.jitter

    def slots(self) -> tuple[int, ...]:
        last = self.length - self.horizon - self.delay - self.jitter
        return tuple(range(self.spacing, last, self.spacing))

    def to_payload(self) -> dict[str, Any]:
        return {
            "train_seeds": list(self.train_seeds),
            "eval_seeds": list(self.eval_seeds),
            "length": self.length,
            "delay": self.delay,
            "hazard_count": self.hazard_count,
            "opportunity_count": self.opportunity_count,
            "decoy_count": self.decoy_count,
            "false_cue_count": self.false_cue_count,
            "decoy_reward": self.decoy_reward,
            "horizon": self.horizon,
            "lookbacks": list(self.lookbacks),
            "budgets": list(self.budgets),
            "uniform_share_milli": self.uniform_share_milli,
            "gain_threshold": self.gain_threshold,
            "gamma": [self.gamma.numerator, self.gamma.denominator],
            "jitter": self.jitter,
        }


def make_world(config: BenchmarkConfig, seed: int) -> CausalDecisionWorld:
    """Place every event on its own jittered slot, deterministically from ``seed``."""

    rng = random.Random(seed)
    picks = [slot + rng.randint(0, config.jitter) for slot in rng.sample(list(config.slots()), config.event_count)]
    counts = (config.hazard_count, config.opportunity_count, config.decoy_count, config.false_cue_count)
    groups = []
    start = 0
    for count in counts:
        groups.append(tuple(sorted(picks[start : start + count])))
        start += count
    hazards, opportunities, decoys, false_cues = groups
    return CausalDecisionWorld(
        length=config.length,
        hazards=hazards,
        opportunities=opportunities,
        decoys=decoys,
        false_cues=false_cues,
        delay=config.delay,
        decoy_reward=config.decoy_reward,
    )


def _cue_feature(world: CausalDecisionWorld, step: int) -> int:
    """Observable feature: steps since the last cue, capped at ``delay + 1``."""

    for back in range(world.delay + 1):
        if step - back in world.cue_steps:
            return back
    return world.delay + 1


def _rollout_baseline(world: CausalDecisionWorld, seed: int) -> tuple[ReferenceSession, list]:
    session = ReferenceSession.open(
        session_id=f"causal_seed_{seed}",
        seed=seed,
        agent_ids=(AGENT,),
        policy_ref=POLICY_REF,
        world=world,
    )
    heads = [session.head(session.baseline)]
    while not session.is_terminated(session.baseline):
        session.step(session.baseline, {AGENT: WAIT}, observation_provenance=OBSERVATION)
        heads.append(session.head(session.baseline))
    return session, heads


def _baseline_rewards(session: ReferenceSession) -> list[int]:
    return [item.rewards[0][1] for item in session.trace(session.baseline).transitions]


@lru_cache(maxsize=8)
def fit_value(config: BenchmarkConfig) -> Mapping[int, Fraction]:
    """Monte Carlo value of each cue feature over the training seeds' baselines.

    Cached per (frozen, hashable) config; callers must not mutate the result.
    """

    totals: dict[int, Fraction] = {}
    counts: dict[int, int] = {}
    for seed in config.train_seeds:
        world = make_world(config, seed)
        session, _ = _rollout_baseline(world, seed)
        rewards = _baseline_rewards(session)
        ret = Fraction(0)
        for step in range(len(rewards) - 1, -1, -1):
            ret = rewards[step] + config.gamma * ret
            feature = _cue_feature(world, step)
            totals[feature] = totals.get(feature, Fraction(0)) + ret
            counts[feature] = counts.get(feature, 0) + 1
    return MappingProxyType({feature: totals[feature] / counts[feature] for feature in totals})


@dataclass(frozen=True)
class StepSignals:
    """Per-step baseline signals plus the hidden oracle gain."""

    step: int
    reward: int
    td_surprise_milli: int
    oracle_gain: int
    kind: str


def measure_signals(
    world: CausalDecisionWorld, config: BenchmarkConfig, seed: int, value: Mapping[int, Fraction]
) -> tuple[ReferenceSession, tuple[StepSignals, ...]]:
    """Baseline rollout, TD surprise from the training value, one branch per step."""

    session, heads = _rollout_baseline(world, seed)
    rewards = _baseline_rewards(session)
    default = sum(value.values(), Fraction(0)) / len(value)
    kinds = {step: kind for kind in EVENT_KINDS for step in world.events(kind)}
    signals = []
    for step in range(len(rewards) - config.horizon):
        v_now = value.get(_cue_feature(world, step), default)
        v_next = value.get(_cue_feature(world, step + 1), default)
        surprise = abs(rewards[step] + config.gamma * v_next - v_now)
        branch = session.fork(
            session.baseline, heads[step], intervention={AGENT: ACT}, label=f"act_at_{step}"
        )
        branch_total = 0
        for offset in range(config.horizon):
            transition = session.step(
                branch, {AGENT: ACT if offset == 0 else WAIT}, observation_provenance=OBSERVATION
            )
            branch_total += transition.rewards[0][1]
        gain = branch_total - sum(rewards[step : step + config.horizon])
        signals.append(
            StepSignals(step, rewards[step], round(surprise * 1000), gain, kinds.get(step, "inert"))
        )
    return session, tuple(signals)


def _median(values: Sequence[Fraction]) -> Fraction:
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def triggers(scores: Mapping[int, Fraction]) -> list[int]:
    """Steps scoring above ``median + 3 * MAD``, strongest first."""

    values = list(scores.values())
    median = _median(values)
    mad = _median([abs(value - median) for value in values])
    threshold = median + 3 * mad
    hits = [step for step, score in scores.items() if score > threshold]
    return sorted(hits, key=lambda step: (-scores[step], step))


def _expand(
    trigger_steps: Sequence[int], lookback: int, budget: int, exclude: set[int], *, lead: int
) -> list[int]:
    chosen: list[int] = []
    for trigger in trigger_steps:
        for step in range(trigger + lead, trigger - lookback - 1, -1):
            if len(chosen) == budget:
                return chosen
            if step >= 0 and step not in chosen and step not in exclude:
                chosen.append(step)
    return chosen


def _fill_uniform(steps: Sequence[int], taken: set[int], count: int) -> set[int]:
    free = [step for step in steps if step not in taken]
    return {free[index] for index in evenly_spaced_indices(len(free), count)}


def _scores(selector: str, signals: Sequence[StepSignals]) -> dict[int, Fraction]:
    if selector == "reward":
        mean = Fraction(sum(item.reward for item in signals), len(signals))
        return {item.step: abs(item.reward - mean) for item in signals}
    return {item.step: Fraction(item.td_surprise_milli) for item in signals}


@dataclass(frozen=True)
class Selection:
    steps: tuple[int, ...]
    triggered: int


def select(
    selector: str, signals: Sequence[StepSignals], budget: int, lookback: int, uniform_share_milli: int
) -> Selection:
    """Pick candidate branch steps. Only ``oracle`` reads the oracle gain."""

    if budget < 1:
        raise BenchmarkError("budget must be positive")
    steps = [item.step for item in signals]
    if selector == "uniform":
        return Selection(tuple(sorted(_fill_uniform(steps, set(), budget))), 0)
    if selector == "oracle":
        ranked = sorted(signals, key=lambda item: (-item.oracle_gain, item.step))
        return Selection(tuple(sorted(item.step for item in ranked[:budget])), 0)
    if selector not in ("reward", "td", "td_uniform"):
        raise BenchmarkError(f"unknown selector {selector!r}")
    signal = "td" if selector == "td_uniform" else selector
    trigger_steps = triggers(_scores(signal, signals))
    reserved: set[int] = set()
    if selector == "td_uniform":
        reserved = _fill_uniform(steps, set(), (budget * uniform_share_milli) // 1000)
    known = set(steps)
    proposed = [
        step
        for step in _expand(
            trigger_steps, lookback, budget - len(reserved), reserved, lead=1 if signal == "td" else 0
        )
        if step in known
    ]
    chosen = reserved | set(proposed)
    chosen |= _fill_uniform(steps, chosen, budget - len(chosen))
    return Selection(tuple(sorted(chosen)), len(proposed))


def selector_grid(config: BenchmarkConfig) -> tuple[tuple[str, int], ...]:
    """Every (selector, lookback) pair; lookback is irrelevant for uniform/oracle."""

    grid: list[tuple[str, int]] = [("uniform", 0), ("oracle", 0)]
    for name in ("reward", "td", "td_uniform"):
        grid.extend((name, lookback) for lookback in config.lookbacks)
    return tuple(grid)


def _recall(chosen: set[int], targets: Sequence[int]) -> int | None:
    if not targets:
        return None
    return (1000 * len(chosen & set(targets))) // len(targets)


def evaluate(config: BenchmarkConfig | None = None) -> dict[str, Any]:
    """Run the benchmark on held-out seeds; aggregate per selector and budget."""

    config = BenchmarkConfig() if config is None else config
    value = fit_value(config)
    rows: list[dict[str, Any]] = []
    seed_rows: list[dict[str, Any]] = []
    for seed in config.eval_seeds:
        world = make_world(config, seed)
        session, signals = measure_signals(world, config, seed, value)
        gains = {item.step: item.oracle_gain for item in signals}
        important = [step for step, gain in gains.items() if gain >= config.gain_threshold]
        by_kind = {
            kind: [item.step for item in signals if item.kind == kind and item.step in important]
            for kind in DECISION_KINDS
        }
        oracle_best = max(gains.values())
        seed_rows.append(
            {
                "seed": seed,
                "events": {kind: list(world.events(kind)) for kind in EVENT_KINDS},
                "important_steps": important,
                "decision_density_milli": (1000 * len(important)) // len(signals),
                "manifest_digest": session.manifest().digest,
            }
        )
        for budget in config.budgets:
            for selector, lookback in selector_grid(config):
                selection = select(selector, signals, budget, lookback, config.uniform_share_milli)
                chosen = set(selection.steps)
                best = max(gains[step] for step in chosen)
                rows.append(
                    {
                        "seed": seed,
                        "selector": selector,
                        "lookback": lookback,
                        "budget": budget,
                        "branches": len(chosen),
                        "triggered": selection.triggered,
                        "recall_milli": _recall(chosen, important),
                        "hazard_recall_milli": _recall(chosen, by_kind["hazard"]),
                        "opportunity_recall_milli": _recall(chosen, by_kind["opportunity"]),
                        "regret": oracle_best - best,
                    }
                )
    summary = []
    for budget in config.budgets:
        for selector, lookback in selector_grid(config):
            group = [
                r for r in rows if r["selector"] == selector and r["lookback"] == lookback and r["budget"] == budget
            ]

            def mean_milli(key: str) -> int:
                values = [r[key] for r in group if r[key] is not None]
                return sum(values) // len(values) if values else -1

            summary.append(
                {
                    "selector": selector,
                    "lookback": lookback,
                    "budget": budget,
                    "mean_recall_milli": mean_milli("recall_milli"),
                    "mean_hazard_recall_milli": mean_milli("hazard_recall_milli"),
                    "mean_opportunity_recall_milli": mean_milli("opportunity_recall_milli"),
                    "total_regret": sum(r["regret"] for r in group),
                    "zero_regret_seeds": sum(1 for r in group if r["regret"] == 0),
                    "mean_triggered_milli": (1000 * sum(r["triggered"] for r in group)) // len(group),
                    "branch_steps": max(r["branches"] for r in group) * config.horizon,
                }
            )
    report = {
        "evidence_label": "synthetic",
        "config": config.to_payload(),
        "value_by_cue_feature_milli": {str(k): round(v * 1000) for k, v in sorted(value.items())},
        "seeds": seed_rows,
        "summary": summary,
    }
    report["report_digest"] = content_digest("experiment.candidate-discovery-report", report)
    return report


__all__ = [
    "ACT",
    "DECISION_KINDS",
    "EVENT_KINDS",
    "WAIT",
    "BenchmarkConfig",
    "BenchmarkError",
    "CausalDecisionWorld",
    "Selection",
    "evaluate",
    "fit_value",
    "make_world",
    "measure_signals",
    "select",
    "selector_grid",
    "triggers",
]
