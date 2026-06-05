#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import Counter
from types import SimpleNamespace
from typing import Any

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from python.testing.runtime import ensure_repo_imports, resolve_repo_path

ensure_repo_imports()

from tools.diagnostics import air_combat_stage0_process_probe as process_probe  # noqa: E402


DEFAULT_SCENARIO = resolve_repo_path(
    "scenarios",
    "air_combat",
    "1v1",
    "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_training_shaped_v1.json",
)
DEFAULT_TRAIN_CONFIG = resolve_repo_path(
    "examples",
    "config",
    "training",
    "active",
    "air_combat",
    "air_combat_1v1_stage1_bvr_nonmaneuvering_target_c2_roe_hybrid_temporal_m3s1_grouped_stopping_state_completed_world_batch_probe_v1.json",
)


def _finite_float(value: Any, default: float = float("nan")) -> float:
    try:
        out = float(value)
    except Exception:
        return float(default)
    return out if math.isfinite(out) else float(default)


def _parse_delays(value: str) -> list[int]:
    delays: list[int] = []
    for item in str(value or "").split(","):
        item = item.strip()
        if not item:
            continue
        delay = max(0, int(item))
        if delay not in delays:
            delays.append(delay)
    return delays or [0]


def _mean(values: list[float]) -> float:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    if not finite:
        return float("nan")
    return float(sum(finite) / len(finite))


def _spread(values: list[float]) -> float:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    if not finite:
        return 0.0
    return float(max(finite) - min(finite))


def _first_step_mean(episodes: list[dict[str, Any]], key: str) -> float:
    values = [
        float(ep[key])
        for ep in episodes
        if ep.get(key) is not None and math.isfinite(_finite_float(ep.get(key)))
    ]
    return _mean(values)


def _case_summary(case_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    episodes = [ep for ep in payload.get("episode_summaries", []) if isinstance(ep, dict)]
    rejection_reasons: Counter[str] = Counter()
    release_steps: list[int] = []
    for ep in episodes:
        rejection_reasons.update(
            {
                str(key): int(value)
                for key, value in dict(ep.get("fire_once_rejected_reason_counts", {}) or {}).items()
            }
        )
        for step in ep.get("release_steps", []) or []:
            try:
                release_steps.append(int(step))
            except Exception:
                pass

    final_health = [_finite_float(ep.get("final_target_health", float("nan"))) for ep in episodes]
    return {
        "case": str(case_name),
        "mode": str(payload.get("mode", "")),
        "fire_delay_steps": int(payload.get("fire_delay_steps", 0) or 0),
        "legal_fire_range_m": _finite_float(payload.get("legal_fire_range_m", 0.0), 0.0),
        "episodes": int(len(episodes)),
        "mean_total_reward": _mean([_finite_float(ep.get("total_reward", float("nan"))) for ep in episodes]),
        "mean_final_target_health": _mean(final_health),
        "mean_release_count": _mean([_finite_float(ep.get("release_count", 0.0), 0.0) for ep in episodes]),
        "mean_fire_once_accepted_count": _mean(
            [_finite_float(ep.get("fire_once_accepted_count", 0.0), 0.0) for ep in episodes]
        ),
        "mean_fire_once_rejected_count": _mean(
            [_finite_float(ep.get("fire_once_rejected_count", 0.0), 0.0) for ep in episodes]
        ),
        "mean_effects_event_count": _mean(
            [_finite_float(ep.get("effects_event_count", 0.0), 0.0) for ep in episodes]
        ),
        "mean_damage_report_count": _mean(
            [_finite_float(ep.get("damage_report_count", 0.0), 0.0) for ep in episodes]
        ),
        "release_episode_count": int(sum(int(ep.get("release_count", 0) or 0) > 0 for ep in episodes)),
        "effects_episode_count": int(sum(int(ep.get("effects_event_count", 0) or 0) > 0 for ep in episodes)),
        "damage_episode_count": int(sum(int(ep.get("damage_report_count", 0) or 0) > 0 for ep in episodes)),
        "target_health_drop_episode_count": int(
            sum(
                ep.get("first_target_health_drop_step") is not None
                or _finite_float(ep.get("last_damage_system_health_delta", 0.0), 0.0) < 0.0
                for ep in episodes
            )
        ),
        "first_release_step_mean": _first_step_mean(episodes, "first_release_step"),
        "first_effects_event_step_mean": _first_step_mean(episodes, "first_effects_event_step"),
        "release_steps": release_steps,
        "rejected_reason_counts": dict(sorted(rejection_reasons.items())),
        "termination_reasons": dict(payload.get("termination_reasons", {}) or {}),
    }


def _learnability_verdict(case_summaries: list[dict[str, Any]], *, reward_epsilon: float) -> dict[str, Any]:
    hold_cases = [case for case in case_summaries if case.get("mode") == "hold_fire"]
    forced_cases = [case for case in case_summaries if case.get("mode") == "forced_fire"]
    legal_cases = [case for case in case_summaries if case.get("mode") == "legal_mask_fire"]

    release_reachable = any(int(case.get("release_episode_count", 0) or 0) > 0 for case in legal_cases)
    post_release_effect_observable = any(
        int(case.get("effects_episode_count", 0) or 0) > 0
        or int(case.get("damage_episode_count", 0) or 0) > 0
        or int(case.get("target_health_drop_episode_count", 0) or 0) > 0
        for case in legal_cases
    )

    hold_reward = _mean([_finite_float(case.get("mean_total_reward", float("nan"))) for case in hold_cases])
    legal_rewards = [_finite_float(case.get("mean_total_reward", float("nan"))) for case in legal_cases]
    legal_reward_mean = _mean(legal_rewards)
    legal_timing_reward_spread = _spread(legal_rewards)
    release_vs_hold_reward_delta = (
        legal_reward_mean - hold_reward
        if math.isfinite(legal_reward_mean) and math.isfinite(hold_reward)
        else float("nan")
    )
    release_vs_hold_reward_distinguishable = (
        math.isfinite(release_vs_hold_reward_delta)
        and abs(float(release_vs_hold_reward_delta)) > float(reward_epsilon)
    )
    legal_timing_reward_distinguishable = legal_timing_reward_spread > float(reward_epsilon)

    edge_trigger_adapter_hazard = bool(
        forced_cases
        and any(int(case.get("release_episode_count", 0) or 0) <= 0 for case in forced_cases)
        and any(dict(case.get("rejected_reason_counts", {}) or {}) for case in forced_cases)
        and release_reachable
    )

    if not release_reachable:
        primary = "action_mask_or_release_unreachable"
    elif not post_release_effect_observable and not legal_timing_reward_distinguishable:
        primary = "legal_timing_unidentifiable_from_current_return"
    elif edge_trigger_adapter_hazard:
        primary = "edge_trigger_adapter_credit_hazard"
    else:
        primary = "policy_credit_or_optimizer"

    return {
        "primary_breakpoint": primary,
        "release_reachable_with_legal_oracle": bool(release_reachable),
        "release_vs_hold_reward_distinguishable": bool(release_vs_hold_reward_distinguishable),
        "release_vs_hold_reward_delta": release_vs_hold_reward_delta,
        "post_release_effect_observable": bool(post_release_effect_observable),
        "legal_timing_reward_distinguishable": bool(legal_timing_reward_distinguishable),
        "legal_timing_reward_spread": float(legal_timing_reward_spread),
        "edge_trigger_adapter_hazard": bool(edge_trigger_adapter_hazard),
        "interpretation": (
            "Legal fire is reachable and rewarded, but legal timing alternatives are not "
            "distinguished by effects, damage, target health, or return under this audit."
            if primary == "legal_timing_unidentifiable_from_current_return"
            else ""
        ),
    }


def _probe_namespace(args: argparse.Namespace, *, mode: str, delay: int = 0) -> SimpleNamespace:
    return SimpleNamespace(
        scenario=str(args.scenario),
        train_config=str(args.train_config),
        mode=str(mode),
        fire_range_m=float(args.fire_range_m),
        fire_delay_steps=int(delay),
        legal_fire_range_m=float(args.legal_fire_range_m),
        model="",
        algo="auto",
        device="auto",
        episodes=int(args.episodes),
        seed=int(args.seed),
        max_steps=int(args.max_steps),
        stochastic=False,
        csv_out="",
        json_out="",
        plot_out="",
    )


def run_audit(args: argparse.Namespace) -> dict[str, Any]:
    cases: list[tuple[str, SimpleNamespace]] = [
        ("hold_fire", _probe_namespace(args, mode="hold_fire")),
        ("forced_fire_edge_at_reset", _probe_namespace(args, mode="forced_fire")),
    ]
    for delay in _parse_delays(str(args.delays)):
        cases.append(
            (
                f"legal_mask_fire_delay_{int(delay)}",
                _probe_namespace(args, mode="legal_mask_fire", delay=int(delay)),
            )
        )

    payload_cases: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for case_name, probe_args in cases:
        payload = process_probe.run_probe(probe_args)
        summary = _case_summary(case_name, payload)
        summaries.append(summary)
        payload_cases.append(
            {
                "case": case_name,
                "probe_args": {
                    "mode": str(probe_args.mode),
                    "fire_delay_steps": int(probe_args.fire_delay_steps),
                    "legal_fire_range_m": float(probe_args.legal_fire_range_m),
                    "episodes": int(probe_args.episodes),
                    "seed": int(probe_args.seed),
                    "max_steps": int(probe_args.max_steps),
                },
                "episode_summaries": payload.get("episode_summaries", []),
            }
        )

    return {
        "scenario": os.path.abspath(args.scenario),
        "train_config": os.path.abspath(args.train_config),
        "episodes": int(args.episodes),
        "seed": int(args.seed),
        "max_steps": int(args.max_steps),
        "delays": _parse_delays(str(args.delays)),
        "reward_epsilon": float(args.reward_epsilon),
        "case_summaries": summaries,
        "verdict": _learnability_verdict(summaries, reward_epsilon=float(args.reward_epsilon)),
        "cases": payload_cases,
    }


def write_json(path: str, payload: dict[str, Any]) -> None:
    out_path = os.path.abspath(path)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=True)
        f.write("\n")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit learnability of one-shot air-combat fire timing.")
    parser.add_argument("--scenario", default=DEFAULT_SCENARIO)
    parser.add_argument("--train_config", default=DEFAULT_TRAIN_CONFIG)
    parser.add_argument("--episodes", type=int, default=2)
    parser.add_argument("--seed", type=int, default=31)
    parser.add_argument("--max_steps", type=int, default=2000)
    parser.add_argument("--delays", default="0,31,63")
    parser.add_argument("--fire_range_m", type=float, default=12000.0)
    parser.add_argument("--legal_fire_range_m", type=float, default=0.0)
    parser.add_argument("--reward_epsilon", type=float, default=1.0)
    parser.add_argument("--json_out", default="")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    payload = run_audit(args)
    if args.json_out:
        write_json(args.json_out, payload)
    print(json.dumps(payload, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
