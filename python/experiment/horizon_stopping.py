"""Adaptive horizon stopping benchmark (E1, hypothesis ``H4``).

Part of the adaptive counterfactual search plan
(``docs/learning/work/issues/adaptive_counterfactual_search/README.md``). It
asks how far a branch must be rolled before its conclusion can be trusted,
and whether a stopping rule on the doubling schedule ``1, 2, 4, 8, ...`` can
answer that cheaply. The value of action ``a`` at horizon ``H`` is

    Q_H(s, a) = sum_{k<H} gamma^k r_{t+k} + gamma^H V(s_{t+H}),

computed from real branches: the probe forks the reference session at the
decision snapshot once per action, then rolls a fixed continuation policy
(``hold``) and reads the rewards off the branch transitions.

The world
---------
:class:`HorizonWorld` is a single-agent timeline. ``hold`` pays ``+1`` every
step. At a placed :class:`Decision`, ``commit`` pays ``-cost`` now and
schedules ``payoff`` exactly ``delay`` steps later (on the decision step itself
when ``delay == 0``). ``commit`` anywhere else pays ``0`` and does nothing.
With the ``hold`` continuation the long-run gain of committing is
``gamma^delay * payoff - (1 + cost)``, so each instance is one of

- ``delayed_gain``: the gain is positive and ``delay >= 1``. Under ``V = 0``
  hold wins every horizon ``H <= delay`` and commit wins every ``H > delay``.
  This is the pinned hazard of :mod:`python.experiment.counterfactual_toy`.
- ``immediate_gain``: positive gain with ``delay == 0``; commit wins at every
  horizon.
- ``no_gain``: the gain is not positive; under ``V = 0`` hold wins at every
  horizon (an exact tie counts both actions as correct).

``cost``, ``payoff``, and ``delay`` are drawn independently and uniformly per
decision from fixed integer ranges, so the class mix is a property of those
ranges, not something the benchmark measures about the world class.

Bootstrap values
----------------
- ``zero``: ``V = 0``.
- ``fitted``: tabular over the observable feature "steps until the pending
  payoff lands" (``None`` when nothing is pending), fit as the Monte Carlo
  return over ``fit_window`` steps of the ``hold`` continuation on *training*
  seeds: the hold baseline plus one commit branch per decision. It sees how
  long a payoff is pending, never how large it is, so it predicts the training
  mean payoff for that remaining delay.
- ``oracle``: the exact ``hold``-continuation value to the episode end. With it
  ``Q_H`` is the same at every horizon; it is an upper bound only.

Stopping rules
--------------
At each schedule horizon after the first, compare ``Q_H`` with the previous
horizon's ``Q``:

- ``rank_agreement``: stop when the argmax is unchanged.
- ``value_gap@m``: stop when the argmax is unchanged and the best-minus-second
  gap at the new horizon exceeds ``m``.
- ``value_stability@t``: stop when the new argmax action's ``Q`` moved by less
  than ``t``.
- ``fixed_max``: never stop early.

A rule that never stops takes the cap's argmax. Correctness is measured
against the oracle value's best actions (any tied best counts). A rule that
stops at ``H`` spends ``len(actions) * H`` branch steps; the benchmark replays
rules over one cap-length probe per decision point, and a test pins that a
live adaptive run spends exactly that.

Evidence boundary: everything here is ``synthetic``. It characterizes stopping
rules on a world built with these delayed-payoff shapes; it says nothing about
the maintained runtime or any combat scenario.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from fractions import Fraction
from types import MappingProxyType
from typing import Any, Callable, Hashable, Mapping, Sequence

from python.experiment.contracts import BranchRef
from python.experiment.contracts import SnapshotRef
from python.experiment.contracts import content_digest
from python.experiment.reference_session import ReferenceSession
from python.experiment.reference_session import ReferenceWorld

HOLD = "hold"
COMMIT = "commit"
HOLD_REWARD = 1
OBSERVATION = "decision_belief_packet"
POLICY_REF = "synthetic_policy:always_hold"
AGENT = "agent_0"
CONTINUATIONS: tuple[str, ...] = ("hold", "repeat")
RULE_KINDS: tuple[str, ...] = ("rank_agreement", "value_gap", "value_stability", "fixed_max")
VALUE_VARIANTS: tuple[str, ...] = ("zero", "fitted", "oracle")
INSTANCE_KINDS: tuple[str, ...] = ("delayed_gain", "immediate_gain", "no_gain")

ValueFn = Callable[[Hashable], Fraction]


class HorizonError(ValueError):
    """Raised when a horizon-stopping configuration or operation is not admissible."""


def _require_int(value: Any, name: str, *, minimum: int = 0) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise HorizonError(f"{name} must be an integer >= {minimum}, got {value!r}")


def _require_exact(value: Any, name: str) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (int, Fraction)):
        raise HorizonError(f"{name} must be an int or Fraction, got {value!r}")
    return Fraction(value)


def _pair(value: Fraction) -> list[int]:
    return [value.numerator, value.denominator]


def _milli(value: Fraction) -> int:
    return round(value * 1000)


# --- world ---------------------------------------------------------------------


@dataclass(frozen=True)
class Decision:
    """A step where ``commit`` costs ``cost`` now and pays ``payoff`` after ``delay``."""

    step: int
    cost: int
    payoff: int
    delay: int

    def __post_init__(self) -> None:
        for name in ("step", "cost", "payoff", "delay"):
            _require_int(getattr(self, name), name)

    @property
    def due(self) -> int:
        return self.step + self.delay


@dataclass(frozen=True)
class HorizonWorld:
    """Hold pays now; commit at a decision pays later. State: ``(step, pending)``."""

    length: int
    decisions: tuple[Decision, ...]
    scenario_ref: str = "synthetic:horizon_stopping"
    actions: tuple[str, ...] = (HOLD, COMMIT)
    evidence_label: str = "synthetic"
    reward_units_per_point: int = 1

    def __post_init__(self) -> None:
        _require_int(self.length, "length", minimum=1)
        if not all(isinstance(item, Decision) for item in self.decisions):
            raise HorizonError("decisions must be Decision values")
        for index, item in enumerate(self.decisions):
            if item.due >= self.length:
                raise HorizonError("every payoff must land before the episode ends")
            following = self.decisions[index + 1 :]
            if following and following[0].step <= item.step:
                raise HorizonError("decision steps must be strictly increasing")
            if following and item.due >= following[0].step:
                raise HorizonError("a payoff must land before the next decision")

    def decision_at(self, step: int) -> Decision | None:
        for item in self.decisions:
            if item.step == step:
                return item
        return None

    def config_payload(self) -> Mapping[str, Any]:
        return {
            "length": self.length,
            "decisions": [[d.step, d.cost, d.payoff, d.delay] for d in self.decisions],
            "hold_reward": HOLD_REWARD,
        }

    def initial_state(self, seed: int, agent_count: int) -> tuple[int, tuple[tuple[int, int], ...]]:
        if agent_count != 1:
            raise HorizonError("the horizon world is single-agent")
        return (0, ())

    def encode_state(self, state: tuple[int, tuple[tuple[int, int], ...]]) -> Mapping[str, Any]:
        step, pending = state
        return {"step": step, "pending": [list(item) for item in pending]}

    def step(
        self, state: tuple[int, tuple[tuple[int, int], ...]], actions: tuple[str, ...]
    ) -> tuple[tuple[int, tuple[tuple[int, int], ...]], tuple[int, ...], bool]:
        step, pending = state
        (action,) = actions
        if action not in self.actions:
            raise HorizonError(f"unknown action {action!r}")
        scheduled = list(pending)
        reward = HOLD_REWARD
        if action == COMMIT:
            decision = self.decision_at(step)
            reward = 0
            if decision is not None:
                reward = -decision.cost
                scheduled.append((decision.due, decision.payoff))
        reward += sum(amount for due, amount in scheduled if due == step)
        remaining = tuple(sorted(item for item in scheduled if item[0] > step))
        return (step + 1, remaining), (reward,), step + 1 >= self.length


def pending_feature(state: tuple[int, tuple[tuple[int, int], ...]]) -> int | None:
    """Observable feature: steps until the next pending payoff lands, else ``None``.

    ``0`` means it lands on the next step taken from this state.
    """

    step, pending = state
    if not pending:
        return None
    return min(due for due, _ in pending) - step


# --- configuration ---------------------------------------------------------------


def _check_range(value: Any, name: str) -> None:
    if (
        not isinstance(value, tuple)
        or len(value) != 2
        or any(isinstance(item, bool) or not isinstance(item, int) for item in value)
        or not 0 <= value[0] <= value[1]
    ):
        raise HorizonError(f"{name} must be a (low, high) pair of integers with 0 <= low <= high")


@dataclass(frozen=True)
class HorizonConfig:
    """Fixed protocol for one run; every field is part of the report identity."""

    train_seeds: tuple[int, ...] = tuple(range(301, 317))
    eval_seeds: tuple[int, ...] = tuple(range(401, 433))
    decisions_per_seed: int = 8
    spacing: int = 16
    delay_range: tuple[int, int] = (0, 12)
    cost_range: tuple[int, int] = (0, 3)
    payoff_range: tuple[int, int] = (0, 24)
    gamma: Fraction = Fraction(9, 10)
    schedule: tuple[int, ...] = (1, 2, 4, 8, 16)
    margins: tuple[Fraction, ...] = (Fraction(1), Fraction(2), Fraction(4), Fraction(8))
    tolerances: tuple[Fraction, ...] = (Fraction(1, 4), Fraction(1, 2), Fraction(1), Fraction(2))
    fit_window: int = 64

    def __post_init__(self) -> None:
        for name in ("train_seeds", "eval_seeds"):
            seeds = getattr(self, name)
            if (
                not isinstance(seeds, tuple)
                or not seeds
                or any(isinstance(seed, bool) or not isinstance(seed, int) for seed in seeds)
                or list(seeds) != sorted(set(seeds))
            ):
                raise HorizonError(f"{name} must be a non-empty sorted tuple of unique integers")
        if set(self.train_seeds) & set(self.eval_seeds):
            raise HorizonError("training and evaluation seeds must be disjoint")
        _require_int(self.decisions_per_seed, "decisions_per_seed", minimum=1)
        for name in ("delay_range", "cost_range", "payoff_range"):
            _check_range(getattr(self, name), name)
        _require_int(self.spacing, "spacing", minimum=1)
        if self.spacing <= self.delay_range[1]:
            raise HorizonError("spacing must exceed the largest delay so payoffs land before the next decision")
        if not isinstance(self.gamma, Fraction) or not 0 < self.gamma < 1:
            raise HorizonError("gamma must be a Fraction in (0, 1)")
        if (
            not isinstance(self.schedule, tuple)
            or len(self.schedule) < 2
            or any(isinstance(h, bool) or not isinstance(h, int) for h in self.schedule)
            or self.schedule[0] < 1
            or any(later <= earlier for earlier, later in zip(self.schedule, self.schedule[1:]))
        ):
            raise HorizonError("schedule must be at least two strictly increasing positive integers")
        for name, strict in (("margins", False), ("tolerances", True)):
            values = getattr(self, name)
            if not isinstance(values, tuple) or not values:
                raise HorizonError(f"{name} must be a non-empty tuple")
            for value in values:
                exact = _require_exact(value, name)
                if exact < 0 or (strict and exact == 0):
                    raise HorizonError(f"{name} must be {'positive' if strict else 'non-negative'}")
        _require_int(self.fit_window, "fit_window", minimum=1)
        if self.fit_window < self.delay_range[1]:
            raise HorizonError("fit_window must cover the largest delay")

    @property
    def cap(self) -> int:
        return self.schedule[-1]

    @property
    def length(self) -> int:
        """Room for the cap probe and for every training Monte Carlo window."""

        last = (self.decisions_per_seed - 1) * self.spacing
        return last + self.delay_range[1] + max(self.fit_window, self.cap) + 1

    def to_payload(self) -> dict[str, Any]:
        return {
            "train_seeds": list(self.train_seeds),
            "eval_seeds": list(self.eval_seeds),
            "decisions_per_seed": self.decisions_per_seed,
            "spacing": self.spacing,
            "delay_range": list(self.delay_range),
            "cost_range": list(self.cost_range),
            "payoff_range": list(self.payoff_range),
            "gamma": _pair(self.gamma),
            "schedule": list(self.schedule),
            "margins": [_pair(Fraction(m)) for m in self.margins],
            "tolerances": [_pair(Fraction(t)) for t in self.tolerances],
            "fit_window": self.fit_window,
            "length": self.length,
        }


def make_world(config: HorizonConfig, seed: int) -> HorizonWorld:
    """Draw every decision's ``(cost, payoff, delay)`` deterministically from ``seed``."""

    rng = random.Random(seed)
    decisions = []
    for index in range(config.decisions_per_seed):
        delay = rng.randint(*config.delay_range)
        cost = rng.randint(*config.cost_range)
        payoff = rng.randint(*config.payoff_range)
        decisions.append(Decision(step=index * config.spacing, cost=cost, payoff=payoff, delay=delay))
    return HorizonWorld(length=config.length, decisions=tuple(decisions))


# --- sessions, probes, and values ---------------------------------------------------


@dataclass(frozen=True)
class Baseline:
    """The always-hold rollout: snapshots, mirrored states, and rewards per step."""

    session: ReferenceSession
    heads: tuple[SnapshotRef, ...]
    states: tuple[Hashable, ...]
    rewards: tuple[int, ...]


def rollout_baseline(world: ReferenceWorld, seed: int, *, until: int | None = None) -> Baseline:
    """Roll the hold baseline to termination (or to step ``until``)."""

    session = ReferenceSession.open(
        session_id=f"horizon_seed_{seed}", seed=seed, agent_ids=(AGENT,), policy_ref=POLICY_REF, world=world
    )
    state = world.initial_state(seed, 1)
    heads, states, rewards = [session.head(session.baseline)], [state], []
    while not session.is_terminated(session.baseline) and (until is None or len(rewards) < until):
        transition = session.step(session.baseline, {AGENT: HOLD}, observation_provenance=OBSERVATION)
        state, (reward,), _ = world.step(state, (HOLD,))
        if transition.rewards[0][1] != reward:
            raise HorizonError("mirrored world state diverged from the session")
        heads.append(session.head(session.baseline))
        states.append(state)
        rewards.append(reward)
    return Baseline(session, tuple(heads), tuple(states), tuple(rewards))


class HorizonProbe:
    """One branch per action from a decision snapshot, extended on demand.

    The probe mirrors the pure world step alongside each session step so that
    the bootstrap value can read the leaf state; a reward or termination
    mismatch fails closed.
    """

    def __init__(
        self,
        session: ReferenceSession,
        parent: BranchRef,
        snapshot: SnapshotRef,
        state: Hashable,
        *,
        continuation: str,
        gamma: Fraction,
        label: str,
    ) -> None:
        if continuation not in CONTINUATIONS:
            raise HorizonError(f"continuation must be one of {CONTINUATIONS}")
        if not isinstance(gamma, Fraction) or not 0 < gamma <= 1:
            raise HorizonError("gamma must be a Fraction in (0, 1]")
        if len(session.spec.agent_ids) != 1:
            raise HorizonError("the horizon probe is single-agent")
        self.session = session
        self.gamma = gamma
        self.continuation = continuation
        self.actions: tuple[str, ...] = tuple(session.world.actions)
        self._agent = session.spec.agent_ids[0]
        self._branches = {
            action: session.fork(parent, snapshot, intervention={self._agent: action}, label=f"{label}_{action}")
            for action in self.actions
        }
        self._rewards: dict[str, list[int]] = {action: [] for action in self.actions}
        self._states: dict[str, list[Hashable]] = {action: [state] for action in self.actions}
        self._prefix: dict[str, list[Fraction]] = {action: [Fraction(0)] for action in self.actions}
        self._powers = [Fraction(1)]

    @property
    def steps_taken(self) -> int:
        return sum(len(rewards) for rewards in self._rewards.values())

    @property
    def depth(self) -> int:
        return min(len(rewards) for rewards in self._rewards.values())

    def extend_to(self, horizon: int) -> None:
        _require_int(horizon, "horizon", minimum=1)
        world = self.session.world
        for action in self.actions:
            branch, rewards, states = self._branches[action], self._rewards[action], self._states[action]
            while len(rewards) < horizon:
                if self.session.is_terminated(branch):
                    raise HorizonError("branch terminated before the requested horizon")
                chosen = action if not rewards or self.continuation == "repeat" else HOLD
                transition = self.session.step(branch, {self._agent: chosen}, observation_provenance=OBSERVATION)
                successor, mirrored, terminated = world.step(states[-1], (chosen,))
                if transition.rewards[0][1] != mirrored[0] or transition.terminated != bool(terminated):
                    raise HorizonError("mirrored world state diverged from the session")
                prefix = self._prefix[action]
                prefix.append(prefix[-1] + self._power(len(rewards)) * mirrored[0])
                rewards.append(mirrored[0])
                states.append(successor)

    def _power(self, exponent: int) -> Fraction:
        while len(self._powers) <= exponent:
            self._powers.append(self._powers[-1] * self.gamma)
        return self._powers[exponent]

    def q(self, horizon: int, value: ValueFn) -> tuple[Fraction, ...]:
        """``Q_H`` for every action, in ``world.actions`` order."""

        _require_int(horizon, "horizon", minimum=1)
        if horizon > self.depth:
            raise HorizonError("extend the probe before reading this horizon")
        discount = self._power(horizon)
        return tuple(
            self._prefix[action][horizon] + discount * value(self._states[action][horizon])
            for action in self.actions
        )


def zero_value(state: Hashable) -> Fraction:
    """No bootstrap: ``V = 0``."""

    return Fraction(0)


@dataclass(frozen=True)
class OracleValue:
    """Exact hold-continuation value to the episode end. Upper bound only."""

    world: HorizonWorld
    gamma: Fraction

    def __call__(self, state: tuple[int, tuple[tuple[int, int], ...]]) -> Fraction:
        step, pending = state
        remaining = self.world.length - step
        stream = (1 - self.gamma**remaining) / (1 - self.gamma) * HOLD_REWARD
        return stream + sum(
            (amount * self.gamma ** (due - step) for due, amount in pending if due < self.world.length),
            Fraction(0),
        )


@dataclass(frozen=True)
class TabularValue:
    """Fitted value over :func:`pending_feature`; unseen features read ``fallback``."""

    table: Mapping[int | None, Fraction]
    fallback: Fraction
    samples: Mapping[int | None, int]

    def __call__(self, state: tuple[int, tuple[tuple[int, int], ...]]) -> Fraction:
        return self.table.get(pending_feature(state), self.fallback)


def window_returns(rewards: Sequence[int], window: int, gamma: Fraction) -> list[Fraction]:
    """``G[i] = sum_{k<window} gamma^k r[i+k]`` for every ``i`` (rewards past the end are 0)."""

    tail = gamma**window
    returns = [Fraction(0)] * (len(rewards) + 1)
    for index in range(len(rewards) - 1, -1, -1):
        dropped = rewards[index + window] if index + window < len(rewards) else 0
        returns[index] = rewards[index] + gamma * returns[index + 1] - tail * dropped
    return returns[:-1]


def fit_value(config: HorizonConfig) -> TabularValue:
    """Monte Carlo hold-continuation value per pending feature on training seeds only.

    Samples are discounted ``fit_window`` returns: every hold-baseline state
    with a full window ahead (feature ``None``), plus every pending state on one
    real commit branch per decision. A commit branch is rolled until its payoff
    lands; from there its snapshot must equal the baseline's at the same step
    (the world keeps no other memory), so its later rewards are the baseline's.
    The fallback for features never seen in training is the mean of the table.
    """

    totals: dict[int | None, Fraction] = {}
    counts: dict[int | None, int] = {}

    def record(feature: int | None, value: Fraction) -> None:
        totals[feature] = totals.get(feature, Fraction(0)) + value
        counts[feature] = counts.get(feature, 0) + 1

    window, gamma = config.fit_window, config.gamma
    for seed in config.train_seeds:
        world = make_world(config, seed)
        base = rollout_baseline(world, seed)
        returns = window_returns(base.rewards, window, gamma)
        for step in range(len(base.rewards) - window + 1):
            record(pending_feature(base.states[step]), returns[step])
        session = base.session
        for decision in world.decisions:
            if decision.delay == 0:
                continue
            rejoin = decision.due + 1
            if rejoin + window > len(base.rewards):
                raise HorizonError("the episode is too short for a full fit window after a payoff")
            branch = session.fork(
                session.baseline,
                base.heads[decision.step],
                intervention={AGENT: COMMIT},
                label=f"fit_{decision.step}",
            )
            state, rewards, states = base.states[decision.step], [], []
            for offset in range(decision.delay + 1):
                chosen = COMMIT if offset == 0 else HOLD
                transition = session.step(branch, {AGENT: chosen}, observation_provenance=OBSERVATION)
                state, (reward,), _ = world.step(state, (chosen,))
                if transition.rewards[0][1] != reward:
                    raise HorizonError("mirrored world state diverged from the session")
                rewards.append(reward)
                states.append(state)
            if session.head(branch) != base.heads[rejoin]:
                raise HorizonError("a landed commit branch must rejoin the baseline state")
            ahead = returns[rejoin]
            for offset in range(decision.delay, 0, -1):
                # The reward dropped off the window's far end comes from the baseline.
                dropped = base.rewards[decision.step + offset + window]
                ahead = rewards[offset] + gamma * ahead - gamma**window * dropped
                record(pending_feature(states[offset - 1]), ahead)
    table = {feature: totals[feature] / counts[feature] for feature in totals}
    fallback = sum(table.values(), Fraction(0)) / len(table)
    return TabularValue(MappingProxyType(table), fallback, MappingProxyType(dict(counts)))


# --- stopping rules -----------------------------------------------------------------


@dataclass(frozen=True)
class StoppingRule:
    kind: str
    threshold: Fraction | None = None

    def __post_init__(self) -> None:
        if self.kind not in RULE_KINDS:
            raise HorizonError(f"unknown stopping rule {self.kind!r}")
        needs = self.kind in ("value_gap", "value_stability")
        if needs != (self.threshold is not None):
            raise HorizonError(f"{self.kind} {'needs' if needs else 'takes no'} threshold")
        if needs:
            exact = _require_exact(self.threshold, "threshold")
            if exact < 0 or (self.kind == "value_stability" and exact == 0):
                raise HorizonError("margins must be non-negative and tolerances positive")
            object.__setattr__(self, "threshold", exact)

    @property
    def name(self) -> str:
        return self.kind if self.threshold is None else f"{self.kind}@{self.threshold}"

    def should_stop(self, previous: Sequence[Fraction], current: Sequence[Fraction]) -> bool:
        best = argmax(current)
        if self.kind == "rank_agreement":
            return argmax(previous) == best
        if self.kind == "value_gap":
            return argmax(previous) == best and gap(current) > self.threshold
        if self.kind == "value_stability":
            return abs(current[best] - previous[best]) < self.threshold
        return False


def rule_grid(config: HorizonConfig) -> tuple[StoppingRule, ...]:
    return (
        StoppingRule("rank_agreement"),
        *(StoppingRule("value_gap", Fraction(m)) for m in config.margins),
        *(StoppingRule("value_stability", Fraction(t)) for t in config.tolerances),
        StoppingRule("fixed_max"),
    )


def argmax(values: Sequence[Fraction]) -> int:
    """Index of the best value; ties go to the earliest action."""

    return max(range(len(values)), key=lambda index: (values[index], -index))


def gap(values: Sequence[Fraction]) -> Fraction:
    ordered = sorted(values, reverse=True)
    return ordered[0] - ordered[1]


@dataclass(frozen=True)
class RuleOutcome:
    horizon: int
    action: str
    branch_steps: int


def stop_on_sequence(
    rule: StoppingRule, schedule: Sequence[int], q_sequence: Sequence[Sequence[Fraction]], actions: Sequence[str]
) -> RuleOutcome:
    """Replay a rule over precomputed ``Q_H`` for each schedule horizon."""

    if len(q_sequence) != len(schedule):
        raise HorizonError("one Q vector per schedule horizon is required")
    for index in range(1, len(schedule)):
        if rule.should_stop(q_sequence[index - 1], q_sequence[index]):
            return RuleOutcome(schedule[index], actions[argmax(q_sequence[index])], len(actions) * schedule[index])
    return RuleOutcome(schedule[-1], actions[argmax(q_sequence[-1])], len(actions) * schedule[-1])


def run_rule(probe: HorizonProbe, rule: StoppingRule, schedule: Sequence[int], value: ValueFn) -> RuleOutcome:
    """Live adaptive run: extend the probe one schedule horizon at a time."""

    previous: tuple[Fraction, ...] | None = None
    current: tuple[Fraction, ...] = ()
    for horizon in schedule:
        probe.extend_to(horizon)
        current = probe.q(horizon, value)
        if previous is not None and rule.should_stop(previous, current):
            return RuleOutcome(horizon, probe.actions[argmax(current)], len(probe.actions) * horizon)
        previous = current
    return RuleOutcome(schedule[-1], probe.actions[argmax(current)], len(probe.actions) * schedule[-1])


def horizon_need(
    schedule: Sequence[int], q_sequence: Sequence[Sequence[Fraction]], best: frozenset[int]
) -> int | None:
    """Smallest schedule horizon from which every argmax is a best action, else ``None``."""

    need = None
    for index in range(len(schedule) - 1, -1, -1):
        if argmax(q_sequence[index]) not in best:
            break
        need = schedule[index]
    return need


# --- evaluation ---------------------------------------------------------------------


def _instance_kind(decision: Decision, oracle_gain: Fraction) -> str:
    if oracle_gain <= 0:
        return "no_gain"
    return "immediate_gain" if decision.delay == 0 else "delayed_gain"


def evaluate(config: HorizonConfig | None = None) -> dict[str, Any]:
    """Fit on training seeds, compare stopping rules on held-out decision points."""

    config = HorizonConfig() if config is None else config
    fitted = fit_value(config)
    rules = rule_grid(config)
    schedule = config.schedule
    points: list[dict[str, Any]] = []
    outcomes: dict[tuple[str, str], list[tuple[RuleOutcome, bool, str]]] = {
        (variant, rule.name): [] for variant in VALUE_VARIANTS for rule in rules
    }
    needs: dict[str, list[tuple[int | None, str]]] = {variant: [] for variant in VALUE_VARIANTS}
    seed_rows: list[dict[str, Any]] = []
    for seed in config.eval_seeds:
        world = make_world(config, seed)
        base = rollout_baseline(world, seed, until=world.decisions[-1].step)
        values: dict[str, ValueFn] = {
            "zero": zero_value,
            "fitted": fitted,
            "oracle": OracleValue(world, config.gamma),
        }
        for decision in world.decisions:
            probe = HorizonProbe(
                base.session,
                base.session.baseline,
                base.heads[decision.step],
                base.states[decision.step],
                continuation="hold",
                gamma=config.gamma,
                label=f"probe_{decision.step}",
            )
            probe.extend_to(config.cap)
            truth = probe.q(config.cap, values["oracle"])
            best = frozenset(index for index, q in enumerate(truth) if q == max(truth))
            gain = truth[probe.actions.index(COMMIT)] - truth[probe.actions.index(HOLD)]
            kind = _instance_kind(decision, gain)
            point_needs = {}
            for variant in VALUE_VARIANTS:
                sequence = [probe.q(horizon, values[variant]) for horizon in schedule]
                need = horizon_need(schedule, sequence, best)
                needs[variant].append((need, kind))
                point_needs[variant] = need
                for rule in rules:
                    outcome = stop_on_sequence(rule, schedule, sequence, probe.actions)
                    correct = probe.actions.index(outcome.action) in best
                    outcomes[(variant, rule.name)].append((outcome, correct, kind))
            points.append(
                {
                    "seed": seed,
                    "step": decision.step,
                    "cost": decision.cost,
                    "payoff": decision.payoff,
                    "delay": decision.delay,
                    "kind": kind,
                    "oracle_gain_milli": _milli(gain),
                    "need": point_needs,
                }
            )
        seed_rows.append(
            {
                "seed": seed,
                "decisions": [[d.step, d.cost, d.payoff, d.delay] for d in world.decisions],
                "manifest_digest": base.session.manifest().digest,
            }
        )
    count = len(points)
    fixed_steps = count * 2 * config.cap
    summary = []
    for variant in VALUE_VARIANTS:
        for rule in rules:
            group = outcomes[(variant, rule.name)]
            steps = sum(item[0].branch_steps for item in group)
            summary.append(
                {
                    "value": variant,
                    "rule": rule.kind,
                    "threshold": None if rule.threshold is None else _pair(rule.threshold),
                    "name": rule.name,
                    "points": count,
                    "correct": sum(1 for item in group if item[1]),
                    "correct_milli": (1000 * sum(1 for item in group if item[1])) // count,
                    "correct_by_kind": {
                        kind: [
                            sum(1 for item in group if item[2] == kind and item[1]),
                            sum(1 for item in group if item[2] == kind),
                        ]
                        for kind in INSTANCE_KINDS
                    },
                    "mean_stop_h_milli": (1000 * sum(item[0].horizon for item in group)) // count,
                    "branch_steps": steps,
                    "cost_vs_fixed_milli": (1000 * steps) // fixed_steps,
                }
            )
    need_rows = []
    for variant in VALUE_VARIANTS:
        values_needed = needs[variant]
        histogram = {str(h): sum(1 for need, _ in values_needed if need == h) for h in schedule}
        histogram["beyond_cap"] = sum(1 for need, _ in values_needed if need is None)
        high = [kind for need, kind in values_needed if need is None or need > schedule[0]]
        # Reference only: a stopper that knows each point's need but, like the rules,
        # must compare two horizons before it may stop.
        oracle_stop = sum(
            2 * (schedule[-1] if need is None else max(need, schedule[1])) for need, _ in values_needed
        )
        need_rows.append(
            {
                "value": variant,
                "points": count,
                "need_histogram": histogram,
                "needs_above_min": len(high),
                "needs_above_min_milli": (1000 * len(high)) // count,
                "needs_above_min_by_kind": {kind: high.count(kind) for kind in INSTANCE_KINDS},
                "oracle_stop_branch_steps": oracle_stop,
                "oracle_stop_cost_vs_fixed_milli": (1000 * oracle_stop) // fixed_steps,
            }
        )
    report = {
        "evidence_label": "synthetic",
        "config": config.to_payload(),
        "fitted_value_milli": {
            ("none" if feature is None else str(feature)): _milli(value)
            for feature, value in sorted(fitted.table.items(), key=lambda item: -1 if item[0] is None else item[0])
        },
        "fitted_fallback_milli": _milli(fitted.fallback),
        "kind_counts": {kind: sum(1 for p in points if p["kind"] == kind) for kind in INSTANCE_KINDS},
        "points": points,
        "seeds": seed_rows,
        "horizon_need": need_rows,
        "summary": summary,
    }
    report["report_digest"] = content_digest("experiment.horizon-stopping-report", report)
    return report


__all__ = [
    "COMMIT",
    "HOLD",
    "INSTANCE_KINDS",
    "RULE_KINDS",
    "VALUE_VARIANTS",
    "Baseline",
    "Decision",
    "HorizonConfig",
    "HorizonError",
    "HorizonProbe",
    "HorizonWorld",
    "OracleValue",
    "RuleOutcome",
    "StoppingRule",
    "TabularValue",
    "argmax",
    "evaluate",
    "fit_value",
    "gap",
    "horizon_need",
    "make_world",
    "pending_feature",
    "rollout_baseline",
    "rule_grid",
    "run_rule",
    "stop_on_sequence",
    "window_returns",
    "zero_value",
]
