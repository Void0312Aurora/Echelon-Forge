#!/usr/bin/env python3
"""Run named single and cooperative terminal EW surrogate acceptance gates."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from python.runtime_bootstrap import ensure_repo_imports, resolve_repo_path  # noqa: E402


ensure_repo_imports()

from tools.diagnostics.air_combat_ew_scripted_demo import run_demo as run_single_demo  # noqa: E402
from tools.diagnostics.air_cooperative_combat_ew_scripted_demo import (  # noqa: E402
    run_demo as run_cooperative_demo,
)


DEFAULT_SEEDS = (20260516, 20261007)
DEFAULT_MAX_STEPS = 600
SCENARIOS = (
    {
        "id": "air_combat_1v1_c2_roe_ew_terminal_v1",
        "path": resolve_repo_path("scenarios", "air_combat", "air_combat_1v1_c2_roe_ew_terminal_v1.json"),
        "formation": False,
    },
    {
        "id": "cooperative_air_2v2_scripted_c2_roe_ew_terminal_v1",
        "path": resolve_repo_path(
            "scenarios", "air_combat", "cooperative_air_2v2_scripted_c2_roe_ew_terminal_v1.json"
        ),
        "formation": True,
    },
)
RESIDUALS = (
    "generic Aircraft opponents and terminal objectives are engineering surrogates",
    "countermeasure inventory loss is measured; seeker seduction is not part of this terminal gate",
    "jammer transmit state is measured; calibrated radar suppression or burn-through is not",
    "RF platform calibration, emitter libraries, sidelobes, pulse processing and calibrated J/S remain open",
    "independent DRFM ghost-track lifecycle remains open",
    "this acceptance does not establish learned-policy quality or promote the Air/EW playable label",
)
SINGLE_REPLAY_FIELDS = (
    "seed", "action_mode", "steps", "terminated", "truncated", "termination_reason",
    "fire_once_accepted_steps", "release_executed_steps", "launch_warning_steps",
    "countermeasure_request_steps", "pre_request_countermeasure_state",
    "countermeasure_state_samples", "jammer_request_steps", "jammer_transmit_steps",
    "scripted_runtime_identity", "scripted_runtime_decisions", "native_state_sample_last_step",
    "native_countermeasure_state", "last_info",
)
COOPERATIVE_REPLAY_FIELDS = (
    "seed", "action_mode", "steps", "terminated", "truncated", "termination_reasons", "roster",
    "fire_once_accepted_steps", "release_executed_steps", "launch_warning_steps",
    "countermeasure_request_steps", "countermeasure_state_samples", "pre_request_countermeasure_state",
    "jammer_request_steps", "jammer_transmit_steps", "scripted_opponent_reports",
    "scripted_runtime_identity", "scripted_runtime_decisions", "native_state_sample_last_step",
    "native_countermeasure_state", "last_infos",
)


def _fingerprint(report: dict[str, Any], fields: tuple[str, ...]) -> str:
    selected = {field: report.get(field) for field in fields}
    canonical = json.dumps(selected, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _step_list(value: Any, *, label: str, last_step: int) -> list[int]:
    _require(isinstance(value, list) and bool(value), f"{label}: missing step receipts")
    _require(
        all(type(step) is int and 0 < step <= last_step for step in value),
        f"{label}: invalid step receipts",
    )
    _require(value == sorted(set(value)), f"{label}: duplicate or unordered step receipts")
    return value


def _validate_resource_samples(
    samples: Any, baseline: Any, *, requests: list[int], last_step: int, label: str
) -> tuple[int, int]:
    _require(isinstance(samples, list) and bool(samples), f"{label}: no native resource samples")
    _require(isinstance(baseline, dict), f"{label}: missing pre-request native baseline")
    _require(all(isinstance(sample, dict) for sample in samples), f"{label}: malformed resource sample")
    _require(baseline.get("step") == requests[0] - 1, f"{label}: baseline must precede first request")
    _require(
        [sample.get("step") for sample in samples] == [step for step in requests if step <= last_step],
        f"{label}: incomplete or post-reset native samples",
    )
    consumed: list[int] = []
    for resource in ("chaff_remaining", "flare_remaining"):
        values = [baseline.get(resource), *(sample.get(resource) for sample in samples)]
        _require(
            all(type(value) is int and value >= 0 for value in values),
            f"{label}: missing native {resource} readback",
        )
        _require(values == sorted(values, reverse=True), f"{label}: {resource} increased during the episode")
        delta = values[0] - values[-1]
        _require(delta > 0, f"{label}: {resource} was requested but not consumed")
        consumed.append(delta)
    return consumed[0], consumed[1]


def _validate_slot(report: dict[str, Any], *, steps: int, label: str) -> dict[str, int]:
    accepted = _step_list(report.get("fire_once_accepted_steps"), label=f"{label} accepted release", last_step=steps)
    released = _step_list(report.get("release_executed_steps"), label=f"{label} native release", last_step=steps)
    _require(accepted == released, f"{label}: accepted/native release mismatch")
    warnings = _step_list(report.get("launch_warning_steps"), label=f"{label} warning", last_step=steps)
    requests = report.get("countermeasure_request_steps")
    _require(requests == warnings, f"{label}: warning and countermeasure requests differ")
    chaff_delta, flare_delta = _validate_resource_samples(
        report.get("countermeasure_state_samples"), report.get("pre_request_countermeasure_state"),
        requests=requests, last_step=steps - 1, label=label,
    )
    jammer_requests = _step_list(report.get("jammer_request_steps"), label=f"{label} jammer request", last_step=steps)
    jammer_tx = _step_list(report.get("jammer_transmit_steps"), label=f"{label} native jammer transmit", last_step=steps - 1)
    _require(set(jammer_tx).issubset(jammer_requests), f"{label}: transmit without a request")
    _require(report.get("scripted_runtime_decisions") == steps, f"{label}: incomplete runtime decisions")
    identity = report.get("scripted_runtime_identity")
    _require(
        isinstance(identity, str) and f":air.combat_ew.c2_roe_ew_scripted:seed={report.get('seed')}" in identity,
        f"{label}: missing seeded runtime identity",
    )
    return {
        "accepted_release_count": len(accepted),
        "chaff_consumed": chaff_delta,
        "flare_consumed": flare_delta,
        "jammer_request_steps": len(jammer_requests),
        "native_jammer_transmit_steps": len(jammer_tx),
    }


def _validate_common(report: dict[str, Any], *, max_steps: int, label: str) -> int:
    _require(report.get("action_mode") == "air_ew_hybrid_v2", f"{label}: wrong action mode")
    steps = report.get("steps")
    _require(type(steps) is int and 0 < steps < max_steps, f"{label}: invalid terminal step {steps}")
    _require(type(report.get("seed")) is int, f"{label}: missing seed")
    _require(report.get("native_state_sample_last_step") == steps - 1, f"{label}: native auto-reset boundary missing")
    _require(
        report.get("native_countermeasure_state") == "instrument_state_projection",
        f"{label}: native resource provenance missing",
    )
    return steps


def validate_single_report(report: dict[str, Any], *, max_steps: int) -> dict[str, Any]:
    label = "single-aircraft terminal scenario"
    steps = _validate_common(report, max_steps=max_steps, label=label)
    _require(report.get("terminated") is True, f"{label}: did not terminate successfully")
    _require(report.get("truncated") is False, f"{label}: episode timed out")
    _require(report.get("termination_reason") == "combat_win", f"{label}: unexpected terminal reason")
    return {
        "scenario_id": SCENARIOS[0]["id"],
        "seed": int(report["seed"]),
        "steps": steps,
        "terminal_reason": "combat_win",
        **_validate_slot(report, steps=steps, label=label),
    }


def validate_cooperative_report(report: dict[str, Any], *, max_steps: int) -> dict[str, Any]:
    label = "cooperative 2v2 terminal scenario"
    steps = _validate_common(report, max_steps=max_steps, label=label)
    terminated = report.get("terminated")
    truncated = report.get("truncated")
    reasons = report.get("termination_reasons")
    roster = report.get("roster")
    _require(isinstance(roster, list) and len(roster) == 2, f"{label}: unexpected controlled roster")
    _require(all(isinstance(slot, dict) for slot in roster), f"{label}: malformed roster")
    _require(terminated == [True, True], f"{label}: every controlled aircraft must terminate successfully")
    _require(truncated == [False, False], f"{label}: one or more aircraft timed out")
    _require(reasons == ["combat_win", "combat_win"], f"{label}: unexpected terminal reasons")
    _require(
        [slot.get("target_owner_name") for slot in roster] == ["Red_A", "Red_B"]
        and [slot.get("entity_name") for slot in roster] == ["Blue_A_Lead", "Blue_B_Wing"]
        and [slot.get("formation_role_id") for slot in roster] == ["ElementLead", "Wingman"]
        and [slot.get("scripted_opponent_owner") for slot in roster] == [True, False]
        and [slot.get("scripted_opponent_count") for slot in roster] == [2, 0],
        f"{label}: roster ownership changed",
    )
    slot_fields = (
        "fire_once_accepted_steps", "release_executed_steps", "launch_warning_steps",
        "countermeasure_request_steps", "countermeasure_state_samples", "pre_request_countermeasure_state",
        "jammer_request_steps", "jammer_transmit_steps", "scripted_runtime_decisions", "scripted_runtime_identity",
    )
    for field in slot_fields:
        _require(isinstance(report.get(field), list) and len(report[field]) == 2, f"{label}: missing per-slot {field}")
    slot_receipts = []
    for index in range(2):
        slot = {field: report[field][index] for field in slot_fields}
        slot["seed"] = report["seed"]
        slot_receipts.append(
            {
                "entity_name": roster[index]["entity_name"],
                "target_owner_name": roster[index]["target_owner_name"],
                "terminal_reason": reasons[index],
                **_validate_slot(slot, steps=steps, label=f"{label}, slot {index}"),
            }
        )
    return {
        "scenario_id": SCENARIOS[1]["id"],
        "seed": int(report["seed"]),
        "steps": steps,
        "slot_receipts": slot_receipts,
    }


def run_terminal_acceptance(
    *,
    seeds: tuple[int, ...] = DEFAULT_SEEDS,
    max_steps: int = DEFAULT_MAX_STEPS,
    single_runner: Callable[..., dict[str, Any]] = run_single_demo,
    cooperative_runner: Callable[..., dict[str, Any]] = run_cooperative_demo,
) -> dict[str, Any]:
    normalized_seeds = tuple(seeds)
    if any(type(seed) is not int for seed in normalized_seeds):
        raise ValueError("terminal acceptance seeds must be integers")
    if not normalized_seeds or len(set(normalized_seeds)) != len(normalized_seeds):
        raise ValueError("terminal acceptance requires a non-empty set of unique seeds")
    if type(max_steps) is not int or max_steps <= 0:
        raise ValueError("max_steps must be positive")

    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, check=True, capture_output=True, text=True,
    ).stdout.strip()
    source_dirty = bool(subprocess.run(
        ["git", "status", "--porcelain=v1"], cwd=REPO_ROOT, check=True, capture_output=True, text=True,
    ).stdout.strip())
    scenario_records = []
    for scenario in SCENARIOS:
        records = []
        runner = cooperative_runner if scenario["formation"] else single_runner
        for seed in normalized_seeds:
            kwargs = {
                "scenario_path": scenario["path"],
                "seed": seed,
                "max_steps": int(max_steps),
                "response_doctrine": "countermeasure_ready",
                "jammer_doctrine": "self_protect_on_lock",
            }
            first = runner(**kwargs)
            validator = validate_cooperative_report if scenario["formation"] else validate_single_report
            receipt = validator(first, max_steps=max_steps)
            _require(first["seed"] == seed, f"{scenario['id']}: runner returned the wrong seed")
            second = runner(**kwargs)
            validator(second, max_steps=max_steps)
            fingerprint_fields = COOPERATIVE_REPLAY_FIELDS if scenario["formation"] else SINGLE_REPLAY_FIELDS
            fingerprint = _fingerprint(first, fingerprint_fields)
            replay_equal = _fingerprint(second, fingerprint_fields) == fingerprint
            _require(replay_equal, f"{scenario['id']} seed={seed}: same-seed replay mismatch")
            records.append({**receipt, "replay_equal": bool(replay_equal), "trace_sha256": fingerprint})
        scenario_records.append(
            {
                "scenario_id": scenario["id"],
                "scenario_path": Path(scenario["path"]).relative_to(REPO_ROOT).as_posix(),
                "scenario_sha256": hashlib.sha256(Path(scenario["path"]).read_bytes()).hexdigest(),
                "formation": bool(scenario["formation"]),
                "seeds": records,
            }
        )

    native_path = Path(sys.modules["ef_py"].__file__).resolve()
    return {
        "schema_version": "air_ew_named_terminal_acceptance_v1",
        "source_revision": revision,
        "source_dirty": source_dirty,
        "receipt_reproducible": not source_dirty,
        "native_module": {
            "path": str(native_path),
            "sha256": hashlib.sha256(native_path.read_bytes()).hexdigest(),
        },
        "accepted": True,
        "acceptance_scope": "rl_independent_named_terminal_engineering_surrogates",
        "playable_capability_promotion": False,
        "max_steps": int(max_steps),
        "seeds": list(normalized_seeds),
        "replay_checked": True,
        "scenarios": scenario_records,
        "accepted_evidence": [
            "named single-aircraft and cooperative 2v2 terminal objectives close with combat_win",
            "every controlled roster member emits an accepted release and receives native EW state readback",
            "launch warnings map to countermeasure requests and chaff/flare inventory decreases",
            "jammer requests map to native transmit-state receipts",
            "same-seed terminal and EW traces replay exactly for the listed fields",
        ],
        "residuals": list(RESIDUALS),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=list(DEFAULT_SEEDS))
    parser.add_argument("--max_steps", type=int, default=DEFAULT_MAX_STEPS)
    parser.add_argument("--json_out", default="")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report = run_terminal_acceptance(
        seeds=tuple(args.seeds), max_steps=args.max_steps
    )
    rendered = json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False)
    if args.json_out:
        output_path = Path(args.json_out).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
