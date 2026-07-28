from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from python.runtime_bootstrap import ensure_repo_imports

ensure_repo_imports()

from python.env_config import (
    ACTION_MODES,
    EXECUTION_STEP_RUNTIME_MODES,
    FLIGHT_SHAPING_BACKENDS,
    STEP_INFO_MODES,
    resolve_env_settings,
)
from python.mission_obs_taxonomy import BASE_MISSION_OBS_MODES, COOPERATIVE_MISSION_OBS_MODES, NAVAL_MISSION_OBS_MODES
from python.rl.policy_checkpoint import load_sb3_policy
from tools.diagnostics.common import add_json_out_arg, add_model_load_args, add_probe_run_args


def load_json_config(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise TypeError(f"expected dict JSON at {path!r}")
    return data


def make_env_settings(train_config: dict[str, Any], args: argparse.Namespace, *, include_runtime_overrides: bool) -> dict[str, Any]:
    class _Args:
        include_visual = args.include_visual
        include_proprio = args.include_proprio
        action_mode = args.action_mode
        mission_obs_mode = args.mission_obs_mode
        visual_downsample = args.visual_downsample
        visual_update_interval = args.visual_update_interval
        temporal_history_len = getattr(args, "temporal_history_len", None)
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
    add_probe_run_args(parser, include=["scenario"], required={"scenario": True})
    add_model_load_args(
        parser,
        include=["train_config", "model", "algo"],
        required={"train_config": True, "model": True},
        defaults={"algo": "auto"},
        helps={"model": "Path to SB3 model zip.", "algo": "auto / AdaptiveKLPPO / PPO"},
    )
    add_probe_run_args(
        parser,
        include=["episodes", "seed"],
        defaults={"episodes": int(episodes_default), "seed": int(seed_default)},
        helps={"episodes": episodes_help, "seed": seed_help},
    )
    parser.add_argument("--stochastic", action="store_true")
    add_model_load_args(
        parser,
        include=["device"],
        defaults={"device": "auto"},
        types={"device": str},
        helps={"device": "Policy inference device: auto / cpu / cuda"},
    )
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
    mission_choices.extend(NAVAL_MISSION_OBS_MODES)
    parser.add_argument(
        "--mission_obs_mode",
        type=str,
        default=None,
        choices=mission_choices,
    )
    parser.add_argument("--visual_downsample", type=int, default=None)
    parser.add_argument("--visual_update_interval", type=int, default=None)
    parser.add_argument("--temporal_history_len", type=int, default=None)
    parser.add_argument(
        "--action_mode",
        type=str,
        default=None,
        choices=list(ACTION_MODES),
    )
    if include_runtime_overrides:
        parser.add_argument(
            "--execution_step_runtime_mode",
            type=str,
            default=None,
            choices=list(EXECUTION_STEP_RUNTIME_MODES),
        )
        parser.add_argument("--step_info_mode", type=str, default=None, choices=list(STEP_INFO_MODES))
        parser.add_argument(
            "--flight_shaping_backend",
            type=str,
            default=None,
            choices=list(FLIGHT_SHAPING_BACKENDS),
        )
    add_json_out_arg(parser, help="Optional JSON output path.")


def write_json_output(json_out: str, payload: dict[str, Any]) -> None:
    if not json_out:
        return
    out_path = os.path.abspath(json_out)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=True)
        f.write("\n")
