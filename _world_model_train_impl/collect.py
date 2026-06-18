"""Offline dataset collection command for world-model training."""

from __future__ import annotations

import argparse

import numpy as np
import torch

from _world_model_train_impl.bootstrap import configure_repo_imports
from _world_model_train_impl.common import (
    _apply_env_overrides,
    _apply_norm_clip,
    _build_world_model,
    _downsample_visual,
    _flatten_obs,
    _get_stage_overrides,
    _load_curriculum,
    _normalize_action,
    _resolve_visual_encoder_settings,
    _select_curriculum_stage,
    _unnormalize_action,
)

configure_repo_imports()

from gym_envs.universal_env import UniversalEnv  # noqa: E402
from python.rl.control.scripted_stable_flight import ScriptedStableFlightController  # noqa: E402
from python.rl.control.scripted_takeoff import ScriptedTakeoffController, scripted_takeoff_action  # noqa: E402
from python.world_model.features import (  # noqa: E402
    DEFAULT_ANGLE_DEG_INDICES,
    angle_sincos_features,
    append_angle_sincos_features,
    nav_tracking_features,
)
from python.world_model.networks import Actor, GRUActor  # noqa: E402
from python.world_model.replay import DatasetSpec, Episode, EpisodeStore  # noqa: E402
from python.world_model.utils import DeviceConfig, set_seed  # noqa: E402


def collect_dataset(args: argparse.Namespace) -> None:
    set_seed(int(args.seed))
    rng = np.random.default_rng(int(args.seed))

    env = UniversalEnv(
        args.scenario,
        include_visual=bool(args.include_visual),
        include_proprio=bool(getattr(args, "include_proprio", False)),
        action_mode=str(args.action_mode),
    )
    _apply_env_overrides(env, args)
    curriculum = None
    if getattr(args, "curriculum", None) and not bool(getattr(args, "no_randomization", False)):
        curriculum = _load_curriculum(str(args.curriculum))

    # Build dataset spec from a single reset.
    obs, _ = env.reset(seed=int(args.seed))
    obs_vec0 = _flatten_obs(obs)
    visual_shape = None
    if args.include_visual:
        v0 = np.asarray(obs["visual"], dtype=np.float32)
        v0 = _downsample_visual(v0, int(args.visual_downsample))
        visual_shape = tuple(int(x) for x in v0.shape)

    try:
        action_low = np.asarray(env.action_space.low, dtype=np.float32).reshape(-1)
        action_high = np.asarray(env.action_space.high, dtype=np.float32).reshape(-1)
    except Exception:
        action_low = None
        action_high = None

    spec = DatasetSpec(
        action_dim=int(env.action_space.shape[0]),
        obs_vec_dim=int(obs_vec0.shape[0]),
        action_low=action_low,
        action_high=action_high,
        visual_shape=visual_shape,
    )
    store = EpisodeStore(args.out_dir, spec)

    # Optional DAgger-style student policy for collecting trajectories that follow the student's
    # state distribution while labeling each step with a scripted (expert) action.
    student_device = None
    student_wm = None
    student_actor = None
    student_actor_input = None
    student_obs_mean = None
    student_obs_std = None
    student_visual_mean = None
    student_visual_std = None
    student_obs_norm_clip = None
    student_visual_norm_clip = None
    dagger_teacher_prob = float(getattr(args, "dagger_teacher_prob", 0.0))
    dagger_teacher_prob = float(np.clip(dagger_teacher_prob, 0.0, 1.0))
    student_stochastic = bool(getattr(args, "student_stochastic", False))
    student_deterministic_state = True

    if str(args.policy) in (
        "dagger_scripted_takeoff",
        "dagger_scripted_stable_flight",
        "dagger_scripted_waypoint",
    ):
        if not getattr(args, "student_checkpoint", None):
            raise ValueError("--student_checkpoint is required for DAgger policies")
        if spec.action_low is None or spec.action_high is None:
            raise ValueError("DAgger policy requires env.action_space low/high to be defined")

        student_device = DeviceConfig(getattr(args, "device", "cpu")).torch_device()
        try:
            ckpt = torch.load(
                str(args.student_checkpoint), map_location=student_device, weights_only=False
            )
        except TypeError:
            ckpt = torch.load(str(args.student_checkpoint), map_location=student_device)
        if not isinstance(ckpt, dict):
            raise ValueError("student_checkpoint must be a dict-like checkpoint")
        ckpt_spec = ckpt.get("spec", {}) if isinstance(ckpt.get("spec", {}), dict) else {}
        ckpt_action_dim = int(ckpt_spec.get("action_dim", spec.action_dim))
        ckpt_obs_vec_dim = int(ckpt_spec.get("obs_vec_dim", spec.obs_vec_dim))
        if ckpt_action_dim != int(spec.action_dim):
            raise ValueError(
                f"student_checkpoint action_dim={ckpt_action_dim} does not match env action_dim={spec.action_dim}"
            )
        if ckpt_obs_vec_dim != int(spec.obs_vec_dim):
            raise ValueError(
                f"student_checkpoint obs_vec_dim={ckpt_obs_vec_dim} does not match env obs_vec_dim={spec.obs_vec_dim}"
            )
        ckpt_visual_shape = ckpt_spec.get("visual_shape", None)
        if args.include_visual:
            if ckpt_visual_shape is None:
                raise ValueError(
                    "student_checkpoint was trained without visual, but --include_visual is set"
                )
            # Validate downsample factor matches the checkpoint visual shape.
            v0_raw = np.asarray(obs["visual"], dtype=np.float32)
            v0_ds = _downsample_visual(v0_raw, int(args.visual_downsample))
            if tuple(int(x) for x in v0_ds.shape) != tuple(
                int(x) for x in np.asarray(ckpt_visual_shape).reshape(-1).tolist()
            ):
                raise ValueError(
                    f"--visual_downsample={int(args.visual_downsample)} yields visual_shape={tuple(int(x) for x in v0_ds.shape)}, "
                    f"but student_checkpoint expects visual_shape={tuple(int(x) for x in np.asarray(ckpt_visual_shape).reshape(-1).tolist())}. "
                    "Use the same downsample factor as the checkpoint training dataset."
                )
        else:
            if (
                ckpt_visual_shape is not None
                and tuple(int(x) for x in np.asarray(ckpt_visual_shape).reshape(-1).tolist())[0]
                >= 0
            ):
                raise ValueError(
                    "student_checkpoint expects visual, but --include_visual is not set"
                )

        cfg = ckpt.get("cfg", {}) if isinstance(ckpt.get("cfg", {}), dict) else {}
        student_actor_input = str(cfg.get("actor_input", "rssm"))
        student_deterministic_state = bool(cfg.get("bc_deterministic_state", True))
        student_obs_norm_clip = cfg.get("obs_norm_clip", None)
        student_visual_norm_clip = cfg.get("visual_norm_clip", None)
        student_visual_encoder_type, student_visual_cnn_channels = _resolve_visual_encoder_settings(
            ckpt_cfg=cfg
        )
        try:
            student_angle_deg_indices = tuple(
                int(x) for x in cfg.get("angle_deg_indices", DEFAULT_ANGLE_DEG_INDICES)
            )
        except Exception:
            student_angle_deg_indices = DEFAULT_ANGLE_DEG_INDICES

        student_wm = _build_world_model(
            action_dim=spec.action_dim,
            obs_vec_dim=spec.obs_vec_dim,
            visual_shape=spec.visual_shape,
            visual_encoder_type=student_visual_encoder_type,
            visual_cnn_channels=student_visual_cnn_channels,
        ).to(student_device)
        if "world_model" not in ckpt:
            raise ValueError("student_checkpoint missing 'world_model' weights")
        student_wm.load_state_dict(ckpt["world_model"])
        student_wm.eval()

        rssm_feat_dim = student_wm.rssm.deter_dim + student_wm.rssm.stoch_dim
        if student_actor_input in ("obs", "obs_gru"):
            actor_feat_dim = int(spec.obs_vec_dim)
        elif student_actor_input in ("obs_sincos", "obs_sincos_gru"):
            actor_feat_dim = int(spec.obs_vec_dim) + 2 * len(student_angle_deg_indices)
        elif student_actor_input in ("obs_sincos_track", "obs_sincos_track_gru"):
            actor_feat_dim = int(spec.obs_vec_dim) + 2 * len(student_angle_deg_indices) + 8
        elif student_actor_input in ("obs_sincos_track_vis", "obs_sincos_track_vis_gru"):
            if student_wm.encoder.visual is None:
                raise ValueError(
                    "student_checkpoint actor_input='obs_sincos_track_vis*' requires visual"
                )
            actor_feat_dim = (
                int(spec.obs_vec_dim)
                + 2 * len(student_angle_deg_indices)
                + 8
                + int(getattr(student_wm.encoder, "visual_embed_dim", 0))
            )
        elif student_actor_input in ("embed_sincos", "embed_sincos_gru"):
            actor_feat_dim = int(student_wm.encoder.embed_dim) + 2 * len(student_angle_deg_indices)
        elif student_actor_input in ("embed_sincos_track", "embed_sincos_track_gru"):
            actor_feat_dim = (
                int(student_wm.encoder.embed_dim) + 2 * len(student_angle_deg_indices) + 8
            )
        elif student_actor_input in ("embed", "embed_gru"):
            actor_feat_dim = int(student_wm.encoder.embed_dim)
        else:
            actor_feat_dim = int(rssm_feat_dim)
        if student_actor_input in (
            "embed_gru",
            "embed_sincos_gru",
            "embed_sincos_track_gru",
            "obs_gru",
            "obs_sincos_gru",
            "obs_sincos_track_gru",
            "obs_sincos_track_vis_gru",
        ):
            student_actor = GRUActor(input_dim=actor_feat_dim, action_dim=spec.action_dim).to(
                student_device
            )
        else:
            student_actor = Actor(feat_dim=actor_feat_dim, action_dim=spec.action_dim).to(
                student_device
            )
        if "actor" not in ckpt:
            raise ValueError("student_checkpoint missing 'actor' weights")
        student_actor.load_state_dict(ckpt["actor"])
        student_actor.eval()

        obs_mean = ckpt.get("obs_mean", None)
        obs_std = ckpt.get("obs_std", None)
        if obs_mean is None or obs_std is None:
            raise ValueError("student_checkpoint missing obs_mean/obs_std (required for inference)")
        student_obs_mean = (
            obs_mean.to(student_device).float()
            if isinstance(obs_mean, torch.Tensor)
            else torch.from_numpy(np.asarray(obs_mean, dtype=np.float32)).to(student_device)
        )
        student_obs_std = (
            obs_std.to(student_device).float()
            if isinstance(obs_std, torch.Tensor)
            else torch.from_numpy(np.asarray(obs_std, dtype=np.float32)).to(student_device)
        )

        if args.include_visual:
            vmean = ckpt.get("visual_mean", None)
            vstd = ckpt.get("visual_std", None)
            if vmean is None or vstd is None:
                raise ValueError(
                    "student_checkpoint missing visual_mean/visual_std (required when --include_visual)"
                )
            student_visual_mean = (
                vmean.to(student_device).float()
                if isinstance(vmean, torch.Tensor)
                else torch.from_numpy(np.asarray(vmean, dtype=np.float32)).to(student_device)
            )
            student_visual_std = (
                vstd.to(student_device).float()
                if isinstance(vstd, torch.Tensor)
                else torch.from_numpy(np.asarray(vstd, dtype=np.float32)).to(student_device)
            )

    active_stage_idx = None
    saved = 0
    for ep_idx in range(int(args.episodes)):
        seed = int(args.seed) + ep_idx
        if curriculum is not None:
            idx = _select_curriculum_stage(curriculum, ep_idx, key="until_episodes")
            if active_stage_idx != idx:
                env.set_randomization_overrides(_get_stage_overrides(curriculum[idx]))
                active_stage_idx = idx
        obs, _ = env.reset(seed=seed)
        obs_vecs = [_flatten_obs(obs)]
        visuals = []
        if args.include_visual:
            v = np.asarray(obs["visual"], dtype=np.float32)
            v = _downsample_visual(v, int(args.visual_downsample)).astype(np.float16)
            visuals.append(v)

        actions = []
        expert_actions = []
        rewards = []
        dones = []
        last_info: dict = {}
        on_ground_steps = 0
        on_runway_geom_steps = 0
        max_abs_runway_cross_m = 0.0

        # Student policy internal state (DAgger only).
        student_embed0 = None
        student_state = None
        student_h = None
        takeoff_ctrl = None
        stable_ctrl = None
        if str(args.policy) in (
            "dagger_scripted_takeoff",
            "dagger_scripted_stable_flight",
            "dagger_scripted_waypoint",
        ):
            assert student_device is not None
            assert student_wm is not None
            assert student_actor is not None
            assert student_obs_mean is not None
            assert student_obs_std is not None
            vec0 = obs_vecs[-1]
            obs_t = (
                torch.from_numpy(np.asarray(vec0, dtype=np.float32))
                .to(student_device)
                .float()
                .unsqueeze(0)
            )
            obs_t = (obs_t - student_obs_mean.view(1, -1)) / student_obs_std.view(1, -1)
            obs_t = _apply_norm_clip(obs_t, student_obs_norm_clip)
            if args.include_visual:
                assert student_visual_mean is not None and student_visual_std is not None
                v0 = np.asarray(obs["visual"], dtype=np.float32)
                v0 = _downsample_visual(v0, int(args.visual_downsample))
                v0 = np.clip(v0, -10.0, 10.0).astype(np.float32, copy=False)
                vis_t = torch.from_numpy(v0).to(student_device).float().unsqueeze(0)  # (1,H,W,C)
                vis_t = (vis_t - student_visual_mean.view(1, 1, 1, -1)) / student_visual_std.view(
                    1, 1, 1, -1
                )
                vis_t = _apply_norm_clip(vis_t, student_visual_norm_clip)
                vis_t = vis_t.reshape(1, -1)
            else:
                vis_t = None
            with torch.no_grad():
                if str(student_actor_input) in (
                    "rssm",
                    "embed",
                    "embed_gru",
                    "embed_sincos",
                    "embed_sincos_gru",
                    "embed_sincos_track",
                    "embed_sincos_track_gru",
                    "obs_sincos_track_vis",
                    "obs_sincos_track_vis_gru",
                ):
                    student_embed0 = (
                        student_wm.encoder(obs_t, vis_t)
                        if vis_t is not None
                        else student_wm.encoder(obs_t)
                    )
                    if str(student_actor_input) == "rssm":
                        student_state, _ = student_wm.rssm.observe_init(
                            student_embed0, deterministic=student_deterministic_state
                        )
                    elif str(student_actor_input) in (
                        "embed_gru",
                        "embed_sincos_gru",
                        "embed_sincos_track_gru",
                        "obs_sincos_track_vis_gru",
                    ):
                        student_h = student_actor.init_h(batch_size=1, device=student_device)  # type: ignore[union-attr]
                elif str(student_actor_input) in (
                    "obs_gru",
                    "obs_sincos_gru",
                    "obs_sincos_track_gru",
                ):
                    student_h = student_actor.init_h(batch_size=1, device=student_device)  # type: ignore[union-attr]

        max_steps = int(args.max_steps) if args.max_steps is not None else 10**9
        if str(args.policy) in (
            "scripted_stable_flight",
            "dagger_scripted_stable_flight",
            "scripted_waypoint",
            "dagger_scripted_waypoint",
        ):
            stable_ctrl = ScriptedStableFlightController(
                action_dim=int(spec.action_dim),
                dt=float(getattr(env.sim, "get_time_step", lambda: 0.05)()),
            )
            stable_ctrl.reset(obs)
        if str(args.policy) in ("scripted_takeoff", "dagger_scripted_takeoff"):
            takeoff_ctrl = ScriptedTakeoffController(
                action_dim=int(spec.action_dim),
                dt=float(getattr(env.sim, "get_time_step", lambda: 0.05)()),
            )
            takeoff_ctrl.reset(obs)
        done = False
        steps = 0
        while not done and steps < max_steps:
            # --- Teacher (scripted) action (expert label) ---
            teacher_action_env = None
            if str(args.policy) in ("scripted_takeoff", "dagger_scripted_takeoff"):
                if takeoff_ctrl is not None:
                    teacher_action_env = takeoff_ctrl.step(obs)
                else:
                    teacher_action_env = scripted_takeoff_action(
                        obs, action_dim=int(spec.action_dim)
                    )
            elif stable_ctrl is not None:
                teacher_action_env = stable_ctrl.step(obs)

            # --- Choose executed action ---
            if str(args.policy) == "random":
                exec_action_env = env.action_space.sample()
            elif str(args.policy) == "scripted_takeoff":
                assert teacher_action_env is not None
                exec_action_env = teacher_action_env
            elif str(args.policy) == "scripted_stable_flight":
                assert teacher_action_env is not None
                exec_action_env = teacher_action_env
            elif str(args.policy) == "scripted_waypoint":
                assert teacher_action_env is not None
                exec_action_env = teacher_action_env
            elif str(args.policy) in (
                "dagger_scripted_takeoff",
                "dagger_scripted_stable_flight",
                "dagger_scripted_waypoint",
            ):
                assert teacher_action_env is not None
                assert student_device is not None
                assert student_wm is not None
                assert student_actor is not None
                if str(student_actor_input) == "rssm":
                    assert student_state is not None
                    feat = student_wm.feat(student_state)
                elif str(student_actor_input) in (
                    "obs",
                    "obs_gru",
                    "obs_sincos",
                    "obs_sincos_gru",
                    "obs_sincos_track",
                    "obs_sincos_track_gru",
                    "obs_sincos_track_vis",
                    "obs_sincos_track_vis_gru",
                ):
                    vec_cur = obs_vecs[-1]
                    obs_raw = (
                        torch.from_numpy(np.asarray(vec_cur, dtype=np.float32))
                        .to(student_device)
                        .float()
                        .unsqueeze(0)
                    )
                    obs_t = (obs_raw - student_obs_mean.view(1, -1)) / student_obs_std.view(1, -1)
                    obs_t = _apply_norm_clip(obs_t, student_obs_norm_clip)
                    if str(student_actor_input) in (
                        "obs_sincos",
                        "obs_sincos_gru",
                        "obs_sincos_track",
                        "obs_sincos_track_gru",
                        "obs_sincos_track_vis",
                        "obs_sincos_track_vis_gru",
                    ):
                        feat = append_angle_sincos_features(
                            obs_raw_deg=obs_raw,
                            obs_norm=obs_t,
                            angle_deg_indices=student_angle_deg_indices,
                        )
                    else:
                        feat = obs_t
                    if str(student_actor_input) in (
                        "obs_sincos_track",
                        "obs_sincos_track_gru",
                        "obs_sincos_track_vis",
                        "obs_sincos_track_vis_gru",
                    ):
                        track = nav_tracking_features(obs_raw)
                        feat = torch.cat([feat, track], dim=-1)
                    if str(student_actor_input) in (
                        "obs_sincos_track_vis",
                        "obs_sincos_track_vis_gru",
                    ):
                        assert student_embed0 is not None
                        vis_dim = int(getattr(student_wm.encoder, "visual_embed_dim", 0))
                        if vis_dim <= 0:
                            raise ValueError(
                                "student_actor_input='obs_sincos_track_vis*' requires a visual encoder"
                            )
                        vis_embed = student_embed0[:, -vis_dim:]
                        feat = torch.cat([feat, vis_embed], dim=-1)
                elif str(student_actor_input) in ("embed_sincos", "embed_sincos_gru"):
                    assert student_embed0 is not None
                    vec_cur = obs_vecs[-1]
                    obs_raw = (
                        torch.from_numpy(np.asarray(vec_cur, dtype=np.float32))
                        .to(student_device)
                        .float()
                        .unsqueeze(0)
                    )
                    ang = angle_sincos_features(
                        obs_raw, angle_deg_indices=student_angle_deg_indices
                    )
                    feat = torch.cat([student_embed0, ang], dim=-1)
                elif str(student_actor_input) in ("embed_sincos_track", "embed_sincos_track_gru"):
                    assert student_embed0 is not None
                    vec_cur = obs_vecs[-1]
                    obs_raw = (
                        torch.from_numpy(np.asarray(vec_cur, dtype=np.float32))
                        .to(student_device)
                        .float()
                        .unsqueeze(0)
                    )
                    ang = angle_sincos_features(
                        obs_raw, angle_deg_indices=student_angle_deg_indices
                    )
                    track = nav_tracking_features(obs_raw)
                    feat = torch.cat([student_embed0, ang, track], dim=-1)
                else:
                    assert student_embed0 is not None
                    feat = student_embed0
                with torch.no_grad():
                    if student_stochastic:
                        if str(student_actor_input) in (
                            "embed_gru",
                            "embed_sincos_gru",
                            "embed_sincos_track_gru",
                        ):
                            a_norm_t, _logp, student_h = student_actor.sample_step(feat, student_h)  # type: ignore[union-attr]
                        elif str(student_actor_input) in (
                            "obs_gru",
                            "obs_sincos_gru",
                            "obs_sincos_track_gru",
                            "obs_sincos_track_vis_gru",
                        ):
                            a_norm_t, _logp, student_h = student_actor.sample_step(feat, student_h)  # type: ignore[union-attr]
                        else:
                            a_norm_t, _logp = student_actor.sample(feat)  # type: ignore[union-attr]
                    else:
                        if str(student_actor_input) in (
                            "embed_gru",
                            "embed_sincos_gru",
                            "embed_sincos_track_gru",
                        ):
                            mean, _std, student_h = student_actor.step(feat, student_h)  # type: ignore[union-attr]
                            a_norm_t = torch.tanh(mean)
                        elif str(student_actor_input) in (
                            "obs_gru",
                            "obs_sincos_gru",
                            "obs_sincos_track_gru",
                            "obs_sincos_track_vis_gru",
                        ):
                            mean, _std, student_h = student_actor.step(feat, student_h)  # type: ignore[union-attr]
                            a_norm_t = torch.tanh(mean)
                        else:
                            mean, _std = student_actor(feat)  # type: ignore[union-attr]
                            a_norm_t = torch.tanh(mean)
                student_action_norm = (
                    a_norm_t.squeeze(0).detach().cpu().numpy().astype(np.float32, copy=False)
                )
                student_action_env = _unnormalize_action(
                    student_action_norm, spec.action_low, spec.action_high
                )
                if float(rng.random()) < dagger_teacher_prob:
                    exec_action_env = teacher_action_env
                else:
                    exec_action_env = student_action_env
            else:
                raise ValueError(f"Unknown collect policy: {args.policy}")

            # Normalize executed action for storage / model training.
            if spec.action_low is not None and spec.action_high is not None:
                exec_action = _normalize_action(exec_action_env, spec.action_low, spec.action_high)
            else:
                exec_action = np.asarray(exec_action_env, dtype=np.float32)

            if (
                teacher_action_env is not None
                and spec.action_low is not None
                and spec.action_high is not None
            ):
                expert_action = _normalize_action(
                    teacher_action_env, spec.action_low, spec.action_high
                )
            elif teacher_action_env is not None:
                expert_action = np.asarray(teacher_action_env, dtype=np.float32)
            else:
                expert_action = None

            next_obs, reward, terminated, truncated, info = env.step(exec_action_env)
            if isinstance(info, dict):
                last_info = info
                try:
                    if float(info.get("on_ground", 0.0)) > 0.5:
                        on_ground_steps += 1
                        max_abs_runway_cross_m = max(
                            max_abs_runway_cross_m, abs(float(info.get("runway_cross_m", 0.0)))
                        )
                        if float(info.get("on_runway_geom", 0.0)) > 0.5:
                            on_runway_geom_steps += 1
                except Exception:
                    pass
            collector_truncated = (steps + 1) >= max_steps
            done = bool(terminated or truncated or collector_truncated)

            actions.append(np.asarray(exec_action, dtype=np.float32))
            if expert_action is not None:
                expert_actions.append(np.asarray(expert_action, dtype=np.float32))
            rewards.append(float(reward))
            dones.append(done)

            obs = next_obs
            obs_vecs.append(_flatten_obs(next_obs))
            if args.include_visual:
                v = np.asarray(next_obs["visual"], dtype=np.float32)
                v = _downsample_visual(v, int(args.visual_downsample)).astype(np.float16)
                visuals.append(v)

            # Advance the student policy internal state (DAgger).
            if str(args.policy) in (
                "dagger_scripted_takeoff",
                "dagger_scripted_stable_flight",
                "dagger_scripted_waypoint",
            ):
                assert student_device is not None
                assert student_wm is not None
                assert student_obs_mean is not None and student_obs_std is not None
                next_vec = obs_vecs[-1]
                obs_t = (
                    torch.from_numpy(np.asarray(next_vec, dtype=np.float32))
                    .to(student_device)
                    .float()
                    .unsqueeze(0)
                )
                obs_t = (obs_t - student_obs_mean.view(1, -1)) / student_obs_std.view(1, -1)
                obs_t = _apply_norm_clip(obs_t, student_obs_norm_clip)
                if args.include_visual:
                    assert student_visual_mean is not None and student_visual_std is not None
                    v1 = np.asarray(next_obs["visual"], dtype=np.float32)
                    v1 = _downsample_visual(v1, int(args.visual_downsample))
                    v1 = np.clip(v1, -10.0, 10.0).astype(np.float32, copy=False)
                    vis_t = torch.from_numpy(v1).to(student_device).float().unsqueeze(0)
                    vis_t = (
                        vis_t - student_visual_mean.view(1, 1, 1, -1)
                    ) / student_visual_std.view(1, 1, 1, -1)
                    vis_t = _apply_norm_clip(vis_t, student_visual_norm_clip)
                    vis_t = vis_t.reshape(1, -1)
                else:
                    vis_t = None
                with torch.no_grad():
                    if str(student_actor_input) in (
                        "rssm",
                        "embed",
                        "embed_gru",
                        "embed_sincos",
                        "embed_sincos_gru",
                        "embed_sincos_track",
                        "embed_sincos_track_gru",
                        "obs_sincos_track_vis",
                        "obs_sincos_track_vis_gru",
                    ):
                        embed_next = (
                            student_wm.encoder(obs_t, vis_t)
                            if vis_t is not None
                            else student_wm.encoder(obs_t)
                        )
                        if str(student_actor_input) == "rssm":
                            assert student_state is not None
                            a_t = (
                                torch.from_numpy(exec_action)
                                .to(student_device)
                                .float()
                                .unsqueeze(0)
                            )
                            student_state, _prior, _post = student_wm.rssm.obs_step(
                                student_state,
                                a_t,
                                embed_next,
                                deterministic=student_deterministic_state,
                            )
                        student_embed0 = embed_next

            steps += 1

        success_flag = None
        try:
            ms = last_info.get("mission_status", None)
            if ms is not None:
                ms_arr = np.asarray(ms, dtype=np.float32).reshape(-1)
                if ms_arr.size >= 4:
                    if float(ms_arr[3]) > 0.5:
                        success_flag = True
                    elif float(ms_arr[3]) < -0.5:
                        success_flag = False
        except Exception:
            success_flag = None

        runway_frac = 0.0
        if on_ground_steps > 0:
            runway_frac = float(on_runway_geom_steps) / float(on_ground_steps)

        require_success = bool(getattr(args, "require_success", False))
        min_runway_frac = float(getattr(args, "min_on_runway_geom_frac", 0.0) or 0.0)
        max_runway_cross = getattr(args, "max_abs_runway_cross_m", None)
        if max_runway_cross is not None:
            try:
                max_runway_cross = float(max_runway_cross)
            except Exception:
                max_runway_cross = None
        succ_str = "unk" if success_flag is None else str(int(bool(success_flag)))
        if require_success and success_flag is not True:
            print(
                f"[collect] skip ep={ep_idx} steps={steps} success={succ_str} "
                f"runway_frac={runway_frac:.3f} max|cross|={max_abs_runway_cross_m:.1f}m"
            )
            continue
        if min_runway_frac > 0.0 and runway_frac < min_runway_frac:
            print(
                f"[collect] skip ep={ep_idx} steps={steps} success={succ_str} "
                f"runway_frac={runway_frac:.3f} < {min_runway_frac:.3f} max|cross|={max_abs_runway_cross_m:.1f}m"
            )
            continue
        if max_runway_cross is not None and max_abs_runway_cross_m > float(max_runway_cross):
            print(
                f"[collect] skip ep={ep_idx} steps={steps} success={succ_str} "
                f"max|cross|={max_abs_runway_cross_m:.1f}m > {float(max_runway_cross):.1f}m runway_frac={runway_frac:.3f}"
            )
            continue

        episode = Episode(
            obs_vec=np.stack(obs_vecs, axis=0),
            actions=np.stack(actions, axis=0),
            rewards=np.asarray(rewards, dtype=np.float32),
            dones=np.asarray(dones, dtype=np.bool_),
            visual=(np.stack(visuals, axis=0) if visuals else None),
            expert_actions=(np.stack(expert_actions, axis=0) if expert_actions else None),
        )
        path = store.add(episode, seed=seed)
        saved += 1
        print(
            f"[collect] episode {ep_idx} steps={steps} success={succ_str} "
            f"runway_frac={runway_frac:.3f} max|cross|={max_abs_runway_cross_m:.1f}m -> {path}"
        )

    print(f"[collect] done: attempted={int(args.episodes)} saved={saved} out_dir={args.out_dir}")
