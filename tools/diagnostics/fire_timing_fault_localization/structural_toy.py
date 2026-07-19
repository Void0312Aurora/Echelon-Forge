#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import asdict, dataclass
from typing import Any

import torch as th

_REPO_ROOT_HINT = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT_HINT = os.path.dirname(_REPO_ROOT_HINT)
_REPO_ROOT_HINT = os.path.dirname(_REPO_ROOT_HINT)
if _REPO_ROOT_HINT not in sys.path:
    sys.path.insert(0, _REPO_ROOT_HINT)
from python.runtime_bootstrap import ensure_repo_imports

ensure_repo_imports()

from python.rl.policy_algo.grouped_stopping import (  # noqa: E402
    GroupedStoppingEvidence,
    compute_grouped_stopping_loss,
)


@dataclass(frozen=True)
class ToyProbeConfig:
    model: str
    prewindow_steps: int
    quality_steps: int
    train_steps: int
    learning_rate: float
    initial_logit: float
    hidden_size: int
    seed: int
    early_mass_coef: float
    early_mass_budget: float
    early_survival_coef: float
    window_delay_coef: float
    window_deadline_coef: float
    window_deadline_steps: int
    max_grad_norm: float
    prewindow_risk_gate: float
    window_mass_gate: float


def _build_group(logits: th.Tensor, *, prewindow_steps: int, quality_steps: int) -> GroupedStoppingEvidence:
    total_steps = int(prewindow_steps) + int(quality_steps)
    return GroupedStoppingEvidence(
        group_id="toy-window",
        episode_id="toy-episode",
        route_source="structural_toy",
        row_indices=list(range(total_steps)),
        step_indices=list(range(total_steps)),
        env_indices=[0] * total_steps,
        legal_mask=[True] * total_steps,
        quality_mask=[False] * int(prewindow_steps) + [True] * int(quality_steps),
        stopping_logits=logits.reshape(-1),
    )


def _loss(logits: th.Tensor, config: ToyProbeConfig):
    return compute_grouped_stopping_loss(
        [_build_group(logits, prewindow_steps=config.prewindow_steps, quality_steps=config.quality_steps)],
        early_mass_coef=float(config.early_mass_coef),
        early_mass_budget=float(config.early_mass_budget),
        early_survival_coef=float(config.early_survival_coef),
        window_delay_coef=float(config.window_delay_coef),
        window_deadline_coef=float(config.window_deadline_coef),
        window_deadline_steps=int(config.window_deadline_steps),
        boundary_threshold=0.0,
    )


def _features(*, prewindow_steps: int, quality_steps: int) -> th.Tensor:
    total_steps = int(prewindow_steps) + int(quality_steps)
    positions = th.arange(total_steps, dtype=th.float32)
    denom = float(max(1, total_steps - 1))
    age_norm = positions / denom
    quality_open = (positions >= float(prewindow_steps)).to(dtype=th.float32)
    quality_age = th.clamp(
        (positions - float(prewindow_steps)) / float(max(1, quality_steps - 1)),
        min=0.0,
        max=1.0,
    )
    return th.stack((age_norm, quality_open, quality_age), dim=1)


def _init_mlp(config: ToyProbeConfig) -> th.nn.Module:
    model = th.nn.Sequential(
        th.nn.Linear(3, int(config.hidden_size)),
        th.nn.Tanh(),
        th.nn.Linear(int(config.hidden_size), 1),
    )
    final = model[-1]
    if isinstance(final, th.nn.Linear):
        th.nn.init.zeros_(final.weight)
        th.nn.init.constant_(final.bias, float(config.initial_logit))
    return model


def _cumulative_risk(probs: th.Tensor) -> float:
    if int(probs.numel()) <= 0:
        return 0.0
    safe = probs.detach().to(dtype=th.float64).clamp(min=0.0, max=1.0 - 1.0e-12)
    return float(1.0 - th.exp(th.log1p(-safe).sum()).item())


def _first_index(mask: th.Tensor) -> int | None:
    positions = th.nonzero(mask.reshape(-1), as_tuple=False).reshape(-1)
    if int(positions.numel()) <= 0:
        return None
    return int(positions[0].detach().cpu().item())


def _finite(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {str(k): _finite(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_finite(v) for v in value]
    return value


def run_probe(config: ToyProbeConfig) -> dict[str, Any]:
    if int(config.prewindow_steps) < 0 or int(config.quality_steps) <= 0:
        raise ValueError("toy probe requires prewindow_steps >= 0 and quality_steps > 0")
    if str(config.model) not in {"free_logits", "mlp"}:
        raise ValueError("model must be 'free_logits' or 'mlp'")

    th.manual_seed(int(config.seed))
    total_steps = int(config.prewindow_steps) + int(config.quality_steps)
    if str(config.model) == "free_logits":
        logits_param = th.nn.Parameter(th.full((total_steps,), float(config.initial_logit)))
        params = [logits_param]

        def logits_fn() -> th.Tensor:
            return logits_param

    else:
        features = _features(prewindow_steps=config.prewindow_steps, quality_steps=config.quality_steps)
        network = _init_mlp(config)
        params = list(network.parameters())

        def logits_fn() -> th.Tensor:
            return network(features).reshape(-1)

    optimizer = th.optim.Adam(params, lr=float(config.learning_rate))
    history: list[dict[str, Any]] = []
    sample_steps = {
        0,
        max(0, int(config.train_steps) // 4),
        max(0, int(config.train_steps) // 2),
        max(0, (3 * int(config.train_steps)) // 4),
        int(config.train_steps),
    }

    def snapshot(step: int, grad_norm: float | None = None) -> dict[str, Any]:
        with th.no_grad():
            logits = logits_fn().detach()
            loss_result = _loss(logits, config)
            probs = th.sigmoid(logits)
            pre_probs = probs[: int(config.prewindow_steps)]
            quality_probs = probs[int(config.prewindow_steps) :]
            quality_logits = logits[int(config.prewindow_steps) :]
            pre_logits = logits[: int(config.prewindow_steps)]
            quality_cross = quality_logits >= 0.0
            pre_cross = pre_logits >= 0.0
            first_quality_cross_local = _first_index(quality_cross)
            first_quality_cross_step = (
                int(config.prewindow_steps) + first_quality_cross_local
                if first_quality_cross_local is not None
                else None
            )
            return {
                "step": int(step),
                "loss": float(loss_result.loss.detach().cpu().item()),
                "mean_p_window": float(loss_result.stats.mean_p_window),
                "mean_p_early": float(loss_result.stats.mean_p_early),
                "mean_p_deadline": float(loss_result.stats.mean_p_deadline),
                "mean_quality_delay": float(loss_result.stats.mean_quality_delay),
                "boundary_cross_count": int(loss_result.stats.boundary_cross_count),
                "boundary_cross_in_window_count": int(loss_result.stats.boundary_cross_in_window_count),
                "prewindow_boundary_cross_count": int(pre_cross.sum().detach().cpu().item()),
                "quality_boundary_cross_count": int(quality_cross.sum().detach().cpu().item()),
                "first_quality_boundary_cross_step": first_quality_cross_step,
                "prewindow_prob_mean": float(pre_probs.mean().detach().cpu().item())
                if int(pre_probs.numel()) > 0
                else 0.0,
                "prewindow_prob_max": float(pre_probs.max().detach().cpu().item())
                if int(pre_probs.numel()) > 0
                else 0.0,
                "prewindow_cumulative_event_risk": _cumulative_risk(pre_probs),
                "quality_prob_mean": float(quality_probs.mean().detach().cpu().item()),
                "quality_prob_max": float(quality_probs.max().detach().cpu().item()),
                "quality_logit_max": float(quality_logits.max().detach().cpu().item()),
                "prewindow_logit_max": float(pre_logits.max().detach().cpu().item())
                if int(pre_logits.numel()) > 0
                else None,
                "grad_norm": grad_norm,
            }

    history.append(snapshot(0))
    for step in range(1, int(config.train_steps) + 1):
        optimizer.zero_grad(set_to_none=True)
        loss_result = _loss(logits_fn(), config)
        loss_result.loss.backward()
        grad_norm = None
        if float(config.max_grad_norm) > 0.0:
            grad_norm_tensor = th.nn.utils.clip_grad_norm_(params, float(config.max_grad_norm))
            grad_norm = float(grad_norm_tensor.detach().cpu().item())
        optimizer.step()
        if step in sample_steps:
            history.append(snapshot(step, grad_norm=grad_norm))

    final = history[-1]
    pass_window_mass = bool(float(final["mean_p_window"]) >= float(config.window_mass_gate))
    pass_prewindow_survival = bool(
        float(final["prewindow_cumulative_event_risk"]) <= float(config.prewindow_risk_gate)
    )
    pass_quality_boundary = final["first_quality_boundary_cross_step"] is not None
    pass_no_prewindow_boundary = bool(int(final["prewindow_boundary_cross_count"]) == 0)
    verdict = {
        "structural_toy_pass": bool(
            pass_window_mass and pass_prewindow_survival and pass_quality_boundary and pass_no_prewindow_boundary
        ),
        "pass_window_mass": pass_window_mass,
        "pass_prewindow_survival": pass_prewindow_survival,
        "pass_quality_boundary": pass_quality_boundary,
        "pass_no_prewindow_boundary": pass_no_prewindow_boundary,
    }
    return _finite(
        {
            "config": asdict(config),
            "history": history,
            "final": final,
            "verdict": verdict,
        }
    )


def _config_from_args(args: argparse.Namespace, *, model: str) -> ToyProbeConfig:
    return ToyProbeConfig(
        model=model,
        prewindow_steps=int(args.prewindow_steps),
        quality_steps=int(args.quality_steps),
        train_steps=int(args.train_steps),
        learning_rate=float(args.learning_rate),
        initial_logit=float(args.initial_logit),
        hidden_size=int(args.hidden_size),
        seed=int(args.seed),
        early_mass_coef=float(args.early_mass_coef),
        early_mass_budget=float(args.early_mass_budget),
        early_survival_coef=float(args.early_survival_coef),
        window_delay_coef=float(args.window_delay_coef),
        window_deadline_coef=float(args.window_deadline_coef),
        window_deadline_steps=int(args.window_deadline_steps),
        max_grad_norm=float(args.max_grad_norm),
        prewindow_risk_gate=float(args.prewindow_risk_gate),
        window_mass_gate=float(args.window_mass_gate),
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=("free_logits", "mlp", "both"), default="both")
    parser.add_argument("--prewindow-steps", type=int, default=800)
    parser.add_argument("--quality-steps", type=int, default=1080)
    parser.add_argument("--train-steps", type=int, default=2000)
    parser.add_argument("--learning-rate", type=float, default=0.05)
    parser.add_argument("--initial-logit", type=float, default=-6.0)
    parser.add_argument("--hidden-size", type=int, default=32)
    parser.add_argument("--seed", type=int, default=20260606)
    parser.add_argument("--early-mass-coef", type=float, default=2.0)
    parser.add_argument("--early-mass-budget", type=float, default=0.02)
    parser.add_argument("--early-survival-coef", type=float, default=8.0)
    parser.add_argument("--window-delay-coef", type=float, default=0.5)
    parser.add_argument("--window-deadline-coef", type=float, default=0.5)
    parser.add_argument("--window-deadline-steps", type=int, default=64)
    parser.add_argument("--max-grad-norm", type=float, default=2.0)
    parser.add_argument("--prewindow-risk-gate", type=float, default=0.02)
    parser.add_argument("--window-mass-gate", type=float, default=0.95)
    parser.add_argument("--json-out", type=str, default="")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    models = ("free_logits", "mlp") if str(args.model) == "both" else (str(args.model),)
    runs = [run_probe(_config_from_args(args, model=model)) for model in models]
    payload = {
        "runs": runs,
        "verdict": {
            "all_structural_toys_pass": all(bool(run["verdict"]["structural_toy_pass"]) for run in runs),
            "run_count": len(runs),
        },
    }
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.write("\n")
    print(text)
    return 0 if bool(payload["verdict"]["all_structural_toys_pass"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
