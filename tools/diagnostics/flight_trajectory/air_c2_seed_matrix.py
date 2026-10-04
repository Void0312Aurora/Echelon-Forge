#!/usr/bin/env python3
"""Run the accepted-seed and same-process replay gate for scripted Air C2."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence


DEFAULT_ACCEPTED_SEEDS = (0, 1, 2)
DEFAULT_SCENARIO = "scenarios/combined/takeoff_to_landing_c2_task_demo_v1.json"


@dataclass(frozen=True)
class SeedGateRecord:
    seed: int
    termination_reason: str
    mission_status: tuple[float, ...]
    c2_report_valid: bool
    final_command_code: int
    final_on_runway_geom: float | None
    steps: int
    replay_equal: bool


def _episode_fingerprint(data: dict[str, Any]) -> str:
    """Hash summary and trajectory arrays so replay checks include full state."""

    digest = hashlib.sha256()
    summary = asdict(data["summary"])
    digest.update(json.dumps(summary, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    for key in ("x", "y", "z", "cmd_code", "waypoint_idx"):
        value = data[key]
        digest.update(str(key).encode("ascii"))
        digest.update(value.dtype.str.encode("ascii"))
        digest.update(json.dumps(tuple(int(size) for size in value.shape)).encode("ascii"))
        digest.update(value.tobytes())
    digest.update(json.dumps(list(data["baseline_mode"]), separators=(",", ":")).encode("utf-8"))
    return digest.hexdigest()


def _run_once(*, trajectory: Any, scenario_path: str, seed: int, max_steps: int | None, zero_randomization: bool):
    env = trajectory._make_env(
        scenario_path=scenario_path,
        train_config=None,
        scripted=True,
        zero_randomization=zero_randomization,
    )
    try:
        return trajectory._collect_episode(
            env=env,
            model=None,
            scripted=True,
            seed=int(seed),
            max_steps=max_steps,
            zero_randomization=zero_randomization,
            scenario_path=scenario_path,
        )
    finally:
        env.close()


def run_seed_matrix(
    *,
    scenario_path: str,
    seeds: Sequence[int] = DEFAULT_ACCEPTED_SEEDS,
    max_steps: int | None = None,
    zero_randomization: bool = False,
    replay: bool = True,
) -> dict[str, Any]:
    """Run every accepted seed and fail closed on any episode/replay mismatch."""

    repo_root = Path(__file__).resolve().parents[3]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from python.runtime_bootstrap import ensure_repo_imports

    ensure_repo_imports()
    from tools.diagnostics.flight_trajectory import takeoff_to_landing as trajectory

    normalized_seeds = tuple(int(seed) for seed in seeds)
    if not normalized_seeds or len(set(normalized_seeds)) != len(normalized_seeds):
        raise ValueError("Air C2 seed matrix requires a non-empty set of unique seeds")
    scenario_candidate = Path(str(scenario_path))
    if not scenario_candidate.is_absolute():
        scenario_candidate = repo_root / scenario_candidate
    resolved_scenario = str(scenario_candidate.resolve())
    records: list[SeedGateRecord] = []
    for seed in normalized_seeds:
        first = _run_once(
            trajectory=trajectory,
            scenario_path=resolved_scenario,
            seed=seed,
            max_steps=max_steps,
            zero_randomization=zero_randomization,
        )
        second = (
            _run_once(
                trajectory=trajectory,
                scenario_path=resolved_scenario,
                seed=seed,
                max_steps=max_steps,
                zero_randomization=zero_randomization,
            )
            if replay
            else None
        )
        summary = first["summary"]
        replay_equal = second is None or _episode_fingerprint(first) == _episode_fingerprint(second)
        status = tuple(float(value) for value in summary.mission_status)
        runway = summary.final_on_runway_geom
        record = SeedGateRecord(
            seed=int(seed),
            termination_reason=str(summary.termination_reason),
            mission_status=status,
            c2_report_valid=bool(summary.c2_report_valid),
            final_command_code=int(summary.final_command_code),
            final_on_runway_geom=None if runway is None else float(runway),
            steps=int(summary.steps),
            replay_equal=bool(replay_equal),
        )
        records.append(record)
        if (
            record.termination_reason != "success_objective"
            or record.mission_status != (4.0, 1.0, 1.0, 1.0)
            or not record.c2_report_valid
            or record.final_command_code != 4
            or record.final_on_runway_geom is None
            or record.final_on_runway_geom < 0.5
            or not record.replay_equal
        ):
            raise RuntimeError(f"Air C2 seed gate failed for seed {seed}: {asdict(record)}")

    return {
        "scenario": resolved_scenario,
        "seeds": list(normalized_seeds),
        "zero_randomization": bool(zero_randomization),
        "replay_checked": bool(replay),
        "records": [asdict(record) for record in records],
        "accepted": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", default=DEFAULT_SCENARIO)
    parser.add_argument("--seed", action="append", type=int, dest="seeds")
    parser.add_argument("--max_steps", type=int, default=None)
    parser.add_argument("--zero_randomization", action="store_true")
    parser.add_argument("--no_replay", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = run_seed_matrix(
        scenario_path=args.scenario,
        seeds=tuple(args.seeds) if args.seeds else DEFAULT_ACCEPTED_SEEDS,
        max_steps=args.max_steps,
        zero_randomization=bool(args.zero_randomization),
        replay=not bool(args.no_replay),
    )
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
