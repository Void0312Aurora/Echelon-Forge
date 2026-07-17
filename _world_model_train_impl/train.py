"""Offline world-model training command."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from datetime import datetime

import torch

from _world_model_train_impl.checkpoint import (
    _checkpoint_tensor,
    _load_actor_checkpoint,
)
from _world_model_train_impl.common import (
    _apply_preset,
    _build_world_model,
    _format_metrics,
    _parse_angle_deg_indices,
    _resolve_visual_encoder_settings,
)

from python.world_model.dreamer import DreamerConfig, DreamerTrainer
from python.world_model.replay import EpisodeDataset
from python.world_model.utils import DeviceConfig, ensure_dir


def train_world_model(args: argparse.Namespace) -> None:
    ensure_dir(args.run_dir)
    _apply_preset(args)
    device = DeviceConfig(args.device).torch_device()
    reward_symlog_clip: float | None = float(args.reward_symlog_clip)
    if reward_symlog_clip <= 0.0:
        reward_symlog_clip = None
    dataset = EpisodeDataset(args.dataset_dir)
    ckpt = None
    ckpt_cfg = None
    if getattr(args, "checkpoint", None):
        ckpt_path = str(args.checkpoint)
        try:
            ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
        except TypeError:
            ckpt = torch.load(ckpt_path, map_location=device)
        if "spec" in ckpt:
            spec = ckpt.get("spec", {})
            if int(spec.get("action_dim", dataset.spec.action_dim)) != int(dataset.spec.action_dim):
                raise ValueError("Checkpoint action_dim does not match dataset spec")
            if int(spec.get("obs_vec_dim", dataset.spec.obs_vec_dim)) != int(
                dataset.spec.obs_vec_dim
            ):
                raise ValueError("Checkpoint obs_vec_dim does not match dataset spec")
        ckpt_cfg = ckpt.get("cfg", {}) if isinstance(ckpt, dict) else {}
    visual_encoder_type, visual_cnn_channels = _resolve_visual_encoder_settings(
        args=args, ckpt_cfg=ckpt_cfg
    )
    cfg = DreamerConfig(
        seed=int(args.seed),
        batch_size=int(args.batch_size),
        seq_len=int(args.seq_len),
        wm_lr=float(args.wm_lr),
        actor_lr=float(args.actor_lr),
        value_lr=float(args.value_lr),
        horizon=int(args.horizon),
        entropy_scale=float(args.entropy_scale),
        reward_symlog_clip=reward_symlog_clip,
        bc_scale=float(args.bc_scale),
        bc_teacher_prob=float(getattr(args, "bc_teacher_prob", 1.0)),
        bc_rudder_mag_weight=float(getattr(args, "bc_rudder_mag_weight", 0.0)),
        bc_rudder_weight=float(getattr(args, "bc_rudder_weight", 1.0)),
        bc_pitch_mag_weight=float(getattr(args, "bc_pitch_mag_weight", 0.0)),
        bc_pitch_weight=float(getattr(args, "bc_pitch_weight", 1.0)),
        bc_roll_mag_weight=float(getattr(args, "bc_roll_mag_weight", 0.0)),
        bc_roll_weight=float(getattr(args, "bc_roll_weight", 1.0)),
        bc_throttle_mag_weight=float(getattr(args, "bc_throttle_mag_weight", 0.0)),
        bc_throttle_weight=float(getattr(args, "bc_throttle_weight", 1.0)),
        bc_ground_alt_threshold=float(getattr(args, "bc_ground_alt_threshold", 5.0)),
        bc_ground_weight=float(getattr(args, "bc_ground_weight", 1.0)),
        bc_airborne_weight=float(getattr(args, "bc_airborne_weight", 1.0)),
        bc_loc_weight=float(getattr(args, "bc_loc_weight", 0.0)),
        bc_hdg_weight=float(getattr(args, "bc_hdg_weight", 0.0)),
        bc_hdg_norm_deg=float(getattr(args, "bc_hdg_norm_deg", 30.0)),
        bc_gru_burn_in=int(getattr(args, "bc_gru_burn_in", 0) or 0),
        bc_start_at_zero_prob=float(getattr(args, "bc_start_at_zero_prob", 0.0) or 0.0),
        actor_input=str(getattr(args, "actor_input", "rssm")),
        angle_deg_indices=_parse_angle_deg_indices(getattr(args, "angle_deg_indices", None)),
        stats_force_recompute=bool(getattr(args, "recompute_stats", False)),
        visual_encoder_type=visual_encoder_type,
        visual_cnn_channels=visual_cnn_channels,
    )

    wm = _build_world_model(
        action_dim=dataset.spec.action_dim,
        obs_vec_dim=dataset.spec.obs_vec_dim,
        visual_shape=dataset.spec.visual_shape,
        visual_encoder_type=visual_encoder_type,
        visual_cnn_channels=visual_cnn_channels,
    )
    trainer = DreamerTrainer(dataset=dataset, world_model=wm, device=device, cfg=cfg)

    if ckpt is not None:
        ckpt_path = str(args.checkpoint)
        if "world_model" in ckpt:
            trainer.wm.load_state_dict(ckpt["world_model"])
        ckpt_cfg = ckpt.get("cfg", {}) if isinstance(ckpt, dict) else {}
        ckpt_actor_input = (
            str(ckpt_cfg.get("actor_input", "rssm")) if isinstance(ckpt_cfg, dict) else "rssm"
        )
        if bool(getattr(args, "reset_actor", False)):
            print(f"[train] reset actor weights (not loading from checkpoint): {ckpt_path}")
        elif "actor" in ckpt:
            _load_actor_checkpoint(
                trainer.actor,
                ckpt["actor"],
                source_input=ckpt_actor_input,
                target_input=str(cfg.actor_input),
                source_angle_deg_indices=(
                    ckpt_cfg.get("angle_deg_indices")
                    if isinstance(ckpt_cfg, dict)
                    else None
                ),
                target_angle_deg_indices=cfg.angle_deg_indices,
            )
        if "value" in ckpt:
            trainer.value.load_state_dict(ckpt["value"])
        # IMPORTANT: The world model encoder is trained on normalized observations.
        # If we resume from a checkpoint but use a different dataset (with different stats),
        # the checkpoint weights become incompatible and rollouts can fail catastrophically.
        #
        # Default behavior: reuse the checkpoint's normalization stats unless the user
        # explicitly requests a recomputation via --recompute_stats.
        if not bool(getattr(args, "recompute_stats", False)):
            trainer.obs_mean = _checkpoint_tensor(
                ckpt,
                "obs_mean",
                trainer.obs_mean,
                device=device,
            )
            trainer.obs_std = _checkpoint_tensor(
                ckpt,
                "obs_std",
                trainer.obs_std,
                device=device,
                minimum=cfg.obs_min_std,
            )
            if dataset.spec.visual_shape is not None:
                trainer.visual_mean = _checkpoint_tensor(
                    ckpt,
                    "visual_mean",
                    trainer.visual_mean,
                    device=device,
                )
                trainer.visual_std = _checkpoint_tensor(
                    ckpt,
                    "visual_std",
                    trainer.visual_std,
                    device=device,
                    minimum=cfg.visual_min_std,
                )
        print(f"[train] loaded checkpoint {ckpt_path}")

    meta = {"time": datetime.now().isoformat(), "cfg": asdict(cfg), "dataset": args.dataset_dir}
    if getattr(args, "checkpoint", None):
        meta["resume_from"] = str(args.checkpoint)
    with open(os.path.join(args.run_dir, "meta.json"), "w", encoding="utf-8") as f:
        import json

        json.dump(meta, f, indent=2, ensure_ascii=False)

    steps = int(args.steps)
    for step in range(1, steps + 1):
        m: dict[str, float] = {}
        if not bool(getattr(args, "skip_wm", False)):
            m.update(trainer.train_world_model())
        if args.train_policy:
            if str(getattr(args, "policy_mode", "dreamer")) == "bc":
                m.update(trainer.train_actor_bc())
            else:
                m.update(trainer.train_actor_value())
        if step % int(args.log_every) == 0 or step == 1:
            msg = _format_metrics(m, compact=bool(getattr(args, "log_compact", False)))
            print(f"[train] step={step}/{steps} {msg}")

        if step % int(args.save_every) == 0 or step == steps:
            ckpt = {
                "world_model": trainer.wm.state_dict(),
                "actor": trainer.actor.state_dict(),
                "value": trainer.value.state_dict(),
                "obs_mean": trainer.obs_mean.detach().cpu(),
                "obs_std": trainer.obs_std.detach().cpu(),
                "visual_mean": (
                    trainer.visual_mean.detach().cpu() if trainer.visual_mean is not None else None
                ),
                "visual_std": (
                    trainer.visual_std.detach().cpu() if trainer.visual_std is not None else None
                ),
                "cfg": asdict(cfg),
                "spec": asdict(dataset.spec),
            }
            torch.save(ckpt, os.path.join(args.run_dir, "checkpoint.pt"))
