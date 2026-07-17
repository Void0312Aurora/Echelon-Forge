"""Online world-model training command."""

from __future__ import annotations

import argparse
import os
from dataclasses import asdict

import numpy as np
import torch

from _world_model_train_impl.checkpoint import (
    _checkpoint_tensor,
    _load_actor_checkpoint,
)
from _world_model_train_impl.common import (
    _apply_env_overrides,
    _apply_norm_clip,
    _apply_preset,
    _build_world_model,
    _downsample_visual,
    _flatten_obs,
    _format_metrics,
    _get_stage_overrides,
    _load_curriculum,
    _normalize_action,
    _parse_angle_deg_indices,
    _resolve_visual_encoder_settings,
    _select_curriculum_stage,
    _unnormalize_action,
)

from _world_model_train_impl.runtime_env import build_world_model_execution_env
from python.rl.control.scripted_stable_flight import ScriptedStableFlightController
from python.rl.control.scripted_takeoff import ScriptedTakeoffController, scripted_takeoff_action
from python.world_model.dreamer import DreamerConfig, DreamerTrainer
from python.world_model.features import (
    angle_sincos_features,
    append_angle_sincos_features,
    nav_tracking_features,
)
from python.world_model.replay import Episode, EpisodeDataset, EpisodeStore
from python.world_model.utils import DeviceConfig, ensure_dir


def online_train(args: argparse.Namespace) -> None:
    """
    Online training loop: interleave real-environment rollouts with world-model updates.
    This helps reduce offline model exploitation by keeping the dataset close to the current policy.
    """
    ensure_dir(args.run_dir)
    _apply_preset(args)
    device = DeviceConfig(args.device).torch_device()

    reward_symlog_clip: float | None = float(args.reward_symlog_clip)
    if reward_symlog_clip <= 0.0:
        reward_symlog_clip = None
    dataset = EpisodeDataset(args.dataset_dir)
    store = EpisodeStore(args.dataset_dir, dataset.spec)
    ckpt = None
    ckpt_cfg = None
    if args.checkpoint is not None:
        ckpt_path = str(args.checkpoint)
        try:
            ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
        except TypeError:
            ckpt = torch.load(ckpt_path, map_location=device)
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
        ckpt_actor_input = (
            str(ckpt_cfg.get("actor_input", "rssm")) if isinstance(ckpt_cfg, dict) else "rssm"
        )
        if bool(getattr(args, "reset_actor", False)):
            print(f"[online] reset actor weights (not loading from checkpoint): {ckpt_path}")
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
        # See train_world_model(): keep checkpoint normalization stats by default, otherwise
        # the resumed encoder can become incompatible with the new dataset stats.
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
        print(f"[online] loaded checkpoint {ckpt_path}")

    include_visual = dataset.spec.visual_shape is not None
    env = build_world_model_execution_env(
        scenario_path=args.scenario,
        include_visual=bool(include_visual),
        include_proprio=bool(getattr(args, "include_proprio", False)),
        action_mode=str(args.action_mode),
    )
    _apply_env_overrides(env, args)
    curriculum = None
    if getattr(args, "curriculum", None) and not bool(getattr(args, "no_randomization", False)):
        curriculum = _load_curriculum(str(args.curriculum))
    active_stage_idx = None

    try:
        action_low = np.asarray(env.action_space.low, dtype=np.float32).reshape(-1)
        action_high = np.asarray(env.action_space.high, dtype=np.float32).reshape(-1)
    except Exception:
        raise RuntimeError("Online training requires a bounded Box action_space")

    if dataset.spec.action_low is None or dataset.spec.action_high is None:
        raise ValueError(
            "Dataset is missing action_low/action_high; re-collect it using the updated collector "
            "or regenerate the dataset spec."
        )
    spec_low = np.asarray(dataset.spec.action_low, dtype=np.float32).reshape(-1)
    spec_high = np.asarray(dataset.spec.action_high, dtype=np.float32).reshape(-1)
    if spec_low.shape != action_low.shape or spec_high.shape != action_high.shape:
        raise ValueError("Action-space bounds mismatch between env and dataset spec")

    if include_visual:
        env_visual_shape = (48, 96, 10)
        h, w, c = dataset.spec.visual_shape  # type: ignore[misc]
        if int(c) != int(env_visual_shape[2]):
            raise ValueError(f"Visual channel mismatch: dataset C={c}, env C={env_visual_shape[2]}")
        if env_visual_shape[0] % int(h) != 0 or env_visual_shape[1] % int(w) != 0:
            raise ValueError(
                f"Cannot downsample env visual {env_visual_shape} -> {dataset.spec.visual_shape}"
            )
        factor_h = env_visual_shape[0] // int(h)
        factor_w = env_visual_shape[1] // int(w)
        if factor_h != factor_w:
            raise ValueError(f"Non-uniform visual downsample factors: h={factor_h}, w={factor_w}")
        visual_downsample = int(factor_h)
    else:
        visual_downsample = 1

    actor_input = str(getattr(cfg, "actor_input", "rssm"))
    deterministic_state = not bool(getattr(args, "stochastic_state", False))
    expert_labels = str(getattr(args, "expert_labels", "none"))

    def collect_one_episode(seed: int) -> str:
        obs, _ = env.reset(seed=int(seed))
        obs_vecs = [_flatten_obs(obs)]
        visuals = []
        if include_visual:
            v = np.asarray(obs["visual"], dtype=np.float32)
            v = _downsample_visual(v, visual_downsample).astype(np.float16)
            visuals.append(v)

        # Init latent state from first observation.
        obs_raw_t = torch.from_numpy(obs_vecs[0]).to(device).float().unsqueeze(0)
        obs_t = (obs_raw_t - trainer.obs_mean.unsqueeze(0)) / trainer.obs_std.unsqueeze(0)
        obs_t = _apply_norm_clip(obs_t, trainer.cfg.obs_norm_clip)
        if include_visual:
            v0 = np.asarray(obs["visual"], dtype=np.float32)
            v0 = _downsample_visual(v0, visual_downsample)
            v0 = np.clip(v0, -10.0, 10.0).astype(np.float32, copy=False)
            vis_t = torch.from_numpy(v0).to(device).float().unsqueeze(0)  # (1,H,W,C)
            vis_t = (vis_t - trainer.visual_mean.view(1, 1, 1, -1)) / trainer.visual_std.view(
                1, 1, 1, -1
            )
            vis_t = _apply_norm_clip(vis_t, trainer.cfg.visual_norm_clip)
            vis_t = vis_t.reshape(1, -1)
        else:
            vis_t = None
        with torch.no_grad():
            embed0 = None
            if actor_input not in (
                "obs",
                "obs_gru",
                "obs_sincos",
                "obs_sincos_gru",
                "obs_sincos_track",
                "obs_sincos_track_gru",
            ):
                embed0 = (
                    trainer.wm.encoder(obs_t, vis_t)
                    if vis_t is not None
                    else trainer.wm.encoder(obs_t)
                )
        with torch.no_grad():
            state = None
            if actor_input == "rssm":
                assert embed0 is not None
                state, _ = trainer.wm.rssm.observe_init(embed0, deterministic=deterministic_state)
        actor_h = None
        if actor_input in (
            "embed_gru",
            "embed_sincos_gru",
            "embed_sincos_track_gru",
            "obs_gru",
            "obs_sincos_gru",
            "obs_sincos_track_gru",
            "obs_sincos_track_vis_gru",
        ):
            actor_h = trainer.actor.init_h(batch_size=1, device=device)  # type: ignore[union-attr]

        actions = []
        expert_actions = []
        rewards = []
        dones = []

        expert_ctrl = None
        if expert_labels != "none":
            try:
                dt = float(env.get_time_step())
            except Exception:
                dt = 0.05
            if expert_labels == "scripted_takeoff":
                expert_ctrl = ScriptedTakeoffController(
                    action_dim=int(dataset.spec.action_dim), dt=dt
                )
                expert_ctrl.reset(obs)
            elif expert_labels == "scripted_stable_flight":
                expert_ctrl = ScriptedStableFlightController(
                    action_dim=int(dataset.spec.action_dim), dt=dt
                )
                expert_ctrl.reset(obs)
            elif expert_labels == "scripted_waypoint":
                # Waypoint navigation uses the same realism-first controller: it tracks the mission heading/alt/speed,
                # and for command_code==3 the ScenarioLoader updates the mission heading to "bearing-to-waypoint".
                expert_ctrl = ScriptedStableFlightController(
                    action_dim=int(dataset.spec.action_dim), dt=dt
                )
                expert_ctrl.reset(obs)
            else:
                raise ValueError(f"Unknown expert_labels: {expert_labels}")

        done = False
        steps = 0
        max_steps = int(args.max_steps) if args.max_steps is not None else 10**9

        while not done and steps < max_steps:
            with torch.no_grad():
                if actor_input == "obs":
                    feat = obs_t
                    if args.deterministic:
                        mean, _std = trainer.actor(feat)  # type: ignore[union-attr]
                        action_norm = torch.tanh(mean)
                    else:
                        action_norm, _logp = trainer.actor.sample(feat)  # type: ignore[union-attr]
                elif actor_input == "obs_gru":
                    feat = obs_t
                    if args.deterministic:
                        mean, _std, actor_h = trainer.actor.step(feat, actor_h)  # type: ignore[union-attr]
                        action_norm = torch.tanh(mean)
                    else:
                        action_norm, _logp, actor_h = trainer.actor.sample_step(feat, actor_h)  # type: ignore[union-attr]
                elif actor_input == "obs_sincos":
                    feat = append_angle_sincos_features(
                        obs_raw_deg=obs_raw_t,
                        obs_norm=obs_t,
                        angle_deg_indices=trainer.angle_deg_indices,
                    )
                    if args.deterministic:
                        mean, _std = trainer.actor(feat)  # type: ignore[union-attr]
                        action_norm = torch.tanh(mean)
                    else:
                        action_norm, _logp = trainer.actor.sample(feat)  # type: ignore[union-attr]
                elif actor_input == "obs_sincos_gru":
                    feat = append_angle_sincos_features(
                        obs_raw_deg=obs_raw_t,
                        obs_norm=obs_t,
                        angle_deg_indices=trainer.angle_deg_indices,
                    )
                    if args.deterministic:
                        mean, _std, actor_h = trainer.actor.step(feat, actor_h)  # type: ignore[union-attr]
                        action_norm = torch.tanh(mean)
                    else:
                        action_norm, _logp, actor_h = trainer.actor.sample_step(feat, actor_h)  # type: ignore[union-attr]
                elif actor_input == "obs_sincos_track":
                    feat = append_angle_sincos_features(
                        obs_raw_deg=obs_raw_t,
                        obs_norm=obs_t,
                        angle_deg_indices=trainer.angle_deg_indices,
                    )
                    track = nav_tracking_features(obs_raw_t)
                    feat = torch.cat([feat, track], dim=-1)
                    if args.deterministic:
                        mean, _std = trainer.actor(feat)  # type: ignore[union-attr]
                        action_norm = torch.tanh(mean)
                    else:
                        action_norm, _logp = trainer.actor.sample(feat)  # type: ignore[union-attr]
                elif actor_input == "obs_sincos_track_gru":
                    feat = append_angle_sincos_features(
                        obs_raw_deg=obs_raw_t,
                        obs_norm=obs_t,
                        angle_deg_indices=trainer.angle_deg_indices,
                    )
                    track = nav_tracking_features(obs_raw_t)
                    feat = torch.cat([feat, track], dim=-1)
                    if args.deterministic:
                        mean, _std, actor_h = trainer.actor.step(feat, actor_h)  # type: ignore[union-attr]
                        action_norm = torch.tanh(mean)
                    else:
                        action_norm, _logp, actor_h = trainer.actor.sample_step(feat, actor_h)  # type: ignore[union-attr]
                elif actor_input == "obs_sincos_track_vis":
                    assert embed0 is not None
                    feat = append_angle_sincos_features(
                        obs_raw_deg=obs_raw_t,
                        obs_norm=obs_t,
                        angle_deg_indices=trainer.angle_deg_indices,
                    )
                    track = nav_tracking_features(obs_raw_t)
                    vis_dim = int(getattr(trainer.wm.encoder, "visual_embed_dim", 0))
                    if vis_dim <= 0:
                        raise ValueError(
                            "actor_input='obs_sincos_track_vis' requires a visual encoder"
                        )
                    vis_embed = embed0[:, -vis_dim:]
                    feat = torch.cat([feat, track, vis_embed], dim=-1)
                    if args.deterministic:
                        mean, _std = trainer.actor(feat)  # type: ignore[union-attr]
                        action_norm = torch.tanh(mean)
                    else:
                        action_norm, _logp = trainer.actor.sample(feat)  # type: ignore[union-attr]
                elif actor_input == "obs_sincos_track_vis_gru":
                    assert embed0 is not None
                    feat = append_angle_sincos_features(
                        obs_raw_deg=obs_raw_t,
                        obs_norm=obs_t,
                        angle_deg_indices=trainer.angle_deg_indices,
                    )
                    track = nav_tracking_features(obs_raw_t)
                    vis_dim = int(getattr(trainer.wm.encoder, "visual_embed_dim", 0))
                    if vis_dim <= 0:
                        raise ValueError(
                            "actor_input='obs_sincos_track_vis_gru' requires a visual encoder"
                        )
                    vis_embed = embed0[:, -vis_dim:]
                    feat = torch.cat([feat, track, vis_embed], dim=-1)
                    if args.deterministic:
                        mean, _std, actor_h = trainer.actor.step(feat, actor_h)  # type: ignore[union-attr]
                        action_norm = torch.tanh(mean)
                    else:
                        action_norm, _logp, actor_h = trainer.actor.sample_step(feat, actor_h)  # type: ignore[union-attr]
                elif actor_input == "embed":
                    assert embed0 is not None
                    feat = embed0
                    if args.deterministic:
                        mean, _std = trainer.actor(feat)  # type: ignore[union-attr]
                        action_norm = torch.tanh(mean)
                    else:
                        action_norm, _logp = trainer.actor.sample(feat)  # type: ignore[union-attr]
                elif actor_input == "embed_sincos":
                    assert embed0 is not None
                    ang = angle_sincos_features(
                        obs_raw_t, angle_deg_indices=trainer.angle_deg_indices
                    )
                    feat = torch.cat([embed0, ang], dim=-1)
                    if args.deterministic:
                        mean, _std = trainer.actor(feat)  # type: ignore[union-attr]
                        action_norm = torch.tanh(mean)
                    else:
                        action_norm, _logp = trainer.actor.sample(feat)  # type: ignore[union-attr]
                elif actor_input == "embed_sincos_track":
                    assert embed0 is not None
                    ang = angle_sincos_features(
                        obs_raw_t, angle_deg_indices=trainer.angle_deg_indices
                    )
                    track = nav_tracking_features(obs_raw_t)
                    feat = torch.cat([embed0, ang, track], dim=-1)
                    if args.deterministic:
                        mean, _std = trainer.actor(feat)  # type: ignore[union-attr]
                        action_norm = torch.tanh(mean)
                    else:
                        action_norm, _logp = trainer.actor.sample(feat)  # type: ignore[union-attr]
                elif actor_input == "embed_gru":
                    assert embed0 is not None
                    feat = embed0
                    if args.deterministic:
                        mean, _std, actor_h = trainer.actor.step(feat, actor_h)  # type: ignore[union-attr]
                        action_norm = torch.tanh(mean)
                    else:
                        action_norm, _logp, actor_h = trainer.actor.sample_step(feat, actor_h)  # type: ignore[union-attr]
                elif actor_input == "embed_sincos_gru":
                    assert embed0 is not None
                    ang = angle_sincos_features(
                        obs_raw_t, angle_deg_indices=trainer.angle_deg_indices
                    )
                    feat = torch.cat([embed0, ang], dim=-1)
                    if args.deterministic:
                        mean, _std, actor_h = trainer.actor.step(feat, actor_h)  # type: ignore[union-attr]
                        action_norm = torch.tanh(mean)
                    else:
                        action_norm, _logp, actor_h = trainer.actor.sample_step(feat, actor_h)  # type: ignore[union-attr]
                elif actor_input == "embed_sincos_track_gru":
                    assert embed0 is not None
                    ang = angle_sincos_features(
                        obs_raw_t, angle_deg_indices=trainer.angle_deg_indices
                    )
                    track = nav_tracking_features(obs_raw_t)
                    feat = torch.cat([embed0, ang, track], dim=-1)
                    if args.deterministic:
                        mean, _std, actor_h = trainer.actor.step(feat, actor_h)  # type: ignore[union-attr]
                        action_norm = torch.tanh(mean)
                    else:
                        action_norm, _logp, actor_h = trainer.actor.sample_step(feat, actor_h)  # type: ignore[union-attr]
                else:
                    assert state is not None
                    feat = trainer.wm.feat(state)
                    if args.deterministic:
                        mean, _std = trainer.actor(feat)  # type: ignore[union-attr]
                        action_norm = torch.tanh(mean)
                    else:
                        action_norm, _logp = trainer.actor.sample(feat)  # type: ignore[union-attr]
            action_np = action_norm.squeeze(0).cpu().numpy().astype(np.float32, copy=False)
            action_env = _unnormalize_action(action_np, spec_low, spec_high)

            if expert_ctrl is not None:
                # DAgger-style labeling: store expert action for the *current* observation.
                # This does not leak privileged information: the scripted controllers use only
                # pilot-observable instruments/mission/ILS signals.
                expert_env = expert_ctrl.step(obs)
                expert_np = _normalize_action(expert_env, spec_low, spec_high)
                expert_actions.append(expert_np.astype(np.float32, copy=False))

            next_obs, reward, terminated, truncated, _info = env.step(action_env)
            collector_truncated = (steps + 1) >= max_steps
            done = bool(terminated or truncated or collector_truncated)

            actions.append(action_np.astype(np.float32, copy=False))
            rewards.append(float(reward))
            dones.append(done)

            next_vec = _flatten_obs(next_obs)
            obs_vecs.append(next_vec)
            if include_visual:
                v = np.asarray(next_obs["visual"], dtype=np.float32)
                v = _downsample_visual(v, visual_downsample).astype(np.float16)
                visuals.append(v)

            # Update latent state using the true next observation.
            next_raw = torch.from_numpy(next_vec).to(device).float().unsqueeze(0)
            next_t = (next_raw - trainer.obs_mean.unsqueeze(0)) / trainer.obs_std.unsqueeze(0)
            next_t = _apply_norm_clip(next_t, trainer.cfg.obs_norm_clip)
            if include_visual:
                v1 = np.asarray(next_obs["visual"], dtype=np.float32)
                v1 = _downsample_visual(v1, visual_downsample)
                v1 = np.clip(v1, -10.0, 10.0).astype(np.float32, copy=False)
                vis_next = torch.from_numpy(v1).to(device).float().unsqueeze(0)
                vis_next = (
                    vis_next - trainer.visual_mean.view(1, 1, 1, -1)
                ) / trainer.visual_std.view(1, 1, 1, -1)
                vis_next = _apply_norm_clip(vis_next, trainer.cfg.visual_norm_clip)
                vis_next = vis_next.reshape(1, -1)
            else:
                vis_next = None
            embed_next = None
            if actor_input not in (
                "obs",
                "obs_gru",
                "obs_sincos",
                "obs_sincos_gru",
                "obs_sincos_track",
                "obs_sincos_track_gru",
            ):
                with torch.no_grad():
                    embed_next = (
                        trainer.wm.encoder(next_t, vis_next)
                        if vis_next is not None
                        else trainer.wm.encoder(next_t)
                    )

            a_t = torch.from_numpy(action_np).to(device).float().unsqueeze(0)
            with torch.no_grad():
                if actor_input == "rssm":
                    assert state is not None
                    assert embed_next is not None
                    state, _prior, _post = trainer.wm.rssm.obs_step(
                        state, a_t, embed_next, deterministic=deterministic_state
                    )
                if actor_input not in (
                    "obs",
                    "obs_gru",
                    "obs_sincos",
                    "obs_sincos_gru",
                    "obs_sincos_track",
                    "obs_sincos_track_gru",
                ):
                    assert embed_next is not None
                    embed0 = embed_next
                obs_raw_t = next_raw
                if actor_input in (
                    "obs",
                    "obs_gru",
                    "obs_sincos",
                    "obs_sincos_gru",
                    "obs_sincos_track",
                    "obs_sincos_track_gru",
                    "obs_sincos_track_vis",
                    "obs_sincos_track_vis_gru",
                ):
                    obs_t = next_t

            obs = next_obs
            steps += 1

        episode = Episode(
            obs_vec=np.stack(obs_vecs, axis=0),
            actions=np.stack(actions, axis=0)
            if actions
            else np.zeros((0, dataset.spec.action_dim), dtype=np.float32),
            rewards=np.asarray(rewards, dtype=np.float32),
            dones=np.asarray(dones, dtype=np.bool_),
            visual=(np.stack(visuals, axis=0) if visuals else None),
            expert_actions=(np.stack(expert_actions, axis=0) if expert_actions else None),
        )
        path = store.add(episode, seed=int(seed))
        print(f"[online] collected steps={steps} done={done} -> {path}")
        return path

    steps = int(args.steps)
    for step in range(1, steps + 1):
        if curriculum is not None:
            idx = _select_curriculum_stage(curriculum, step, key="until_steps")
            if active_stage_idx != idx:
                env.set_randomization_overrides(_get_stage_overrides(curriculum[idx]))
                active_stage_idx = idx
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
            print(f"[online-train] step={step}/{steps} {msg}")

        collect_every = int(args.collect_every)
        if collect_every > 0 and step % collect_every == 0:
            for i in range(int(args.collect_episodes)):
                ep_seed = int(args.seed) + step * 1000 + i
                collect_one_episode(ep_seed)
            dataset.refresh()
            print(f"[online] dataset refreshed: episodes={len(dataset)}")

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
