"""Agent interaction-order benchmark: world mechanics, branch-measured terms, estimators.

The finding tests at the bottom pin the observed synthetic behavior at a
reduced configuration (8 seeds, 6 agents). They are regressions on this
benchmark, not claims about the runtime: the coupling structure, its sparsity,
and which couplings are delayed are all chosen by the world generator.
"""

from __future__ import annotations

from itertools import combinations

import pytest

from python.experiment.interaction_order import ACT
from python.experiment.interaction_order import ESTIMATORS
from python.experiment.interaction_order import GATED
from python.experiment.interaction_order import HOLD
from python.experiment.interaction_order import BranchTable
from python.experiment.interaction_order import InteractionConfig
from python.experiment.interaction_order import InteractionError
from python.experiment.interaction_order import InteractionWorld
from python.experiment.interaction_order import QueryLedger
from python.experiment.interaction_order import Term
from python.experiment.interaction_order import estimate
from python.experiment.interaction_order import evaluate
from python.experiment.interaction_order import joint_actions
from python.experiment.interaction_order import make_world
from python.experiment.interaction_order import open_decision_session
from python.experiment.interaction_order import predict
from python.experiment.interaction_order import run_label
from python.experiment.interaction_order import runs
from python.experiment.interaction_order import sample_holdout

DECISION = 2


def _world(*terms: tuple, n: int = 4, max_steps: int = 8, base: int = 1) -> InteractionWorld:
    return InteractionWorld(
        agent_count=n,
        terms=tuple(Term(agents, amount, delay) for agents, amount, delay in terms),
        max_steps=max_steps,
        base_reward=base,
    )


_MAINS4 = (((0,), 3, 0), ((1,), -2, 0), ((2,), 4, 0), ((3,), -1, 0))
#: Instant pair (0, 1) worth +5; pair (2, 3) worth -6, paid three steps later.
PLANTED = _world(*_MAINS4, ((0, 1), 5, 0), ((2, 3), -6, 3))
UNCOUPLED = _world(*_MAINS4)

_MAINS6 = (((0,), 2, 0), ((1,), -3, 0), ((2,), 1, 0), ((3,), -1, 0), ((4,), 4, 0), ((5,), -2, 0))
UNCOUPLED6 = _world(*_MAINS6, n=6, max_steps=10)
#: Instant (0, 3) worth +6 and (1, 4) worth -4 paid four steps later. The two do
#: not cancel to within tolerance; the cancelling case has its own test below.
PAIRS6 = _world(*_MAINS6, ((0, 3), 6, 0), ((1, 4), -4, 4), n=6, max_steps=10)
#: A pure triple synergy with no pairwise terms at all.
TRIPLE6 = _world(*_MAINS6, ((1, 2, 5), 9, 0), n=6, max_steps=10)


def _table(world: InteractionWorld, horizon: int, seed: int = 0):
    session, snapshot = open_decision_session(world, seed, DECISION)
    return session, BranchTable(session, snapshot, horizon)


def _pair_term(q, n: int, i: int, j: int) -> int:
    def corner(*agents: int) -> tuple[int, ...]:
        return tuple(1 if index in agents else 0 for index in range(n))

    return q(corner(i, j)) - q(corner(i)) - q(corner(j)) + q(corner())


# --- world mechanics -----------------------------------------------------------


def test_world_pays_main_effects_now_and_couplings_on_schedule() -> None:
    state = PLANTED.initial_state(0, 4)
    state, rewards, done = PLANTED.step(state, (ACT, ACT, HOLD, HOLD))
    # base 1 each; mains +3 / -2; the instant +5 coupling is split 3 + 2.
    assert rewards == (1 + 3 + 3, 1 - 2 + 2, 1, 1) and not done
    assert PLANTED.encode_state(state) == {"step": 1, "pending": []}
    state, rewards, _ = PLANTED.step(state, (HOLD, HOLD, ACT, ACT))
    assert rewards == (1, 1, 1 + 4, 1 - 1)
    assert PLANTED.encode_state(state) == {"step": 2, "pending": [[4, 5]]}
    for _ in range(2):
        state, rewards, _ = PLANTED.step(state, (HOLD,) * 4)
        assert rewards == (1, 1, 1, 1)
    state, rewards, _ = PLANTED.step(state, (HOLD,) * 4)
    assert rewards == (1, 1, 1 - 3, 1 - 3)
    assert PLANTED.encode_state(state) == {"step": 5, "pending": []}
    for _ in range(2):
        state, _, done = PLANTED.step(state, (HOLD,) * 4)
        assert not done
    _, _, done = PLANTED.step(state, (HOLD,) * 4)
    assert done


def test_planted_coefficients_drop_couplings_paid_after_the_horizon() -> None:
    assert PLANTED.coefficients(3) == {
        (): 12,
        (0,): 3,
        (1,): -2,
        (2,): 4,
        (3,): -1,
        (0, 1): 5,
    }
    assert PLANTED.coefficients(4)[(2, 3)] == -6


@pytest.mark.parametrize(
    "agents, amount, delay",
    [
        ((1, 0), 3, 0),
        ((0, 0), 3, 0),
        ((), 3, 0),
        ((-1,), 3, 0),
        ((True,), 3, 0),
        ((0,), 0, 0),
        ((0,), True, 0),
        ((0,), 3, -1),
        ((0,), 3.0, 0),
        ([0], 3, 0),
    ],
)
def test_terms_fail_closed(agents: object, amount: object, delay: object) -> None:
    with pytest.raises(InteractionError):
        Term(agents, amount, delay)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "overrides",
    [
        {"agent_count": 1},
        {"agent_count": 11},
        {"terms": (Term((4,), 1),)},
        {"terms": (Term((0, 1), 1), Term((0, 1), 2))},
        {"terms": ((0, 1),)},
        {"max_steps": 0},
        {"base_reward": True},
    ],
)
def test_world_fails_closed(overrides: dict) -> None:
    fields = {"agent_count": 4, "terms": (), "max_steps": 8}
    fields.update(overrides)
    with pytest.raises(InteractionError):
        InteractionWorld(**fields)


def test_world_step_and_branch_table_reject_malformed_actions() -> None:
    state = PLANTED.initial_state(0, 4)
    for actions in ((ACT, ACT, HOLD), (ACT, ACT, HOLD, "wait"), [ACT, ACT, HOLD, HOLD]):
        with pytest.raises(InteractionError):
            PLANTED.step(state, actions)  # type: ignore[arg-type]
    with pytest.raises(InteractionError):
        PLANTED.initial_state(0, 3)
    _, table = _table(PLANTED, 6)
    for bits in ((1, 0, 0), (1, 0, 0, 2), (1, 0, 0, True), [1, 0, 0, 0]):
        with pytest.raises(InteractionError):
            table(bits)  # type: ignore[arg-type]
    session, snapshot = open_decision_session(PLANTED, 0, DECISION)
    with pytest.raises(InteractionError):
        BranchTable(session, snapshot, 7)  # runs past max_steps
    with pytest.raises(InteractionError):
        open_decision_session(PLANTED, 0, 8)


def test_estimators_fail_closed() -> None:
    _, table = _table(PLANTED, 6)
    with pytest.raises(InteractionError):
        estimate("order_9", table, 4)
    with pytest.raises(InteractionError):
        estimate("adaptive", table, 4, holdout=())
    with pytest.raises(InteractionError):
        estimate("adaptive", table, 4, holdout=((1, 1, 0),))
    with pytest.raises(InteractionError):
        estimate("adaptive", table, 4, holdout=((1, 1, 0, 0),), max_order=4)
    with pytest.raises(InteractionError):
        estimate("additive_m1", table, 4, tolerance=-1)


@pytest.mark.parametrize(
    "overrides",
    [
        {"seeds": ()},
        {"seeds": (2, 1)},
        {"seeds": (-1,)},
        {"agent_counts": (2,)},
        {"agent_counts": (11,)},
        {"agent_counts": (6, 4)},
        {"horizons": (8, 2)},
        {"horizons": (2,)},
        {"horizons": (0, 8)},
        {"decision_step": -1},
        {"main_min": 6},
        {"coupling_min": 0},
        {"coupling_min": 9},
        {"tolerance": 2},
        {"edge_threshold": 0},
        {"edge_threshold": 3},
        {"triple_min": 0},
        {"triple_min": 11},
        {"max_pairs": 7, "agent_counts": (4,)},
        {"delayed_milli": 1001},
        {"triple_milli": -1},
        {"holdout_sizes": ()},
        {"holdout_sizes": (0, 8)},
        {"holdout_sizes": (8, 4)},
        {"tolerance": -1},
        {"max_order": 4},
        {"max_order": 0},
    ],
)
def test_config_fails_closed(overrides: dict) -> None:
    with pytest.raises(InteractionError):
        InteractionConfig(**overrides)


def test_generated_worlds_are_seeded_and_place_delayed_couplings_between_horizons() -> None:
    config = InteractionConfig()
    assert make_world(config, 6, 301) == make_world(config, 6, 301)
    delays = set()
    for seed in config.seeds:
        world = make_world(config, 6, seed)
        assert world.max_steps == config.decision_step + max(config.horizons)
        for term in world.terms:
            if term.order == 1:
                assert term.delay == 0 and config.main_min <= abs(term.amount) <= config.main_max
            elif term.order == 2:
                assert config.coupling_min <= abs(term.amount) <= config.coupling_max
            else:
                assert term.order == 3 and term.delay == 0
                assert config.triple_min <= abs(term.amount) <= config.triple_max
            if term.order > 1:
                assert term.delay == 0 or min(config.horizons) <= term.delay < max(config.horizons)
                delays.add(term.delay)
        assert sum(1 for term in world.terms if term.order == 2) <= config.max_pairs
    assert 0 in delays and len(delays) > 1


def test_holdout_is_seeded_distinct_and_multi_agent() -> None:
    holdout = sample_holdout(6, 301, 8)
    assert holdout == sample_holdout(6, 301, 8)
    assert len(set(holdout)) == 8 and all(sum(bits) >= 2 for bits in holdout)
    assert len(sample_holdout(3, 1, 8)) == 4  # only four 3-agent actions have >= 2 actors
    # Nested: a larger holdout for the same seed extends the smaller one.
    assert set(sample_holdout(6, 301, 4)) <= set(holdout) <= set(sample_holdout(6, 301, 16))


# --- branch-measured interaction terms ------------------------------------------


def test_branch_measured_pair_terms_equal_the_planted_couplings() -> None:
    session, table = _table(PLANTED, 6)
    assert _pair_term(table, 4, 0, 1) == 5
    assert _pair_term(table, 4, 2, 3) == -6
    for i, j in [(0, 2), (0, 3), (1, 2), (1, 3)]:
        assert _pair_term(table, 4, i, j) == 0
    model = estimate("pairwise_m2", table, 4).coefficients
    assert {s: v for s, v in model.items() if len(s) == 2} == {
        (0, 1): 5,
        (0, 2): 0,
        (0, 3): 0,
        (1, 2): 0,
        (1, 3): 0,
        (2, 3): -6,
    }
    assert [model[(i,)] for i in range(4)] == [3, -2, 4, -1]
    assert model[()] == 4 * 6
    assert table.branches == 1 + 4 + 6
    children = [t for t in session.manifest().branches if t.branch.parent_digest is not None]
    assert len(children) == table.branches
    for trace in children:
        assert trace.branch.origin_step == DECISION
        assert len(trace.branch.intervention) == 4
        assert len(trace.transitions) == 6


def test_exhaustive_expansion_recovers_exactly_the_planted_terms() -> None:
    for horizon in (2, 6):
        _, table = _table(PLANTED, horizon)
        model = estimate("exhaustive", table, 4).coefficients
        assert {s: v for s, v in model.items() if v} == PLANTED.coefficients(horizon)
        assert table.branches == 16


def test_estimator_branch_costs_are_fixed_by_order() -> None:
    _, table = _table(TRIPLE6, 8)
    for name, cost in [("additive_m1", 7), ("pairwise_m2", 22), ("triple_m3", 42), ("exhaustive", 64)]:
        ledger = QueryLedger(table)
        estimate(name, ledger, 6)
        assert ledger.branches == cost


def test_additive_estimator_is_exact_without_coupling_and_wrong_with_it() -> None:
    _, table = _table(UNCOUPLED, 6)
    model = estimate("additive_m1", table, 4).coefficients
    assert all(predict(model, bits) == table(bits) for bits in joint_actions(4))

    _, table = _table(PLANTED, 6)
    model = estimate("additive_m1", table, 4).coefficients
    error = {bits: predict(model, bits) - table(bits) for bits in joint_actions(4)}
    assert error[(1, 1, 0, 0)] == -5
    assert error[(0, 0, 1, 1)] == 6
    assert error[(1, 1, 1, 1)] == 1  # +5 and -6 partly cancel
    assert max(abs(value) for value in error.values()) == 6
    predicted_best = max(joint_actions(4), key=lambda bits: (predict(model, bits), bits))
    assert predicted_best == (1, 0, 1, 0)
    assert table((1, 0, 1, 0)) == 31 and max(table(bits) for bits in joint_actions(4)) == 34


@pytest.mark.parametrize("horizon, delayed", [(2, 0), (3, 0), (4, -6), (6, -6)])
def test_delayed_coupling_is_zero_at_short_horizon(horizon: int, delayed: int) -> None:
    _, table = _table(PLANTED, horizon)
    assert _pair_term(table, 4, 0, 1) == 5
    assert _pair_term(table, 4, 2, 3) == delayed


def test_triple_synergy_is_invisible_to_pairwise_terms() -> None:
    _, table = _table(TRIPLE6, 8)
    pairwise = estimate("pairwise_m2", table, 6).coefficients
    assert all(value == 0 for subset, value in pairwise.items() if len(subset) == 2)
    assert estimate("triple_m3", table, 6).coefficients[(1, 2, 5)] == 9


# --- adaptive escalation -----------------------------------------------------------


@pytest.mark.parametrize(
    "world, horizon, stop_order, edges, triples",
    [
        (UNCOUPLED6, 8, 1, set(), set()),
        (PAIRS6, 2, 2, {(0, 3)}, set()),
        (PAIRS6, 8, 2, {(0, 3), (1, 4)}, set()),
        (TRIPLE6, 8, 3, set(), {(1, 2, 5)}),
    ],
)
def test_adaptive_escalation_spends_less_than_exhaustive_and_matches_its_best_action(
    world: InteractionWorld, horizon: int, stop_order: int, edges: set, triples: set
) -> None:
    _, table = _table(world, horizon, seed=11)
    ledger = QueryLedger(table)
    result = estimate("adaptive", ledger, 6, holdout=sample_holdout(6, 11, 16), tolerance=1)
    assert ledger.branches < 2**6 // 2
    assert result.stop_order == stop_order and not result.unresolved
    assert result.edges(1) == edges
    assert result.hyperedges(3, 1) == triples
    truth = {bits: table(bits) for bits in joint_actions(6)}
    assert all(predict(result.coefficients, bits) == truth[bits] for bits in truth)
    exhaustive = estimate("exhaustive", table, 6).coefficients
    best = max(truth, key=lambda bits: (predict(exhaustive, bits), bits))
    assert max(truth, key=lambda bits: (predict(result.coefficients, bits), bits)) == best


def test_a_coupling_no_holdout_action_contains_is_never_measured() -> None:
    # Seed-11 holdouts of size 4 and 8 contain no action where agents 1 and 4
    # both act, so the delayed (1, 4) coupling stays invisible to the gate.
    _, table = _table(PAIRS6, 8, seed=11)
    for size in (4, 8):
        holdout = sample_holdout(6, 11, size)
        assert not any(bits[1] and bits[4] for bits in holdout)
        result = estimate("adaptive", table, 6, holdout=holdout, tolerance=1)
        assert result.edges(1) == {(0, 3)} and result.holdout_residual == 0
    # Agents 1, 2, 5 never act together in the size-4 holdout, so the gate stops at M=1.
    _, table = _table(TRIPLE6, 8, seed=11)
    assert estimate("adaptive", table, 6, holdout=sample_holdout(6, 11, 4), tolerance=1).stop_order == 1


def test_adaptive_stops_at_order_one_when_the_holdout_is_clean() -> None:
    _, table = _table(UNCOUPLED6, 8, seed=11)
    ledger = QueryLedger(table)
    result = estimate("adaptive", ledger, 6, holdout=sample_holdout(6, 11, 8), tolerance=1)
    assert result.holdout_residual == 0
    assert ledger.branches == 1 + 6 + 8


def test_screening_relies_on_terms_not_cancelling() -> None:
    world = _world(((0, 1), 5, 0), ((2, 3), -5, 0))
    _, table = _table(world, 2)
    # The all-act probe sums +5 and -5 to zero, looks clean, and stops at M=1.
    fooled = estimate("adaptive", table, 4, holdout=((1, 1, 1, 1),), tolerance=1)
    assert fooled.stop_order == 1 and fooled.edges(1) == frozenset() and not fooled.unresolved
    assert fooled.holdout_residual == 0
    # A second probe exposes the residual. The clean all-act probe "certifies"
    # (0, 1), so no uncertified candidate is left; the fallback measures the
    # certified pair, which turns the all-act probe dirty and exposes (2, 3).
    found = estimate("adaptive", table, 4, holdout=((1, 1, 0, 0), (1, 1, 1, 1)), tolerance=1)
    assert found.edges(1) == {(0, 1), (2, 3)} and not found.unresolved
    assert found.fallbacks == 1
    assert estimate("exhaustive", table, 4).edges(1) == {(0, 1), (2, 3)}


def test_gated_escalation_measures_every_pair_once_the_holdout_is_dirty() -> None:
    _, table = _table(PAIRS6, 8, seed=11)
    ledger = QueryLedger(table)
    result = estimate("gated", ledger, 6, holdout=sample_holdout(6, 11, 8), tolerance=1)
    assert result.stop_order == 2 and not result.unresolved
    assert ledger.branches == 1 + 6 + 8 + 15 - sum(
        1 for bits in sample_holdout(6, 11, 8) if sum(bits) == 2
    )
    assert result.edges(1) == {(0, 3), (1, 4)}


# --- report ------------------------------------------------------------------------

SMALL = InteractionConfig(seeds=tuple(range(301, 309)), agent_counts=(6,), holdout_sizes=(4, 8, 16))


@pytest.fixture(scope="module")
def report() -> dict:
    return evaluate(SMALL)


def _row(report: dict, estimator: str, horizon: int, holdout_size: int | None = None) -> dict:
    (row,) = [
        item
        for item in report["summary"]
        if item["estimator"] == estimator
        and item["horizon"] == horizon
        and item["holdout_size"] == holdout_size
        and item["agent_count"] == 6
    ]
    return row


def _need(report: dict, horizon: int) -> dict:
    (row,) = [item for item in report["order_need"] if item["horizon"] == horizon and item["agent_count"] == 6]
    return row


def test_report_is_synthetic_and_deterministic() -> None:
    tiny = InteractionConfig(seeds=(301, 302), agent_counts=(4,))
    first = evaluate(tiny)
    second = evaluate(tiny)
    assert first == second
    assert first["evidence_label"] == "synthetic"
    assert first["config"] == tiny.to_payload()
    assert first["runs"] == [[name, size] for name, size in runs(tiny)]
    assert {name for name, _ in runs(tiny)} == set(ESTIMATORS)
    assert all(size is None for name, size in runs(tiny) if name not in GATED)
    assert len(first["report_digest"]) == 64
    assert first["report_digest"] != evaluate(InteractionConfig(seeds=(303, 304), agent_counts=(4,)))[
        "report_digest"
    ]


def test_fixed_order_costs_and_exhaustive_reference(report: dict) -> None:
    seeds = len(SMALL.seeds)
    for horizon in SMALL.horizons:
        for name, cost in [("additive_m1", 7), ("pairwise_m2", 22), ("triple_m3", 42), ("exhaustive", 64)]:
            row = _row(report, name, horizon)
            assert row["total_branches"] == cost * seeds
            assert row["branch_steps"] == cost * seeds * horizon
        exhaustive = _row(report, "exhaustive", horizon)
        assert exhaustive["max_abs_error"] == 0
        assert exhaustive["best_correct_seeds"] == seeds
        assert exhaustive["edge_precision_milli"] in (1000, None)
        assert exhaustive["edge_recall_milli"] in (1000, None)
        # The generator plants nothing above third order, so M=3 is exact.
        assert _row(report, "triple_m3", horizon)["max_abs_error"] == 0


def test_seed_rows_bind_each_seed_to_its_branch_manifest(report: dict) -> None:
    assert len(report["seeds"]) == len(SMALL.seeds)
    for row in report["seeds"]:
        assert len(row["manifest_digest"]) == 64
        assert [item["horizon"] for item in row["horizons"]] == list(SMALL.horizons)
        for item in row["horizons"]:
            assert set(item["estimators"]) == {run_label(name, size) for name, size in runs(SMALL)}


def test_delayed_couplings_only_appear_at_the_long_horizon(report: dict) -> None:
    short, long = SMALL.horizons
    for row in report["seeds"]:
        by_h = {item["horizon"]: item for item in row["horizons"]}
        short_edges = {tuple(edge) for edge in by_h[short]["true_edges"]}
        long_edges = {tuple(edge) for edge in by_h[long]["true_edges"]}
        assert short_edges <= long_edges
        delayed = {
            tuple(term["agents"]) for term in row["terms"] if len(term["agents"]) == 2 and term["delay"]
        }
        assert long_edges - short_edges == delayed
    assert _need(report, short)["m1_suffices_seeds"] >= _need(report, long)["m1_suffices_seeds"]


def test_coefficient_keys_follow_combination_order() -> None:
    # Coefficient keys are the sorted agent tuples that itertools.combinations yields.
    _, table = _table(PLANTED, 6)
    model = estimate("pairwise_m2", table, 4).coefficients
    assert [s for s in model if len(s) == 2] == list(combinations(range(4), 2))


# --- findings at the reduced configuration (8 seeds, N = 6) -------------------------


def test_order_need_tracks_the_generator_and_grows_with_horizon(report: dict) -> None:
    short, long = _need(report, 2), _need(report, 8)
    # By construction: M=1 suffices exactly on seeds with no visible coupling,
    # M=2 on seeds with no triple, M=3 always.
    for need in (short, long):
        assert need["m1_suffices_seeds"] == need["uncoupled_seeds"]
        assert need["m3_suffices_seeds"] == 8
    assert (short["m1_suffices_seeds"], long["m1_suffices_seeds"]) == (2, 1)
    assert (short["m2_suffices_seeds"], long["m2_suffices_seeds"]) == (6, 6)
    assert (short["m1_best_correct_seeds"], long["m1_best_correct_seeds"]) == (5, 3)
    assert (_row(report, "pairwise_m2", 2)["edge_true"], _row(report, "pairwise_m2", 8)["edge_true"]) == (6, 13)


def test_additive_ranks_worse_at_the_long_horizon(report: dict) -> None:
    short, long = _row(report, "additive_m1", 2), _row(report, "additive_m1", 8)
    assert (short["max_abs_error"], long["max_abs_error"]) == (11, 16)
    assert (short["total_best_regret"], long["total_best_regret"]) == (11, 24)
    assert _row(report, "pairwise_m2", 8)["best_correct_seeds"] == 8


def test_gate_false_accepts_shrink_with_holdout_size(report: dict) -> None:
    gate = {item["holdout_size"]: item for item in _need(report, 2)["gate"]}
    assert gate[4]["m1_false_accept_seeds"] == 1
    assert gate[8]["m1_false_accept_seeds"] == gate[16]["m1_false_accept_seeds"] == 0
    for horizon in SMALL.horizons:
        assert all(item["m1_false_escalate_seeds"] == 0 for item in _need(report, horizon)["gate"])


def test_adaptive_matches_exhaustive_best_at_a_third_of_its_branches(report: dict) -> None:
    for horizon, branches in ((2, 158), (8, 167)):
        row = _row(report, "adaptive", horizon, 8)
        assert row["total_branches"] == branches
        assert 3 * row["total_branches"] < _row(report, "exhaustive", horizon)["total_branches"]
        assert row["best_correct_seeds"] == 8
        assert (row["edge_precision_milli"], row["edge_recall_milli"]) == (1000, 1000)
        # One seed keeps a triple outside every holdout action at size 8.
        assert row["within_tolerance_seeds"] == 7 and row["triple_recall_milli"] == 500
    small = _row(report, "adaptive", 8, 4)
    assert (small["edge_recall_milli"], small["best_correct_seeds"]) == (692, 7)
    # Screening only saves branches; with the same holdout it never adds terms the gate misses.
    for horizon in SMALL.horizons:
        for size in SMALL.holdout_sizes:
            adaptive, gated = _row(report, "adaptive", horizon, size), _row(report, "gated", horizon, size)
            assert adaptive["total_branches"] <= gated["total_branches"]
            assert adaptive["edge_tp"] <= gated["edge_tp"]
