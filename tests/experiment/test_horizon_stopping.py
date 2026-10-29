"""Adaptive horizon stopping (E1, ``H4``): world mechanics, Q_H, rules, findings.

The finding tests pin the observed synthetic behavior. They are regressions on
the benchmark, not claims about the runtime.
"""

from __future__ import annotations

import subprocess
import sys
from fractions import Fraction

import pytest

import python.experiment.horizon_stopping as hs
from python.experiment.counterfactual_toy import REWARD_UNITS_PER_POINT
from python.experiment.counterfactual_toy import rollout_branch
from python.experiment.horizon_stopping import COMMIT
from python.experiment.horizon_stopping import HOLD
from python.experiment.horizon_stopping import Decision
from python.experiment.horizon_stopping import HorizonConfig
from python.experiment.horizon_stopping import HorizonError
from python.experiment.horizon_stopping import HorizonProbe
from python.experiment.horizon_stopping import HorizonWorld
from python.experiment.horizon_stopping import OracleValue
from python.experiment.horizon_stopping import StoppingRule
from python.experiment.horizon_stopping import evaluate
from python.experiment.horizon_stopping import fit_value
from python.experiment.horizon_stopping import make_world
from python.experiment.horizon_stopping import pending_feature
from python.experiment.horizon_stopping import rollout_baseline
from python.experiment.horizon_stopping import rule_grid
from python.experiment.horizon_stopping import run_rule
from python.experiment.horizon_stopping import zero_value
from python.experiment.reference_session import DelayedCommitmentWorld
from python.experiment.reference_session import ReferenceSession

GAMMA = Fraction(9, 10)
SCHEDULE = (1, 2, 4, 8, 16)
SMALL = HorizonConfig(train_seeds=tuple(range(301, 309)), eval_seeds=tuple(range(401, 409)))
RANK = StoppingRule("rank_agreement")
FIXED = StoppingRule("fixed_max")


@pytest.fixture(scope="module")
def report() -> dict:
    return evaluate()


def _row(report: dict, value: str, kind: str, threshold: Fraction | None = None) -> dict:
    wanted = None if threshold is None else [threshold.numerator, threshold.denominator]
    (row,) = [
        item
        for item in report["summary"]
        if item["value"] == value and item["rule"] == kind and item["threshold"] == wanted
    ]
    return row


def _need(report: dict, value: str) -> dict:
    (row,) = [item for item in report["horizon_need"] if item["value"] == value]
    return row


def _single(cost: int = 3, payoff: int = 10, delay: int = 5, step: int = 2, length: int = 40) -> HorizonWorld:
    return HorizonWorld(length=length, decisions=(Decision(step=step, cost=cost, payoff=payoff, delay=delay),))


def _probe(world: HorizonWorld, step: int, label: str = "probe") -> HorizonProbe:
    base = rollout_baseline(world, seed=0)
    return HorizonProbe(
        base.session,
        base.session.baseline,
        base.heads[step],
        base.states[step],
        continuation="hold",
        gamma=GAMMA,
        label=label,
    )


def _rewards(world: HorizonWorld, actions: dict[int, str]) -> list[int]:
    session = ReferenceSession.open(
        session_id="mechanics", seed=0, agent_ids=("agent_0",), policy_ref="probe", world=world
    )
    rewards = []
    step = 0
    while not session.is_terminated(session.baseline):
        transition = session.step(
            session.baseline,
            {"agent_0": actions.get(step, HOLD)},
            observation_provenance="decision_belief_packet",
        )
        rewards.append(transition.rewards[0][1])
        step += 1
    return rewards


def test_import_has_no_runtime_bootstrap_side_effects() -> None:
    probe = (
        "import sys\n"
        "import python.experiment.horizon_stopping\n"
        "roots = {name.split('.')[0] for name in sys.modules}\n"
        "assert not roots & {'ef_py', 'gymnasium', 'stable_baselines3', 'torch'}\n"
    )
    result = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr


# --- world mechanics ---------------------------------------------------------


def test_commit_costs_now_and_pays_exactly_delay_steps_later() -> None:
    world = _single(cost=3, payoff=10, delay=5)
    baseline = _rewards(world, {})
    assert baseline == [1] * 40
    committed = _rewards(world, {2: COMMIT})
    assert committed[2] == -3
    assert committed[7] == 1 + 10
    assert [r for i, r in enumerate(committed) if i not in (2, 7)] == [1] * 38
    assert all(type(r) is int for r in committed)


def test_zero_delay_pays_on_the_decision_step_and_off_decision_commit_forgoes_base() -> None:
    world = _single(cost=2, payoff=9, delay=0)
    assert _rewards(world, {2: COMMIT})[2] == -2 + 9
    off = _rewards(world, {5: COMMIT})
    assert off[5] == 0 and sum(off) == 39


def test_pending_feature_counts_steps_until_the_payoff_lands() -> None:
    world = _single(cost=3, payoff=10, delay=5)
    state = world.initial_state(0, 1)
    features = []
    for step in range(9):
        state, _, _ = world.step(state, (COMMIT if step == 2 else HOLD,))
        features.append(pending_feature(state))
    assert features == [None, None, 4, 3, 2, 1, 0, None, None]


@pytest.mark.parametrize(
    "raw",
    [
        ((2, 1, 5, 4), (6, 1, 5, 2)),  # payoff window reaches the next decision
        ((6, 1, 5, 2), (2, 1, 5, 2)),  # unsorted
        ((35, 1, 5, 5),),  # payoff lands at or past the episode end
        ((2, -1, 5, 2),),  # negative cost
        ((2, 1, 5, True),),  # bool is not an integer here
        ((2, 1, Fraction(5), 2),),  # rewards are integers only
    ],
)
def test_world_rejects_inadmissible_decisions(raw: tuple[tuple, ...]) -> None:
    with pytest.raises(HorizonError):
        HorizonWorld(length=40, decisions=tuple(Decision(*fields) for fields in raw))


@pytest.mark.parametrize(
    "overrides",
    [
        {"train_seeds": (1, 2), "eval_seeds": (2, 3)},
        {"train_seeds": (2, 1)},
        {"eval_seeds": ()},
        {"spacing": 12},  # must exceed the largest delay
        {"delay_range": (5, 3)},
        {"cost_range": (-1, 2)},
        {"gamma": Fraction(1)},
        {"gamma": 0.9},
        {"schedule": (1,)},
        {"schedule": (2, 1, 4)},
        {"margins": (Fraction(-1),)},
        {"tolerances": (0.5,)},
        {"decisions_per_seed": 0},
    ],
)
def test_config_fails_closed(overrides: dict) -> None:
    with pytest.raises(HorizonError):
        HorizonConfig(**overrides)


def test_rules_fail_closed_on_unknown_kind_or_missing_threshold() -> None:
    with pytest.raises(HorizonError):
        StoppingRule("first_guess")
    with pytest.raises(HorizonError):
        StoppingRule("value_gap")
    with pytest.raises(HorizonError):
        StoppingRule("rank_agreement", Fraction(1))
    names = [rule.name for rule in rule_grid(HorizonConfig())]
    assert names[0] == "rank_agreement" and names[-1] == "fixed_max"
    assert "value_gap@2" in names and "value_stability@1/2" in names


def test_worlds_are_seeded_and_delays_span_beyond_every_short_horizon() -> None:
    config = HorizonConfig()
    assert make_world(config, 401) == make_world(config, 401)
    assert make_world(config, 401) != make_world(config, 402)
    delays = {d.delay for seed in config.eval_seeds for d in make_world(config, seed).decisions}
    assert 0 in delays and max(delays) > 8 and max(delays) < config.schedule[-1]


# --- Q_H through real branches ------------------------------------------------


def test_branch_q_equals_the_closed_form_sum() -> None:
    probe = _probe(_single(cost=3, payoff=10, delay=5), step=2)
    probe.extend_to(16)

    def hold(h: int) -> Fraction:
        return sum((GAMMA**k for k in range(h)), Fraction(0))

    def commit(h: int) -> Fraction:
        tail = sum((GAMMA**k for k in range(1, h)), Fraction(0))
        return -3 + tail + (GAMMA**5 * 10 if 5 < h else 0)

    for h in SCHEDULE:
        assert probe.q(h, zero_value) == (hold(h), commit(h))
        assert probe.q(h, lambda state: Fraction(7)) == (hold(h) + GAMMA**h * 7, commit(h) + GAMMA**h * 7)


def test_oracle_bootstrap_makes_q_horizon_invariant_and_equal_to_the_full_return() -> None:
    world = _single(cost=3, payoff=10, delay=5)
    probe = _probe(world, step=2)
    oracle = OracleValue(world, GAMMA)
    probe.extend_to(16)
    full_hold = sum((GAMMA**k for k in range(38)), Fraction(0))
    for h in SCHEDULE:
        assert probe.q(h, oracle) == (full_hold, full_hold - 4 + 10 * GAMMA**5)


def test_live_adaptive_run_spends_exactly_the_accounted_branch_steps() -> None:
    for index, rule in enumerate((RANK, StoppingRule("value_gap", Fraction(4)), FIXED)):
        probe = _probe(_single(cost=3, payoff=10, delay=5), step=2, label=f"rule{index}")
        outcome = run_rule(probe, rule, SCHEDULE, zero_value)
        assert probe.steps_taken == outcome.branch_steps == 2 * outcome.horizon
        session = probe.session
        traced = sum(len(trace.transitions) for trace in session.manifest().branches)
        assert traced - len(session.trace(session.baseline).transitions) == outcome.branch_steps


# --- the pinned hazard ---------------------------------------------------------


def test_rank_agreement_reproduces_the_pinned_delayed_commitment_failure() -> None:
    """Same hazard as the counterfactual-toy pin, now through real branches."""

    schedule = (1, 2, 4, 8)
    world = DelayedCommitmentWorld()

    def probe(label: str) -> HorizonProbe:
        session = ReferenceSession.open(
            session_id="toy", seed=0, agent_ids=("agent_0",), policy_ref="probe", world=world
        )
        return HorizonProbe(
            session,
            session.baseline,
            session.head(session.baseline),
            world.initial_state(0, 1),
            continuation="repeat",
            gamma=Fraction(1),
            label=label,
        )

    full = probe("full")
    full.extend_to(8)
    for h in schedule:
        # rollout_branch reports points; the session reports integer quarter points.
        expected = tuple(
            Fraction(rollout_branch((code,), h).discounted_return) * REWARD_UNITS_PER_POINT for code in (0, 1)
        )
        assert full.q(h, zero_value) == expected
    naive = run_rule(probe("rank"), RANK, schedule, zero_value)
    assert (naive.horizon, naive.action) == (2, HOLD)
    reference = run_rule(probe("fixed"), FIXED, schedule, zero_value)
    assert (reference.horizon, reference.action) == (8, COMMIT)


def test_rank_agreement_stops_at_two_with_the_wrong_action_on_a_delayed_payoff() -> None:
    world = _single(cost=3, payoff=10, delay=5)
    naive = run_rule(_probe(world, 2, "rank"), RANK, SCHEDULE, zero_value)
    assert (naive.horizon, naive.action) == (2, HOLD)
    truth = run_rule(_probe(world, 2, "oracle"), FIXED, SCHEDULE, OracleValue(world, GAMMA))
    assert truth.action == COMMIT


# --- fitted value and held-out protocol ----------------------------------------


def test_fitted_value_reads_only_training_seeds() -> None:
    a = fit_value(SMALL)
    b = fit_value(HorizonConfig(train_seeds=SMALL.train_seeds, eval_seeds=tuple(range(901, 905))))
    assert a.table == b.table and a.fallback == b.fallback
    train_delays = [d.delay for seed in SMALL.train_seeds for d in make_world(SMALL, seed).decisions]
    # A pending feature k is seen in training exactly when some training delay exceeds k.
    assert set(a.table) == {None, *range(max(train_delays))}
    # No pending payoff: the hold stream over the fit window.
    assert a.table[None] == sum((SMALL.gamma**i for i in range(SMALL.fit_window)), Fraction(0))
    # One step before landing, the fitted value carries the mean training payoff, not the actual one.
    payoffs = [
        d.payoff for seed in SMALL.train_seeds for d in make_world(SMALL, seed).decisions if d.delay >= 1
    ]
    assert a.table[0] - a.table[None] == Fraction(sum(payoffs), len(payoffs))


def test_heldout_evaluation_never_touches_training_seeds(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[int, bool]] = []
    fitting = [False]
    real_make, real_fit = hs.make_world, hs.fit_value

    def recording_make(config: HorizonConfig, seed: int) -> HorizonWorld:
        calls.append((seed, fitting[0]))
        return real_make(config, seed)

    def recording_fit(config: HorizonConfig) -> hs.TabularValue:
        fitting[0] = True
        try:
            return real_fit(config)
        finally:
            fitting[0] = False

    monkeypatch.setattr(hs, "make_world", recording_make)
    monkeypatch.setattr(hs, "fit_value", recording_fit)
    result = hs.evaluate(SMALL)
    assert {seed for seed, during_fit in calls if during_fit} == set(SMALL.train_seeds)
    assert {seed for seed, during_fit in calls if not during_fit} == set(SMALL.eval_seeds)
    assert [row["seed"] for row in result["seeds"]] == list(SMALL.eval_seeds)


# --- report ---------------------------------------------------------------------


def test_report_is_deterministic_and_labelled_synthetic(report: dict) -> None:
    assert report["evidence_label"] == "synthetic"
    again = evaluate()
    assert again == report
    assert again["report_digest"] == report["report_digest"]
    assert report["config"] == HorizonConfig().to_payload()
    rows = report["summary"]
    assert len(rows) == len(rule_grid(HorizonConfig())) * len(hs.VALUE_VARIANTS)


# --- findings (default 16 training / 32 held-out seeds, 256 decision points) -------


def test_h4_horizon_need_is_a_property_of_the_bootstrap_not_of_the_state(report: dict) -> None:
    """Fraction of held-out points whose argmax is not final from H=1 on.

    By construction for ``zero`` (need is the first schedule horizon above the
    delay on every delayed-gain point) and for ``oracle`` (Q_H is horizon
    invariant). The ``fitted`` number is the measurement.
    """

    assert report["kind_counts"] == {"delayed_gain": 176, "immediate_gain": 8, "no_gain": 72}
    zero, fitted, oracle = (_need(report, variant) for variant in ("zero", "fitted", "oracle"))
    assert zero["needs_above_min"] == 176
    assert zero["needs_above_min_by_kind"] == {"delayed_gain": 176, "immediate_gain": 0, "no_gain": 0}
    assert zero["need_histogram"] == {"1": 80, "2": 14, "4": 32, "8": 54, "16": 76, "beyond_cap": 0}
    for point in report["points"]:
        if point["kind"] == "delayed_gain":
            assert point["need"]["zero"] == min(h for h in SCHEDULE if h > point["delay"])
    assert fitted["needs_above_min"] == 58
    assert fitted["needs_above_min_by_kind"] == {"delayed_gain": 3, "immediate_gain": 0, "no_gain": 55}
    assert oracle["needs_above_min"] == 0


def test_rank_agreement_is_cheap_and_wrong_on_most_delayed_payoffs(report: dict) -> None:
    zero = _row(report, "zero", "rank_agreement")
    assert zero["correct"] == 94 and zero["branch_steps"] == 1080
    # Only delay-1 commits flip before the H=2 check; every other delayed gain is lost.
    assert zero["correct_by_kind"]["delayed_gain"] == [14, 176]
    fitted = _row(report, "fitted", "rank_agreement")
    assert fitted["correct"] == 200 and fitted["branch_steps"] == 1032
    # The fitted bootstrap moves the error: delayed gains are now found, no-gain commits are taken.
    assert fitted["correct_by_kind"] == {
        "delayed_gain": [173, 176],
        "immediate_gain": [8, 8],
        "no_gain": [19, 72],
    }


def test_value_gap_beats_rank_agreement_at_lower_cost_than_fixed_max(report: dict) -> None:
    fixed = _row(report, "zero", "fixed_max")
    assert fixed["correct"] == 256 and fixed["branch_steps"] == 8192
    for value in ("zero", "fitted"):
        rank = _row(report, value, "rank_agreement")
        assert _row(report, value, "fixed_max") == {**fixed, "value": value}
        for margin in (1, 2, 4, 8):
            row = _row(report, value, "value_gap", Fraction(margin))
            assert rank["correct"] < row["correct"] and row["branch_steps"] < fixed["branch_steps"]
    # The cheapest perfect rule per bootstrap; fitted value saves little at full correctness.
    assert _row(report, "zero", "value_gap", Fraction(4))["correct"] == 256
    assert _row(report, "zero", "value_gap", Fraction(4))["branch_steps"] == 7280
    assert _row(report, "fitted", "value_gap", Fraction(4))["correct"] == 239
    assert _row(report, "fitted", "value_gap", Fraction(8))["correct"] == 256
    assert _row(report, "fitted", "value_gap", Fraction(8))["branch_steps"] == 7092
    # Below full correctness the fitted bootstrap buys accuracy per branch step.
    for margin, zero_correct, fitted_correct in ((1, 154, 209), (2, 193, 219)):
        zero_row = _row(report, "zero", "value_gap", Fraction(margin))
        fitted_row = _row(report, "fitted", "value_gap", Fraction(margin))
        assert (zero_row["correct"], fitted_row["correct"]) == (zero_correct, fitted_correct)
        assert fitted_row["branch_steps"] < zero_row["branch_steps"]


def test_value_stability_is_all_or_nothing_under_a_hold_stream(report: dict) -> None:
    """Under V=0 the hold action's Q grows by sum_{k=H..2H-1} gamma^k per doubling.

    That increment is 0.9, 1.539, 2.256, 2.452 for gamma=9/10, so a tolerance
    below 0.9 never stops before the cap and one of 2 stops at H=2 like the
    naive rule. By construction of the hold reward stream.
    """

    for tolerance in (Fraction(1, 4), Fraction(1, 2)):
        row = _row(report, "zero", "value_stability", tolerance)
        assert (row["correct"], row["branch_steps"]) == (256, 8192)
    for tolerance in (Fraction(1), Fraction(2)):
        assert _row(report, "zero", "value_stability", tolerance)["correct"] == 94
    assert _row(report, "zero", "value_stability", Fraction(2)) == {
        **_row(report, "zero", "rank_agreement"),
        "rule": "value_stability",
        "threshold": [2, 1],
        "name": "value_stability@2",
    }
    for tolerance in (Fraction(1, 4), Fraction(1, 2), Fraction(1), Fraction(2)):
        assert _row(report, "fitted", "value_stability", tolerance)["correct"] == 200


def test_no_rule_reaches_the_known_need_stopper(report: dict) -> None:
    """A stopper told each point's need, still checking two horizons, is the floor."""

    assert [_need(report, v)["oracle_stop_branch_steps"] for v in ("zero", "fitted", "oracle")] == [
        3928,
        2024,
        1024,
    ]
    assert _row(report, "oracle", "rank_agreement")["correct"] == 256
    assert _row(report, "oracle", "rank_agreement")["branch_steps"] == 1024


def test_reduced_config_keeps_the_ordering() -> None:
    small = evaluate(SMALL)
    for value in ("zero", "fitted"):
        rank = _row(small, value, "rank_agreement")["correct"]
        gap4 = _row(small, value, "value_gap", Fraction(4))
        assert rank < gap4["correct"] and gap4["branch_steps"] < 64 * 32
    assert _row(small, "zero", "rank_agreement")["correct"] < _row(small, "fitted", "rank_agreement")["correct"]
