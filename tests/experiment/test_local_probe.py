"""Local response-surface probes (E3, ``H6``): world mechanics, fit, and findings.

The finding tests pin the observed synthetic behavior at a reduced
configuration (3 tuning and 6 held-out seeds per family and dimension). They
are regressions on the benchmark, not claims about the runtime. Assertions
marked "by construction" follow from how the worlds are built, not from the
probes being good.
"""

from __future__ import annotations

import dataclasses

from fractions import Fraction

import pytest

from python.experiment.local_probe import KEEP
from python.experiment.local_probe import METHODS
from python.experiment.local_probe import BranchOracle
from python.experiment.local_probe import LocalProbeConfig
from python.experiment.local_probe import ProbeError
from python.experiment.local_probe import RateTrackingWorld
from python.experiment.local_probe import TableOracle
from python.experiment.local_probe import action_name
from python.experiment.local_probe import evaluate
from python.experiment.local_probe import fit_quadratic
from python.experiment.local_probe import grid_actions
from python.experiment.local_probe import make_world
from python.experiment.local_probe import parse_action
from python.experiment.local_probe import run_exhaustive
from python.experiment.local_probe import run_p2
from python.experiment.local_probe import stencil

SMALL = LocalProbeConfig(tuning_seeds=(301, 302, 303), eval_seeds=tuple(range(401, 407)))


@pytest.fixture(scope="module")
def report() -> dict:
    return evaluate(SMALL)


def _row(report: dict, method: str, family: str, dims: int) -> dict:
    (row,) = [
        item
        for item in report["summary"]
        if item["method"] == method and item["family"] == family and item["dims"] == dims
    ]
    return row


def _tiny(**overrides: object) -> RateTrackingWorld:
    fields = {
        "dims": 1,
        "grid_radius": 2,
        "warmup": 1,
        "horizon": 3,
        "targets": (10,),
        "initial_command": (0,),
        "baseline_action": (0,),
    }
    fields.update(overrides)
    return RateTrackingWorld(**fields)


def _direct_q(world: RateTrackingWorld, action: tuple[int, ...]) -> int:
    state = world.initial_state(0, 1)
    for _ in range(world.warmup):
        state, _, _ = world.step(state, (KEEP,))
    total = 0
    for offset in range(world.horizon):
        state, (reward,), done = world.step(state, (action_name(action) if offset == 0 else KEEP,))
        total += reward
    assert done
    return total


def test_action_names_round_trip_and_cover_the_grid() -> None:
    assert action_name((-3,)) == "a_-3"
    assert action_name((0, 2)) == "a_+0_+2"
    assert parse_action("a_+0_+2") == (0, 2)
    with pytest.raises(ProbeError):
        parse_action("commit")
    world = _tiny()
    assert len(grid_actions(world)) == 5
    assert world.actions == (KEEP, "a_-2", "a_-1", "a_+0", "a_+1", "a_+2")


def test_branch_q_matches_hand_computed_dynamics() -> None:
    # warmup: rate 0, position 0; decision a sets rate 8a, then the rate is kept.
    world = _tiny()
    oracle = BranchOracle(world, session_id="tiny", seed=0)
    assert oracle.value((1,)) == -(4 + 36 + 196)
    assert oracle.value((2,)) == -(36 + 484 + 1444)
    assert oracle.value((0,)) == -300
    assert oracle.value((-1,)) == -(324 + 676 + 1156)
    assert oracle.value((1,)) == -236  # cached: no new branch
    assert oracle.spent == 4
    assert len(oracle.session.manifest().branches) == 1 + oracle.spent


def test_cliff_penalty_is_delayed_and_truncated_by_the_horizon() -> None:
    cliff = {"cliff_level": 1, "penalty": 1000}
    seen = BranchOracle(_tiny(penalty_delay=2, **cliff), session_id="cliff_seen", seed=0)
    assert seen.value((2,)) == -1964 - 1000
    assert seen.value((1,)) == -236  # at the level, not above it: no penalty
    rewards = [item.rewards[0][1] for item in seen.session.trace(seen.branch_of((2,))).transitions]
    assert rewards == [-36, -484, -1444 - 1000]
    hidden = BranchOracle(_tiny(penalty_delay=3, **cliff), session_id="cliff_hidden", seed=0)
    assert hidden.value((2,)) == -1964  # due after the horizon: invisible to Q_H


@pytest.mark.parametrize("family", ["smooth", "mild", "rugged"])
@pytest.mark.parametrize("dims", [1, 2])
def test_branch_values_equal_direct_dynamics_for_every_family(family: str, dims: int) -> None:
    world = make_world(SMALL, family, dims, 401)
    oracle = BranchOracle(world, session_id=f"direct_{family}_{dims}", seed=401)
    for action in grid_actions(world)[:: 7 if dims == 2 else 2]:
        assert oracle.value(action) == _direct_q(world, action)


def test_world_and_config_fail_closed() -> None:
    with pytest.raises(ProbeError):
        _tiny(dims=3, targets=(1, 2, 3), initial_command=(0, 0, 0), baseline_action=(0, 0, 0))
    with pytest.raises(ProbeError):
        _tiny(baseline_action=(3,))
    with pytest.raises(ProbeError):
        _tiny(targets=(1, 2))
    with pytest.raises(ProbeError):
        _tiny(coupling=4)
    with pytest.raises(ProbeError):
        _tiny(penalty=10, penalty_delay=0)
    with pytest.raises(ProbeError):
        _tiny(horizon=True)
    with pytest.raises(ProbeError):
        _tiny().initial_state(0, 2)
    with pytest.raises(ProbeError, match="disjoint"):
        LocalProbeConfig(tuning_seeds=(1, 2), eval_seeds=(2, 3))
    with pytest.raises(ProbeError):
        make_world(SMALL, "chaotic", 1, 401)
    with pytest.raises(ProbeError):
        BranchOracle(_tiny(), session_id="range", seed=0).value((3,))


def _analytic_gradient_hessian(world: RateTrackingWorld, anchor: tuple[int, ...]):
    """Closed form for cubic-free, symmetric-weight, cliff-free, reward_div=1 worlds."""

    u = world.rate_unit
    m = [[Fraction(u)]] if world.dims == 1 else [
        [Fraction(u), Fraction(0)],
        [Fraction(world.coupling), Fraction(u)],
    ]
    d = world.dims

    def mul(vec):
        return [sum(m[i][j] * vec[j] for j in range(d)) for i in range(d)]

    p_w = [world.warmup * x for x in mul(list(world.initial_command))]
    m_anchor = mul(list(anchor))
    grad = [Fraction(0)] * d
    hess = [[Fraction(0)] * d for _ in range(d)]
    for k in range(1, world.horizon + 1):
        err = [p_w[i] + k * m_anchor[i] - world.targets[i] for i in range(d)]
        for j in range(d):
            grad[j] += -2 * k * sum(m[i][j] * err[i] for i in range(d))
            for col in range(d):
                hess[j][col] += -2 * k * k * sum(m[i][j] * m[i][col] for i in range(d))
    return tuple(grad), tuple(tuple(row) for row in hess)


@pytest.mark.parametrize("dims", [1, 2])
def test_quadratic_fit_recovers_exact_gradient_and_hessian(dims: int) -> None:
    world = RateTrackingWorld(
        dims=dims,
        grid_radius=4,
        warmup=2,
        horizon=5,
        targets=(70,) if dims == 1 else (70, -30),
        initial_command=(1,) if dims == 1 else (1, -1),
        baseline_action=(1,) if dims == 1 else (1, -2),
        coupling=0 if dims == 1 else 4,
    )
    oracle = BranchOracle(world, session_id=f"exact_{dims}", seed=0)
    for step in (1, 2):
        offsets = stencil(dims, step)
        values = [
            oracle.value(tuple(a + x for a, x in zip(world.baseline_action, offset)))
            for offset in offsets
        ]
        model = fit_quadratic(offsets, values)
        grad, hess = _analytic_gradient_hessian(world, world.baseline_action)
        assert model.gradient == grad
        assert model.hessian == hess
        assert model.constant == oracle.value(world.baseline_action)


def test_fit_rejects_singular_and_mismatched_stencils() -> None:
    with pytest.raises(ProbeError, match="singular"):
        fit_quadratic([(0,), (1,), (1,)], [0, 1, 1])
    with pytest.raises(ProbeError):
        fit_quadratic([(0,), (1,)], [0, 1, 2])


def test_table_and_branch_oracles_give_identical_probe_outcomes() -> None:
    world = make_world(SMALL, "mild", 2, 402)
    exhaustive = BranchOracle(world, session_id="table_source", seed=402)
    run_exhaustive(exhaustive, world)
    table = TableOracle(exhaustive.table())
    branched = BranchOracle(world, session_id="table_check", seed=402)
    kwargs = {"radius": 4, "step": 1, "tolerance_milli": 250, "trust_region": True}
    via_table = run_p2(table, world, **kwargs)
    via_branches = run_p2(branched, world, **kwargs)
    assert via_table == via_branches
    assert via_branches.branches == branched.spent == len(branched.session.manifest().branches) - 1


def test_report_is_deterministic_synthetic_and_float_free(report: dict) -> None:
    assert report["evidence_label"] == "synthetic"
    assert report["config"] == SMALL.to_payload()
    tiny = LocalProbeConfig(tuning_seeds=(301,), eval_seeds=(401,), dims=(1,))
    first = evaluate(tiny)
    assert evaluate(tiny)["report_digest"] == first["report_digest"]
    assert first["report_digest"] != report["report_digest"]

    def walk(value: object) -> None:
        assert not isinstance(value, float)
        if isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(report)


def test_tuned_constants_depend_only_on_tuning_seeds() -> None:
    a = LocalProbeConfig(tuning_seeds=(301,), eval_seeds=(401,), dims=(1,))
    b = LocalProbeConfig(tuning_seeds=(301,), eval_seeds=(402, 403), dims=(1,))
    assert evaluate(a)["tuned"] == evaluate(b)["tuned"]


def test_every_method_is_charged_real_branches_from_one_snapshot(report: dict) -> None:
    for row in report["worlds"]:
        spent = sum(row["methods"][m]["branches"] for m in METHODS if m != "p2_guarded")
        assert row["manifest_branches"] == spent
        assert row["methods"]["exhaustive"]["branches"] == row["grid_size"]
        assert row["methods"]["p2"]["branches"] == (4 if row["dims"] == 1 else 7)
        assert row["methods"]["random"]["branches"] == row["methods"]["p2"]["branches"]
        assert row["methods"]["random_tr"]["branches"] == row["methods"]["p2_tr"]["branches"]


def test_tuning_picks_the_same_constants_as_the_full_protocol(report: dict) -> None:
    tuned = report["tuned"]
    assert (tuned["p1_radius"], tuned["p2_radius"]) == (3, 4)
    # Crossed and intact first checks are separated by ~3 orders of magnitude on the
    # tuning seeds, so every tolerance in the grid is perfect (J = 1) and ties pick 2000.
    assert set(tuned["tolerance_youden_milli"].values()) == {1000}
    assert tuned["tolerance_milli"] == 2000
    assert tuned["tuning_intact_error_milli_max"] < 50 < 20_000 < tuned["tuning_crossed_error_milli_min"]


def test_rugged_argmax_sits_at_the_cliff_edge_by_construction(report: dict) -> None:
    for row in report["worlds"]:
        if row["family"] == "rugged":
            world = make_world(SMALL, "rugged", row["dims"], row["seed"])
            assert world.cliff_sign * row["argmax"][0] == world.cliff_level
            anchor = world.baseline_action
            for offset in stencil(world.dims, SMALL.stencil_step):
                assert not world.triggers_cliff(tuple(a + o for a, o in zip(anchor, offset)))


@pytest.mark.parametrize("stencil_step", [1, 2])
def test_no_baseline_stencil_point_triggers_the_cliff(stencil_step: int) -> None:
    config = dataclasses.replace(SMALL, stencil_step=stencil_step)
    for dims in (1, 2):
        for seed in (*config.tuning_seeds, *config.eval_seeds):
            world = make_world(config, "rugged", dims, seed)
            anchor = world.baseline_action
            for offset in stencil(dims, stencil_step):
                assert not world.triggers_cliff(tuple(a + o for a, o in zip(anchor, offset)))


@pytest.mark.parametrize("dims", [1, 2])
def test_p2_on_smooth_worlds_beats_random_at_equal_budget_for_a_fraction_of_exhaustive(
    report: dict, dims: int
) -> None:
    p2 = _row(report, "p2", "smooth", dims)
    exhaustive = _row(report, "exhaustive", "smooth", dims)
    random_match = _row(report, "random", "smooth", dims)
    assert p2["max_branches"] * (4 if dims == 1 else 40) <= exhaustive["max_branches"]
    assert p2["mean_regret_share_milli"] <= 40
    assert random_match["mean_regret_share_milli"] >= 500
    assert p2["argmax_hit_milli"] >= 666 > random_match["argmax_hit_milli"]
    # Measured: on the reduced config one trust-region iteration closes the remaining gap.
    p2_tr = _row(report, "p2_tr", "smooth", dims)
    assert p2_tr["argmax_hit_milli"] == 1000
    assert p2_tr["max_branches"] <= (7 if dims == 1 else 12)
    assert _row(report, "random_tr", "smooth", dims)["argmax_hit_milli"] <= 166


def test_p1_trails_p2_on_smooth_and_mild_worlds(report: dict) -> None:
    for family in ("smooth", "mild"):
        for dims in (1, 2):
            p1 = _row(report, "p1", family, dims)
            p2 = _row(report, "p2", family, dims)
            assert p1["mean_regret_share_milli"] > 2 * p2["mean_regret_share_milli"]
            assert p1["argmax_hit_milli"] < p2["argmax_hit_milli"]


def test_mild_cubic_term_barely_moves_the_quadratic_probe(report: dict) -> None:
    for dims in (1, 2):
        mild = [d for d in report["detector"] if d["method"] == "p2" and d["family"] == "mild"]
        (row,) = [d for d in mild if d["dims"] == dims]
        assert row["flagged"] == 0
        assert row["intact_error_milli_spread"][-1] < 50
        assert _row(report, "p2_tr", "mild", dims)["argmax_hit_milli"] == 1000


def _detector(report: dict, method: str, family: str, dims: int) -> dict:
    (row,) = [
        d
        for d in report["detector"]
        if d["method"] == method and d["family"] == family and d["dims"] == dims
    ]
    return row


@pytest.mark.parametrize("dims", [1, 2])
def test_untrusted_flag_fires_on_rugged_worlds_and_never_on_smooth_ones(report: dict, dims: int) -> None:
    for family in ("smooth", "mild"):
        assert _detector(report, "p2", family, dims)["flagged"] == 0
    rugged = _detector(report, "p2", "rugged", dims)
    assert rugged["flagged"] >= 5
    # Every flag is a real model break (the proposal crossed the cliff) and every
    # break is flagged: the separation is large because the penalty is large.
    assert rugged["flagged"] == rugged["flagged_crossed"] == rugged["crossed"]
    assert rugged["flagged_intact"] == 0
    assert rugged["missed_failures"] == 0
    assert _row(report, "p2", "rugged", dims)["flag_milli"] > _row(report, "p2", "smooth", dims)["flag_milli"]


def test_p2_regret_on_rugged_worlds_exceeds_smooth_and_the_guard_repairs_it(report: dict) -> None:
    for dims in (1, 2):
        rugged = _row(report, "p2", "rugged", dims)
        smooth = _row(report, "p2", "smooth", dims)
        assert rugged["mean_regret_share_milli"] > 4 * max(smooth["mean_regret_share_milli"], 1)
        guarded = _row(report, "p2_guarded", "rugged", dims)
        assert guarded["argmax_hit_milli"] == 1000
        # The guard only pays the grid where it fired: on smooth worlds it costs what p2 costs.
        assert _row(report, "p2_guarded", "smooth", dims)["max_branches"] == smooth["max_branches"]
        assert guarded["mean_branches_milli"] >= 800 * guarded["max_branches"]
    # In 2-D no probe method finds the cliff-edge argmax on these seeds.
    for method in ("p1", "p2", "p2_tr", "random", "random_tr"):
        assert _row(report, method, "rugged", 2)["argmax_hit_milli"] == 0
