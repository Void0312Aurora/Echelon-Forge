from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from python.testing.runtime import ensure_repo_imports

ensure_repo_imports()

from python.env_config import resolve_env_settings
from python.mission_obs_taxonomy import BASE_MISSION_OBS_MODES, COOPERATIVE_MISSION_OBS_MODES
from python.rl.policy_algo.ppo_adaptive_kl import AdaptiveKLPPO


def load_json_config(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise TypeError(f"expected dict JSON at {path!r}")
    return data


def load_sb3_policy(model_path: str, *, algo: str, device: str):
    load_path = model_path[:-4] if model_path.endswith(".zip") else model_path
    algo_name = str(algo).strip()
    if algo_name in ("auto", "AdaptiveKLPPO", "PPOAdaptiveKL", "PPO_AdaptiveKL"):
        try:
            return AdaptiveKLPPO.load(load_path, device=device)
        except Exception:
            if algo_name != "auto":
                raise
    from stable_baselines3 import PPO

    return PPO.load(load_path, device=device)


def make_env_settings(train_config: dict[str, Any], args: argparse.Namespace, *, include_runtime_overrides: bool) -> dict[str, Any]:
    class _Args:
        include_visual = args.include_visual
        include_proprio = args.include_proprio
        action_mode = args.action_mode
        mission_obs_mode = args.mission_obs_mode
        visual_downsample = args.visual_downsample
        visual_update_interval = args.visual_update_interval
        execution_step_runtime_mode = getattr(args, "execution_step_runtime_mode", None) if include_runtime_overrides else None
        step_info_mode = getattr(args, "step_info_mode", None) if include_runtime_overrides else None
        flight_shaping_backend = getattr(args, "flight_shaping_backend", None) if include_runtime_overrides else None

    return resolve_env_settings(train_config, _Args())


def add_common_sb3_eval_args(
    parser: argparse.ArgumentParser,
    *,
    include_runtime_overrides: bool,
    cooperative: bool,
    episodes_default: int = 8,
    seed_default: int = 0,
    episodes_help: str | None = None,
    seed_help: str | None = None,
) -> None:
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--train_config", required=True)
    parser.add_argument("--model", required=True, help="Path to SB3 model zip.")
    parser.add_argument("--algo", default="auto", help="auto / AdaptiveKLPPO / PPO")
    parser.add_argument("--episodes", type=int, default=int(episodes_default), help=episodes_help)
    parser.add_argument("--seed", type=int, default=int(seed_default), help=seed_help)
    parser.add_argument("--stochastic", action="store_true")
    parser.add_argument("--device", type=str, default="auto", help="Policy inference device: auto / cpu / cuda")
    parser.add_argument(
        "--include_visual",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Override env visual flag from train config.",
    )
    parser.add_argument(
        "--include_proprio",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Override env proprio flag from train config.",
    )
    mission_choices = list(BASE_MISSION_OBS_MODES)
    if cooperative:
        mission_choices.extend(COOPERATIVE_MISSION_OBS_MODES)
    parser.add_argument(
        "--mission_obs_mode",
        type=str,
        default=None,
        choices=mission_choices,
    )
    parser.add_argument("--visual_downsample", type=int, default=None)
    parser.add_argument("--visual_update_interval", type=int, default=None)
    parser.add_argument("--action_mode", type=str, default=None, choices=["full", "takeoff2", "takeoff4"])
    if include_runtime_overrides:
        parser.add_argument("--execution_step_runtime_mode", type=str, default=None, choices=["compiled", "legacy"])
        parser.add_argument("--step_info_mode", type=str, default=None, choices=["full", "terminal", "off"])
        parser.add_argument(
            "--flight_shaping_backend",
            type=str,
            default=None,
            choices=["auto", "legacy", "compiled", "gpu_host"],
        )
    parser.add_argument("--json_out", default="", help="Optional JSON output path.")


def write_json_output(json_out: str, payload: dict[str, Any]) -> None:
    if not json_out:
        return
    out_path = os.path.abspath(json_out)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=True)
        f.write("\n")
