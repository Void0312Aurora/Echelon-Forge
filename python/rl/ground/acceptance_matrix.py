"""Native acceptance matrix over fixture-derived Ground infantry cases.

Each case from :mod:`python.rl.ground.fixture_cases` is run through
``GroundInfantryNativeEnv`` under a scripted heading-to-goal controller. The
record keeps the native preflight verdict, the rollout outcome, and a trace
digest, and compares them with the fixture-derived expectation. A case whose
native outcome disagrees with that expectation, or that ends in neither
termination nor truncation, fails closed.

Authority stays ``native_probe_only``: this is acceptance tooling, not a
production WorldBatch environment, a route planner, or a training entry.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, replace
from typing import Any, Callable, Hashable, Mapping, MutableMapping, Sequence

import numpy as np

from .fixture_cases import ArnisInfantryFixture, FixtureCase, derive_acceptance_cases
from .native_env import GroundInfantryNativeEnv
from .native_probe import GroundInfantryNativeProbe


ACCEPTANCE_MATRIX_CONTRACT_VERSION = "ground_infantry_native_acceptance_matrix.v1"

# Native env/probe contract defaults. The matrix reuses them unchanged; it
# introduces no reward, termination, or speed coefficient of its own.
_PROBE_DEFAULTS = GroundInfantryNativeProbe.__init__.__kwdefaults__ or {}
CONTRACT_GOAL_RADIUS_M = float(_PROBE_DEFAULTS["goal_radius_m"])
CONTRACT_MAX_SPEED_MPS = float(_PROBE_DEFAULTS["max_speed_mps"])
CONTRACT_TIME_STEP_S = float(_PROBE_DEFAULTS["time_step_s"])
CONTRACT_BLOCKED_STEP_LIMIT = int(_PROBE_DEFAULTS["blocked_step_limit"])

HELD_CLAIMS = (
    "route_planning",
    "line_of_sight",
    "cover",
    "sensing",
    "multi_agent",
)


def heading_to_goal_action(observation: Mapping[str, Any]) -> np.ndarray:
    """Scripted baseline: full-speed standing walk straight at the active goal.

    The action lies in the declared normalized Gym space
    (heading / 180 deg, speed fraction, stance / 2).
    """

    goal_dx, goal_dy, _distance = (float(value) for value in observation["mission_state"])
    heading_deg = math.degrees(math.atan2(goal_dx, goal_dy))
    return np.asarray([heading_deg / 180.0, 1.0, 0.0], dtype=np.float32)


def rollout_step_budget(route_distance_m: float, minimum_route_multiplier: float) -> int:
    """Finite horizon from the native preflight's own worst-case route cost.

    ``minimum_route_multiplier`` is the smallest native sampled combined
    movement multiplier across the validated segments; the budget is the
    number of contract ticks needed to cover the route at that speed.
    """

    if minimum_route_multiplier <= 0.0 or not math.isfinite(minimum_route_multiplier):
        return CONTRACT_BLOCKED_STEP_LIMIT
    per_step_m = CONTRACT_MAX_SPEED_MPS * CONTRACT_TIME_STEP_S * minimum_route_multiplier
    return max(1, int(math.ceil(route_distance_m / per_step_m)))


def _canonical(record: Mapping[str, Any]) -> bytes:
    return json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"


def trace_digest(records: Sequence[Mapping[str, Any]]) -> str:
    """SHA-256 over canonical JSON lines (one record per reset/step)."""

    digest = hashlib.sha256()
    for record in records:
        digest.update(_canonical(record))
    return digest.hexdigest()


@dataclass(frozen=True)
class CaseRollout:
    """Native outcome of one scripted rollout of one case."""

    case_id: str
    seed: int
    max_steps: int
    preflight: Mapping[str, Any]
    steps: int
    terminated: bool
    truncated: bool
    termination_reason: str | None
    truncation_reason: str | None
    blocked_reasons: tuple[str, ...]
    bridge_admitted_steps: int
    final_position_xy_m: tuple[float, float]
    total_reward: float
    digest: str
    first_divergent_record: int | None
    records: tuple[Mapping[str, Any], ...] | None
    actions: tuple[tuple[float, ...], ...] | None

    @property
    def outcome(self) -> str:
        if self.termination_reason == "waypoint_reached":
            return "reach"
        if self.truncation_reason == "blocked_step_limit":
            return "block"
        if self.termination_reason is not None:
            return f"terminated:{self.termination_reason}"
        if self.truncation_reason is not None:
            return f"truncated:{self.truncation_reason}"
        return "unterminated"


def _probe_for_case(case: FixtureCase, *, max_steps: int) -> GroundInfantryNativeProbe:
    return GroundInfantryNativeProbe.from_fixture(
        start_xy_m=case.start_xy_m,
        waypoints_xy_m=case.waypoints_xy_m,
        max_steps=max_steps,
    )


def preflight_case(case: FixtureCase, *, seed: int) -> dict[str, Any]:
    """Native fixed-sequence validation verdict for a case (read-only)."""

    probe = _probe_for_case(case, max_steps=1)
    _observation, info = probe.reset(seed=seed)
    return dict(info["route_validation"])


def minimum_route_multiplier(preflight: Mapping[str, Any]) -> float:
    multipliers = [
        float(observation[7]) for observation in preflight["segment_movement_observations"]
    ]
    return min(multipliers) if multipliers else 0.0


def case_step_budget(case: FixtureCase, *, seed: int) -> int:
    """Rollout horizon derived from native preflight evidence for the case.

    A passable route is budgeted at its worst sampled native multiplier. A
    blocked route is budgeted for the distance to its first predicted blocked
    sample at the worst native multiplier of its dry approach (start to the
    last predicted passable sample), plus the contract blocked-step limit.
    """

    if case.approach_xy_m is None:
        preflight = preflight_case(case, seed=seed)
        return rollout_step_budget(case.route_distance_m, minimum_route_multiplier(preflight))
    approach = replace(
        case,
        expected="reach",
        expected_block_reason=None,
        waypoints_xy_m=(case.approach_xy_m,),
    )
    approach_preflight = preflight_case(approach, seed=seed)
    if not approach_preflight["passable"]:
        # The predicted dry approach is itself blocked natively, so the
        # rollout must block at once, within the blocked-step limit.
        return CONTRACT_BLOCKED_STEP_LIMIT
    distance_m = case.block_distance_m if case.block_distance_m is not None else case.route_distance_m
    return (
        rollout_step_budget(distance_m, minimum_route_multiplier(approach_preflight))
        + CONTRACT_BLOCKED_STEP_LIMIT
    )


def run_case(
    case: FixtureCase,
    *,
    seed: int,
    max_steps: int | None = None,
    controller: Callable[[Mapping[str, Any]], np.ndarray] = heading_to_goal_action,
    keep_records: bool = False,
    compare_records: Sequence[Mapping[str, Any]] | None = None,
) -> CaseRollout:
    """Reset/step one case under ``controller`` until termination or truncation.

    The trace is hashed incrementally as canonical JSON lines. ``keep_records``
    retains the records in memory; ``compare_records`` reports the index of the
    first record that differs from a previous run of the same case.
    """

    if max_steps is None:
        max_steps = case_step_budget(case, seed=seed)
    env = GroundInfantryNativeEnv(_probe_for_case(case, max_steps=max_steps))
    observation, info = env.reset(seed=seed)
    preflight = dict(info["route_validation"])
    digest = hashlib.sha256()
    kept: list[dict[str, Any]] = []
    first_divergent: int | None = None
    record_index = 0

    def record(entry: dict[str, Any]) -> None:
        nonlocal first_divergent, record_index
        digest.update(_canonical(entry))
        if keep_records:
            kept.append(entry)
        if compare_records is not None and first_divergent is None:
            if record_index >= len(compare_records) or _canonical(compare_records[record_index]) != _canonical(entry):
                first_divergent = record_index
        record_index += 1

    record(
        {
            "observation": {key: value.tolist() for key, value in observation.items()},
            "trace": info["trace"],
        }
    )
    terminated = truncated = False
    termination_reason = truncation_reason = None
    blocked_reasons: list[str] = []
    actions: list[tuple[float, ...]] = []
    bridge_steps = 0
    total_reward = 0.0
    steps = 0
    while not (terminated or truncated):
        action = controller(observation)
        if keep_records:
            actions.append(tuple(float(value) for value in np.asarray(action).reshape(-1)))
        observation, reward, terminated, truncated, info = env.step(action)
        steps += 1
        total_reward += reward
        record(
            {
                "observation": {key: value.tolist() for key, value in observation.items()},
                "reward": reward,
                "terminated": terminated,
                "truncated": truncated,
                "trace": info["trace"],
            }
        )
        if info["blocked_reason"] is not None:
            blocked_reasons.append(str(info["blocked_reason"]))
        if float(info["trace"]["transition_effects"][5]) > 0.5:
            bridge_steps += 1
        termination_reason = info["termination_reason"]
        truncation_reason = info["truncation_reason"]
    position = observation["position_local_enu_m"]
    return CaseRollout(
        case_id=case.case_id,
        seed=seed,
        max_steps=max_steps,
        preflight=preflight,
        steps=steps,
        terminated=terminated,
        truncated=truncated,
        termination_reason=termination_reason,
        truncation_reason=truncation_reason,
        blocked_reasons=tuple(dict.fromkeys(blocked_reasons)),
        bridge_admitted_steps=bridge_steps,
        final_position_xy_m=(float(position[0]), float(position[1])),
        total_reward=total_reward,
        digest=digest.hexdigest(),
        first_divergent_record=(
            first_divergent
            if first_divergent is not None or compare_records is None or record_index == len(compare_records)
            else record_index
        ),
        records=tuple(kept) if keep_records else None,
        actions=tuple(actions) if keep_records else None,
    )


def case_failures(case: FixtureCase, rollout: CaseRollout) -> list[str]:
    """Fail-closed comparison between the fixture expectation and native outcome."""

    failures: list[str] = []
    if not (rollout.terminated or rollout.truncated):
        failures.append("rollout_did_not_end")
    if case.expected == "held":
        # Held semantics carry no admission claim; only the end state is gated.
        return failures
    preflight = rollout.preflight
    if case.expected == "reach":
        if not preflight["passable"]:
            failures.append(f"preflight_blocked:{preflight['blocked_reason']}")
        if rollout.outcome != "reach":
            failures.append(f"outcome:{rollout.outcome}")
        if rollout.blocked_reasons:
            failures.append(f"blocked_during_reach:{','.join(rollout.blocked_reasons)}")
        if case.requires_bridge_admission and rollout.bridge_admitted_steps == 0:
            failures.append("bridge_not_admitted")
    else:
        if preflight["passable"]:
            failures.append("preflight_passable_for_block_case")
        elif preflight["blocked_reason"] != case.expected_block_reason:
            failures.append(f"preflight_reason:{preflight['blocked_reason']}")
        if rollout.outcome != "block":
            failures.append(f"outcome:{rollout.outcome}")
        if case.expected_block_reason not in rollout.blocked_reasons:
            failures.append(f"rollout_reasons:{','.join(rollout.blocked_reasons) or 'none'}")
        goal = case.waypoints_xy_m[-1]
        start_gap = math.hypot(goal[0] - case.start_xy_m[0], goal[1] - case.start_xy_m[1])
        final_gap = math.hypot(goal[0] - rollout.final_position_xy_m[0], goal[1] - rollout.final_position_xy_m[1])
        if case.block_distance_m is not None and final_gap < start_gap - case.block_distance_m:
            failures.append("advanced_past_predicted_block")
    return failures


def matrix_row(case: FixtureCase, rollout: CaseRollout) -> dict[str, Any]:
    failures = case_failures(case, rollout)
    preflight = rollout.preflight
    return {
        "case_id": case.case_id,
        "category": case.category,
        "expected": case.expected,
        "expected_block_reason": case.expected_block_reason,
        "preflight_passable": bool(preflight["passable"]),
        "preflight_blocked_reason": preflight["blocked_reason"],
        "outcome": rollout.outcome,
        "termination_reason": rollout.termination_reason,
        "truncation_reason": rollout.truncation_reason,
        "blocked_reasons": list(rollout.blocked_reasons),
        "bridge_admitted_steps": rollout.bridge_admitted_steps,
        "steps": rollout.steps,
        "max_steps": rollout.max_steps,
        "seed": rollout.seed,
        "trace_sha256": rollout.digest,
        "verdict": "pass" if not failures else "fail",
        "failures": failures,
    }


def _leaf(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def difference_paths(left: Any, right: Any, path: str = "") -> set[str]:
    """JSON paths whose values differ; list indices collapse to ``[]``.

    Values are compared by canonical JSON, the encoding the trace digest
    hashes. A subtree whose canonical JSON is identical has no differing path,
    so the walk only descends into subtrees that actually differ.
    """

    if _leaf(left) == _leaf(right):
        return set()
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        paths: set[str] = set()
        for key in sorted(set(left) | set(right)):
            child = f"{path}.{key}" if path else str(key)
            if key not in left or key not in right:
                paths.add(child)
            else:
                paths |= difference_paths(left[key], right[key], child)
        return paths
    if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
        if len(left) != len(right):
            return {f"{path}[]#length"}
        paths = set()
        for left_item, right_item in zip(left, right):
            paths |= difference_paths(left_item, right_item, f"{path}[]")
        return paths
    return {path}


def replay_determinism(
    case: FixtureCase,
    *,
    seed: int,
    alternate_seed: int,
    reference: CaseRollout | None = None,
) -> dict[str, Any]:
    """Same-seed, probe-replay, and cross-seed determinism evidence for one case.

    * ``same_seed_identical``: two independent env rollouts with the same seed
      give a byte-identical canonical trace. ``reference`` may supply the
      first of them: an earlier default-horizon rollout of this case and seed
      (for example the acceptance-matrix row's), so the same-seed check does
      not repeat it. Without one, a second rollout here is compared record by
      record. On a digest mismatch with ``reference``, a further same-seed
      rollout localizes ``same_seed_first_divergent_record``.
    * ``probe_replay_identical``: ``GroundInfantryNativeProbe.replay`` of the
      recorded controller actions reproduces the env's probe trace exactly.
    * ``cross_seed_difference_paths``: every trace path that differs when only
      the reset seed changes.
    """

    max_steps = case_step_budget(case, seed=seed)
    if reference is not None and (reference.case_id, reference.seed) != (case.case_id, seed):
        raise ValueError(
            f"{case.case_id}: reference rollout is {reference.case_id!r} seed {reference.seed}, not seed {seed}"
        )
    first = run_case(case, seed=seed, max_steps=max_steps, keep_records=True)
    assert first.records is not None and first.actions is not None
    same_seed_identical = reference is not None and (
        reference.max_steps == max_steps and reference.digest == first.digest
    )
    first_divergent: int | None = None
    if not same_seed_identical:
        second = run_case(case, seed=seed, max_steps=max_steps, compare_records=first.records)
        first_divergent = second.first_divergent_record
        if reference is None:
            same_seed_identical = second.digest == first.digest and first_divergent is None
    probe = _probe_for_case(case, max_steps=max_steps)
    replayed = probe.replay(
        [GroundInfantryNativeEnv._probe_action(action) for action in first.actions],
        seed=seed,
    )
    env_traces = [record["trace"] for record in first.records]
    probe_identical = trace_digest(list(replayed)) == trace_digest(env_traces)
    alternate = run_case(case, seed=alternate_seed, max_steps=max_steps, keep_records=True)
    assert alternate.records is not None
    cross_paths = sorted(difference_paths(list(first.records), list(alternate.records)))
    return {
        "case_id": case.case_id,
        "seed": seed,
        "alternate_seed": alternate_seed,
        "records": len(first.records),
        "trace_sha256": first.digest,
        "same_seed_reference": "supplied_rollout" if reference is not None else "second_rollout",
        "same_seed_identical": same_seed_identical,
        "same_seed_first_divergent_record": first_divergent,
        "probe_replay_identical": probe_identical,
        "cross_seed_identical": alternate.digest == first.digest,
        "cross_seed_difference_paths": cross_paths,
        "cross_seed_outcome_identical": (
            alternate.outcome == first.outcome and alternate.steps == first.steps
        ),
    }


RolloutCache = MutableMapping[Hashable, CaseRollout]
"""Scripted default-horizon rollouts shared across reports (see :func:`cached_rollout`)."""


def _rollout_key(case: FixtureCase, seed: int) -> Hashable:
    # Every input that determines the scripted default-horizon rollout: the
    # reset seed, the route, and the block geometry the step budget reads.
    return (
        int(seed),
        case.case_id,
        case.start_xy_m,
        case.waypoints_xy_m,
        case.approach_xy_m,
        case.block_distance_m,
    )


def cached_rollout(case: FixtureCase, *, seed: int, rollouts: RolloutCache | None) -> CaseRollout:
    """Scripted default-horizon rollout of ``case``, reused from ``rollouts``.

    ``rollouts`` lets the acceptance matrix, the curriculum stages, and the
    replay-determinism reference share one native rollout per case and seed
    instead of re-running it. A missing entry is run and stored.
    """

    if rollouts is None:
        return run_case(case, seed=seed)
    key = _rollout_key(case, seed)
    rollout = rollouts.get(key)
    if rollout is None:
        rollout = rollouts[key] = run_case(case, seed=seed)
    return rollout


def build_acceptance_matrix(
    *,
    seed: int,
    fixture: ArnisInfantryFixture | None = None,
    cases: Sequence[FixtureCase] | None = None,
    rollouts: RolloutCache | None = None,
) -> dict[str, Any]:
    """Run every derived case and return a deterministic matrix report.

    ``rollouts`` is an optional per-seed cache shared with the curriculum
    runner; see :func:`cached_rollout`.
    """

    fixture = fixture or ArnisInfantryFixture()
    cases = tuple(cases) if cases is not None else derive_acceptance_cases(
        fixture, goal_radius_m=CONTRACT_GOAL_RADIUS_M
    )
    rows = [matrix_row(case, cached_rollout(case, seed=seed, rollouts=rollouts)) for case in cases]
    summary: dict[str, dict[str, int]] = {}
    for row in rows:
        bucket = summary.setdefault(row["category"], {"cases": 0, "pass": 0, "fail": 0})
        bucket["cases"] += 1
        bucket[row["verdict"]] += 1
    return {
        "contract_version": ACCEPTANCE_MATRIX_CONTRACT_VERSION,
        "authority": "native_probe_only",
        "production_boundary": "not_world_batch",
        "controller": "scripted_heading_to_goal",
        "seed": seed,
        "case_count": len(rows),
        "summary": summary,
        "valid": all(row["verdict"] == "pass" for row in rows),
        "rows": rows,
        "cases": [case.as_dict() for case in cases],
        "does_not_claim": list(HELD_CLAIMS),
    }


__all__ = [
    "ACCEPTANCE_MATRIX_CONTRACT_VERSION",
    "CONTRACT_BLOCKED_STEP_LIMIT",
    "CONTRACT_GOAL_RADIUS_M",
    "CONTRACT_MAX_SPEED_MPS",
    "CONTRACT_TIME_STEP_S",
    "CaseRollout",
    "HELD_CLAIMS",
    "RolloutCache",
    "build_acceptance_matrix",
    "cached_rollout",
    "case_failures",
    "case_step_budget",
    "difference_paths",
    "replay_determinism",
    "heading_to_goal_action",
    "matrix_row",
    "minimum_route_multiplier",
    "preflight_case",
    "rollout_step_budget",
    "run_case",
    "trace_digest",
]
