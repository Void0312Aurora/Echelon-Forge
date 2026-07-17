"""World-model policy rollout command."""

from __future__ import annotations

import argparse

import numpy as np
import torch

from _world_model_train_impl.common import (
    _apply_env_overrides,
    _apply_norm_clip,
    _build_world_model,
    _downsample_visual,
    _flatten_obs,
    _resolve_visual_encoder_settings,
    _unnormalize_action,
)

from _world_model_train_impl.runtime_env import build_world_model_execution_env
from python.world_model.networks import Actor, GRUActor
from python.world_model.utils import DeviceConfig


def rollout_policy(args: argparse.Namespace) -> None:
    def _wrap_deg(x: float) -> float:
        return (float(x) + 180.0) % 360.0 - 180.0

    device = DeviceConfig(args.device).torch_device()
    try:
        ckpt = torch.load(args.checkpoint, map_location=device, weights_only=False)
    except TypeError:
        ckpt = torch.load(args.checkpoint, map_location=device)
    cfg = ckpt.get("cfg", {}) if isinstance(ckpt, dict) else {}
    obs_norm_clip = None
    visual_norm_clip = None
    if isinstance(cfg, dict):
        obs_norm_clip = cfg.get("obs_norm_clip", None)
        visual_norm_clip = cfg.get("visual_norm_clip", None)
    spec = ckpt.get("spec", {})
    action_dim = int(spec.get("action_dim", 17))
    obs_vec_dim = int(spec.get("obs_vec_dim", 46))
    action_low = spec.get("action_low", None)
    action_high = spec.get("action_high", None)
    visual_shape = spec.get("visual_shape", None)
    if visual_shape is not None:
        visual_shape = tuple(int(x) for x in visual_shape)
    if action_low is None or action_high is None:
        raise ValueError(
            "Checkpoint is missing action_low/action_high; re-collect dataset with the updated collector."
        )
    action_low = np.asarray(action_low, dtype=np.float32).reshape(-1)
    action_high = np.asarray(action_high, dtype=np.float32).reshape(-1)

    visual_encoder_type, visual_cnn_channels = _resolve_visual_encoder_settings(
        ckpt_cfg=(cfg if isinstance(cfg, dict) else None)
    )
    wm = _build_world_model(
        action_dim=action_dim,
        obs_vec_dim=obs_vec_dim,
        visual_shape=visual_shape,
        visual_encoder_type=visual_encoder_type,
        visual_cnn_channels=visual_cnn_channels,
    ).to(device)
    wm.load_state_dict(ckpt["world_model"])
    wm.eval()

    actor_input = str(cfg.get("actor_input", "rssm")) if isinstance(cfg, dict) else "rssm"
    if actor_input in ("embed", "embed_gru"):
        actor_feat_dim = int(wm.encoder.embed_dim)
    else:
        actor_feat_dim = int(wm.rssm.deter_dim + wm.rssm.stoch_dim)
    if actor_input == "embed_gru":
        actor = GRUActor(input_dim=actor_feat_dim, action_dim=action_dim).to(device)
    else:
        actor = Actor(feat_dim=actor_feat_dim, action_dim=action_dim).to(device)
    actor.load_state_dict(ckpt["actor"])
    actor.eval()

    obs_mean = ckpt.get("obs_mean", None)
    obs_std = ckpt.get("obs_std", None)
    if obs_mean is None or obs_std is None:
        raise ValueError("Checkpoint missing obs_mean/obs_std; retrain with updated trainer.")
    obs_mean = torch.as_tensor(obs_mean, device=device, dtype=torch.float32).reshape(1, -1)
    obs_std = torch.as_tensor(obs_std, device=device, dtype=torch.float32).reshape(1, -1)

    visual_mean = ckpt.get("visual_mean", None)
    visual_std = ckpt.get("visual_std", None)
    if visual_shape is not None:
        if not args.include_visual:
            raise ValueError(
                "This checkpoint expects ARB visual input; run rollout with --include_visual."
            )
        if visual_mean is None or visual_std is None:
            raise ValueError(
                "Checkpoint missing visual_mean/visual_std; retrain with updated trainer."
            )
        visual_mean_t = torch.as_tensor(visual_mean, device=device, dtype=torch.float32).reshape(
            1, 1, 1, -1
        )
        visual_std_t = torch.as_tensor(visual_std, device=device, dtype=torch.float32).reshape(
            1, 1, 1, -1
        )
    else:
        visual_mean_t = None
        visual_std_t = None

    env = build_world_model_execution_env(
        scenario_path=args.scenario,
        include_visual=bool(args.include_visual),
        include_proprio=bool(getattr(args, "include_proprio", False)),
        action_mode=str(args.action_mode),
    )
    _apply_env_overrides(env, args)
    total_rewards = []
    successes = 0
    failures = 0

    env_visual_shape = None
    if args.include_visual:
        env_visual_shape = (48, 96, 10)

    deterministic_state = not bool(getattr(args, "stochastic_state", False))
    for ep in range(int(args.episodes)):
        obs, _ = env.reset(seed=int(args.seed) + ep)
        obs_vec = _flatten_obs(obs)
        if obs_vec.shape[0] != obs_vec_dim:
            raise ValueError(
                f"obs_vec_dim mismatch: got {obs_vec.shape[0]}, expected {obs_vec_dim}"
            )

        tgt_hdg = None
        tgt_alt = None
        tgt_spd = None
        try:
            m = np.asarray(obs.get("mission", []), dtype=np.float32).reshape(-1)
            if m.size >= 4:
                tgt_hdg = float(m[1])
                tgt_alt = float(m[2])
                tgt_spd = float(m[3])
        except Exception:
            tgt_hdg = None
            tgt_alt = None
            tgt_spd = None

        sum_abs_alt_err = 0.0
        sum_abs_spd_err = 0.0
        sum_abs_hdg_err = 0.0
        max_abs_roll = 0.0
        max_abs_pitch = 0.0
        max_abs_beta = 0.0
        max_abs_r = 0.0
        metric_steps = 0

        obs_t = torch.from_numpy(obs_vec).to(device).float().unsqueeze(0)
        obs_t = (obs_t - obs_mean) / obs_std
        obs_t = _apply_norm_clip(obs_t, obs_norm_clip)
        if visual_shape is not None:
            visual = np.asarray(obs["visual"], dtype=np.float32)
            if env_visual_shape is not None and visual.shape != env_visual_shape:
                raise ValueError(
                    f"Unexpected env visual shape {visual.shape}, expected {env_visual_shape}"
                )
            h, w, c = visual_shape
            if visual.shape[0] % h != 0 or visual.shape[1] % w != 0:
                raise ValueError(f"Cannot downsample env visual {visual.shape} -> {visual_shape}")
            factor_h = visual.shape[0] // h
            factor_w = visual.shape[1] // w
            if factor_h != factor_w:
                raise ValueError(
                    f"Non-uniform visual downsample factors: h={factor_h}, w={factor_w}"
                )
            if int(visual.shape[2]) != int(c):
                raise ValueError(f"Visual channel mismatch: env C={visual.shape[2]}, expected {c}")
            visual = _downsample_visual(visual, factor_h)
            visual = np.clip(visual, -10.0, 10.0).astype(np.float32, copy=False)
            vis_t = torch.from_numpy(visual).to(device).float().unsqueeze(0)  # (1,H,W,C)
            vis_t = (vis_t - visual_mean_t) / visual_std_t
            vis_t = _apply_norm_clip(vis_t, visual_norm_clip)
            vis_t = vis_t.reshape(1, -1)
        else:
            vis_t = None
        with torch.no_grad():
            embed0 = wm.encoder(obs_t, vis_t) if vis_t is not None else wm.encoder(obs_t)
            state = None
            if actor_input == "rssm":
                state, _ = wm.rssm.observe_init(embed0, deterministic=deterministic_state)
        actor_h = None
        if actor_input == "embed_gru":
            actor_h = actor.init_h(batch_size=1, device=device)  # type: ignore[union-attr]

        done = False
        ep_rew = 0.0
        steps = 0
        max_steps = int(args.max_steps) if args.max_steps is not None else 10**9
        last_info = {}
        last_inst = None
        max_ias = float("-inf")
        max_alt_radar = float("-inf")
        max_abs_cross_m = 0.0
        while not done and steps < max_steps:
            with torch.no_grad():
                use_stochastic = bool(getattr(args, "stochastic", False))
                if bool(getattr(args, "deterministic", False)):
                    use_stochastic = False

                if actor_input == "embed":
                    feat = embed0
                    if use_stochastic:
                        action_norm, _logp = actor.sample(feat)  # type: ignore[union-attr]
                    else:
                        mean, _std = actor(feat)  # type: ignore[union-attr]
                        action_norm = torch.tanh(mean)
                elif actor_input == "embed_gru":
                    feat = embed0
                    if use_stochastic:
                        action_norm, _logp, actor_h = actor.sample_step(feat, actor_h)  # type: ignore[union-attr]
                    else:
                        mean, _std, actor_h = actor.step(feat, actor_h)  # type: ignore[union-attr]
                        action_norm = torch.tanh(mean)
                else:
                    assert state is not None
                    feat = wm.feat(state)
                    if use_stochastic:
                        action_norm, _logp = actor.sample(feat)  # type: ignore[union-attr]
                    else:
                        mean, _std = actor(feat)  # type: ignore[union-attr]
                        action_norm = torch.tanh(mean)

            action_np = action_norm.squeeze(0).cpu().numpy().astype(np.float32, copy=False)
            action_env = _unnormalize_action(action_np, action_low, action_high)

            next_obs, reward, terminated, truncated, _info = env.step(action_env)
            collector_truncated = (steps + 1) >= max_steps
            done = bool(terminated or truncated or collector_truncated)
            last_info = dict(_info) if isinstance(_info, dict) else {}
            try:
                if float(last_info.get("on_ground", 0.0)) > 0.5:
                    max_abs_cross_m = max(
                        max_abs_cross_m, abs(float(last_info.get("runway_cross_m", 0.0)))
                    )
            except Exception:
                pass

            try:
                last_inst = np.asarray(next_obs.get("instruments", None), dtype=np.float32)
            except Exception:
                last_inst = None
            if last_inst is not None and last_inst.size >= 4:
                max_ias = max(max_ias, float(last_inst[0]))
                max_alt_radar = max(max_alt_radar, float(last_inst[3]))

                # Stability metrics (for non-terminal evaluation).
                try:
                    roll = float(last_inst[8])
                    pitch = float(last_inst[7])
                    beta = float(last_inst[6])
                    r_deg_s = float(last_inst[14]) if last_inst.size > 14 else 0.0
                    hdg = float(last_inst[9])
                    alt_baro = float(last_inst[2])
                    ias = float(last_inst[0])
                    max_abs_roll = max(max_abs_roll, abs(roll))
                    max_abs_pitch = max(max_abs_pitch, abs(pitch))
                    max_abs_beta = max(max_abs_beta, abs(beta))
                    max_abs_r = max(max_abs_r, abs(r_deg_s))
                    if tgt_alt is not None:
                        sum_abs_alt_err += abs(alt_baro - float(tgt_alt))
                    if tgt_spd is not None:
                        sum_abs_spd_err += abs(ias - float(tgt_spd))
                    if tgt_hdg is not None:
                        sum_abs_hdg_err += abs(_wrap_deg(float(tgt_hdg) - hdg))
                    metric_steps += 1
                except Exception:
                    pass
            ep_rew += float(reward)

            next_vec = _flatten_obs(next_obs)
            next_t = torch.from_numpy(next_vec).to(device).float().unsqueeze(0)
            next_t = (next_t - obs_mean) / obs_std
            next_t = _apply_norm_clip(next_t, obs_norm_clip)
            if visual_shape is not None:
                visual = np.asarray(next_obs["visual"], dtype=np.float32)
                visual = _downsample_visual(visual, factor_h)
                visual = np.clip(visual, -10.0, 10.0).astype(np.float32, copy=False)
                vis_next = torch.from_numpy(visual).to(device).float().unsqueeze(0)  # (1,H,W,C)
                vis_next = (vis_next - visual_mean_t) / visual_std_t
                vis_next = _apply_norm_clip(vis_next, visual_norm_clip)
                vis_next = vis_next.reshape(1, -1)
            else:
                vis_next = None
            with torch.no_grad():
                embed_next = (
                    wm.encoder(next_t, vis_next) if vis_next is not None else wm.encoder(next_t)
                )
                if actor_input == "rssm":
                    assert state is not None
                    a_t = torch.from_numpy(action_np).to(device).float().unsqueeze(0)
                    state, _prior, _post = wm.rssm.obs_step(
                        state, a_t, embed_next, deterministic=deterministic_state
                    )
                embed0 = embed_next

            steps += 1

        total_rewards.append(ep_rew)
        ms = last_info.get("mission_status", None)
        ms_str = ""
        success_flag = None
        if ms is not None:
            try:
                ms_arr = np.asarray(ms, dtype=np.float32).reshape(-1)
                ms_str = f" mission_status={ms_arr.tolist()}"
                if ms_arr.size >= 4:
                    if float(ms_arr[3]) > 0.5:
                        success_flag = True
                    elif float(ms_arr[3]) < -0.5:
                        success_flag = False
            except Exception:
                ms_str = ""
        runway_str = ""
        if "on_ground" in last_info:
            runway_str += f" on_ground={last_info.get('on_ground')}"
        if "on_runway" in last_info:
            runway_str += f" on_runway={last_info.get('on_runway')}"
        if "on_runway_geom" in last_info:
            runway_str += f" on_runway_geom={last_info.get('on_runway_geom')}"
        if "runway_cross_m" in last_info:
            runway_str += f" runway_cross_m={float(last_info.get('runway_cross_m')):.1f}"
        if "gear_collapsed" in last_info:
            runway_str += f" gear_collapsed={last_info.get('gear_collapsed')}"
        if "gear_stress" in last_info:
            runway_str += f" gear_stress={last_info.get('gear_stress')}"
        if max_abs_cross_m > 0.0:
            runway_str += f" max|cross|={max_abs_cross_m:.1f}"
        inst_str = ""
        if last_inst is not None and last_inst.size >= 4:
            inst_str = f" ias={float(last_inst[0]):.1f} alt_baro={float(last_inst[2]):.1f} alt_radar={float(last_inst[3]):.1f}"
        peak_str = ""
        if max_ias > float("-inf") and max_alt_radar > float("-inf"):
            peak_str = f" max_ias={max_ias:.1f} max_alt_radar={max_alt_radar:.1f}"
        metric_str = ""
        if metric_steps > 0:
            if tgt_alt is not None:
                metric_str += f" alt_err_mean={sum_abs_alt_err / float(metric_steps):.1f}"
            if tgt_spd is not None:
                metric_str += f" spd_err_mean={sum_abs_spd_err / float(metric_steps):.1f}"
            if tgt_hdg is not None:
                metric_str += f" hdg_err_mean={sum_abs_hdg_err / float(metric_steps):.1f}"
            metric_str += (
                f" max|roll|={max_abs_roll:.1f}"
                f" max|pitch|={max_abs_pitch:.1f}"
                f" max|beta|={max_abs_beta:.1f}"
                f" max|r|={max_abs_r:.1f}"
            )
        outcome_str = ""
        if success_flag is True:
            successes += 1
            outcome_str = " success=1"
        elif success_flag is False:
            failures += 1
            outcome_str = " success=0"
        print(
            f"[rollout] ep={ep} steps={steps} ep_rew={ep_rew:.2f}{inst_str}{peak_str}{metric_str}{runway_str}{outcome_str}{ms_str}"
        )

    if total_rewards:
        arr = np.asarray(total_rewards, dtype=np.float32)
        print(
            f"[rollout] mean={arr.mean():.2f} std={arr.std():.2f} min={arr.min():.2f} max={arr.max():.2f}"
        )
        if int(args.episodes) > 0:
            known = successes + failures
            if known > 0:
                print(f"[rollout] success_rate={successes}/{int(args.episodes)} known={known}")
