"""Argument parser and dispatcher for the world-model training CLI."""

from __future__ import annotations

import argparse


def main() -> None:
    p = argparse.ArgumentParser(description="Initial world-model (Dreamer-style) training for CMO")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_collect = sub.add_parser("collect", help="Collect an offline dataset from the env")
    p_collect.add_argument("--scenario", required=True)
    p_collect.add_argument("--out_dir", required=True)
    p_collect.add_argument("--episodes", type=int, default=10)
    p_collect.add_argument("--max_steps", type=int, default=None)
    p_collect.add_argument("--seed", type=int, default=0)
    p_collect.add_argument(
        "--action_mode", type=str, default="full", choices=["full", "takeoff2", "takeoff4"]
    )
    p_collect.add_argument(
        "--policy",
        type=str,
        default="random",
        choices=[
            "random",
            "scripted_takeoff",
            "scripted_stable_flight",
            "scripted_waypoint",
            "dagger_scripted_takeoff",
            "dagger_scripted_stable_flight",
            "dagger_scripted_waypoint",
        ],
        help="Data collection policy: random, scripted expert, or DAgger (student executes, scripted labels).",
    )
    p_collect.add_argument(
        "--student_checkpoint",
        type=str,
        default=None,
        help="Required for DAgger policies: checkpoint.pt for the student policy.",
    )
    p_collect.add_argument(
        "--device",
        type=str,
        default="cpu",
        help="Inference device for DAgger student policy (cpu/cuda).",
    )
    p_collect.add_argument(
        "--dagger_teacher_prob",
        type=float,
        default=0.0,
        help="DAgger: probability of executing the scripted teacher action (0=student-only, 1=teacher-only).",
    )
    p_collect.add_argument(
        "--student_stochastic",
        action="store_true",
        help="DAgger: sample stochastic actions from the student policy (default: deterministic mean).",
    )
    p_collect.add_argument("--include_visual", action="store_true")
    p_collect.add_argument(
        "--include_proprio",
        action="store_true",
        help="Include previous action (proprioception) in observations; realism-safe and can improve control stability.",
    )
    p_collect.add_argument("--visual_downsample", type=int, default=4)
    p_collect.add_argument(
        "--no_randomization", action="store_true", help="Disable wind/world-yaw randomization"
    )
    p_collect.add_argument(
        "--curriculum", type=str, default=None, help="Path to randomization curriculum JSON"
    )
    p_collect.add_argument(
        "--require_success",
        action="store_true",
        help="Only save episodes that terminate with mission success (useful for scripted demo collection).",
    )
    p_collect.add_argument(
        "--min_on_runway_geom_frac",
        type=float,
        default=0.0,
        help="Optional minimum fraction of ground steps that remain within runway geometry (0 to disable).",
    )
    p_collect.add_argument(
        "--max_abs_runway_cross_m",
        type=float,
        default=None,
        help="Optional maximum absolute runway cross-track on the ground (meters); episodes exceeding it are skipped.",
    )

    p_train = sub.add_parser(
        "train", help="Train world model (and optionally the policy) from a dataset"
    )
    p_train.add_argument("--dataset_dir", required=True)
    p_train.add_argument("--run_dir", required=True)
    p_train.add_argument(
        "--checkpoint", type=str, default=None, help="Optional checkpoint.pt to resume from"
    )
    p_train.add_argument(
        "--reset_actor",
        action="store_true",
        help="Do not load actor weights from --checkpoint (useful when changing --actor_input architecture).",
    )
    p_train.add_argument(
        "--bc_gru_burn_in",
        type=int,
        default=0,
        help="Recurrent BC: burn-in steps when using a *_gru actor_input (0 disables).",
    )
    p_train.add_argument(
        "--bc_start_at_zero_prob",
        type=float,
        default=0.0,
        help="Non-recurrent BC: probability of sampling sequences starting at t=0 to emphasize transients (0 disables).",
    )
    p_train.add_argument("--steps", type=int, default=2000)
    p_train.add_argument("--seed", type=int, default=0)
    p_train.add_argument("--device", type=str, default="cuda")
    p_train.add_argument("--batch_size", type=int, default=16)
    p_train.add_argument("--seq_len", type=int, default=50)
    p_train.add_argument("--wm_lr", type=float, default=3e-4)
    p_train.add_argument("--actor_lr", type=float, default=3e-4)
    p_train.add_argument("--value_lr", type=float, default=3e-4)
    p_train.add_argument("--horizon", type=int, default=15)
    p_train.add_argument("--entropy_scale", type=float, default=1e-3)
    p_train.add_argument("--reward_symlog_clip", type=float, default=6.0, help="<=0 to disable")
    p_train.add_argument(
        "--bc_scale",
        type=float,
        default=0.0,
        help="Behavior cloning regularizer for offline stability",
    )
    p_train.add_argument(
        "--bc_teacher_prob",
        type=float,
        default=1.0,
        help="BC scheduled sampling: probability of using dataset actions to advance RSSM state (0=student, 1=teacher).",
    )
    p_train.add_argument(
        "--bc_rudder_mag_weight",
        type=float,
        default=0.0,
        help="BC loss reweighting: increases penalty on rudder error when expert rudder magnitude is large (0 disables).",
    )
    p_train.add_argument(
        "--bc_rudder_weight",
        type=float,
        default=1.0,
        help="BC loss reweighting: constant multiplier on rudder error (applies even when expert rudder is small).",
    )
    p_train.add_argument(
        "--bc_pitch_mag_weight",
        type=float,
        default=0.0,
        help="BC loss reweighting: increases penalty on pitch error when expert pitch magnitude is large (0 disables).",
    )
    p_train.add_argument(
        "--bc_pitch_weight",
        type=float,
        default=1.0,
        help="BC loss reweighting: constant multiplier on pitch error (applies even when expert pitch is small).",
    )
    p_train.add_argument(
        "--bc_roll_mag_weight",
        type=float,
        default=0.0,
        help="BC loss reweighting: increases penalty on roll error when expert roll magnitude is large (0 disables).",
    )
    p_train.add_argument(
        "--bc_roll_weight",
        type=float,
        default=1.0,
        help="BC loss reweighting: constant multiplier on roll error (applies even when expert roll is small).",
    )
    p_train.add_argument(
        "--bc_throttle_mag_weight",
        type=float,
        default=0.0,
        help="BC loss reweighting: increases penalty on throttle error when expert throttle magnitude is large (0 disables).",
    )
    p_train.add_argument(
        "--bc_throttle_weight",
        type=float,
        default=1.0,
        help="BC loss reweighting: constant multiplier on throttle error (applies even when expert throttle is small).",
    )
    p_train.add_argument(
        "--bc_ground_alt_threshold",
        type=float,
        default=5.0,
        help="BC step weighting: treat radar altitude < threshold (m) as ground-roll.",
    )
    p_train.add_argument(
        "--bc_ground_weight",
        type=float,
        default=1.0,
        help="BC step weighting multiplier for ground-roll timesteps (1=disable).",
    )
    p_train.add_argument(
        "--bc_airborne_weight",
        type=float,
        default=1.0,
        help="BC step weighting multiplier for airborne timesteps (1=disable).",
    )
    p_train.add_argument(
        "--bc_loc_weight",
        type=float,
        default=0.0,
        help="BC step weighting: multiply loss by (1 + k*abs(ILS loc_dev)) to emphasize recovery (0=disable).",
    )
    p_train.add_argument(
        "--bc_hdg_weight",
        type=float,
        default=0.0,
        help="BC step weighting: multiply loss by (1 + k*abs(mission heading error)/norm) to emphasize capture phases.",
    )
    p_train.add_argument(
        "--bc_hdg_norm_deg",
        type=float,
        default=30.0,
        help="BC heading-error weight normalization in degrees (used by --bc_hdg_weight).",
    )
    p_train.add_argument(
        "--actor_input",
        type=str,
        default="rssm",
        choices=[
            "rssm",
            "embed",
            "embed_gru",
            "embed_sincos",
            "embed_sincos_gru",
            "embed_sincos_track",
            "embed_sincos_track_gru",
            "obs",
            "obs_gru",
            "obs_sincos",
            "obs_sincos_gru",
            "obs_sincos_track",
            "obs_sincos_track_gru",
            "obs_sincos_track_vis",
            "obs_sincos_track_vis_gru",
        ],
        help=(
            "Actor conditioning: 'rssm' (Dreamer-style), "
            "'embed'/'embed_gru' (encoder embed), "
            "'embed_sincos'/'embed_sincos_gru' (embed + sin/cos angle features), "
            "'embed_sincos_track'/'embed_sincos_track_gru' (embed + sin/cos + tracking features), "
            "'obs'/'obs_gru' (raw obs_vec), or 'obs_sincos'/'obs_sincos_gru' "
            "(obs_vec + sin/cos angle features), "
            "'obs_sincos_track'/'obs_sincos_track_gru' (obs_vec + sin/cos + tracking features), "
            "or 'obs_sincos_track_vis'/'obs_sincos_track_vis_gru' (adds visual embedding for full-observation training)."
        ),
    )
    p_train.add_argument(
        "--angle_deg_indices",
        type=str,
        default=None,
        help="Comma-separated obs_vec indices (raw degrees) to encode as sin/cos features for *_sincos actor inputs.",
    )
    p_train.add_argument(
        "--visual_encoder_type",
        type=str,
        default="cnn",
        choices=["cnn", "mlp"],
        help="World-model visual encoder architecture for new runs. Checkpoint resume keeps the checkpoint architecture.",
    )
    p_train.add_argument(
        "--visual_cnn_channels",
        type=int,
        default=64,
        help="Base channel count for the CNN visual encoder.",
    )
    p_train.add_argument("--train_policy", action="store_true")
    p_train.add_argument("--policy_mode", type=str, default="dreamer", choices=["dreamer", "bc"])
    p_train.add_argument(
        "--skip_wm",
        action="store_true",
        help="Skip world-model updates (useful to fine-tune the actor with a frozen world model).",
    )
    p_train.add_argument(
        "--preset", type=str, default="default", choices=["default", "takeoff_stable"]
    )
    p_train.add_argument("--log_compact", action="store_true")
    p_train.add_argument(
        "--recompute_stats",
        action="store_true",
        help="Recompute dataset normalization stats and overwrite stats.npz (use after appending new episodes).",
    )
    p_train.add_argument("--log_every", type=int, default=50)
    p_train.add_argument("--save_every", type=int, default=500)

    p_online = sub.add_parser(
        "online", help="Online training: interleave env rollouts with training"
    )
    p_online.add_argument("--scenario", required=True)
    p_online.add_argument("--dataset_dir", required=True)
    p_online.add_argument("--run_dir", required=True)
    p_online.add_argument("--checkpoint", type=str, default=None)
    p_online.add_argument("--steps", type=int, default=2000)
    p_online.add_argument("--seed", type=int, default=0)
    p_online.add_argument("--device", type=str, default="cuda")
    p_online.add_argument("--batch_size", type=int, default=16)
    p_online.add_argument("--seq_len", type=int, default=50)
    p_online.add_argument("--wm_lr", type=float, default=3e-4)
    p_online.add_argument("--actor_lr", type=float, default=3e-4)
    p_online.add_argument("--value_lr", type=float, default=3e-4)
    p_online.add_argument("--horizon", type=int, default=15)
    p_online.add_argument("--entropy_scale", type=float, default=1e-3)
    p_online.add_argument("--reward_symlog_clip", type=float, default=6.0, help="<=0 to disable")
    p_online.add_argument("--bc_scale", type=float, default=0.0)
    p_online.add_argument(
        "--bc_teacher_prob",
        type=float,
        default=1.0,
        help="BC scheduled sampling: probability of using dataset actions to advance RSSM state (0=student, 1=teacher).",
    )
    p_online.add_argument(
        "--bc_gru_burn_in",
        type=int,
        default=0,
        help="Recurrent BC: burn-in steps when using a *_gru actor_input (0 disables).",
    )
    p_online.add_argument(
        "--bc_start_at_zero_prob",
        type=float,
        default=0.0,
        help="Non-recurrent BC: probability of sampling sequences starting at t=0 to emphasize transients (0 disables).",
    )
    p_online.add_argument(
        "--bc_rudder_mag_weight",
        type=float,
        default=0.0,
        help="BC loss reweighting: increases penalty on rudder error when expert rudder magnitude is large (0 disables).",
    )
    p_online.add_argument(
        "--bc_rudder_weight",
        type=float,
        default=1.0,
        help="BC loss reweighting: constant multiplier on rudder error (applies even when expert rudder is small).",
    )
    p_online.add_argument(
        "--bc_pitch_mag_weight",
        type=float,
        default=0.0,
        help="BC loss reweighting: increases penalty on pitch error when expert pitch magnitude is large (0 disables).",
    )
    p_online.add_argument(
        "--bc_pitch_weight",
        type=float,
        default=1.0,
        help="BC loss reweighting: constant multiplier on pitch error (applies even when expert pitch is small).",
    )
    p_online.add_argument(
        "--bc_roll_mag_weight",
        type=float,
        default=0.0,
        help="BC loss reweighting: increases penalty on roll error when expert roll magnitude is large (0 disables).",
    )
    p_online.add_argument(
        "--bc_roll_weight",
        type=float,
        default=1.0,
        help="BC loss reweighting: constant multiplier on roll error (applies even when expert roll is small).",
    )
    p_online.add_argument(
        "--bc_throttle_mag_weight",
        type=float,
        default=0.0,
        help="BC loss reweighting: increases penalty on throttle error when expert throttle magnitude is large (0 disables).",
    )
    p_online.add_argument(
        "--bc_throttle_weight",
        type=float,
        default=1.0,
        help="BC loss reweighting: constant multiplier on throttle error (applies even when expert throttle is small).",
    )
    p_online.add_argument(
        "--bc_ground_alt_threshold",
        type=float,
        default=5.0,
        help="BC step weighting: treat radar altitude < threshold (m) as ground-roll.",
    )
    p_online.add_argument(
        "--bc_ground_weight",
        type=float,
        default=1.0,
        help="BC step weighting multiplier for ground-roll timesteps (1=disable).",
    )
    p_online.add_argument(
        "--bc_airborne_weight",
        type=float,
        default=1.0,
        help="BC step weighting multiplier for airborne timesteps (1=disable).",
    )
    p_online.add_argument(
        "--bc_loc_weight",
        type=float,
        default=0.0,
        help="BC step weighting: multiply loss by (1 + k*abs(ILS loc_dev)) to emphasize recovery (0=disable).",
    )
    p_online.add_argument(
        "--bc_hdg_weight",
        type=float,
        default=0.0,
        help="BC step weighting: multiply loss by (1 + k*abs(mission heading error)/norm) to emphasize capture phases.",
    )
    p_online.add_argument(
        "--bc_hdg_norm_deg",
        type=float,
        default=30.0,
        help="BC heading-error weight normalization in degrees (used by --bc_hdg_weight).",
    )
    p_online.add_argument(
        "--actor_input",
        type=str,
        default="rssm",
        choices=[
            "rssm",
            "embed",
            "embed_gru",
            "embed_sincos",
            "embed_sincos_gru",
            "embed_sincos_track",
            "embed_sincos_track_gru",
            "obs",
            "obs_gru",
            "obs_sincos",
            "obs_sincos_gru",
            "obs_sincos_track",
            "obs_sincos_track_gru",
            "obs_sincos_track_vis",
            "obs_sincos_track_vis_gru",
        ],
        help=(
            "Actor conditioning: 'rssm' (Dreamer-style), "
            "'embed'/'embed_gru' (encoder embed), "
            "'embed_sincos'/'embed_sincos_gru' (embed + sin/cos angle features), "
            "'embed_sincos_track'/'embed_sincos_track_gru' (embed + sin/cos + tracking features), "
            "'obs'/'obs_gru' (raw obs_vec), or 'obs_sincos'/'obs_sincos_gru' "
            "(obs_vec + sin/cos angle features), "
            "'obs_sincos_track'/'obs_sincos_track_gru' (obs_vec + sin/cos + tracking features), "
            "or 'obs_sincos_track_vis'/'obs_sincos_track_vis_gru' (adds visual embedding for full-observation training)."
        ),
    )
    p_online.add_argument(
        "--angle_deg_indices",
        type=str,
        default=None,
        help="Comma-separated obs_vec indices (raw degrees) to encode as sin/cos features for *_sincos actor inputs.",
    )
    p_online.add_argument(
        "--visual_encoder_type",
        type=str,
        default="cnn",
        choices=["cnn", "mlp"],
        help="World-model visual encoder architecture for new runs. Checkpoint resume keeps the checkpoint architecture.",
    )
    p_online.add_argument(
        "--visual_cnn_channels",
        type=int,
        default=64,
        help="Base channel count for the CNN visual encoder.",
    )
    p_online.add_argument("--train_policy", action="store_true")
    p_online.add_argument("--policy_mode", type=str, default="dreamer", choices=["dreamer", "bc"])
    p_online.add_argument(
        "--skip_wm",
        action="store_true",
        help="Skip world-model updates (useful to validate online rollouts without changing WM weights).",
    )
    p_online.add_argument(
        "--action_mode", type=str, default="full", choices=["full", "takeoff2", "takeoff4"]
    )
    p_online.add_argument(
        "--include_proprio",
        action="store_true",
        help="Include previous action (proprioception) in observations; must match how the dataset was collected.",
    )
    p_online.add_argument(
        "--preset", type=str, default="default", choices=["default", "takeoff_stable"]
    )
    p_online.add_argument("--log_compact", action="store_true")
    p_online.add_argument(
        "--recompute_stats",
        action="store_true",
        help="Recompute dataset normalization stats and overwrite stats.npz (use after appending new episodes).",
    )
    p_online.add_argument("--max_steps", type=int, default=2000)
    p_online.add_argument("--collect_every", type=int, default=200)
    p_online.add_argument("--collect_episodes", type=int, default=1)
    p_online.add_argument(
        "--expert_labels",
        type=str,
        default="none",
        choices=["none", "scripted_takeoff", "scripted_stable_flight", "scripted_waypoint"],
        help="Optional DAgger-style expert labels for online-collected episodes (stored as expert_actions).",
    )
    p_online.add_argument("--deterministic", action="store_true")
    p_online.add_argument(
        "--stochastic_state",
        action="store_true",
        help="Sample stochastic RSSM latent states during rollouts (default: use posterior mean for stability).",
    )
    p_online.add_argument(
        "--no_randomization", action="store_true", help="Disable wind/world-yaw randomization"
    )
    p_online.add_argument(
        "--curriculum", type=str, default=None, help="Path to randomization curriculum JSON"
    )
    p_online.add_argument("--log_every", type=int, default=50)
    p_online.add_argument("--save_every", type=int, default=500)

    p_roll = sub.add_parser("rollout", help="Roll out a trained world-model policy in the real env")
    p_roll.add_argument("--scenario", required=True)
    p_roll.add_argument("--checkpoint", required=True)
    p_roll.add_argument("--episodes", type=int, default=3)
    p_roll.add_argument("--max_steps", type=int, default=2000)
    p_roll.add_argument("--seed", type=int, default=0)
    p_roll.add_argument("--device", type=str, default="cuda")
    p_roll.add_argument(
        "--action_mode", type=str, default="full", choices=["full", "takeoff2", "takeoff4"]
    )
    p_roll.add_argument("--include_visual", action="store_true")
    p_roll.add_argument(
        "--include_proprio",
        action="store_true",
        help="Include previous action (proprioception) in observations; required if the checkpoint expects it.",
    )
    p_roll.add_argument(
        "--stochastic",
        action="store_true",
        help="Sample stochastic actions (default: deterministic mean action).",
    )
    p_roll.add_argument(
        "--deterministic",
        action="store_true",
        help="(deprecated) deterministic is the default; kept for compatibility.",
    )
    p_roll.add_argument(
        "--stochastic_state",
        action="store_true",
        help="Sample stochastic RSSM latent states during rollouts (default: use posterior mean for stability).",
    )
    p_roll.add_argument(
        "--no_randomization", action="store_true", help="Disable wind/world-yaw randomization"
    )

    args = p.parse_args()
    if args.cmd == "collect":
        from _world_model_train_impl.collect import collect_dataset

        collect_dataset(args)
    elif args.cmd == "train":
        from _world_model_train_impl.train import train_world_model

        train_world_model(args)
    elif args.cmd == "online":
        from _world_model_train_impl.online import online_train

        online_train(args)
    elif args.cmd == "rollout":
        from _world_model_train_impl.rollout import rollout_policy

        rollout_policy(args)
    else:  # pragma: no cover
        raise ValueError(args.cmd)
