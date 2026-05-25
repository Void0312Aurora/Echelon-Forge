from __future__ import annotations

import argparse


MISSION_OBS_MODE_CHOICES = [
    "basic",
    "nav_v1",
    "nav_v2",
    "nav_v2_formation_v1",
    "nav_v2_formation_role_v1",
    "nav_v2_cooperative_takeoff_v1",
]

ACTION_MODE_CHOICES = ["full", "takeoff2", "takeoff4"]


def build_train_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Universal Training Base for CMO")
    parser.add_argument("--scenario", type=str, required=True, help="Path to JSON scenario file")
    parser.add_argument(
        "--train_config",
        type=str,
        default="examples/config/training/default_ppo.json",
        help="Path to training config JSON",
    )
    parser.add_argument("--test_only", action="store_true", help="Run in test mode without training")
    parser.add_argument(
        "--include_visual",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Include ARB visual observation (defaults to train_config env/policy settings).",
    )
    parser.add_argument(
        "--include_proprio",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Include previous action in observations (defaults to train_config env settings).",
    )
    parser.add_argument(
        "--mission_obs_mode",
        type=str,
        default=None,
        choices=MISSION_OBS_MODE_CHOICES,
        help="Mission observation format (defaults to train_config env settings).",
    )
    parser.add_argument(
        "--visual_downsample",
        type=int,
        default=None,
        help="Visual downsample factor (defaults to train_config env settings).",
    )
    parser.add_argument(
        "--visual_update_interval",
        type=int,
        default=None,
        help="Visual refresh interval (defaults to train_config env settings).",
    )
    parser.add_argument(
        "--temporal_history_len",
        type=int,
        default=None,
        help="Temporal observation history length for opt-in temporal policies.",
    )
    parser.add_argument(
        "--action_mode",
        type=str,
        default=None,
        choices=ACTION_MODE_CHOICES,
        help="Action space mode (defaults to train_config env settings).",
    )
    parser.add_argument("--run_name", type=str, default=None, help="Name of the run. If None, uses Timestamp.")
    parser.add_argument("--resume_path", type=str, default=None, help="Path to .zip model to resume training from.")
    parser.add_argument(
        "--init_from",
        type=str,
        default=None,
        help=(
            "Path to a .zip model checkpoint used only to initialize model parameters. "
            "This preserves the new run directory, optimizer state, and hyperparameters."
        ),
    )
    parser.add_argument("--output_base", type=str, default="experiments", help="Base directory for experiments.")
    parser.add_argument("--n_envs", type=int, default=None, help="Number of parallel environments (overrides config)")
    parser.add_argument(
        "--torch_threads",
        type=int,
        default=None,
        help="PyTorch intra-op CPU threads per process. If omitted, keep PyTorch defaults.",
    )
    parser.add_argument(
        "--torch_interop_threads",
        type=int,
        default=None,
        help="PyTorch inter-op CPU threads per process. If omitted, keep PyTorch defaults.",
    )
    parser.add_argument("--diagnostics", action="store_true", help="Log extra diagnostics scalars to TensorBoard")
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Global training seed for Python/NumPy/Torch and vec-env construction.",
    )
    parser.add_argument(
        "--diagnostics_every",
        type=int,
        default=10000,
        help="Diagnostics logging interval (in environment timesteps, not gradient updates)",
    )
    parser.add_argument(
        "--diagnostics_preterm_window",
        type=int,
        default=32,
        help="How many recent steps to aggregate for pre-termination diagnostics.",
    )
    parser.add_argument(
        "--no_init_safe_action_bias",
        action="store_true",
        help="Disable safe initialization bias for mixed-range actions (throttle/brakes/flaps/etc).",
    )
    parser.add_argument(
        "--nonfinite_probe",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable the opt-in training non-finite tensor probe.",
    )
    parser.add_argument(
        "--nonfinite_probe_report",
        type=str,
        default=None,
        help="Optional path for the non-finite probe report JSON. Defaults inside the experiment directory.",
    )
    parser.add_argument(
        "--nonfinite_probe_history",
        type=int,
        default=None,
        help="Optional history length for the non-finite probe event buffer.",
    )
    return parser
