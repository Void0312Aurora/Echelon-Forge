#!/usr/bin/env python3
"""Run the accepted-seed and same-process replay gate for scripted Air EW."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence


DEFAULT_ACCEPTED_SEEDS = (20260516,)
DEFAULT_SCENARIO = "scenarios/air_combat/air_combat_1v1_headon_sensor_smoke_v1.json"
DEFAULT_RESPONSE_DOCTRINE = "countermeasure_ready"


@dataclass(frozen=True)
class EWSeedGateRecord:
    seed: int
    steps: int
    launch_warning_steps: tuple[int, ...]
    countermeasure_request_steps: tuple[int, ...]
    countermeasure_samples: int
    scripted_runtime_decisions: int
    replay_equal: bool


def _fingerprint(data: dict[str, Any]) -> str:
    """Hash the complete JSON-compatible demo record for replay comparison."""

    digest = hashlib.sha256()
    digest.update(json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    return digest.hexdigest()


def _run_once(*, scenario_path: str, seed: int, max_steps: int, response_doctrine: str) -> dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from python.runtime_bootstrap import ensure_repo_imports

    ensure_repo_imports()
    from tools.diagnostics.air_ew_scripted_demo import run_demo

    return run_demo(
        scenario_path=scenario_path,
        seed=int(seed),
        max_steps=int(max_steps),
        response_doctrine=response_doctrine,
    )


def _validate_record(
    *,
    data: dict[str, Any],
    seed: int,
    response_doctrine: str,
) -> EWSeedGateRecord:
    warnings = tuple(int(step) for step in data.get("launch_warning_steps", []))
    requests = tuple(int(step) for step in data.get("countermeasure_request_steps", []))
    samples = list(data.get("countermeasure_state_samples", []))
    if not warnings:
        raise RuntimeError(f"Air EW seed gate found no launch warning for seed {seed}")
    if requests != warnings:
        raise RuntimeError(
            f"Air EW seed gate warning/request mismatch for seed {seed}: "
            f"warnings={warnings}, requests={requests}"
        )
    if len(samples) != len(requests):
        raise RuntimeError(
            f"Air EW seed gate resource trace length mismatch for seed {seed}: "
            f"requests={len(requests)}, samples={len(samples)}"
        )
    previous_chaff: int | None = None
    previous_flare: int | None = None
    for sample in samples:
        chaff = int(sample.get("chaff_remaining", -1))
        flare = int(sample.get("flare_remaining", -1))
        if chaff < 0 or flare < 0:
            raise RuntimeError(f"Air EW seed gate has invalid resource sample for seed {seed}: {sample}")
        if previous_chaff is not None and chaff > previous_chaff:
            raise RuntimeError(f"Air EW chaff inventory increased for seed {seed}")
        if previous_flare is not None and flare > previous_flare:
            raise RuntimeError(f"Air EW flare inventory increased for seed {seed}")
        previous_chaff = chaff
        previous_flare = flare
    if response_doctrine in {"countermeasure_ready", "chaff_only"} and min(
        int(sample["chaff_remaining"]) for sample in samples
    ) >= 60:
        raise RuntimeError(f"Air EW chaff request did not consume native inventory for seed {seed}")
    if response_doctrine in {"countermeasure_ready", "flare_only"} and min(
        int(sample["flare_remaining"]) for sample in samples
    ) >= 30:
        raise RuntimeError(f"Air EW flare request did not consume native inventory for seed {seed}")
    decisions = int(data.get("scripted_runtime_decisions", 0))
    if decisions != int(data.get("steps", 0)):
        raise RuntimeError(
            f"Air EW scripted decision count does not cover the episode for seed {seed}: "
            f"decisions={decisions}, steps={data.get('steps')}"
        )
    if data.get("native_countermeasure_state") != "instrument_state_projection":
        raise RuntimeError(f"Air EW seed gate lost native resource provenance for seed {seed}")
    if not str(data.get("scripted_runtime_identity", "")):
        raise RuntimeError(f"Air EW seed gate has no scripted replay identity for seed {seed}")
    return EWSeedGateRecord(
        seed=int(seed),
        steps=int(data.get("steps", 0)),
        launch_warning_steps=warnings,
        countermeasure_request_steps=requests,
        countermeasure_samples=len(samples),
        scripted_runtime_decisions=decisions,
        replay_equal=False,
    )


def run_seed_matrix(
    *,
    scenario_path: str,
    seeds: Sequence[int] = DEFAULT_ACCEPTED_SEEDS,
    max_steps: int = 120,
    response_doctrine: str = DEFAULT_RESPONSE_DOCTRINE,
    replay: bool = True,
) -> dict[str, Any]:
    """Run every accepted seed and fail closed on response/replay mismatch."""

    response_doctrine = str(response_doctrine).strip().lower()
    if response_doctrine not in {"countermeasure_ready", "chaff_only", "flare_only"}:
        raise ValueError(
            "Air EW seed gate requires an active countermeasure doctrine: "
            "countermeasure_ready, chaff_only, or flare_only"
        )
    repo_root = Path(__file__).resolve().parents[2]
    candidate = Path(str(scenario_path))
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    resolved_scenario = str(candidate.resolve())
    normalized_seeds = tuple(int(seed) for seed in seeds)
    if not normalized_seeds or len(set(normalized_seeds)) != len(normalized_seeds):
        raise ValueError("Air EW seed matrix requires a non-empty set of unique seeds")
    records: list[EWSeedGateRecord] = []
    for seed in normalized_seeds:
        first = _run_once(
            scenario_path=resolved_scenario,
            seed=seed,
            max_steps=max_steps,
            response_doctrine=response_doctrine,
        )
        record = _validate_record(data=first, seed=seed, response_doctrine=response_doctrine)
        second = (
            _run_once(
                scenario_path=resolved_scenario,
                seed=seed,
                max_steps=max_steps,
                response_doctrine=response_doctrine,
            )
            if replay
            else None
        )
        replay_equal = second is None or _fingerprint(first) == _fingerprint(second)
        if not replay_equal:
            raise RuntimeError(f"Air EW seed replay gate failed for seed {seed}")
        records.append(
            EWSeedGateRecord(
                **{**asdict(record), "replay_equal": bool(replay_equal)}
            )
        )
    return {
        "scenario": resolved_scenario,
        "seeds": list(normalized_seeds),
        "response_doctrine": response_doctrine,
        "replay_checked": bool(replay),
        "records": [asdict(record) for record in records],
        "accepted": True,
        "playable_boundary": "ew_response_demo_without_terminal_objective",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", default=DEFAULT_SCENARIO)
    parser.add_argument("--seed", action="append", type=int, dest="seeds")
    parser.add_argument("--max_steps", type=int, default=120)
    parser.add_argument(
        "--response_doctrine",
        choices=("countermeasure_ready", "chaff_only", "flare_only"),
        default=DEFAULT_RESPONSE_DOCTRINE,
    )
    parser.add_argument("--no_replay", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = run_seed_matrix(
        scenario_path=args.scenario,
        seeds=tuple(args.seeds) if args.seeds else DEFAULT_ACCEPTED_SEEDS,
        max_steps=int(args.max_steps),
        response_doctrine=args.response_doctrine,
        replay=not bool(args.no_replay),
    )
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
