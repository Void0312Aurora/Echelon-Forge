"""Agent interaction-order benchmark over a synthetic world with planted couplings.

Cluster ``E2`` of the adaptive counterfactual search plan
(``docs/learning/work/issues/adaptive_counterfactual_search/README.md``). It
measures ``H5`` (most multi-agent states need only a low interaction order)
on a world whose interaction structure is known, using real joint-action
branches through the reference session.

Value expansion
---------------
At a decision snapshot each of ``N`` agents either holds or acts once, then
everyone holds for the rest of the horizon ``H``. Writing a joint action as the
set ``A`` of acting agents, the branch value has the exact expansion

    Q(A) = sum over S subset of A of c_S,
    c_S = sum over T subset of S of (-1)^(|S| - |T|) Q(T).

``c_{}`` is the all-hold value, ``c_i`` the single-agent effect ``Delta_i``, and
``c_ij = Q(ij) - Q(i) - Q(j) + Q()`` the pairwise term ``Delta_ij`` of the
research note. Every ``Q`` is one fork from the same snapshot, so an estimator
of order ``M`` costs one branch per subset of size at most ``M``.

The world
---------
:class:`InteractionWorld` pays every agent ``base_reward`` per step. Each
:class:`Term` names a set of agents and pays ``amount`` (split evenly across its
members, remainder to the lowest indices) ``delay`` steps after all of them act
on the same step. Order-one terms are main effects, order-two terms pairwise
couplings, order-three terms synergies. Because the continuation only holds,
``c_S`` equals the amount of the planted term on ``S`` when its delay is below
``H``, and zero otherwise: a coupling with ``delay >= H`` is invisible at that
horizon. :func:`make_world` draws sparse structures from a seed: up to
``max_pairs`` couplings, some delayed past the short horizon, and sometimes one
triple synergy. Seeds with no coupling at all occur by construction.

Estimators
----------
- ``additive_m1``, ``pairwise_m2``, ``triple_m3``: the expansion truncated at
  order 1, 2, 3 (``1 + N``, ``+ C(N, 2)``, ``+ C(N, 3)`` branches).
- ``exhaustive``: all ``2^N`` joint actions; the reference.
- ``gated``: fit order 1, test on a held-out set of random joint actions with
  at least two actors, and add *all* pairs (then all triples) only while a
  held-out residual exceeds the tolerance.
- ``adaptive``: the same gate, but each round measures only the terms that sit
  inside a dirty held-out action and are not certified by a clean one. A clean
  action certifies every unmeasured term it contains; that assumes couplings in
  one action do not cancel to within tolerance, and a test pins the failure.
  When certification leaves nothing to measure the round falls back to the
  certified terms. Pairs are exhausted before triples. Measured terms with
  ``|c_S| < edge_threshold`` stay out of the model and the graph.

Both gated estimators run once per configured holdout size, and a seed's
smaller holdout is a subset of its larger one, so the sweep isolates coverage:
a term no held-out action contains can never raise the residual, and the gate
never measures it. Every holdout query is a branch and is counted in the cost.

Evidence boundary: everything here is ``synthetic``. Interaction sparsity,
which couplings are delayed, and how large they are come from the generator,
so the share of seeds where order one suffices is a property of that generator.
What the benchmark does measure is whether a residual gate notices the
couplings that exist, what it spends to find them, and how the needed order
moves with the horizon. It says nothing about the maintained runtime.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from itertools import combinations
from itertools import product
from typing import Any, Callable, Mapping, Sequence

from python.experiment.contracts import SnapshotRef
from python.experiment.contracts import content_digest
from python.experiment.reference_session import ReferenceSession

HOLD = "hold"
ACT = "act"
OBSERVATION = "decision_belief_packet"
POLICY_REF = "synthetic_policy:always_hold"
MAX_AGENTS = 10
FIXED_ORDERS: Mapping[str, int] = {"additive_m1": 1, "pairwise_m2": 2, "triple_m3": 3}
#: Estimators that read a held-out set and so run once per configured holdout size.
GATED: tuple[str, ...] = ("adaptive", "gated")
ESTIMATORS: tuple[str, ...] = ("additive_m1", "pairwise_m2", "triple_m3", *GATED, "exhaustive")

Subset = tuple[int, ...]
Bits = tuple[int, ...]


class InteractionError(ValueError):
    """Raised when an interaction-order world, config, or query is not admissible."""


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _require_int(value: Any, name: str, low: int | None = None, high: int | None = None) -> None:
    if not _is_int(value):
        raise InteractionError(f"{name} must be an integer, got {value!r}")
    if (low is not None and value < low) or (high is not None and value > high):
        raise InteractionError(f"{name} must be within [{low}, {high}], got {value}")


@dataclass(frozen=True)
class Term:
    """``amount`` paid to ``agents`` ``delay`` steps after they all act together."""

    agents: Subset
    amount: int
    delay: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.agents, tuple) or not self.agents:
            raise InteractionError("term agents must be a non-empty tuple")
        if not all(_is_int(agent) and agent >= 0 for agent in self.agents):
            raise InteractionError("term agents must be non-negative integers")
        if list(self.agents) != sorted(set(self.agents)):
            raise InteractionError("term agents must be strictly increasing")
        if not _is_int(self.amount) or self.amount == 0:
            raise InteractionError("term amount must be a non-zero integer")
        _require_int(self.delay, "term delay", 0)

    @property
    def order(self) -> int:
        return len(self.agents)


@dataclass(frozen=True)
class InteractionWorld:
    """Synthetic world: per-agent base reward plus planted interaction terms."""

    agent_count: int
    terms: tuple[Term, ...]
    max_steps: int
    base_reward: int = 1
    scenario_ref: str = "synthetic:interaction_order"
    actions: tuple[str, ...] = (HOLD, ACT)
    evidence_label: str = "synthetic"
    reward_units_per_point: int = 1

    def __post_init__(self) -> None:
        _require_int(self.agent_count, "agent_count", 2, MAX_AGENTS)
        _require_int(self.max_steps, "max_steps", 1)
        _require_int(self.base_reward, "base_reward")
        if not isinstance(self.terms, tuple) or not all(isinstance(term, Term) for term in self.terms):
            raise InteractionError("terms must be a tuple of Term")
        if any(term.agents[-1] >= self.agent_count for term in self.terms):
            raise InteractionError("a term names an agent outside the world")
        if len({term.agents for term in self.terms}) != len(self.terms):
            raise InteractionError("each agent set may carry at most one term")

    def config_payload(self) -> Mapping[str, Any]:
        return {
            "agent_count": self.agent_count,
            "terms": [[list(term.agents), term.amount, term.delay] for term in self.terms],
            "max_steps": self.max_steps,
            "base_reward": self.base_reward,
        }

    def initial_state(self, seed: int, agent_count: int) -> tuple[int, tuple[tuple[int, int], ...]]:
        if agent_count != self.agent_count:
            raise InteractionError(f"world has {self.agent_count} agents, session asked for {agent_count}")
        return (0, ())

    def encode_state(self, state: tuple[int, tuple[tuple[int, int], ...]]) -> Mapping[str, Any]:
        step, pending = state
        return {"step": step, "pending": [list(item) for item in pending]}

    def step(
        self, state: tuple[int, tuple[tuple[int, int], ...]], actions: tuple[str, ...]
    ) -> tuple[tuple[int, tuple[tuple[int, int], ...]], tuple[int, ...], bool]:
        if not isinstance(actions, tuple) or len(actions) != self.agent_count:
            raise InteractionError(f"actions must be a tuple of {self.agent_count} names")
        if any(action not in self.actions for action in actions):
            raise InteractionError(f"actions must be drawn from {self.actions}")
        step, pending = state
        acting = {index for index, action in enumerate(actions) if action == ACT}
        paying = [index for due, index in pending if due == step]
        remaining = [item for item in pending if item[0] > step]
        for index, term in enumerate(self.terms):
            if acting.issuperset(term.agents):
                if term.delay == 0:
                    paying.append(index)
                else:
                    remaining.append((step + term.delay, index))
        rewards = [self.base_reward] * self.agent_count
        for index in paying:
            term = self.terms[index]
            share, extra = divmod(term.amount, term.order)
            for rank, agent in enumerate(term.agents):
                rewards[agent] += share + (1 if rank < extra else 0)
        successor = (step + 1, tuple(sorted(remaining)))
        return successor, tuple(rewards), step + 1 >= self.max_steps

    def coefficients(self, horizon: int) -> dict[Subset, int]:
        """The non-zero expansion terms of a branch value over ``horizon`` steps."""

        _require_int(horizon, "horizon", 1)
        result: dict[Subset, int] = {}
        if self.base_reward:
            result[()] = self.base_reward * self.agent_count * horizon
        visible = sorted(
            (term for term in self.terms if term.delay < horizon),
            key=lambda term: (term.order, term.agents),
        )
        result.update((term.agents, term.amount) for term in visible)
        return result


def joint_actions(agent_count: int) -> tuple[Bits, ...]:
    """Every joint action as a 0/1 tuple, agent 0 most significant."""

    _require_int(agent_count, "agent_count", 1, MAX_AGENTS)
    return tuple(product((0, 1), repeat=agent_count))


def _acting(bits: Bits) -> Subset:
    return tuple(index for index, bit in enumerate(bits) if bit)


def _bits(agent_count: int, subset: Subset) -> Bits:
    chosen = set(subset)
    return tuple(1 if index in chosen else 0 for index in range(agent_count))


def _require_bits(bits: Any, agent_count: int) -> None:
    if (
        not isinstance(bits, tuple)
        or len(bits) != agent_count
        or not all(_is_int(bit) and bit in (0, 1) for bit in bits)
    ):
        raise InteractionError(f"a joint action must be a tuple of {agent_count} integers in (0, 1)")


def _agent_ids(agent_count: int) -> tuple[str, ...]:
    return tuple(f"agent_{index}" for index in range(agent_count))


def open_decision_session(
    world: InteractionWorld, seed: int, decision_step: int
) -> tuple[ReferenceSession, SnapshotRef]:
    """Run the all-hold baseline to ``decision_step`` and return its snapshot."""

    if not isinstance(world, InteractionWorld):
        raise InteractionError("world must be an InteractionWorld")
    _require_int(seed, "seed", 0)
    _require_int(decision_step, "decision_step", 0, world.max_steps - 1)
    agents = _agent_ids(world.agent_count)
    session = ReferenceSession.open(
        session_id=f"interaction_n{world.agent_count}_seed_{seed}",
        seed=seed,
        agent_ids=agents,
        policy_ref=POLICY_REF,
        world=world,
    )
    for _ in range(decision_step):
        session.step(session.baseline, {agent: HOLD for agent in agents}, observation_provenance=OBSERVATION)
    return session, session.head(session.baseline)


class BranchTable:
    """``Q`` of joint actions at one snapshot, one real fork per new joint action.

    A joint action acts on the decision step and holds afterwards; its value is
    the total reward over ``horizon`` steps, in world reward units.
    """

    def __init__(self, session: ReferenceSession, snapshot: SnapshotRef, horizon: int) -> None:
        if not isinstance(session.world, InteractionWorld):
            raise InteractionError("the session must run an InteractionWorld")
        _require_int(horizon, "horizon", 1)
        if snapshot.step + horizon > session.world.max_steps:
            raise InteractionError("the horizon runs past the end of the world")
        self.session = session
        self.snapshot = snapshot
        self.horizon = horizon
        self.agent_count = len(session.spec.agent_ids)
        self._values: dict[Bits, int] = {}

    @property
    def branches(self) -> int:
        return len(self._values)

    def __call__(self, bits: Bits) -> int:
        _require_bits(bits, self.agent_count)
        if bits not in self._values:
            agents = self.session.spec.agent_ids
            joint = {agent: ACT if bit else HOLD for agent, bit in zip(agents, bits)}
            hold = {agent: HOLD for agent in agents}
            branch = self.session.fork(
                self.session.baseline,
                self.snapshot,
                intervention=joint,
                label=f"h{self.horizon}_{''.join(map(str, bits))}",
            )
            total = 0
            for offset in range(self.horizon):
                transition = self.session.step(
                    branch, joint if offset == 0 else hold, observation_provenance=OBSERVATION
                )
                total += sum(reward for _, reward in transition.rewards)
            self._values[bits] = total
        return self._values[bits]


class QueryLedger:
    """Counts the distinct joint actions one estimator asks for.

    Estimators share the underlying :class:`BranchTable`, which forks each
    joint action once; the ledger is what one estimator would spend alone.
    """

    def __init__(self, table: Callable[[Bits], int]) -> None:
        self._table = table
        self._seen: set[Bits] = set()

    @property
    def branches(self) -> int:
        return len(self._seen)

    def __call__(self, bits: Bits) -> int:
        value = self._table(bits)
        self._seen.add(bits)
        return value


def sample_holdout(agent_count: int, seed: int, size: int) -> tuple[Bits, ...]:
    """Distinct random joint actions with at least two actors, sorted.

    Actions with fewer than two actors are fit exactly at order one, so they
    carry no residual. The sample is capped at the number of such actions, and
    for one seed a smaller holdout is always a subset of a larger one.
    """

    _require_int(agent_count, "agent_count", 2, MAX_AGENTS)
    _require_int(size, "holdout size", 1)
    eligible = [bits for bits in joint_actions(agent_count) if sum(bits) >= 2]
    random.Random(f"holdout:{agent_count}:{seed}").shuffle(eligible)
    return tuple(sorted(eligible[:size]))


def predict(model: Mapping[Subset, int], bits: Bits) -> int:
    """Sum of every model term whose agents all act in ``bits``."""

    return sum(value for subset, value in model.items() if all(bits[index] for index in subset))


def _mobius(q: Callable[[Bits], int], agent_count: int, subset: Subset) -> int:
    total = 0
    for size in range(len(subset) + 1):
        sign = -1 if (len(subset) - size) % 2 else 1
        for inner in combinations(subset, size):
            total += sign * q(_bits(agent_count, inner))
    return total


def _canonical(model: Mapping[Subset, int]) -> dict[Subset, int]:
    return {subset: model[subset] for subset in sorted(model, key=lambda item: (len(item), item))}


@dataclass(frozen=True)
class Estimate:
    """Expansion terms an estimator settled on, plus how its escalation ended."""

    name: str
    coefficients: Mapping[Subset, int]
    stop_order: int
    holdout_residual: int | None = None
    unresolved: bool = False
    fallbacks: int = 0

    def hyperedges(self, order: int, threshold: int) -> frozenset[Subset]:
        return frozenset(
            subset
            for subset, value in self.coefficients.items()
            if len(subset) == order and abs(value) >= threshold
        )

    def edges(self, threshold: int) -> frozenset[Subset]:
        return self.hyperedges(2, threshold)


def _fixed_order(name: str, q: Callable[[Bits], int], agent_count: int, order: int) -> Estimate:
    model = {
        subset: _mobius(q, agent_count, subset)
        for size in range(order + 1)
        for subset in combinations(range(agent_count), size)
    }
    return Estimate(name, model, order)


def _exhaustive(q: Callable[[Bits], int], agent_count: int) -> Estimate:
    values = [0] * (1 << agent_count)
    for mask in range(1 << agent_count):
        values[mask] = q(tuple((mask >> index) & 1 for index in range(agent_count)))
    for index in range(agent_count):
        bit = 1 << index
        for mask in range(1 << agent_count):
            if mask & bit:
                values[mask] -= values[mask ^ bit]
    model = {
        subset: values[sum(1 << index for index in subset)]
        for size in range(agent_count + 1)
        for subset in combinations(range(agent_count), size)
    }
    return Estimate("exhaustive", model, agent_count)


def _escalate(
    name: str,
    q: Callable[[Bits], int],
    agent_count: int,
    holdout: Sequence[Bits],
    *,
    tolerance: int,
    edge_threshold: int,
    max_order: int,
    screen: bool,
) -> Estimate:
    model = dict(_fixed_order(name, q, agent_count, 1).coefficients)
    measured: set[Subset] = set()
    level = 1
    fallbacks = 0
    while True:
        residual = {probe: q(probe) - predict(model, probe) for probe in holdout}
        worst = max(abs(value) for value in residual.values())
        dirty = [probe for probe in holdout if abs(residual[probe]) > tolerance]
        if not dirty:
            return Estimate(name, _canonical(model), level, worst, False, fallbacks)
        clean = [probe for probe in holdout if abs(residual[probe]) <= tolerance]
        candidates: set[Subset] = set()
        for order in range(2, max_order + 1):
            if not screen:
                candidates = set(combinations(range(agent_count), order)) - measured
            else:
                inside = {s for probe in dirty for s in combinations(_acting(probe), order)} - measured
                certified = {s for probe in clean for s in combinations(_acting(probe), order)}
                candidates = inside - certified
                if inside and not candidates:
                    candidates = inside
                    fallbacks += 1
            if candidates:
                level = max(level, order)
                break
        if not candidates:
            return Estimate(name, _canonical(model), level, worst, True, fallbacks)
        for subset in sorted(candidates):
            value = _mobius(q, agent_count, subset)
            measured.add(subset)
            if abs(value) >= edge_threshold:
                model[subset] = value


def estimate(
    name: str,
    table: Callable[[Bits], int],
    agent_count: int,
    *,
    holdout: Sequence[Bits] | None = None,
    tolerance: int = 1,
    edge_threshold: int = 1,
    max_order: int = 3,
) -> Estimate:
    """Run one estimator against a ``Q`` table (a :class:`BranchTable` or ledger)."""

    if name not in ESTIMATORS:
        raise InteractionError(f"unknown estimator {name!r}; expected one of {ESTIMATORS}")
    _require_int(agent_count, "agent_count", 2, MAX_AGENTS)
    _require_int(tolerance, "tolerance", 0)
    _require_int(edge_threshold, "edge_threshold", 1)
    _require_int(max_order, "max_order", 1, 3)
    if name in FIXED_ORDERS:
        return _fixed_order(name, table, agent_count, FIXED_ORDERS[name])
    if name == "exhaustive":
        return _exhaustive(table, agent_count)
    if not holdout:
        raise InteractionError(f"{name} needs a non-empty holdout")
    for probe in holdout:
        _require_bits(probe, agent_count)
    if len(set(holdout)) != len(holdout):
        raise InteractionError("holdout actions must be distinct")
    return _escalate(
        name,
        table,
        agent_count,
        tuple(holdout),
        tolerance=tolerance,
        edge_threshold=edge_threshold,
        max_order=max_order,
        screen=name == "adaptive",
    )


@dataclass(frozen=True)
class InteractionConfig:
    """Fixed protocol for one run; every field is part of the report identity."""

    seeds: tuple[int, ...] = tuple(range(301, 325))
    agent_counts: tuple[int, ...] = (4, 6, 8)
    horizons: tuple[int, ...] = (2, 8)
    decision_step: int = 2
    base_reward: int = 1
    main_min: int = 1
    main_max: int = 5
    max_pairs: int = 3
    coupling_min: int = 2
    coupling_max: int = 8
    delayed_milli: int = 500
    triple_milli: int = 250
    triple_min: int = 3
    triple_max: int = 10
    holdout_sizes: tuple[int, ...] = (4, 8, 16, 32)
    tolerance: int = 1
    edge_threshold: int = 2
    max_order: int = 3

    def __post_init__(self) -> None:
        for name in ("seeds", "agent_counts", "horizons", "holdout_sizes"):
            values = getattr(self, name)
            if not isinstance(values, tuple) or not values or not all(_is_int(item) for item in values):
                raise InteractionError(f"{name} must be a non-empty tuple of integers")
            if list(values) != sorted(set(values)):
                raise InteractionError(f"{name} must be strictly increasing")
        if self.seeds[0] < 0:
            raise InteractionError("seeds must be non-negative")
        if self.agent_counts[0] < 3 or self.agent_counts[-1] > MAX_AGENTS:
            raise InteractionError(f"agent counts must be within [3, {MAX_AGENTS}]")
        if len(self.horizons) != 2 or self.horizons[0] < 1:
            raise InteractionError("horizons must be one short and one long positive horizon")
        _require_int(self.decision_step, "decision_step", 0)
        _require_int(self.base_reward, "base_reward")
        for low, high in (("main_min", "main_max"), ("coupling_min", "coupling_max"), ("triple_min", "triple_max")):
            _require_int(getattr(self, low), low, 1)
            _require_int(getattr(self, high), high, getattr(self, low))
        smallest = self.agent_counts[0]
        _require_int(self.max_pairs, "max_pairs", 0, smallest * (smallest - 1) // 2)
        _require_int(self.delayed_milli, "delayed_milli", 0, 1000)
        _require_int(self.triple_milli, "triple_milli", 0, 1000)
        if self.holdout_sizes[0] < 1:
            raise InteractionError("holdout sizes must be positive")
        weakest = min(self.coupling_min, self.triple_min)
        # A planted term at or below tolerance could never be told apart from none.
        _require_int(self.tolerance, "tolerance", 0, weakest - 1)
        _require_int(self.edge_threshold, "edge_threshold", 1, weakest)
        _require_int(self.max_order, "max_order", 1, 3)

    def to_payload(self) -> dict[str, Any]:
        return {
            "seeds": list(self.seeds),
            "agent_counts": list(self.agent_counts),
            "horizons": list(self.horizons),
            "decision_step": self.decision_step,
            "base_reward": self.base_reward,
            "main_min": self.main_min,
            "main_max": self.main_max,
            "max_pairs": self.max_pairs,
            "coupling_min": self.coupling_min,
            "coupling_max": self.coupling_max,
            "delayed_milli": self.delayed_milli,
            "triple_milli": self.triple_milli,
            "triple_min": self.triple_min,
            "triple_max": self.triple_max,
            "holdout_sizes": list(self.holdout_sizes),
            "tolerance": self.tolerance,
            "edge_threshold": self.edge_threshold,
            "max_order": self.max_order,
        }


def make_world(config: InteractionConfig, agent_count: int, seed: int) -> InteractionWorld:
    """Seeded sparse structure: signed main effects, 0..max_pairs couplings, maybe a triple.

    A delayed coupling pays between the short and the long horizon, so it is
    invisible at the short one and visible at the long one.
    """

    _require_int(agent_count, "agent_count", 2, MAX_AGENTS)
    rng = random.Random(f"world:{agent_count}:{seed}")

    def signed(low: int, high: int) -> int:
        return rng.randint(low, high) * rng.choice((-1, 1))

    short, long = config.horizons
    terms = [Term((agent,), signed(config.main_min, config.main_max)) for agent in range(agent_count)]
    pairs = rng.sample(list(combinations(range(agent_count), 2)), rng.randint(0, config.max_pairs))
    for pair in sorted(pairs):
        amount = signed(config.coupling_min, config.coupling_max)
        delayed = rng.randrange(1000) < config.delayed_milli
        terms.append(Term(pair, amount, rng.randint(short, long - 1) if delayed else 0))
    if rng.randrange(1000) < config.triple_milli:
        triple = tuple(sorted(rng.sample(range(agent_count), 3)))
        terms.append(Term(triple, signed(config.triple_min, config.triple_max)))
    return InteractionWorld(
        agent_count=agent_count,
        terms=tuple(terms),
        max_steps=config.decision_step + long,
        base_reward=config.base_reward,
    )


def _predict_all(model: Mapping[Subset, int], agent_count: int) -> list[int]:
    """Predictions for every joint action, indexed by acting-agent bitmask."""

    values = [0] * (1 << agent_count)
    for subset, value in model.items():
        values[sum(1 << index for index in subset)] += value
    for index in range(agent_count):
        bit = 1 << index
        for mask in range(1 << agent_count):
            if mask & bit:
                values[mask] += values[mask ^ bit]
    return values


def _mask(bits: Bits) -> int:
    return sum(1 << index for index, bit in enumerate(bits) if bit)


def _ratio_milli(numerator: int, denominator: int) -> int | None:
    return None if denominator == 0 else (1000 * numerator) // denominator


def _score(
    result: Estimate,
    branches: int,
    truth: Mapping[Bits, int],
    true_edges: frozenset[Subset],
    true_triples: frozenset[Subset],
    config: InteractionConfig,
    agent_count: int,
) -> dict[str, Any]:
    predicted = _predict_all(result.coefficients, agent_count)
    errors = [abs(predicted[_mask(bits)] - value) for bits, value in truth.items()]
    chosen = max(truth, key=lambda bits: (predicted[_mask(bits)], bits))
    edges = result.edges(config.edge_threshold)
    triples = result.hyperedges(3, config.edge_threshold)
    return {
        "branches": branches,
        "max_abs_error": max(errors),
        "sum_abs_error": sum(errors),
        "chosen": list(chosen),
        "best_regret": max(truth.values()) - truth[chosen],
        "edges": [list(edge) for edge in sorted(edges)],
        "edge_tp": len(edges & true_edges),
        "triples": [list(item) for item in sorted(triples)],
        "triple_tp": len(triples & true_triples),
        "stop_order": result.stop_order,
        "holdout_residual": result.holdout_residual,
        "unresolved": result.unresolved,
        "fallbacks": result.fallbacks,
    }


def runs(config: InteractionConfig) -> tuple[tuple[str, int | None], ...]:
    """Every (estimator, holdout size) pair; the size is ``None`` for ungated ones."""

    grid: list[tuple[str, int | None]] = []
    for name in ESTIMATORS:
        if name in GATED:
            grid.extend((name, size) for size in config.holdout_sizes)
        else:
            grid.append((name, None))
    return tuple(grid)


def run_label(name: str, holdout_size: int | None) -> str:
    return name if holdout_size is None else f"{name}_k{holdout_size}"


def _measure_seed(config: InteractionConfig, agent_count: int, seed: int) -> dict[str, Any]:
    world = make_world(config, agent_count, seed)
    session, snapshot = open_decision_session(world, seed, config.decision_step)
    holdouts = {size: sample_holdout(agent_count, seed, size) for size in config.holdout_sizes}
    horizon_rows = []
    for horizon in config.horizons:
        table = BranchTable(session, snapshot, horizon)
        truth = {bits: table(bits) for bits in joint_actions(agent_count)}
        planted = world.coefficients(horizon)
        true_edges = frozenset(s for s, v in planted.items() if len(s) == 2 and abs(v) >= config.edge_threshold)
        true_triples = frozenset(s for s, v in planted.items() if len(s) == 3 and abs(v) >= config.edge_threshold)
        scores = {}
        for name, size in runs(config):
            ledger = QueryLedger(table)
            result = estimate(
                name,
                ledger,
                agent_count,
                holdout=None if size is None else holdouts[size],
                tolerance=config.tolerance,
                edge_threshold=config.edge_threshold,
                max_order=config.max_order,
            )
            scores[run_label(name, size)] = _score(
                result, ledger.branches, truth, true_edges, true_triples, config, agent_count
            )
        horizon_rows.append(
            {
                "horizon": horizon,
                "best_value": max(truth.values()),
                "true_edges": [list(edge) for edge in sorted(true_edges)],
                "true_triples": [list(item) for item in sorted(true_triples)],
                "estimators": scores,
            }
        )
    return {
        "seed": seed,
        "agent_count": agent_count,
        "terms": [{"agents": list(t.agents), "amount": t.amount, "delay": t.delay} for t in world.terms],
        "holdout": [list(probe) for probe in holdouts[config.holdout_sizes[-1]]],
        "manifest_digest": session.manifest().digest,
        "horizons": horizon_rows,
    }


def _summarize(config: InteractionConfig, seed_rows: Sequence[dict[str, Any]]) -> tuple[list, list]:
    summary: list[dict[str, Any]] = []
    order_need: list[dict[str, Any]] = []
    tolerance = config.tolerance
    for agent_count in config.agent_counts:
        for horizon in config.horizons:
            cells = [
                item
                for row in seed_rows
                if row["agent_count"] == agent_count
                for item in row["horizons"]
                if item["horizon"] == horizon
            ]
            count = len(cells)
            for name, size in runs(config):
                label = run_label(name, size)
                scores = [cell["estimators"][label] for cell in cells]
                edge_true = sum(len(cell["true_edges"]) for cell in cells)
                triple_true = sum(len(cell["true_triples"]) for cell in cells)
                edge_pred = sum(len(score["edges"]) for score in scores)
                triple_pred = sum(len(score["triples"]) for score in scores)
                edge_tp = sum(score["edge_tp"] for score in scores)
                triple_tp = sum(score["triple_tp"] for score in scores)
                stops: dict[str, int] = {}
                for score in scores:
                    key = str(score["stop_order"])
                    stops[key] = stops.get(key, 0) + 1
                total_branches = sum(score["branches"] for score in scores)
                summary.append(
                    {
                        "agent_count": agent_count,
                        "horizon": horizon,
                        "estimator": name,
                        "holdout_size": size,
                        "seeds": count,
                        "total_branches": total_branches,
                        "max_branches": max(score["branches"] for score in scores),
                        "branch_steps": total_branches * horizon,
                        "cost_vs_exhaustive_milli": (1000 * total_branches) // (count << agent_count),
                        "max_abs_error": max(score["max_abs_error"] for score in scores),
                        "mean_abs_error_milli": (1000 * sum(score["sum_abs_error"] for score in scores))
                        // (count << agent_count),
                        "within_tolerance_seeds": sum(1 for s in scores if s["max_abs_error"] <= tolerance),
                        "best_correct_seeds": sum(1 for score in scores if score["best_regret"] == 0),
                        "total_best_regret": sum(score["best_regret"] for score in scores),
                        "edge_true": edge_true,
                        "edge_pred": edge_pred,
                        "edge_tp": edge_tp,
                        "edge_precision_milli": _ratio_milli(edge_tp, edge_pred),
                        "edge_recall_milli": _ratio_milli(edge_tp, edge_true),
                        "triple_precision_milli": _ratio_milli(triple_tp, triple_pred),
                        "triple_recall_milli": _ratio_milli(triple_tp, triple_true),
                        "stop_order_counts": stops,
                        "unresolved_seeds": sum(1 for score in scores if score["unresolved"]),
                        "fallback_rounds": sum(score["fallbacks"] for score in scores),
                    }
                )

            def suffices(name: str) -> int:
                return sum(1 for cell in cells if cell["estimators"][name]["max_abs_error"] <= tolerance)

            m1_true = [cell["estimators"]["additive_m1"]["max_abs_error"] <= tolerance for cell in cells]
            gate = []
            for size in config.holdout_sizes:
                # adaptive and gated share the order-one gate, so either label works.
                first = [cell["estimators"][run_label("adaptive", size)] for cell in cells]
                accepted = [score["stop_order"] == 1 and not score["unresolved"] for score in first]
                gate.append(
                    {
                        "holdout_size": size,
                        "m1_accepted_seeds": sum(accepted),
                        "m1_false_accept_seeds": sum(1 for ok, acc in zip(m1_true, accepted) if acc and not ok),
                        "m1_false_escalate_seeds": sum(1 for ok, acc in zip(m1_true, accepted) if ok and not acc),
                    }
                )
            order_need.append(
                {
                    "agent_count": agent_count,
                    "horizon": horizon,
                    "seeds": count,
                    "uncoupled_seeds": sum(
                        1 for cell in cells if not cell["true_edges"] and not cell["true_triples"]
                    ),
                    "m1_suffices_seeds": suffices("additive_m1"),
                    "m1_suffices_milli": (1000 * suffices("additive_m1")) // count,
                    "m2_suffices_seeds": suffices("pairwise_m2"),
                    "m3_suffices_seeds": suffices("triple_m3"),
                    "m1_best_correct_seeds": sum(
                        1 for cell in cells if cell["estimators"]["additive_m1"]["best_regret"] == 0
                    ),
                    "gate": gate,
                }
            )
    return summary, order_need


def evaluate(config: InteractionConfig | None = None) -> dict[str, Any]:
    """Run every estimator on every seed, agent count, and horizon; aggregate."""

    config = InteractionConfig() if config is None else config
    seed_rows = [
        _measure_seed(config, agent_count, seed) for agent_count in config.agent_counts for seed in config.seeds
    ]
    summary, order_need = _summarize(config, seed_rows)
    report = {
        "evidence_label": "synthetic",
        "config": config.to_payload(),
        "runs": [[name, size] for name, size in runs(config)],
        "seeds": seed_rows,
        "summary": summary,
        "order_need": order_need,
    }
    report["report_digest"] = content_digest("experiment.interaction-order-report", report)
    return report


__all__ = [
    "ACT",
    "ESTIMATORS",
    "GATED",
    "HOLD",
    "BranchTable",
    "Estimate",
    "InteractionConfig",
    "InteractionError",
    "InteractionWorld",
    "QueryLedger",
    "Term",
    "estimate",
    "evaluate",
    "joint_actions",
    "make_world",
    "open_decision_session",
    "predict",
    "run_label",
    "runs",
    "sample_holdout",
]
