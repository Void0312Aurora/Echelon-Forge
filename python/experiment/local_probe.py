"""E3 local response-surface probes over a synthetic rate-tracking world (``H6``).

Cluster ``E3`` of the adaptive counterfactual search plan
(``docs/learning/work/issues/adaptive_counterfactual_search/README.md``). It
measures whether a low-order model of the finite-horizon value around the
baseline action, ``Q_H(s, a0 + da) ~ Q0 + g.da + 1/2 da' H da``, can replace an
exhaustive sweep of the action grid: Probe -> Fit -> Predict -> Validate. The
Taylor order ``p`` here is the local nonlinear order in the action; the horizon
``H`` is the temporal propagation depth, and the two are independent.

The world
---------
:class:`RateTrackingWorld` is a single-agent, ``dims``-dimensional tracking
task. A command ``c`` in the integer grid ``[-K, K]^dims`` sets a rate
``r = M c`` with ``M = [[u]]`` in 1-D and ``M = [[u, 0], [kappa, u]]`` in 2-D,
so ``kappa`` couples the axes. Each step ``position += r`` and the reward is
``-(w * sum_i (position_i - T_i)^2 + f * sum_i |c_i|^3)`` minus any penalty that
falls due. Action ``keep`` holds the current command; ``a_+3`` or ``a_+1_-2``
set a new one. Rewards are integers; nothing is a closed-form label, every
value is a sum of per-step rewards produced by stepping the dynamics.

The baseline policy keeps its command for ``warmup`` steps, which fixes the
decision snapshot. ``Q_H(a)`` is the return of a branch forked there that sets
command ``a`` and then keeps it for ``horizon`` steps. Its shape, by the
dynamics above, is::

    Q_H(a) = -sum_{k=1..H} [w |p_w + k M a - T|^2 + f |a|_3^3] - P [s a_x > L]

with ``p_w`` the position at the snapshot. The cliff term exists only when the
world has one: setting a command whose ``cliff_axis`` component lies beyond
``cliff_level`` (in direction ``cliff_sign``) schedules a penalty ``P``
``penalty_delay`` steps later, so the penalty is a delayed consequence that is
visible inside the horizon only because ``penalty_delay < horizon``.

Families, chosen before any method was run and paired by seed (one seed fixes
targets, coupling, and baseline action for all three families):

- ``smooth``: ``f = smooth_fuel``; the cubic curvature at the grid edge is
  about 0.6% of the tracking curvature, so ``Q_H`` is nearly quadratic.
- ``mild``: ``f = mild_fuel``; the cubic curvature at the grid edge is about
  25% of the tracking curvature.
- ``rugged``: the smooth world plus a cliff placed strictly between the
  baseline action and the unconstrained optimum on axis 0, at least one cell
  beyond the baseline. By construction no stencil point at the baseline
  triggers it, and because the penalty dwarfs any gain from crossing, the true
  argmax sits at the cliff edge (64 of 64 default worlds): the note's A4
  failure case, a model break the local probes cannot see before validating.

Methods, each with a counted branch budget (one branch per distinct action)
-------------------------------------------------------------------------
- ``exhaustive``: every grid action; the reference argmax and true values.
- ``p1``: forward-difference gradient on ``dims + 1`` points, one step of the
  tuned length along it, validated by one branch.
- ``p2``: exact least-squares quadratic on the minimal stencil
  (``(dims + 1)(dims + 2) / 2`` points), the Newton step ``-H^-1 g`` scaled into
  the tuned trust radius and rounded (a gradient step when ``H`` is not
  negative definite), validated by one branch.
- ``p2_tr``: ``p2`` plus one trust-region iteration: when the first check is
  untrusted, halve the step and validate again; otherwise refit at the
  validated point and take one more validated step.
- ``random`` / ``random_tr``: the baseline action plus uniformly drawn
  distinct actions, as many branches as ``p2`` / ``p2_tr`` spent on that world.
- ``p2_guarded``: ``p2``, escalated to the full grid when its check is
  untrusted. Derived from the ``p2`` and ``exhaustive`` runs of the same world
  (escalation reuses the probes, so it costs exactly the grid).

Every probe method returns the best action it measured; regret is
``Q(true best) - Q(chosen)`` from the exhaustive table.

The untrusted-model flag compares the model's prediction with the validated
value at the proposed action: it fires when
``|Q_val - Q_pred| > tolerance * max(|Q_pred - Q_center|, 1)``, i.e. when the
trust-region ratio of actual to predicted improvement leaves
``[1 - tolerance, 1 + tolerance]``. A check *crossed the cliff* when its
proposal triggers the rugged world's penalty; that oracle label is the A4
model break the flag is meant to detect, and only the report reads it.

Tuning
------
The ``p1`` step length, the ``p2`` trust radius, and the flag tolerance are
chosen on ``tuning_seeds`` only, pooled over the configured families and
dimensions, from exhaustive tables built by real branches: the radii minimize
the mean regret share (regret over the improvement available from ``a0``), the
tolerance maximizes Youden's ``J`` of the first ``p2`` check's flag against
the crossed-the-cliff label. Ties go to the larger value. The report also
scores the flag against ``p2`` failure (regret share above
``failure_share_milli``), which it is not tuned for. ``eval_seeds`` are
disjoint and never read during tuning.

Evidence boundary: everything here is ``synthetic``. It characterizes probe
methods on worlds built with these shapes; it says nothing about the
maintained runtime or any combat scenario.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, replace
from fractions import Fraction
from functools import lru_cache
from itertools import product
from math import floor
from typing import Any, Mapping, Protocol, Sequence

from python.experiment.contracts import content_digest
from python.experiment.reference_session import ReferenceSession

AGENT = "agent_0"
KEEP = "keep"
OBSERVATION = "decision_belief_packet"
POLICY_REF = "synthetic_policy:keep_command"
FAMILIES: tuple[str, ...] = ("smooth", "mild", "rugged")
METHODS: tuple[str, ...] = (
    "exhaustive",
    "p1",
    "p2",
    "p2_tr",
    "random",
    "random_tr",
    "p2_guarded",
)

Action = tuple[int, ...]


class ProbeError(ValueError):
    """Raised when a world, configuration, or probe request is not admissible."""


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _require_int(value: Any, name: str, minimum: int | None = None) -> None:
    if not _is_int(value) or (minimum is not None and value < minimum):
        bound = "" if minimum is None else f" >= {minimum}"
        raise ProbeError(f"{name} must be an integer{bound}, got {value!r}")


def action_name(action: Sequence[int]) -> str:
    """Grid action name, e.g. ``(0, 2) -> "a_+0_+2"``."""

    if not action or not all(_is_int(value) for value in action):
        raise ProbeError(f"an action is a non-empty integer tuple, got {action!r}")
    return "a_" + "_".join(f"{value:+d}" for value in action)


def parse_action(name: str) -> Action:
    """Inverse of :func:`action_name`; rejects any non-canonical spelling."""

    if not isinstance(name, str) or not name.startswith("a_"):
        raise ProbeError(f"not a grid action name: {name!r}")
    values = []
    for part in name[2:].split("_"):
        digits = part[1:]
        if len(part) < 2 or part[0] not in "+-" or not (digits.isascii() and digits.isdigit()):
            raise ProbeError(f"not a grid action name: {name!r}")
        values.append(int(part))
    if action_name(values) != name:
        raise ProbeError(f"not a canonical grid action name: {name!r}")
    return tuple(values)


@lru_cache(maxsize=16)
def _grid(dims: int, radius: int) -> tuple[Action, ...]:
    return tuple(product(range(-radius, radius + 1), repeat=dims))


@lru_cache(maxsize=16)
def _action_names(dims: int, radius: int) -> tuple[str, ...]:
    return (KEEP, *(action_name(action) for action in _grid(dims, radius)))


@dataclass(frozen=True)
class RateTrackingWorld:
    """Synthetic rate-tracking world; see the module docstring for its law."""

    dims: int
    grid_radius: int
    warmup: int
    horizon: int
    targets: tuple[int, ...]
    initial_command: tuple[int, ...]
    baseline_action: tuple[int, ...]
    rate_unit: int = 8
    coupling: int = 0
    track_weight: int = 1
    fuel: int = 0
    cliff_level: int | None = None
    cliff_sign: int = 1
    cliff_axis: int = 0
    penalty: int = 0
    penalty_delay: int = 1
    scenario_ref: str = "synthetic:rate_tracking"
    evidence_label: str = "synthetic"
    reward_units_per_point: int = 1

    def __post_init__(self) -> None:
        if not _is_int(self.dims) or self.dims not in (1, 2):
            raise ProbeError("dims must be 1 or 2")
        for name, minimum in (
            ("grid_radius", 1),
            ("warmup", 0),
            ("horizon", 1),
            ("rate_unit", 1),
            ("track_weight", 1),
            ("fuel", 0),
            ("penalty", 0),
            ("penalty_delay", 1),
        ):
            _require_int(getattr(self, name), name, minimum)
        _require_int(self.coupling, "coupling")
        if self.dims == 1 and self.coupling != 0:
            raise ProbeError("a 1-D world has no axis coupling")
        for name in ("targets", "initial_command", "baseline_action"):
            value = getattr(self, name)
            if (
                not isinstance(value, tuple)
                or len(value) != self.dims
                or not all(_is_int(item) for item in value)
            ):
                raise ProbeError(f"{name} must be a tuple of {self.dims} integers")
        for name in ("initial_command", "baseline_action"):
            if not self.in_grid(getattr(self, name)):
                raise ProbeError(f"{name} must lie on the action grid")
        if self.cliff_level is not None:
            _require_int(self.cliff_level, "cliff_level")
        if not _is_int(self.cliff_sign) or self.cliff_sign not in (1, -1):
            raise ProbeError("cliff_sign must be +1 or -1")
        if not _is_int(self.cliff_axis) or not 0 <= self.cliff_axis < self.dims:
            raise ProbeError("cliff_axis must name an action axis")

    @property
    def actions(self) -> tuple[str, ...]:
        return _action_names(self.dims, self.grid_radius)

    def grid(self) -> tuple[Action, ...]:
        return _grid(self.dims, self.grid_radius)

    def in_grid(self, action: Sequence[int]) -> bool:
        return (
            isinstance(action, tuple)
            and len(action) == self.dims
            and all(_is_int(value) and abs(value) <= self.grid_radius for value in action)
        )

    def clip(self, point: Sequence[int]) -> Action:
        bound = self.grid_radius
        return tuple(max(-bound, min(bound, value)) for value in point)

    def rates(self, command: Action) -> tuple[int, ...]:
        if self.dims == 1:
            return (self.rate_unit * command[0],)
        first, second = command
        return (self.rate_unit * first, self.coupling * first + self.rate_unit * second)

    def triggers_cliff(self, command: Action) -> bool:
        return self.cliff_level is not None and (
            self.cliff_sign * command[self.cliff_axis] > self.cliff_level
        )

    def cubic_curvature_ratio_milli(self) -> int:
        """Cubic fuel curvature at the grid edge over the smallest tracking curvature."""

        h = self.horizon
        tracking = 2 * self.track_weight * self.rate_unit**2 * (h * (h + 1) * (2 * h + 1) // 6)
        return (1000 * 6 * h * self.fuel * self.grid_radius) // tracking

    def config_payload(self) -> Mapping[str, Any]:
        return {
            "dims": self.dims,
            "grid_radius": self.grid_radius,
            "warmup": self.warmup,
            "horizon": self.horizon,
            "targets": list(self.targets),
            "initial_command": list(self.initial_command),
            "baseline_action": list(self.baseline_action),
            "rate_unit": self.rate_unit,
            "coupling": self.coupling,
            "track_weight": self.track_weight,
            "fuel": self.fuel,
            "cliff_level": self.cliff_level,
            "cliff_sign": self.cliff_sign,
            "cliff_axis": self.cliff_axis,
            "penalty": self.penalty,
            "penalty_delay": self.penalty_delay,
        }

    def initial_state(self, seed: int, agent_count: int) -> tuple:
        if agent_count != 1:
            raise ProbeError("the rate-tracking world is single-agent")
        return (0, (0,) * self.dims, self.initial_command, ())

    def encode_state(self, state: tuple) -> Mapping[str, Any]:
        step, position, command, pending = state
        return {
            "step": step,
            "position": list(position),
            "command": list(command),
            "pending": [list(item) for item in pending],
        }

    def step(self, state: tuple, actions: tuple[str, ...]) -> tuple[tuple, tuple[int, ...], bool]:
        step, position, command, pending = state
        (action,) = actions
        if action != KEEP:
            command = parse_action(action)
            if not self.in_grid(command):
                raise ProbeError(f"action {action!r} is off the grid")
            if self.triggers_cliff(command):
                pending = pending + ((step + self.penalty_delay, self.penalty),)
        position = tuple(p + r for p, r in zip(position, self.rates(command)))
        cost = self.track_weight * sum((p - t) ** 2 for p, t in zip(position, self.targets))
        cost += self.fuel * sum(abs(c) ** 3 for c in command)
        cost += sum(amount for due, amount in pending if due == step)
        pending = tuple(sorted(item for item in pending if item[0] > step))
        successor = (step + 1, position, command, pending)
        return successor, (-cost,), step + 1 >= self.warmup + self.horizon


class Oracle(Protocol):
    """Anything that returns ``Q_H(a)`` and counts the distinct actions it measured."""

    @property
    def spent(self) -> int: ...

    def value(self, action: Sequence[int]) -> int: ...


@dataclass
class _DecisionPoint:
    world: RateTrackingWorld
    session: ReferenceSession
    snapshot: Any
    prefixes: set[str]


def _label_token(action: Action) -> str:
    return "_".join(("p" if value >= 0 else "m") + str(abs(value)) for value in action)


class BranchOracle:
    """Measures ``Q_H(a)`` by real branches forked from one decision snapshot.

    Each distinct action costs one branch of ``horizon`` steps; repeated
    requests are served from this oracle's cache. :meth:`sibling` opens another
    oracle on the same session and snapshot with its own cache and counter, so
    several methods can be charged separately inside one manifest.
    """

    def __init__(
        self,
        world: RateTrackingWorld,
        *,
        session_id: str,
        seed: int,
        prefix: str = "q",
        _point: _DecisionPoint | None = None,
    ) -> None:
        if _point is None:
            session = ReferenceSession.open(
                session_id=session_id,
                seed=seed,
                agent_ids=(AGENT,),
                policy_ref=POLICY_REF,
                world=world,
            )
            for _ in range(world.warmup):
                session.step(session.baseline, {AGENT: KEEP}, observation_provenance=OBSERVATION)
            _point = _DecisionPoint(world, session, session.head(session.baseline), set())
        if prefix in _point.prefixes:
            raise ProbeError(f"branch label prefix {prefix!r} is already in use")
        _point.prefixes.add(prefix)
        self._point = _point
        self._prefix = prefix
        self._values: dict[Action, int] = {}
        self._branches: dict[Action, Any] = {}

    def sibling(self, prefix: str) -> "BranchOracle":
        world = self._point.world
        return BranchOracle(world, session_id="", seed=0, prefix=prefix, _point=self._point)

    @property
    def session(self) -> ReferenceSession:
        return self._point.session

    @property
    def spent(self) -> int:
        return len(self._values)

    def table(self) -> dict[Action, int]:
        return dict(self._values)

    def branch_of(self, action: Sequence[int]):
        return self._branches[tuple(action)]

    def value(self, action: Sequence[int]) -> int:
        action = tuple(action)
        world = self._point.world
        if not world.in_grid(action):
            raise ProbeError(f"action {action!r} is off the grid")
        if action in self._values:
            return self._values[action]
        session = self._point.session
        name = action_name(action)
        branch = session.fork(
            session.baseline,
            self._point.snapshot,
            intervention={AGENT: name},
            label=f"{self._prefix}_{_label_token(action)}",
        )
        total = 0
        for offset in range(world.horizon):
            transition = session.step(
                branch, {AGENT: name if offset == 0 else KEEP}, observation_provenance=OBSERVATION
            )
            total += transition.rewards[0][1]
        if not session.is_terminated(branch):
            raise ProbeError("a value branch must terminate exactly at the horizon")
        self._values[action] = total
        self._branches[action] = branch
        return total


class TableOracle:
    """Replays a table of branch-measured values; used for tuning sweeps."""

    def __init__(self, table: Mapping[Action, int]) -> None:
        self._table = dict(table)
        self._seen: set[Action] = set()

    @property
    def spent(self) -> int:
        return len(self._seen)

    def value(self, action: Sequence[int]) -> int:
        action = tuple(action)
        if action not in self._table:
            raise ProbeError(f"action {action!r} is not in the table")
        self._seen.add(action)
        return self._table[action]


@dataclass(frozen=True)
class QuadraticModel:
    """``Q(center + d) ~ constant + gradient.d + 1/2 d' hessian d``."""

    constant: Fraction
    gradient: tuple[Fraction, ...]
    hessian: tuple[tuple[Fraction, ...], ...]

    def predict(self, delta: Sequence[int]) -> Fraction:
        dims = len(self.gradient)
        linear = sum((self.gradient[i] * delta[i] for i in range(dims)), Fraction(0))
        quadratic = sum(
            (self.hessian[i][j] * delta[i] * delta[j] for i in range(dims) for j in range(dims)),
            Fraction(0),
        )
        return self.constant + linear + quadratic / 2


def _solve(matrix: Sequence[Sequence[Fraction]], rhs: Sequence[Fraction]) -> tuple[Fraction, ...]:
    """Exact Gauss-Jordan solve; fails closed on a singular system."""

    size = len(rhs)
    rows = [[Fraction(item) for item in row] + [Fraction(rhs[i])] for i, row in enumerate(matrix)]
    for col in range(size):
        pivot = next((r for r in range(col, size) if rows[r][col] != 0), None)
        if pivot is None:
            raise ProbeError("singular system: the stencil does not determine the model")
        rows[col], rows[pivot] = rows[pivot], rows[col]
        lead = rows[col][col]
        rows[col] = [item / lead for item in rows[col]]
        for r in range(size):
            if r != col and rows[r][col] != 0:
                factor = rows[r][col]
                rows[r] = [a - factor * b for a, b in zip(rows[r], rows[col])]
    return tuple(row[size] for row in rows)


def _basis(offset: Action) -> list[Fraction]:
    if len(offset) == 1:
        (x,) = offset
        return [Fraction(1), Fraction(x), Fraction(x * x, 2)]
    x, y = offset
    return [
        Fraction(1),
        Fraction(x),
        Fraction(y),
        Fraction(x * x, 2),
        Fraction(x * y),
        Fraction(y * y, 2),
    ]


def fit_quadratic(offsets: Sequence[Action], values: Sequence[int]) -> QuadraticModel:
    """Exact least-squares quadratic through ``(offset, value)`` samples."""

    if not offsets or len(offsets) != len(values):
        raise ProbeError("a fit needs one value per stencil offset")
    dims = len(offsets[0])
    if dims not in (1, 2) or any(len(offset) != dims for offset in offsets):
        raise ProbeError("stencil offsets must share one dimension, 1 or 2")
    rows = [_basis(tuple(offset)) for offset in offsets]
    width = len(rows[0])
    normal = [
        [sum((row[i] * row[j] for row in rows), Fraction(0)) for j in range(width)]
        for i in range(width)
    ]
    moment = [
        sum((row[i] * value for row, value in zip(rows, values)), Fraction(0)) for i in range(width)
    ]
    params = _solve(normal, moment)
    if dims == 1:
        constant, g, h = params
        return QuadraticModel(constant, (g,), ((h,),))
    constant, g1, g2, h11, h12, h22 = params
    return QuadraticModel(constant, (g1, g2), ((h11, h12), (h12, h22)))


def stencil(dims: int, step: int) -> tuple[Action, ...]:
    """Minimal interior stencil: center, +-step per axis, and one diagonal in 2-D."""

    if dims == 1:
        return ((0,), (step,), (-step,))
    if dims == 2:
        return ((0, 0), (step, 0), (-step, 0), (0, step), (0, -step), (step, step))
    raise ProbeError("dims must be 1 or 2")


def _stencil_at(world: RateTrackingWorld, center: Action, step: int) -> tuple[Action, ...]:
    """The minimal stencil at ``center``, made one-sided along an axis at the grid edge."""

    bound = world.grid_radius
    pairs = []
    for value in center:
        if value - step >= -bound and value + step <= bound:
            pairs.append((step, -step))
        elif value + 2 * step <= bound:
            pairs.append((step, 2 * step))
        elif value - 2 * step >= -bound:
            pairs.append((-step, -2 * step))
        else:
            raise ProbeError("the grid is too small for the stencil step")
    dims = len(center)
    offsets: list[Action] = [(0,) * dims]
    for axis, pair in enumerate(pairs):
        for shift in pair:
            offsets.append(tuple(shift if i == axis else 0 for i in range(dims)))
    if dims == 2:
        offsets.append((pairs[0][0], pairs[1][0]))
    return tuple(offsets)


def _round_half_away(value: Fraction) -> int:
    magnitude = floor(abs(value) + Fraction(1, 2))
    return magnitude if value >= 0 else -magnitude


def _toward(vector: Sequence[Fraction], radius: int, *, always_full: bool) -> Action:
    """Round ``vector`` scaled so its largest component is at most ``radius``.

    With ``always_full`` the vector is scaled to exactly ``radius`` (a pure
    direction, as for a gradient step); otherwise it is only shrunk.
    """

    peak = max(abs(item) for item in vector)
    if peak == 0:
        return (0,) * len(vector)
    factor = Fraction(radius) / peak
    if not always_full:
        factor = min(Fraction(1), factor)
    return tuple(_round_half_away(item * factor) for item in vector)


def _negative_definite(hessian: tuple[tuple[Fraction, ...], ...]) -> bool:
    if len(hessian) == 1:
        return hessian[0][0] < 0
    return hessian[0][0] < 0 and hessian[0][0] * hessian[1][1] - hessian[0][1] * hessian[1][0] > 0


def quadratic_step(model: QuadraticModel, radius: int) -> Action:
    """Newton step ``-H^-1 g`` inside the trust radius; a gradient step if ``H`` is not concave."""

    if _negative_definite(model.hessian):
        newton = _solve(model.hessian, [-item for item in model.gradient])
        return _toward(newton, radius, always_full=False)
    return _toward(model.gradient, radius, always_full=True)


@dataclass(frozen=True)
class Check:
    """One validation branch: the model's prediction against the measured value."""

    center: Action
    reference: int
    proposal: Action
    predicted: Fraction
    validated: int
    tolerance_milli: int

    @property
    def scale(self) -> Fraction:
        return max(abs(self.predicted - self.reference), Fraction(1))

    @property
    def error_milli(self) -> int:
        return floor(1000 * abs(self.validated - self.predicted) / self.scale)

    def exceeds(self, tolerance_milli: int) -> bool:
        return 1000 * abs(self.validated - self.predicted) > tolerance_milli * self.scale

    @property
    def flagged(self) -> bool:
        return self.exceeds(self.tolerance_milli)


@dataclass(frozen=True)
class ProbeResult:
    method: str
    branches: int
    chosen: Action
    chosen_value: int
    checks: tuple[Check, ...] = ()

    @property
    def flagged(self) -> bool:
        """The untrusted-model flag of the first validation."""

        return bool(self.checks) and self.checks[0].flagged

    @property
    def final_flagged(self) -> bool:
        return bool(self.checks) and self.checks[-1].flagged


class _Run:
    """Per-method view of an oracle: records what this method measured."""

    def __init__(self, oracle: Oracle) -> None:
        self._oracle = oracle
        self._start = oracle.spent
        self.measured: dict[Action, int] = {}

    def value(self, action: Sequence[int]) -> int:
        action = tuple(action)
        if action not in self.measured:
            self.measured[action] = self._oracle.value(action)
        return self.measured[action]

    def result(self, method: str, checks: Sequence[Check] = ()) -> ProbeResult:
        chosen = min(self.measured, key=lambda action: (-self.measured[action], action))
        return ProbeResult(
            method, self._oracle.spent - self._start, chosen, self.measured[chosen], tuple(checks)
        )


def _shift(center: Action, delta: Sequence[int]) -> Action:
    return tuple(c + d for c, d in zip(center, delta))


def run_exhaustive(oracle: Oracle, world: RateTrackingWorld) -> ProbeResult:
    run = _Run(oracle)
    for action in world.grid():
        run.value(action)
    return run.result("exhaustive")


def run_p1(
    oracle: Oracle, world: RateTrackingWorld, *, radius: int, step: int, tolerance_milli: int
) -> ProbeResult:
    """Forward-difference gradient, one step of length ``radius``, one validation."""

    run = _Run(oracle)
    anchor = world.baseline_action
    q0 = run.value(anchor)
    gradient = []
    for axis in range(world.dims):
        shift = step if anchor[axis] + step <= world.grid_radius else -step
        point = tuple(value + (shift if i == axis else 0) for i, value in enumerate(anchor))
        gradient.append(Fraction(run.value(point) - q0, shift))
    proposal = world.clip(_shift(anchor, _toward(gradient, radius, always_full=True)))
    checks = []
    if proposal != anchor:
        move = [p - a for p, a in zip(proposal, anchor)]
        predicted = q0 + sum((g * m for g, m in zip(gradient, move)), Fraction(0))
        checks.append(Check(anchor, q0, proposal, predicted, run.value(proposal), tolerance_milli))
    return run.result("p1", checks)


def _fit_at(
    run: _Run, world: RateTrackingWorld, center: Action, step: int
) -> tuple[QuadraticModel, int]:
    offsets = _stencil_at(world, center, step)
    values = [run.value(_shift(center, offset)) for offset in offsets]
    return fit_quadratic(offsets, values), values[0]


def _propose(
    world: RateTrackingWorld, model: QuadraticModel, center: Action, radius: int
) -> tuple[Action, Fraction]:
    proposal = world.clip(_shift(center, quadratic_step(model, radius)))
    return proposal, model.predict([p - c for p, c in zip(proposal, center)])


def run_p2(
    oracle: Oracle,
    world: RateTrackingWorld,
    *,
    radius: int,
    step: int,
    tolerance_milli: int,
    trust_region: bool = False,
) -> ProbeResult:
    """Fit, predict, validate; optionally one trust-region iteration."""

    run = _Run(oracle)
    anchor = world.baseline_action
    model, q0 = _fit_at(run, world, anchor, step)
    proposal, predicted = _propose(world, model, anchor, radius)
    checks: list[Check] = []
    if proposal != anchor:
        checks.append(Check(anchor, q0, proposal, predicted, run.value(proposal), tolerance_milli))
    if trust_region and checks:
        if checks[0].flagged:
            moved = max(abs(p - a) for p, a in zip(proposal, anchor))
            retry, predicted = _propose(world, model, anchor, max(1, moved // 2))
            if retry not in (anchor, proposal):
                validated = run.value(retry)
                checks.append(Check(anchor, q0, retry, predicted, validated, tolerance_milli))
        else:
            model, q1 = _fit_at(run, world, proposal, step)
            nxt, predicted = _propose(world, model, proposal, radius)
            if nxt != proposal:
                checks.append(Check(proposal, q1, nxt, predicted, run.value(nxt), tolerance_milli))
    return run.result("p2_tr" if trust_region else "p2", checks)


def run_random(
    oracle: Oracle, world: RateTrackingWorld, *, budget: int, rng_seed: int, method: str = "random"
) -> ProbeResult:
    """The baseline action plus ``budget - 1`` distinct uniformly drawn actions."""

    if budget < 1:
        raise ProbeError("budget must be positive")
    run = _Run(oracle)
    anchor = world.baseline_action
    run.value(anchor)
    others = [action for action in world.grid() if action != anchor]
    for action in random.Random(rng_seed).sample(others, min(budget - 1, len(others))):
        run.value(action)
    return run.result(method)


@dataclass(frozen=True)
class LocalProbeConfig:
    """Fixed protocol for one run; every field is part of the report identity."""

    tuning_seeds: tuple[int, ...] = tuple(range(301, 309))
    eval_seeds: tuple[int, ...] = tuple(range(401, 425))
    families: tuple[str, ...] = FAMILIES
    dims: tuple[int, ...] = (1, 2)
    grid_radius: int = 8
    warmup: int = 2
    horizon: int = 6
    rate_unit: int = 8
    track_weight: int = 4
    coupling_max: int = 4
    offset_range: tuple[int, int] = (2, 6)
    smooth_fuel: int = 1
    mild_fuel: int = 40
    penalty: int = 20_000_000
    penalty_delay: int = 3
    stencil_step: int = 1
    radius_grid: tuple[int, ...] = (1, 2, 3, 4, 6, 8, 16)
    tolerance_grid_milli: tuple[int, ...] = (50, 100, 250, 500, 1000, 2000)
    failure_share_milli: int = 100

    def __post_init__(self) -> None:
        for name in ("tuning_seeds", "eval_seeds", "radius_grid", "tolerance_grid_milli"):
            values = getattr(self, name)
            if (
                not isinstance(values, tuple)
                or not values
                or not all(_is_int(value) and value >= 0 for value in values)
                or list(values) != sorted(set(values))
            ):
                raise ProbeError(f"{name} must be a sorted, unique, non-empty tuple of integers >= 0")
        if set(self.tuning_seeds) & set(self.eval_seeds):
            raise ProbeError("tuning and evaluation seeds must be disjoint")
        if not self.families or len(set(self.families)) != len(self.families) or not set(
            self.families
        ) <= set(FAMILIES):
            raise ProbeError(f"families must be distinct members of {FAMILIES}")
        if not self.dims or len(set(self.dims)) != len(self.dims) or not set(self.dims) <= {1, 2}:
            raise ProbeError("dims must be distinct members of (1, 2)")
        for name, minimum in (
            ("grid_radius", 4),
            ("warmup", 0),
            ("horizon", 2),
            ("rate_unit", 1),
            ("track_weight", 1),
            ("coupling_max", 0),
            ("smooth_fuel", 0),
            ("mild_fuel", 0),
            ("penalty", 1),
            ("penalty_delay", 1),
            ("stencil_step", 1),
            ("failure_share_milli", 0),
        ):
            _require_int(getattr(self, name), name, minimum)
        if self.penalty_delay >= self.horizon:
            raise ProbeError("the cliff penalty must fall due inside the horizon")
        if 0 in self.radius_grid:
            raise ProbeError("trust radii must be positive")
        low, high = self.offset_range
        if not (_is_int(low) and _is_int(high) and 2 <= low <= high <= self.grid_radius - 2):
            raise ProbeError("offset_range must satisfy 2 <= low <= high <= grid_radius - 2")
        if 2 * self.stencil_step > self.grid_radius:
            raise ProbeError("the stencil step is too large for the grid")

    def to_payload(self) -> dict[str, Any]:
        return {
            "tuning_seeds": list(self.tuning_seeds),
            "eval_seeds": list(self.eval_seeds),
            "families": list(self.families),
            "dims": list(self.dims),
            "grid_radius": self.grid_radius,
            "warmup": self.warmup,
            "horizon": self.horizon,
            "rate_unit": self.rate_unit,
            "track_weight": self.track_weight,
            "coupling_max": self.coupling_max,
            "offset_range": list(self.offset_range),
            "smooth_fuel": self.smooth_fuel,
            "mild_fuel": self.mild_fuel,
            "penalty": self.penalty,
            "penalty_delay": self.penalty_delay,
            "stencil_step": self.stencil_step,
            "radius_grid": list(self.radius_grid),
            "tolerance_grid_milli": list(self.tolerance_grid_milli),
            "failure_share_milli": self.failure_share_milli,
        }


def make_world(config: LocalProbeConfig, family: str, dims: int, seed: int) -> RateTrackingWorld:
    """Seeded world; geometry depends only on ``(seed, dims)``, so families are paired."""

    if family not in FAMILIES:
        raise ProbeError(f"unknown family {family!r}; expected one of {FAMILIES}")
    if dims not in (1, 2):
        raise ProbeError("dims must be 1 or 2")
    rng = random.Random(seed * 16 + dims)
    bound = config.grid_radius
    low, high = config.offset_range
    coupling = rng.randint(-config.coupling_max, config.coupling_max) if dims == 2 else 0
    desired: list[Fraction] = []
    anchor: list[int] = []
    for _ in range(dims):
        optimum = rng.randint(-(bound - 2), bound - 2)
        offset = rng.randint(low, high)
        # Of the two placements at this distance, keep the one inside the grid.
        start = optimum - offset if optimum >= 0 else optimum + offset
        desired.append(optimum + Fraction(rng.randint(-3, 3), 8))
        anchor.append(start)
    gap = abs(round(desired[0]) - anchor[0])
    cliff_reach = rng.randint(1, max(1, gap - 1))
    u, h = config.rate_unit, config.horizon
    s1, s2 = h * (h + 1) // 2, h * (h + 1) * (2 * h + 1) // 6
    command = tuple(anchor)

    def rate(vector: Sequence[Fraction | int]) -> list[Fraction]:
        if dims == 1:
            return [u * Fraction(vector[0])]
        return [u * Fraction(vector[0]), coupling * Fraction(vector[0]) + u * Fraction(vector[1])]

    position = [config.warmup * item for item in rate(command)]
    # The unconstrained optimum of the tracking term sets M a* = (T - p_w) * S1 / S2.
    targets = tuple(
        _round_half_away(p + r * Fraction(s2, s1)) for p, r in zip(position, rate(desired))
    )
    fields: dict[str, Any] = {
        "dims": dims,
        "grid_radius": bound,
        "warmup": config.warmup,
        "horizon": config.horizon,
        "targets": targets,
        "initial_command": command,
        "baseline_action": command,
        "rate_unit": u,
        "coupling": coupling,
        "track_weight": config.track_weight,
        "fuel": config.mild_fuel if family == "mild" else config.smooth_fuel,
    }
    if family == "rugged":
        sign = 1 if desired[0] > anchor[0] else -1
        fields.update(
            cliff_level=sign * anchor[0] + cliff_reach,
            cliff_sign=sign,
            cliff_axis=0,
            penalty=config.penalty,
            penalty_delay=config.penalty_delay,
        )
    return RateTrackingWorld(**fields)


def grid_actions(world: RateTrackingWorld) -> tuple[Action, ...]:
    return world.grid()


def _regret_share(best: int, baseline: int, value: int) -> Fraction:
    available = best - baseline
    return Fraction(best - value, available) if available > 0 else Fraction(0)


def _milli(value: Fraction) -> int:
    return floor(1000 * value)


@dataclass(frozen=True)
class _Case:
    world: RateTrackingWorld
    table: Mapping[Action, int]
    best: int
    family: str = ""

    @property
    def baseline(self) -> int:
        return self.table[self.world.baseline_action]


def _ground_truth(
    world: RateTrackingWorld, session_id: str, seed: int
) -> tuple[BranchOracle, ProbeResult]:
    oracle = BranchOracle(world, session_id=session_id, seed=seed, prefix="grid")
    return oracle, run_exhaustive(oracle, world)


def _pick(scores: Mapping[int, Fraction], *, maximize: bool) -> int:
    """Best key; ties go to the larger key."""

    sign = 1 if maximize else -1
    return max(scores, key=lambda key: (sign * scores[key], key))


def tune(config: LocalProbeConfig, cases: Sequence[_Case]) -> dict[str, Any]:
    """Pick the p1 step, the p2 trust radius, and the flag tolerance on tuning cases only."""

    step = config.stencil_step
    if not cases:
        raise ProbeError("tuning needs at least one case")

    def mean_share(runner, subset: Sequence[_Case] = cases) -> Fraction:
        total = Fraction(0)
        for case in subset:
            result = runner(TableOracle(case.table), case.world)
            total += _regret_share(case.best, case.baseline, result.chosen_value)
        return total / len(subset)

    p1_scores = {
        radius: mean_share(
            lambda oracle, world, r=radius: run_p1(oracle, world, radius=r, step=step, tolerance_milli=0)
        )
        for radius in config.radius_grid
    }
    p2_scores = {
        radius: mean_share(
            lambda oracle, world, r=radius: run_p2(oracle, world, radius=r, step=step, tolerance_milli=0)
        )
        for radius in config.radius_grid
    }
    # Diagnostic only, never used for selection: what each family alone would prefer.
    p2_by_family = {
        f"{family}_{dims}d": {
            str(radius): _milli(
                mean_share(
                    lambda oracle, world, r=radius: run_p2(
                        oracle, world, radius=r, step=step, tolerance_milli=0
                    ),
                    subset,
                )
            )
            for radius in config.radius_grid
        }
        for family in FAMILIES
        for dims in (1, 2)
        for subset in [[c for c in cases if c.family == family and c.world.dims == dims]]
        if subset
    }
    p1_radius = _pick(p1_scores, maximize=False)
    p2_radius = _pick(p2_scores, maximize=False)
    outcomes = []
    for case in cases:
        result = run_p2(
            TableOracle(case.table), case.world, radius=p2_radius, step=step, tolerance_milli=0
        )
        check = result.checks[0] if result.checks else None
        outcomes.append((check, check is not None and case.world.triggers_cliff(check.proposal)))
    breaks = sum(1 for _, crossed in outcomes if crossed)
    intact = len(outcomes) - breaks
    youden = {}
    for tolerance in config.tolerance_grid_milli:
        alarms = [check is not None and check.exceeds(tolerance) for check, _ in outcomes]
        hits = sum(1 for alarm, (_, crossed) in zip(alarms, outcomes) if alarm and crossed)
        false_alarms = sum(1 for alarm, (_, crossed) in zip(alarms, outcomes) if alarm and not crossed)
        tpr = Fraction(hits, breaks) if breaks else Fraction(0)
        fpr = Fraction(false_alarms, intact) if intact else Fraction(0)
        youden[tolerance] = tpr - fpr
    intact_errors = [c.error_milli for c, crossed in outcomes if c is not None and not crossed]
    break_errors = [c.error_milli for c, crossed in outcomes if crossed]
    return {
        "p1_radius": p1_radius,
        "p2_radius": p2_radius,
        "tolerance_milli": _pick(youden, maximize=True),
        "tuning_cases": len(cases),
        "tuning_cliff_crossings": breaks,
        "tuning_intact_error_milli_max": max(intact_errors) if intact_errors else -1,
        "tuning_crossed_error_milli_min": min(break_errors) if break_errors else -1,
        "p1_mean_regret_share_milli": {str(k): _milli(v) for k, v in p1_scores.items()},
        "p2_mean_regret_share_milli": {str(k): _milli(v) for k, v in p2_scores.items()},
        "p2_mean_regret_share_milli_by_family": p2_by_family,
        "tolerance_youden_milli": {str(k): _milli(v) for k, v in youden.items()},
    }


def _session_id(role: str, family: str, dims: int, seed: int) -> str:
    return f"{role}_{family}_{dims}d_{seed}"


def _method_row(result: ProbeResult, case: _Case) -> dict[str, Any]:
    return {
        "branches": result.branches,
        "chosen": list(result.chosen),
        "regret": case.best - result.chosen_value,
        "regret_share_milli": _milli(_regret_share(case.best, case.baseline, result.chosen_value)),
        "flagged": result.flagged,
        "final_flagged": result.final_flagged,
        "checks": [
            {
                "center": list(check.center),
                "proposal": list(check.proposal),
                "error_milli": check.error_milli,
                "flagged": check.flagged,
                "crossed_cliff": case.world.triggers_cliff(check.proposal),
            }
            for check in result.checks
        ],
    }


def _spread(values: Sequence[int]) -> list[int]:
    """``[min, median, max]`` or ``[]``."""

    ordered = sorted(values)
    return [ordered[0], ordered[len(ordered) // 2], ordered[-1]] if ordered else []


def _detector_row(
    config: LocalProbeConfig, method: str, family: str, dims: int, group: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    """First-check flag against the model-break label and against regret failure."""

    items = [row["methods"][method] for row in group]
    first = [item["checks"][0] if item["checks"] else None for item in items]
    flagged = [item["flagged"] for item in items]
    crossed = [check is not None and check["crossed_cliff"] for check in first]
    failed = [item["regret_share_milli"] > config.failure_share_milli for item in items]

    def both(a: Sequence[bool], b: Sequence[bool]) -> int:
        return sum(1 for x, y in zip(a, b) if x and y)

    def negate(values: Sequence[bool]) -> list[bool]:
        return [not value for value in values]

    return {
        "method": method,
        "family": family,
        "dims": dims,
        "worlds": len(items),
        "checked": sum(1 for check in first if check is not None),
        "flagged": sum(flagged),
        "crossed": sum(crossed),
        "flagged_crossed": both(flagged, crossed),
        "flagged_intact": both(flagged, negate(crossed)),
        "failures": sum(failed),
        "flagged_failures": both(flagged, failed),
        "missed_failures": both(negate(flagged), failed),
        "intact_error_milli_spread": _spread(
            [c["error_milli"] for c, x in zip(first, crossed) if c is not None and not x]
        ),
        "crossed_error_milli_spread": _spread([c["error_milli"] for c, x in zip(first, crossed) if x]),
    }


def evaluate(config: LocalProbeConfig | None = None) -> dict[str, Any]:
    """Tune on tuning seeds, then run every method on held-out seeds by real branches."""

    config = LocalProbeConfig() if config is None else config
    step = config.stencil_step
    cases = []
    for dims in config.dims:
        for family in config.families:
            for seed in config.tuning_seeds:
                world = make_world(config, family, dims, seed)
                oracle, exhaustive = _ground_truth(
                    world, _session_id("tune", family, dims, seed), seed
                )
                cases.append(_Case(world, oracle.table(), exhaustive.chosen_value, family))
    tuned = tune(config, cases)
    world_rows: list[dict[str, Any]] = []
    for dims in config.dims:
        for family in config.families:
            for seed in config.eval_seeds:
                world = make_world(config, family, dims, seed)
                grid_oracle, exhaustive = _ground_truth(
                    world, _session_id("eval", family, dims, seed), seed
                )
                case = _Case(world, grid_oracle.table(), exhaustive.chosen_value, family)
                runs = {"exhaustive": exhaustive}
                runs["p1"] = run_p1(
                    grid_oracle.sibling("pone"),
                    world,
                    radius=tuned["p1_radius"],
                    step=step,
                    tolerance_milli=tuned["tolerance_milli"],
                )
                for method, trust_region in (("p2", False), ("p2_tr", True)):
                    runs[method] = run_p2(
                        grid_oracle.sibling(method.replace("_", "")),
                        world,
                        radius=tuned["p2_radius"],
                        step=step,
                        tolerance_milli=tuned["tolerance_milli"],
                        trust_region=trust_region,
                    )
                for method, matched in (("random", "p2"), ("random_tr", "p2_tr")):
                    runs[method] = run_random(
                        grid_oracle.sibling(method.replace("_", "")),
                        world,
                        budget=runs[matched].branches,
                        rng_seed=seed * 100 + dims * 10 + FAMILIES.index(family),
                        method=method,
                    )
                p2 = runs["p2"]
                if p2.flagged:
                    runs["p2_guarded"] = replace(
                        exhaustive, method="p2_guarded", checks=p2.checks
                    )
                else:
                    runs["p2_guarded"] = replace(p2, method="p2_guarded")
                for result in runs.values():
                    if case.table[result.chosen] != result.chosen_value:
                        raise ProbeError("branch values diverged between methods on one snapshot")
                manifest = grid_oracle.session.manifest()
                world_rows.append(
                    {
                        "seed": seed,
                        "family": family,
                        "dims": dims,
                        "world_digest": content_digest(
                            "experiment.local-probe-world", world.config_payload()
                        ),
                        "cubic_curvature_ratio_milli": world.cubic_curvature_ratio_milli(),
                        "baseline_action": list(world.baseline_action),
                        "argmax": list(exhaustive.chosen),
                        "q_best": case.best,
                        "q_baseline": case.baseline,
                        "grid_size": len(world.grid()),
                        "manifest_digest": manifest.digest,
                        "manifest_branches": len(manifest.branches) - 1,
                        "methods": {method: _method_row(runs[method], case) for method in METHODS},
                    }
                )
    summary = []
    detector = []
    for dims in config.dims:
        for family in config.families:
            group = [row for row in world_rows if row["dims"] == dims and row["family"] == family]
            n = len(group)
            for method in METHODS:
                items = [row["methods"][method] for row in group]

                def rate(key: str, items: Sequence[Mapping[str, Any]] = items) -> int:
                    return (1000 * sum(1 for item in items if item[key])) // len(items)

                summary.append(
                    {
                        "method": method,
                        "family": family,
                        "dims": dims,
                        "worlds": n,
                        "mean_branches_milli": (1000 * sum(item["branches"] for item in items)) // n,
                        "max_branches": max(item["branches"] for item in items),
                        "mean_regret": sum(item["regret"] for item in items) // n,
                        "mean_regret_share_milli": sum(i["regret_share_milli"] for i in items) // n,
                        "argmax_hit_milli": (1000 * sum(1 for i in items if i["regret"] == 0)) // n,
                        "flag_milli": rate("flagged"),
                        "final_flag_milli": rate("final_flagged"),
                    }
                )
            for method in ("p1", "p2"):
                detector.append(_detector_row(config, method, family, dims, group))
    report = {
        "evidence_label": "synthetic",
        "config": config.to_payload(),
        "tuned": tuned,
        "worlds": world_rows,
        "summary": summary,
        "detector": detector,
    }
    report["report_digest"] = content_digest("experiment.local-probe-report", report)
    return report


__all__ = [
    "FAMILIES",
    "KEEP",
    "METHODS",
    "BranchOracle",
    "Check",
    "LocalProbeConfig",
    "ProbeError",
    "ProbeResult",
    "QuadraticModel",
    "RateTrackingWorld",
    "TableOracle",
    "action_name",
    "evaluate",
    "fit_quadratic",
    "grid_actions",
    "make_world",
    "parse_action",
    "quadratic_step",
    "run_exhaustive",
    "run_p1",
    "run_p2",
    "run_random",
    "stencil",
    "tune",
]
