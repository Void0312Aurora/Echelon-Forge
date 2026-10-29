"""Robustness sweeps over the Phase 1 candidate-discovery findings (cluster ``E4``).

The Phase 1 benchmark (:mod:`python.experiment.candidate_discovery`) reported
five observations on one world configuration (delay 4, decoy spike ``+25``
against a hazard penalty of ``-20``, undiscounted oracle). This module reruns
the benchmark, with real branches through the reference session, across four
sweeps and records which observations survive:

1. **Discounted oracle horizon.** The oracle gain of step ``t`` becomes
   ``sum_k gamma**k * (r_branch[t + k] - r_baseline[t + k])`` over the same
   ``horizon``, computed exactly with :class:`~fractions.Fraction` from the
   per-step reward vectors of the branches :func:`measure_signals` already
   ran. Swept for every delay in the grid.
2. **Decoy magnitude.** ``decoy_reward`` swept against the fixed hazard
   penalty. Event placement does not depend on it, so the same seeds place the
   same events; the value fit is redone on the training seeds of each cell.
3. **Consequence delay.** ``delay`` swept with lookbacks
   ``(0, delay, delay + extra_lookback)``. Changing the delay or the lookbacks
   changes the slot spacing, so each delay places its own events.
4. **Decoy-aware TD.** Two variants scored from the same tabular value ``V``
   and fit on training seeds only:

   - ``td_vchange``: ``|gamma V(x_{t+1}) - V(x_t)|``, the TD error with the
     immediate reward removed;
   - ``td_expected``: ``|rbar(x_t) + gamma V(x_{t+1}) - V(x_t)|``, the TD
     error minus its reward-deviation component ``r_t - rbar(x_t)``, where
     ``rbar`` is the mean training-seed reward per cue feature.

   Both reuse the ``td`` proposal rule (trigger, lead step, lookback window,
   uniform fill) by substituting the score into the signal record that
   :func:`select` reads, so the comparison isolates the score.

Nothing is tuned: the trigger rule, budgets, and threshold are the Phase 1
ones, and ``V``/``rbar`` are fit on the training seeds of each cell and
applied to its held-out seeds.

Two world properties make some answers structural rather than empirical, and
the report says so instead of counting them as evidence:

- every decision has one consequence at one fixed delay and every other step
  costs exactly ``act_cost - base_reward``, so discounting is a monotone
  rescale of decision gains; it can only interact with the absolute
  ``gain_threshold``;
- decoys and opportunities carry no observation, and event spacing keeps every
  trigger window on its own event, so a score built only on observation
  change cannot fire on a decoy, and no trigger window can reach an
  opportunity.

Evidence boundary: ``synthetic``. Nothing here is a runtime or combat claim.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from fractions import Fraction
from functools import lru_cache
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from python.experiment.candidate_discovery import (
    DECISION_KINDS,
    WAIT,
    BenchmarkConfig,
    BenchmarkError,
    CausalDecisionWorld,
    StepSignals,
    _baseline_rewards,
    _cue_feature,
    _expand,
    _fill_uniform,
    _scores,
    fit_value,
    make_world,
    measure_signals,
    select,
    triggers,
)
from python.experiment.contracts import content_digest
from python.experiment.reference_session import ReferenceSession

VARIANTS: tuple[str, ...] = ("td_vchange", "td_expected")
TRIGGER_SELECTORS: tuple[str, ...] = ("reward", "td", "td_uniform", *VARIANTS)
SIGNALS: tuple[str, ...] = ("reward", "td", *VARIANTS)
#: Where a trigger sits relative to the event that caused it. ``pre_cue`` is the
#: step before a cue (the TD lead step reaches the cue from there);
#: ``consequence`` is ``cue + delay``, where a hazard penalty lands or a false
#: cue's window expires; neither ``consequence`` nor ``decoy`` is a decision.
ROLES: tuple[str, ...] = (
    "decoy", "pre_cue", "cue_window", "consequence", "opportunity", "other"
)
REPORT_DOMAIN = "experiment.candidate-discovery-sweeps-report"


@dataclass(frozen=True)
class SweepConfig:
    """Sweep grid around one Phase 1 base configuration; hashable and frozen."""

    base: BenchmarkConfig = field(default_factory=BenchmarkConfig)
    oracle_gammas: tuple[Fraction, ...] = (Fraction(1), Fraction(19, 20), Fraction(4, 5))
    decoy_rewards: tuple[int, ...] = (0, 5, 10, 25, 50)
    delays: tuple[int, ...] = (2, 4, 6)
    extra_lookback: int = 2

    def __post_init__(self) -> None:
        gammas = [Fraction(gamma) for gamma in self.oracle_gammas]
        if not gammas or gammas[0] != 1 or any(not 0 < gamma <= 1 for gamma in gammas):
            raise BenchmarkError("oracle_gammas must start at gamma = 1 and stay within (0, 1]")
        if gammas != sorted(set(gammas), reverse=True):
            raise BenchmarkError("oracle_gammas must be unique and descending")
        if not self.decoy_rewards or list(self.decoy_rewards) != sorted(set(self.decoy_rewards)):
            raise BenchmarkError("decoy_rewards must be sorted and unique")
        if any(reward < 0 for reward in self.decoy_rewards):
            raise BenchmarkError("decoy_rewards must be non-negative")
        if not self.delays or list(self.delays) != sorted(set(self.delays)):
            raise BenchmarkError("delays must be sorted and unique")
        if self.extra_lookback < 1:
            raise BenchmarkError("extra_lookback must be positive")
        for delay in self.delays:
            self.delay_config(delay)
        for reward in self.decoy_rewards:
            self.decoy_config(reward)

    def lookbacks(self, delay: int) -> tuple[int, ...]:
        return (0, delay, delay + self.extra_lookback)

    def delay_config(self, delay: int) -> BenchmarkConfig:
        """Base config at ``delay`` with lookbacks ``(0, delay, delay + extra)``."""

        return dataclasses.replace(self.base, delay=delay, lookbacks=self.lookbacks(delay))

    def decoy_config(self, decoy_reward: int) -> BenchmarkConfig:
        return dataclasses.replace(self.base, decoy_reward=decoy_reward)

    def to_payload(self) -> dict[str, Any]:
        return {
            "base": self.base.to_payload(),
            "grid": {
                "oracle_gammas": [_pair(Fraction(gamma)) for gamma in self.oracle_gammas],
                "decoy_rewards": list(self.decoy_rewards),
                "delays": list(self.delays),
                "lookbacks_by_delay": {
                    str(delay): list(self.lookbacks(delay)) for delay in self.delays
                },
                "selectors": ["uniform", "oracle", *TRIGGER_SELECTORS],
                "variants": list(VARIANTS),
                "dominance_top_k": self.base.decoy_count,
            },
            "fixed": {
                "decoy_sweep_delay": self.base.delay,
                "delay_sweep_decoy_reward": self.base.decoy_reward,
                "value_gamma": _pair(self.base.gamma),
                "hazard_penalty": CausalDecisionWorld.hazard_penalty,
            },
        }


def _pair(value: Fraction) -> list[int]:
    return [value.numerator, value.denominator]


def _milli(value: Fraction) -> int:
    return round(value * 1000)


def _grid(lookbacks: Sequence[int]) -> tuple[tuple[str, int], ...]:
    grid: list[tuple[str, int]] = [("uniform", 0), ("oracle", 0)]
    for name in TRIGGER_SELECTORS:
        grid.extend((name, lookback) for lookback in lookbacks)
    return tuple(grid)


def discounted_gain(diffs: Sequence[int], gamma: Fraction) -> Fraction:
    """``sum_k gamma**k * diffs[k]``, exact."""

    gamma = Fraction(gamma)
    return sum((Fraction(diff) * gamma**index for index, diff in enumerate(diffs)), Fraction(0))


def branch_reward_diffs(session: ReferenceSession) -> dict[int, tuple[int, ...]]:
    """Per-step branch-minus-baseline rewards of every single-step act branch."""

    baseline = _baseline_rewards(session)
    diffs: dict[int, tuple[int, ...]] = {}
    for trace in session.manifest().branches:
        if trace.branch.parent_digest is None:
            continue
        start = trace.branch.origin_step
        if start in diffs:
            raise BenchmarkError("expected one act branch per origin step")
        diffs[start] = tuple(
            item.rewards[0][1] - baseline[start + offset]
            for offset, item in enumerate(trace.transitions)
        )
    return diffs


@lru_cache(maxsize=32)
def fit_reward_mean(config: BenchmarkConfig) -> Mapping[int, Fraction]:
    """Mean baseline reward per cue feature over the training seeds only.

    Steps the pure world directly: this fit reads no branch, so it skips the
    reference-session bookkeeping that :func:`fit_value` pays for.
    """

    totals: dict[int, int] = {}
    counts: dict[int, int] = {}
    for seed in config.train_seeds:
        world = make_world(config, seed)
        state = world.initial_state(seed, 1)
        step, done = 0, False
        while not done:
            state, (reward,), done = world.step(state, (WAIT,))
            feature = _cue_feature(world, step)
            totals[feature] = totals.get(feature, 0) + reward
            counts[feature] = counts.get(feature, 0) + 1
            step += 1
    return MappingProxyType({key: Fraction(totals[key], counts[key]) for key in totals})


@dataclass(frozen=True)
class SeedMeasurement:
    """One held-out seed: Phase 1 signals, branch reward vectors, variant scores."""

    seed: int
    world: CausalDecisionWorld
    signals: tuple[StepSignals, ...]
    diffs: Mapping[int, tuple[int, ...]]
    variant_milli: Mapping[str, Mapping[int, int]]
    manifest_digest: str
    variant_signals: Mapping[str, tuple[StepSignals, ...]]

    def signals_for(self, selector: str) -> tuple[StepSignals, ...]:
        """Signals that :func:`select` reads; a variant replaces the TD score."""

        return self.variant_signals.get(selector, self.signals)

    def scores(self, signal: str) -> dict[int, Fraction]:
        return _scores("reward" if signal == "reward" else "td", self.signals_for(signal))

    @property
    def kinds(self) -> dict[int, str]:
        return {item.step: item.kind for item in self.signals}


def trigger_role(world: CausalDecisionWorld, step: int) -> str:
    """Classify a trigger step by the placed event it is nearest to."""

    if step in world.decoys:
        return "decoy"
    for cue in sorted(world.cue_steps):
        offset = step - cue
        if offset == -1:
            return "pre_cue"
        if offset == world.delay:
            return "consequence"
        if 0 <= offset <= world.delay + 1:
            return "cue_window"
    if any(-1 <= step - item <= world.delay + 1 for item in world.opportunities):
        return "opportunity"
    return "other"


@lru_cache(maxsize=512)
def measure_seed(config: BenchmarkConfig, seed: int) -> SeedMeasurement:
    """Run the Phase 1 measurement for one seed and derive the sweep inputs."""

    world = make_world(config, seed)
    value = fit_value(config)
    session, signals = measure_signals(world, config, seed, value)
    reward_mean = fit_reward_mean(config)
    default_value = sum(value.values(), Fraction(0)) / len(value)
    default_reward = sum(reward_mean.values(), Fraction(0)) / len(reward_mean)
    diffs = branch_reward_diffs(session)
    if any(discounted_gain(diffs[item.step], Fraction(1)) != item.oracle_gain for item in signals):
        raise BenchmarkError("branch reward vectors disagree with the Phase 1 oracle gain")
    vchange: dict[int, int] = {}
    expected: dict[int, int] = {}
    for item in signals:
        now = _cue_feature(world, item.step)
        v_now = value.get(now, default_value)
        v_next = value.get(_cue_feature(world, item.step + 1), default_value)
        vchange[item.step] = _milli(abs(config.gamma * v_next - v_now))
        expected[item.step] = _milli(
            abs(reward_mean.get(now, default_reward) + config.gamma * v_next - v_now)
        )
    variant_milli = {"td_vchange": vchange, "td_expected": expected}
    return SeedMeasurement(
        seed=seed,
        world=world,
        signals=signals,
        diffs=MappingProxyType(diffs),
        variant_milli=MappingProxyType(
            {name: MappingProxyType(scores) for name, scores in variant_milli.items()}
        ),
        manifest_digest=session.manifest().digest,
        variant_signals=MappingProxyType(
            {
                name: tuple(
                    dataclasses.replace(item, td_surprise_milli=scores[item.step])
                    for item in signals
                )
                for name, scores in variant_milli.items()
            }
        ),
    )


@lru_cache(maxsize=4096)
def _trigger_steps(config: BenchmarkConfig, seed: int, signal: str) -> tuple[int, ...]:
    return tuple(triggers(measure_seed(config, seed).scores(signal)))


@lru_cache(maxsize=1 << 16)
def _trigger_selection(
    config: BenchmarkConfig, seed: int, selector: str, budget: int, lookback: int
) -> tuple[frozenset[int], tuple[int, ...]]:
    """``select`` for a trigger selector, plus the steps its triggers proposed.

    The proposal attribution mirrors :func:`select` and is checked against its
    ``triggered`` count, so a drift in the Phase 1 rule fails loudly.
    """

    measurement = measure_seed(config, seed)
    base = "td" if selector in VARIANTS else selector
    signals = measurement.signals_for(selector)
    selection = select(base, signals, budget, lookback, config.uniform_share_milli)
    steps = [item.step for item in signals]
    reserved: set[int] = set()
    if base == "td_uniform":
        reserved = _fill_uniform(steps, set(), (budget * config.uniform_share_milli) // 1000)
    signal = "reward" if base == "reward" else ("td" if base == "td_uniform" else selector)
    known = set(steps)
    proposed = tuple(
        step
        for step in _expand(
            _trigger_steps(config, seed, signal),
            lookback,
            budget - len(reserved),
            reserved,
            lead=0 if signal == "reward" else 1,
        )
        if step in known
    )
    if len(proposed) != selection.triggered:
        raise BenchmarkError("proposal attribution drifted from candidate_discovery.select")
    return frozenset(selection.steps), proposed


def _choose(
    config: BenchmarkConfig,
    measurement: SeedMeasurement,
    oracle_signals: Sequence[StepSignals],
    selector: str,
    budget: int,
    lookback: int,
) -> tuple[frozenset[int], tuple[int, ...] | None]:
    if selector == "oracle":
        picked = select("oracle", oracle_signals, budget, lookback, config.uniform_share_milli)
        return frozenset(picked.steps), None
    if selector == "uniform":
        picked = select(
            "uniform", measurement.signals, budget, lookback, config.uniform_share_milli
        )
        return frozenset(picked.steps), None
    return _trigger_selection(config, measurement.seed, selector, budget, lookback)


def _recall(chosen: set[int] | frozenset[int], targets: Sequence[int]) -> int | None:
    if not targets:
        return None
    return (1000 * len(set(chosen) & set(targets))) // len(targets)


def _mean(values: Sequence[int | None]) -> int | None:
    present = [value for value in values if value is not None]
    return sum(present) // len(present) if present else None


@dataclass(frozen=True)
class _Cell:
    """Exact per-cell results; the report keeps only integer projections."""

    seeds: tuple[dict[str, Any], ...]
    summary: tuple[dict[str, Any], ...]
    regret: Mapping[tuple[str, int, int], Fraction]


@lru_cache(maxsize=64)
def _evaluate_cell(config: BenchmarkConfig, gamma: Fraction) -> _Cell:
    rows: list[dict[str, Any]] = []
    seeds: list[dict[str, Any]] = []
    for seed in config.eval_seeds:
        measurement = measure_seed(config, seed)
        world = measurement.world
        gains = {step: discounted_gain(diff, gamma) for step, diff in measurement.diffs.items()}
        important = sorted(step for step, gain in gains.items() if gain >= config.gain_threshold)
        kinds = measurement.kinds
        by_kind = {kind: [s for s in important if kinds[s] == kind] for kind in DECISION_KINDS}
        oracle_best = max(gains.values())
        # ``select("oracle")`` ranks by ``oracle_gain``; relabel it with the discounted gain.
        oracle_signals = tuple(
            dataclasses.replace(item, oracle_gain=gains[item.step]) for item in measurement.signals
        )
        seeds.append(
            {
                "seed": seed,
                "important": important,
                "positive": sorted(step for step, gain in gains.items() if gain > 0),
                "density_milli": (1000 * len(important)) // len(gains),
                "oracle_best": oracle_best,
                "decision_gains": sorted(
                    {gains[step] for kind in DECISION_KINDS for step in world.events(kind)}
                ),
            }
        )
        for budget in config.budgets:
            for selector, lookback in _grid(config.lookbacks):
                chosen, proposed = _choose(
                    config, measurement, oracle_signals, selector, budget, lookback
                )
                proposed_set = set(proposed) if proposed is not None else None
                rows.append(
                    {
                        "selector": selector,
                        "lookback": lookback,
                        "budget": budget,
                        "branches": len(chosen),
                        "triggered": len(proposed) if proposed is not None else 0,
                        "recall": _recall(chosen, important),
                        "hazard": _recall(chosen, by_kind["hazard"]),
                        "opportunity": _recall(chosen, by_kind["opportunity"]),
                        "triggered_hazard": (
                            _recall(proposed_set, by_kind["hazard"])
                            if proposed_set is not None
                            else None
                        ),
                        "opportunity_proposed": bool(
                            proposed_set is not None
                            and proposed_set & set(world.opportunities)
                        ),
                        "regret": oracle_best - max(gains[step] for step in chosen),
                    }
                )
    summary: list[dict[str, Any]] = []
    regret: dict[tuple[str, int, int], Fraction] = {}
    for budget in config.budgets:
        for selector, lookback in _grid(config.lookbacks):
            group = [
                row
                for row in rows
                if row["selector"] == selector
                and row["lookback"] == lookback
                and row["budget"] == budget
            ]
            total = sum((row["regret"] for row in group), Fraction(0))
            regret[(selector, lookback, budget)] = total
            summary.append(
                {
                    "selector": selector,
                    "lookback": lookback,
                    "budget": budget,
                    "mean_recall_milli": _mean([row["recall"] for row in group]),
                    "mean_hazard_recall_milli": _mean([row["hazard"] for row in group]),
                    "mean_opportunity_recall_milli": _mean([row["opportunity"] for row in group]),
                    "mean_triggered_hazard_recall_milli": _mean(
                        [row["triggered_hazard"] for row in group]
                    ),
                    "opportunity_proposed_seeds": sum(
                        1 for row in group if row["opportunity_proposed"]
                    ),
                    "total_regret_milli": _milli(total),
                    "zero_regret_seeds": sum(1 for row in group if row["regret"] == 0),
                    "mean_triggered_milli": (1000 * sum(row["triggered"] for row in group))
                    // len(group),
                    "branch_steps": max(row["branches"] for row in group) * config.horizon,
                }
            )
    return _Cell(tuple(seeds), tuple(summary), MappingProxyType(regret))


def _dominance(config: BenchmarkConfig) -> list[dict[str, Any]]:
    """How often decoys lead each signal's triggers on the held-out seeds."""

    top_k = config.decoy_count
    rows = []
    for signal in SIGNALS:
        top1 = all_top = decoy_hits = fired = decoy_first = 0
        roles = dict.fromkeys(ROLES, 0)
        top1_roles = dict.fromkeys(ROLES, 0)
        peak: dict[str, Fraction] = {}
        for seed in config.eval_seeds:
            measurement = measure_seed(config, seed)
            kinds = measurement.kinds
            scores = measurement.scores(signal)
            for step, score in scores.items():
                role = trigger_role(measurement.world, step)
                peak[role] = max(peak.get(role, score), score)
            steps = _trigger_steps(config, seed, signal)
            ranked = [kinds[step] for step in steps]
            fired += len(ranked)
            decoy_hits += ranked.count("decoy")
            top1 += bool(ranked) and ranked[0] == "decoy"
            all_top += top_k > 0 and len(ranked) >= top_k and ranked[:top_k] == ["decoy"] * top_k
            ranked_roles = [trigger_role(measurement.world, step) for step in steps]
            for index, role in enumerate(ranked_roles):
                roles[role] += 1
                top1_roles[role] += index == 0
            # A pre-cue trigger is the only one whose lead step reaches a cue at L = 0.
            if "decoy" in ranked_roles and (
                "pre_cue" not in ranked_roles
                or ranked_roles.index("decoy") < ranked_roles.index("pre_cue")
            ):
                decoy_first += 1
        rows.append(
            {
                "signal": signal,
                "triggers": fired,
                "decoy_triggers": decoy_hits,
                "top1_decoy_seeds": top1,
                "all_topk_decoy_seeds": all_top,
                "trigger_roles": roles,
                "top1_role_seeds": top1_roles,
                "decoy_before_pre_cue_seeds": decoy_first,
                # ``reward`` scores are in reward points, TD-family scores already in milli.
                "max_score_milli_by_role": {
                    role: _milli(peak[role]) if signal == "reward" else int(peak[role])
                    for role in ROLES
                    if role in peak
                },
            }
        )
    return rows


def _fits(config: BenchmarkConfig) -> dict[str, Any]:
    return {
        "value_by_cue_feature_milli": {
            str(key): _milli(val) for key, val in sorted(fit_value(config).items())
        },
        "reward_mean_by_cue_feature_milli": {
            str(key): _milli(val) for key, val in sorted(fit_reward_mean(config).items())
        },
        "manifest_digests": [
            measure_seed(config, seed).manifest_digest for seed in config.eval_seeds
        ],
    }


def _ranking(
    summary: Sequence[Mapping[str, Any]], key: str, budgets: Sequence[int], *, reverse: bool
) -> list[list[list[str]]] | None:
    """Per budget, selector tie-groups ordered by ``key``; ``None`` if undefined."""

    ranking = []
    for budget in budgets:
        values: dict[Any, list[str]] = {}
        for row in summary:
            if row["budget"] != budget:
                continue
            if row[key] is None:
                return None
            values.setdefault(row[key], []).append(f"{row['selector']}:{row['lookback']}")
        ranking.append([sorted(values[value]) for value in sorted(values, reverse=reverse)])
    return ranking


def _regret_ranking(cell: _Cell, budgets: Sequence[int]) -> list[list[list[str]]]:
    ranking = []
    for budget in budgets:
        values: dict[Fraction, list[str]] = {}
        for (selector, lookback, row_budget), total in cell.regret.items():
            if row_budget == budget:
                values.setdefault(total, []).append(f"{selector}:{lookback}")
        ranking.append([sorted(values[value]) for value in sorted(values)])
    return ranking


def _gamma_cells(sweep: SweepConfig) -> list[dict[str, Any]]:
    cells = []
    for delay in sweep.delays:
        config = sweep.delay_config(delay)
        reference = _evaluate_cell(config, Fraction(1))
        reference_recall = _ranking(
            reference.summary, "mean_recall_milli", config.budgets, reverse=True
        )
        reference_regret = _regret_ranking(reference, config.budgets)
        for gamma in sweep.oracle_gammas:
            gamma = Fraction(gamma)
            cell = reference if gamma == 1 else _evaluate_cell(config, gamma)
            recall = _ranking(cell.summary, "mean_recall_milli", config.budgets, reverse=True)
            important_gains = [
                gain
                for seed in cell.seeds
                for gain in seed["decision_gains"]
                if gain >= config.gain_threshold
            ]
            best = [seed["oracle_best"] for seed in cell.seeds]
            cells.append(
                {
                    "delay": delay,
                    "gamma": _pair(gamma),
                    "important_changed_seeds": sum(
                        1
                        for seed, ref in zip(cell.seeds, reference.seeds)
                        if seed["important"] != ref["important"]
                    ),
                    "positive_changed_seeds": sum(
                        1
                        for seed, ref in zip(cell.seeds, reference.seeds)
                        if seed["positive"] != ref["positive"]
                    ),
                    "important_empty_seeds": sum(1 for seed in cell.seeds if not seed["important"]),
                    "min_important_gain_milli": (
                        _milli(min(important_gains)) if important_gains else None
                    ),
                    "oracle_best_gain_milli": [_milli(min(best)), _milli(max(best))],
                    "ranking_matches_gamma_one": {
                        "recall": (
                            None
                            if recall is None or reference_recall is None
                            else recall == reference_recall
                        ),
                        "regret": _regret_ranking(cell, config.budgets) == reference_regret,
                    },
                    "summary": [dict(row) for row in cell.summary],
                }
            )
    return cells


def _summary_cell(config: BenchmarkConfig) -> dict[str, Any]:
    cell = _evaluate_cell(config, Fraction(1))
    density = [seed["density_milli"] for seed in cell.seeds]
    return {
        **_fits(config),
        "density_milli": [min(density), max(density)],
        "dominance": _dominance(config),
        "summary": [dict(row) for row in cell.summary],
    }


def _variant_view(cell: Mapping[str, Any], budgets: Sequence[int]) -> dict[str, Any]:
    names = ("td", *VARIANTS)
    rows = {
        (row["selector"], row["budget"]): row
        for row in cell["summary"]
        if row["selector"] in names and row["lookback"] == 0
    }
    keys = ("mean_hazard_recall_milli", "mean_opportunity_recall_milli", "mean_recall_milli")
    versus = []
    for name in VARIANTS:
        for budget in budgets:
            mine, plain = rows[(name, budget)], rows[("td", budget)]
            versus.append(
                {
                    "variant": name,
                    "budget": budget,
                    **{
                        f"{key}_delta": (
                            None
                            if mine[key] is None or plain[key] is None
                            else mine[key] - plain[key]
                        )
                        for key in keys
                    },
                    "triggered_delta_milli": mine["mean_triggered_milli"]
                    - plain["mean_triggered_milli"],
                }
            )
    return {
        "dominance": [row for row in cell["dominance"] if row["signal"] in names],
        "summary": [row for row in cell["summary"] if row["selector"] in names],
        "versus_td_lookback_0": versus,
    }


def _lookup(
    summary: Sequence[Mapping[str, Any]], selector: str, lookback: int, budget: int
) -> dict:
    (row,) = [
        item
        for item in summary
        if (item["selector"], item["lookback"], item["budget"]) == (selector, lookback, budget)
    ]
    return dict(row)


def _phase1_checks(
    sweep: SweepConfig,
    gamma_cells: Sequence[Mapping[str, Any]],
    decoy_cells: Sequence[Mapping[str, Any]],
    delay_cells: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    budgets = sweep.base.budgets

    def dominance(cell: Mapping[str, Any], signal: str, key: str) -> int:
        (row,) = [item for item in cell["dominance"] if item["signal"] == signal]
        return row[key]

    def by_budget(
        summary: Sequence[Mapping[str, Any]], selector: str, lookback: int, key: str
    ) -> dict:
        return {str(b): _lookup(summary, selector, lookback, b)[key] for b in budgets}

    all_cells = [*decoy_cells, *delay_cells]
    hits = sum(
        row["opportunity_proposed_seeds"]
        for cell in [*all_cells, *gamma_cells]
        for row in cell["summary"]
    )
    return {
        "f1_sparsity": {
            "density_milli": sorted({v for cell in all_cells for v in cell["density_milli"]}),
            "cells_with_empty_important_set": [
                [cell["delay"], *cell["gamma"]]
                for cell in gamma_cells
                if cell["important_empty_seeds"] == len(sweep.base.eval_seeds)
            ],
            "cells_with_changed_positive_set": [
                [cell["delay"], *cell["gamma"]]
                for cell in gamma_cells
                if cell["positive_changed_seeds"]
            ],
        },
        "f2_decoy_domination": {
            **{
                f"{signal}_{key}": {
                    str(cell["decoy_reward"]): dominance(cell, signal, key) for cell in decoy_cells
                }
                for signal in SIGNALS
                for key in ("all_topk_decoy_seeds", "top1_decoy_seeds")
            },
            "td_decoy_before_pre_cue_seeds": {
                str(cell["decoy_reward"]): dominance(cell, "td", "decoy_before_pre_cue_seeds")
                for cell in decoy_cells
            },
            "td_top1_role_seeds_by_decoy": {
                str(cell["decoy_reward"]): dominance(cell, "td", "top1_role_seeds")
                for cell in decoy_cells
            },
            "by_delay_td_all_topk_decoy_seeds": {
                str(cell["delay"]): dominance(cell, "td", "all_topk_decoy_seeds")
                for cell in delay_cells
            },
        },
        "f3_reward_hazard_recall": {
            str(cell["delay"]): {
                str(lookback): {
                    "chosen": by_budget(
                        cell["summary"], "reward", lookback, "mean_hazard_recall_milli"
                    ),
                    "triggered": by_budget(
                        cell["summary"], "reward", lookback, "mean_triggered_hazard_recall_milli"
                    ),
                }
                for lookback in sweep.lookbacks(cell["delay"])
            }
            for cell in delay_cells
        },
        "f3_td_l0_hazard_recall": {
            str(cell["delay"]): {
                "chosen": by_budget(cell["summary"], "td", 0, "mean_hazard_recall_milli"),
                "triggered": by_budget(
                    cell["summary"], "td", 0, "mean_triggered_hazard_recall_milli"
                ),
            }
            for cell in delay_cells
        },
        "f4_td_recall_by_lookback": {
            str(cell["decoy_reward"]): {
                str(lookback): by_budget(cell["summary"], "td", lookback, "mean_recall_milli")
                for lookback in sweep.base.lookbacks
            }
            for cell in decoy_cells
        },
        "f5_silent_opportunities": {
            "opportunity_trigger_hits": hits,
            "uniform_opportunity_recall_by_decoy": {
                str(cell["decoy_reward"]): by_budget(
                    cell["summary"], "uniform", 0, "mean_opportunity_recall_milli"
                )
                for cell in decoy_cells
            },
        },
    }


def clear_caches() -> None:
    """Drop every memoized measurement, including the Phase 1 value fit."""

    for cached in (
        measure_seed,
        _trigger_steps,
        _trigger_selection,
        _evaluate_cell,
        fit_reward_mean,
        fit_value,
    ):
        cached.cache_clear()


def run_sweeps(sweep: SweepConfig | None = None) -> dict[str, Any]:
    """Run all four sweeps on held-out seeds; deterministic, integer-only report."""

    sweep = SweepConfig() if sweep is None else sweep
    gamma_cells = _gamma_cells(sweep)
    decoy_cells = [
        {"decoy_reward": reward, **_summary_cell(sweep.decoy_config(reward))}
        for reward in sweep.decoy_rewards
    ]
    delay_cells = [
        {
            "delay": delay,
            "lookbacks": list(sweep.lookbacks(delay)),
            **_summary_cell(sweep.delay_config(delay)),
        }
        for delay in sweep.delays
    ]
    variant_cells = [
        {"decoy_reward": cell["decoy_reward"], **_variant_view(cell, sweep.base.budgets)}
        for cell in decoy_cells
    ]
    report: dict[str, Any] = {
        "evidence_label": "synthetic",
        "config": sweep.to_payload(),
        "gamma_sweep": gamma_cells,
        "decoy_sweep": decoy_cells,
        "delay_sweep": delay_cells,
        "variant_sweep": variant_cells,
        "phase1_checks": _phase1_checks(sweep, gamma_cells, decoy_cells, delay_cells),
    }
    report["report_digest"] = content_digest(REPORT_DOMAIN, report)
    return report


__all__ = [
    "ROLES",
    "SIGNALS",
    "TRIGGER_SELECTORS",
    "VARIANTS",
    "SeedMeasurement",
    "SweepConfig",
    "branch_reward_diffs",
    "clear_caches",
    "discounted_gain",
    "fit_reward_mean",
    "measure_seed",
    "trigger_role",
    "run_sweeps",
]
