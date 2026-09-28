#!/usr/bin/env python3
"""Validate the immutable launch-decision learned-firing acceptance matrix.

A single process-probe run is useful diagnostic evidence, but the C5 closure
contract fixes the final acceptance identity to seeds 0/1/2 with three episodes
per seed.  This module is the final aggregation gate: it consumes retained
process-probe JSON payloads and refuses to issue a pass unless every declared
matrix cell is present exactly once.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from tools.diagnostics._air_combat_weapon_employment_process_probe_impl.summarize import (
    validate_learned_firing_gate,
)


LEARNED_FIRING_GATE_SCHEMA_VERSION = "launch_decision_learned_firing_matrix_v1"
LEARNED_FIRING_REQUIRED_SEEDS = (0, 1, 2)
LEARNED_FIRING_EPISODES_PER_SEED = 3


def _matrix_cells(payload: Mapping[str, Any]) -> list[tuple[int, int]]:
    try:
        seed = int(payload["seed"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("learned_firing_matrix_failed: probe payload has no valid seed") from exc
    summaries = payload.get("episode_summaries")
    if not isinstance(summaries, list):
        raise ValueError("learned_firing_matrix_failed: probe payload has no episode_summaries")
    declared_episodes = int(payload.get("episodes", len(summaries)) or 0)
    if declared_episodes != LEARNED_FIRING_EPISODES_PER_SEED:
        raise ValueError(
            "learned_firing_matrix_failed: "
            f"seed {seed} declares {declared_episodes} episodes, expected "
            f"{LEARNED_FIRING_EPISODES_PER_SEED}"
        )
    if len(summaries) != LEARNED_FIRING_EPISODES_PER_SEED:
        raise ValueError(
            "learned_firing_matrix_failed: "
            f"seed {seed} retained {len(summaries)} episode summaries, expected "
            f"{LEARNED_FIRING_EPISODES_PER_SEED}"
        )
    cells: list[tuple[int, int]] = []
    for position, summary in enumerate(summaries):
        if not isinstance(summary, Mapping):
            raise ValueError("learned_firing_matrix_failed: episode summary is not a mapping")
        episode = int(summary.get("episode", position))
        if episode != position:
            raise ValueError(
                "learned_firing_matrix_failed: "
                f"seed {seed} episode identity {episode} does not match cell {position}"
            )
        cells.append((seed, episode))
    return cells


def validate_learned_firing_matrix_payloads(
    payloads: Sequence[Mapping[str, Any]],
    *,
    max_stochastic_rejections: int = 3,
) -> dict[str, Any]:
    """Validate exactly the fixed 3x3 seed/episode acceptance matrix."""

    required_cells = {
        (seed, episode)
        for seed in LEARNED_FIRING_REQUIRED_SEEDS
        for episode in range(LEARNED_FIRING_EPISODES_PER_SEED)
    }
    observed_cells: list[tuple[int, int]] = []
    aggregate: dict[str, int] = {}
    observed_seeds: list[int] = []

    for payload in payloads:
        if str(payload.get("mode", "")) != "model":
            raise ValueError("learned_firing_matrix_failed: every payload must use mode=model")
        seed = int(payload.get("seed", -1))
        if seed not in LEARNED_FIRING_REQUIRED_SEEDS:
            raise ValueError(
                "learned_firing_matrix_failed: "
                f"undeclared seed {seed}; required seeds are {LEARNED_FIRING_REQUIRED_SEEDS}"
            )
        observed_seeds.append(seed)
        observed_cells.extend(_matrix_cells(payload))
        for summary in payload["episode_summaries"]:
            for key, value in summary.items():
                if str(key).endswith("_count"):
                    aggregate[str(key)] = aggregate.get(str(key), 0) + int(value or 0)

    if len(observed_seeds) != len(LEARNED_FIRING_REQUIRED_SEEDS):
        raise ValueError(
            "learned_firing_matrix_failed: exactly one retained probe payload is required per seed"
        )
    if set(observed_seeds) != set(LEARNED_FIRING_REQUIRED_SEEDS):
        raise ValueError(
            "learned_firing_matrix_failed: retained seed set does not match the declared matrix"
        )
    if len(set(observed_seeds)) != len(observed_seeds):
        raise ValueError("learned_firing_matrix_failed: duplicate seed payload")
    if len(observed_cells) != len(required_cells) or set(observed_cells) != required_cells:
        missing = sorted(required_cells.difference(observed_cells))
        extra = sorted(set(observed_cells).difference(required_cells))
        raise ValueError(
            "learned_firing_matrix_failed: incomplete seed/episode coverage; "
            f"missing={missing}, extra={extra}"
        )

    counter_gate = validate_learned_firing_gate(
        aggregate,
        learned_policy=True,
        non_forced=True,
        max_stochastic_rejections=max_stochastic_rejections,
    )
    return {
        "schema_version": LEARNED_FIRING_GATE_SCHEMA_VERSION,
        "status": "pass",
        "matrix_complete": True,
        "required_seeds": list(LEARNED_FIRING_REQUIRED_SEEDS),
        "episodes_per_seed": LEARNED_FIRING_EPISODES_PER_SEED,
        "cell_count": len(required_cells),
        "cells": [
            {"seed": seed, "episode": episode}
            for seed, episode in sorted(required_cells)
        ],
        "counter_gate": counter_gate,
    }


def _load_payload(path: str) -> Mapping[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"cannot read learned-firing probe payload: {path}") from exc
    if not isinstance(payload, Mapping):
        raise ValueError(f"learned-firing probe payload is not an object: {path}")
    return payload


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the fixed launch-decision learned-firing matrix: "
            "seeds 0/1/2, three retained model episodes per seed."
        )
    )
    parser.add_argument(
        "probe_json",
        nargs="+",
        help="Retained process-probe JSON payloads; exactly one for each seed 0, 1 and 2.",
    )
    parser.add_argument("--max-stochastic-rejections", type=int, default=3)
    parser.add_argument("--json-out", default="")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    result = validate_learned_firing_matrix_payloads(
        [_load_payload(path) for path in args.probe_json],
        max_stochastic_rejections=int(args.max_stochastic_rejections),
    )
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        destination = Path(args.json_out)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
