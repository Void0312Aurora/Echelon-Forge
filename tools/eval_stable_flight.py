import argparse
import math
import os
import sys

import numpy as np
import torch


def _repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _prepend_local_ef_py(repo_root: str) -> None:
    build_dir = os.path.join(repo_root, "build")
    if not os.path.isdir(build_dir):
        return
    if any(fname.startswith("ef_py") and fname.endswith(".so") for fname in os.listdir(build_dir)):
        sys.path.insert(0, build_dir)


def _wrap_deg(x: float) -> float:
    y = (float(x) + 180.0) % 360.0 - 180.0
    return 0.0 if abs(y) < 1.0e-9 else y


def _percentile(xs: list[float], q: float) -> float:
    if not xs:
        return float("nan")
    return float(np.percentile(np.asarray(xs, dtype=np.float64), q))


def _fmt_stats(name: str, xs: list[float], *, unit: str = "") -> str:
    if not xs:
        return f"{name}: <empty>"
    mean = float(np.mean(xs))
    std = float(np.std(xs))
    p50 = _percentile(xs, 50)
    p90 = _percentile(xs, 90)
    p95 = _percentile(xs, 95)
    mn = float(np.min(xs))
    mx = float(np.max(xs))
    suffix = f" {unit}" if unit else ""
    return (
        f"{name}: mean={mean:.3f}{suffix} std={std:.3f}{suffix} "
        f"p50={p50:.3f}{suffix} p90={p90:.3f}{suffix} p95={p95:.3f}{suffix} "
        f"min={mn:.3f}{suffix} max={mx:.3f}{suffix}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate stable-flight tracking for a world-model checkpoint")
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--episodes", type=int, default=20)
    parser.add_argument("--max_steps", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--action_mode", type=str, default="full", choices=["full", "takeoff2", "takeoff4"])
    parser.add_argument("--include_visual", action="store_true")
    parser.add_argument("--include_proprio", action="store_true")
    parser.add_argument("--stochastic_state", action="store_true")
    parser.add_argument("--no_randomization", action="store_true")
    parser.add_argument("--warmup_steps", type=int, default=100, help="Ignore first N steps when computing hold fractions.")
    parser.add_argument("--alt_tol_m", type=float, default=30.0)
    parser.add_argument("--spd_tol_mps", type=float, default=10.0)
    parser.add_argument("--hdg_tol_deg", type=float, default=10.0)
    args = parser.parse_args()

    repo_root = _repo_root()
    _prepend_local_ef_py(repo_root)
    sys.path.insert(0, repo_root)

    from gym_envs.universal_env import UniversalEnv  # noqa: E402
    from python.world_model.features import (  # noqa: E402
        DEFAULT_ANGLE_DEG_INDICES,
        angle_sincos_features,
        append_angle_sincos_features,
        nav_tracking_features,
    )
    from python.world_model.networks import Actor, GRUActor, WorldModel  # noqa: E402
    from python.world_model.utils import DeviceConfig  # noqa: E402

    import world_model_train as wmt  # noqa: E402

    device = DeviceConfig(args.device).torch_device()
    try:
        ckpt = torch.load(args.checkpoint, map_location=device, weights_only=False)
    except TypeError:
        ckpt = torch.load(args.checkpoint, map_location=device)

    cfg = ckpt.get("cfg", {}) if isinstance(ckpt, dict) else {}
    spec = ckpt.get("spec", {}) if isinstance(ckpt, dict) else {}
    action_dim = int(spec.get("action_dim", 17))
    obs_vec_dim = int(spec.get("obs_vec_dim", 46))
    action_low = spec.get("action_low", None)
    action_high = spec.get("action_high", None)
    visual_shape = spec.get("visual_shape", None)
    if visual_shape is not None:
        visual_shape = tuple(int(x) for x in visual_shape)
    if action_low is None or action_high is None:
        raise ValueError("Checkpoint missing action_low/action_high")
    action_low = np.asarray(action_low, dtype=np.float32).reshape(-1)
    action_high = np.asarray(action_high, dtype=np.float32).reshape(-1)

    actor_input = str(cfg.get("actor_input", "rssm")) if isinstance(cfg, dict) else "rssm"
    angle_deg_indices = DEFAULT_ANGLE_DEG_INDICES
    if isinstance(cfg, dict):
        try:
            angle_deg_indices = tuple(int(x) for x in cfg.get("angle_deg_indices", DEFAULT_ANGLE_DEG_INDICES))
        except Exception:
            angle_deg_indices = DEFAULT_ANGLE_DEG_INDICES
    wm = WorldModel(action_dim=action_dim, obs_vec_dim=obs_vec_dim, visual_shape=visual_shape).to(device)
    wm.load_state_dict(ckpt["world_model"])
    wm.eval()

    if actor_input in ("obs", "obs_gru"):
        actor_feat_dim = int(obs_vec_dim)
    elif actor_input in ("obs_sincos", "obs_sincos_gru"):
        actor_feat_dim = int(obs_vec_dim) + 2 * len(angle_deg_indices)
    elif actor_input in ("obs_sincos_track", "obs_sincos_track_gru"):
        actor_feat_dim = int(obs_vec_dim) + 2 * len(angle_deg_indices) + 8
    elif actor_input in ("obs_sincos_track_vis", "obs_sincos_track_vis_gru"):
        if wm.encoder.visual is None:
            raise ValueError("actor_input='obs_sincos_track_vis*' requires visual input")
        actor_feat_dim = int(obs_vec_dim) + 2 * len(angle_deg_indices) + 8 + int(getattr(wm.encoder, "visual_embed_dim", 0))
    elif actor_input in ("embed_sincos", "embed_sincos_gru"):
        actor_feat_dim = int(wm.encoder.embed_dim) + 2 * len(angle_deg_indices)
    elif actor_input in ("embed_sincos_track", "embed_sincos_track_gru"):
        actor_feat_dim = int(wm.encoder.embed_dim) + 2 * len(angle_deg_indices) + 8
    elif actor_input in ("embed", "embed_gru"):
        actor_feat_dim = int(wm.encoder.embed_dim)
    else:
        actor_feat_dim = int(wm.rssm.deter_dim + wm.rssm.stoch_dim)
    if actor_input in (
        "embed_gru",
        "embed_sincos_gru",
        "embed_sincos_track_gru",
        "obs_gru",
        "obs_sincos_gru",
        "obs_sincos_track_gru",
        "obs_sincos_track_vis_gru",
    ):
        actor = GRUActor(input_dim=actor_feat_dim, action_dim=action_dim).to(device)
    else:
        actor = Actor(feat_dim=actor_feat_dim, action_dim=action_dim).to(device)
    actor.load_state_dict(ckpt["actor"])
    actor.eval()

    obs_mean = ckpt.get("obs_mean", None)
    obs_std = ckpt.get("obs_std", None)
    if obs_mean is None or obs_std is None:
        raise ValueError("Checkpoint missing obs_mean/obs_std")
    obs_mean = torch.as_tensor(obs_mean, device=device, dtype=torch.float32).reshape(1, -1)
    obs_std = torch.as_tensor(obs_std, device=device, dtype=torch.float32).reshape(1, -1)

    obs_norm_clip = None
    visual_norm_clip = None
    if isinstance(cfg, dict):
        obs_norm_clip = cfg.get("obs_norm_clip", None)
        visual_norm_clip = cfg.get("visual_norm_clip", None)

    if visual_shape is not None and not bool(args.include_visual) and actor_input not in (
        "obs",
        "obs_gru",
        "obs_sincos",
        "obs_sincos_gru",
        "obs_sincos_track",
        "obs_sincos_track_gru",
    ):
        raise ValueError("This checkpoint expects ARB visual input; rerun with --include_visual.")

    visual_mean_t = None
    visual_std_t = None
    if visual_shape is not None:
        visual_mean = ckpt.get("visual_mean", None)
        visual_std = ckpt.get("visual_std", None)
        if visual_mean is None or visual_std is None:
            raise ValueError("Checkpoint missing visual_mean/visual_std")
        visual_mean_t = torch.as_tensor(visual_mean, device=device, dtype=torch.float32).reshape(1, 1, 1, -1)
        visual_std_t = torch.as_tensor(visual_std, device=device, dtype=torch.float32).reshape(1, 1, 1, -1)

    env = UniversalEnv(
        args.scenario,
        include_visual=bool(args.include_visual),
        include_proprio=bool(args.include_proprio),
        action_mode=str(args.action_mode),
    )
    if bool(args.no_randomization):
        wmt._apply_env_overrides(env, args)

    deterministic_state = not bool(args.stochastic_state)

    alt_err_abs: list[float] = []
    spd_err_abs: list[float] = []
    hdg_err_abs: list[float] = []
    roll_abs: list[float] = []
    pitch_abs: list[float] = []

    ep_alt_err_mean: list[float] = []
    ep_spd_err_mean: list[float] = []
    ep_hdg_err_mean: list[float] = []
    ep_hold_frac: list[float] = []
    ep_rewards: list[float] = []
    ep_steps: list[int] = []
    crashes = 0

    for ep in range(int(args.episodes)):
        obs, _ = env.reset(seed=int(args.seed) + ep)
        obs_vec = wmt._flatten_obs(obs)
        if obs_vec.shape[0] != obs_vec_dim:
            raise ValueError(f"obs_vec_dim mismatch: got {obs_vec.shape[0]}, expected {obs_vec_dim}")

        obs_raw_t = torch.from_numpy(obs_vec).to(device).float().unsqueeze(0)
        obs_t = (obs_raw_t - obs_mean) / obs_std
        obs_t = wmt._apply_norm_clip(obs_t, obs_norm_clip)

        if visual_shape is not None:
            visual = np.asarray(obs["visual"], dtype=np.float32)
            env_visual_shape = (48, 96, 10)
            if visual.shape != env_visual_shape:
                raise ValueError(f"Unexpected env visual shape {visual.shape}, expected {env_visual_shape}")
            h, w, c = visual_shape
            if visual.shape[0] % h != 0 or visual.shape[1] % w != 0:
                raise ValueError(f"Cannot downsample env visual {visual.shape} -> {visual_shape}")
            factor_h = visual.shape[0] // h
            factor_w = visual.shape[1] // w
            if factor_h != factor_w:
                raise ValueError(f"Non-uniform visual downsample factors: h={factor_h}, w={factor_w}")
            visual = wmt._downsample_visual(visual, int(factor_h))
            visual = np.clip(visual, -10.0, 10.0).astype(np.float32, copy=False)
            vis_t = torch.from_numpy(visual).to(device).float().unsqueeze(0)
            vis_t = (vis_t - visual_mean_t) / visual_std_t
            vis_t = wmt._apply_norm_clip(vis_t, visual_norm_clip)
            vis_t = vis_t.reshape(1, -1)
        else:
            vis_t = None

        embed = None
        state = None
        with torch.no_grad():
            if actor_input not in (
                "obs",
                "obs_gru",
                "obs_sincos",
                "obs_sincos_gru",
                "obs_sincos_track",
                "obs_sincos_track_gru",
            ):
                embed = wm.encoder(obs_t, vis_t) if vis_t is not None else wm.encoder(obs_t)
            if actor_input == "rssm":
                assert embed is not None
                state, _ = wm.rssm.observe_init(embed, deterministic=deterministic_state)

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
            actor_h = actor.init_h(batch_size=1, device=device)  # type: ignore[union-attr]

        done = False
        steps = 0
        total_rew = 0.0
        ep_alt: list[float] = []
        ep_spd: list[float] = []
        ep_hdg: list[float] = []
        ep_hold = 0
        hold_total = 0

        last_inst = None
        last_mission = None
        while not done and steps < int(args.max_steps):
            with torch.no_grad():
                if actor_input == "obs":
                    feat = obs_t
                    mean, _std = actor(feat)  # type: ignore[union-attr]
                    action_norm = torch.tanh(mean)
                elif actor_input == "obs_gru":
                    feat = obs_t
                    mean, _std, actor_h = actor.step(feat, actor_h)  # type: ignore[union-attr]
                    action_norm = torch.tanh(mean)
                elif actor_input == "obs_sincos":
                    feat = append_angle_sincos_features(
                        obs_raw_deg=obs_raw_t,
                        obs_norm=obs_t,
                        angle_deg_indices=angle_deg_indices,
                    )
                    mean, _std = actor(feat)  # type: ignore[union-attr]
                    action_norm = torch.tanh(mean)
                elif actor_input == "obs_sincos_gru":
                    feat = append_angle_sincos_features(
                        obs_raw_deg=obs_raw_t,
                        obs_norm=obs_t,
                        angle_deg_indices=angle_deg_indices,
                    )
                    mean, _std, actor_h = actor.step(feat, actor_h)  # type: ignore[union-attr]
                    action_norm = torch.tanh(mean)
                elif actor_input == "obs_sincos_track":
                    feat = append_angle_sincos_features(
                        obs_raw_deg=obs_raw_t,
                        obs_norm=obs_t,
                        angle_deg_indices=angle_deg_indices,
                    )
                    track = nav_tracking_features(obs_raw_t)
                    feat = torch.cat([feat, track], dim=-1)
                    mean, _std = actor(feat)  # type: ignore[union-attr]
                    action_norm = torch.tanh(mean)
                elif actor_input == "obs_sincos_track_gru":
                    feat = append_angle_sincos_features(
                        obs_raw_deg=obs_raw_t,
                        obs_norm=obs_t,
                        angle_deg_indices=angle_deg_indices,
                    )
                    track = nav_tracking_features(obs_raw_t)
                    feat = torch.cat([feat, track], dim=-1)
                    mean, _std, actor_h = actor.step(feat, actor_h)  # type: ignore[union-attr]
                    action_norm = torch.tanh(mean)
                elif actor_input == "obs_sincos_track_vis":
                    assert embed is not None
                    feat = append_angle_sincos_features(
                        obs_raw_deg=obs_raw_t,
                        obs_norm=obs_t,
                        angle_deg_indices=angle_deg_indices,
                    )
                    track = nav_tracking_features(obs_raw_t)
                    vis_dim = int(getattr(wm.encoder, "visual_embed_dim", 0))
                    if vis_dim <= 0:
                        raise ValueError("actor_input='obs_sincos_track_vis' requires visual embedding")
                    vis_embed = embed[:, -vis_dim:]
                    feat = torch.cat([feat, track, vis_embed], dim=-1)
                    mean, _std = actor(feat)  # type: ignore[union-attr]
                    action_norm = torch.tanh(mean)
                elif actor_input == "obs_sincos_track_vis_gru":
                    assert embed is not None
                    feat = append_angle_sincos_features(
                        obs_raw_deg=obs_raw_t,
                        obs_norm=obs_t,
                        angle_deg_indices=angle_deg_indices,
                    )
                    track = nav_tracking_features(obs_raw_t)
                    vis_dim = int(getattr(wm.encoder, "visual_embed_dim", 0))
                    if vis_dim <= 0:
                        raise ValueError("actor_input='obs_sincos_track_vis_gru' requires visual embedding")
                    vis_embed = embed[:, -vis_dim:]
                    feat = torch.cat([feat, track, vis_embed], dim=-1)
                    mean, _std, actor_h = actor.step(feat, actor_h)  # type: ignore[union-attr]
                    action_norm = torch.tanh(mean)
                elif actor_input == "embed":
                    assert embed is not None
                    feat = embed
                    mean, _std = actor(feat)  # type: ignore[union-attr]
                    action_norm = torch.tanh(mean)
                elif actor_input == "embed_gru":
                    assert embed is not None
                    feat = embed
                    mean, _std, actor_h = actor.step(feat, actor_h)  # type: ignore[union-attr]
                    action_norm = torch.tanh(mean)
                elif actor_input == "embed_sincos":
                    assert embed is not None
                    ang = angle_sincos_features(obs_raw_t, angle_deg_indices=angle_deg_indices)
                    feat = torch.cat([embed, ang], dim=-1)
                    mean, _std = actor(feat)  # type: ignore[union-attr]
                    action_norm = torch.tanh(mean)
                elif actor_input == "embed_sincos_track":
                    assert embed is not None
                    ang = angle_sincos_features(obs_raw_t, angle_deg_indices=angle_deg_indices)
                    track = nav_tracking_features(obs_raw_t)
                    feat = torch.cat([embed, ang, track], dim=-1)
                    mean, _std = actor(feat)  # type: ignore[union-attr]
                    action_norm = torch.tanh(mean)
                elif actor_input == "embed_sincos_gru":
                    assert embed is not None
                    ang = angle_sincos_features(obs_raw_t, angle_deg_indices=angle_deg_indices)
                    feat = torch.cat([embed, ang], dim=-1)
                    mean, _std, actor_h = actor.step(feat, actor_h)  # type: ignore[union-attr]
                    action_norm = torch.tanh(mean)
                elif actor_input == "embed_sincos_track_gru":
                    assert embed is not None
                    ang = angle_sincos_features(obs_raw_t, angle_deg_indices=angle_deg_indices)
                    track = nav_tracking_features(obs_raw_t)
                    feat = torch.cat([embed, ang, track], dim=-1)
                    mean, _std, actor_h = actor.step(feat, actor_h)  # type: ignore[union-attr]
                    action_norm = torch.tanh(mean)
                else:
                    assert state is not None
                    feat = wm.feat(state)
                    mean, _std = actor(feat)  # type: ignore[union-attr]
                    action_norm = torch.tanh(mean)

            action_np = action_norm.squeeze(0).cpu().numpy().astype(np.float32, copy=False)
            action_env = wmt._unnormalize_action(action_np, action_low, action_high)

            next_obs, reward, terminated, truncated, info = env.step(action_env)
            total_rew += float(reward)
            done = bool(terminated or truncated or (steps + 1) >= int(args.max_steps))

            try:
                inst = np.asarray(next_obs["instruments"], dtype=np.float32).reshape(-1)
                mission = np.asarray(next_obs.get("mission", []), dtype=np.float32).reshape(-1)
                last_inst = inst
                last_mission = mission
            except Exception:
                inst = None
                mission = None

            if inst is not None and mission is not None and inst.size >= 10 and mission.size >= 4:
                ias = float(inst[0])
                alt = float(inst[2])
                hdg = float(inst[9])
                roll = float(inst[8])
                pitch = float(inst[7])

                tgt_hdg = float(mission[1])
                tgt_alt = float(mission[2])
                tgt_spd = float(mission[3])

                alt_e = abs(alt - tgt_alt)
                spd_e = abs(ias - tgt_spd)
                hdg_e = abs(_wrap_deg(hdg - tgt_hdg))

                alt_err_abs.append(alt_e)
                spd_err_abs.append(spd_e)
                hdg_err_abs.append(hdg_e)
                roll_abs.append(abs(roll))
                pitch_abs.append(abs(pitch))

                ep_alt.append(alt_e)
                ep_spd.append(spd_e)
                ep_hdg.append(hdg_e)

                if steps >= int(args.warmup_steps):
                    hold_total += 1
                    if (
                        alt_e <= float(args.alt_tol_m)
                        and spd_e <= float(args.spd_tol_mps)
                        and hdg_e <= float(args.hdg_tol_deg)
                    ):
                        ep_hold += 1

            next_vec = wmt._flatten_obs(next_obs)
            obs_raw_t = torch.from_numpy(next_vec).to(device).float().unsqueeze(0)
            obs_t = (obs_raw_t - obs_mean) / obs_std
            obs_t = wmt._apply_norm_clip(obs_t, obs_norm_clip)

            if visual_shape is not None:
                visual = np.asarray(next_obs["visual"], dtype=np.float32)
                env_visual_shape = (48, 96, 10)
                if visual.shape != env_visual_shape:
                    raise ValueError(f"Unexpected env visual shape {visual.shape}, expected {env_visual_shape}")
                h, w, _c = visual_shape
                factor_h = visual.shape[0] // h
                visual = wmt._downsample_visual(visual, int(factor_h))
                visual = np.clip(visual, -10.0, 10.0).astype(np.float32, copy=False)
                vis_t = torch.from_numpy(visual).to(device).float().unsqueeze(0)
                vis_t = (vis_t - visual_mean_t) / visual_std_t
                vis_t = wmt._apply_norm_clip(vis_t, visual_norm_clip)
                vis_t = vis_t.reshape(1, -1)
            else:
                vis_t = None

            with torch.no_grad():
                if actor_input in (
                    "obs",
                    "obs_gru",
                    "obs_sincos",
                    "obs_sincos_gru",
                    "obs_sincos_track",
                    "obs_sincos_track_gru",
                ):
                    embed_next = None
                else:
                    embed_next = wm.encoder(obs_t, vis_t) if vis_t is not None else wm.encoder(obs_t)
                if actor_input == "rssm":
                    assert state is not None and embed_next is not None
                    a_t = torch.from_numpy(action_np).to(device).float().unsqueeze(0)
                    state, _, _ = wm.rssm.obs_step(state, a_t, embed_next, deterministic=deterministic_state)
                if actor_input not in ("obs", "obs_gru"):
                    embed = embed_next

            obs = next_obs
            steps += 1

            if isinstance(info, dict):
                ms = info.get("mission_status", None)
                if ms is not None:
                    try:
                        ms_arr = np.asarray(ms, dtype=np.float32).reshape(-1)
                        if ms_arr.size >= 4 and float(ms_arr[3]) < -0.5:
                            crashes += 1
                    except Exception:
                        pass

        ep_rewards.append(float(total_rew))
        ep_steps.append(int(steps))
        ep_alt_err_mean.append(float(np.mean(ep_alt)) if ep_alt else float("nan"))
        ep_spd_err_mean.append(float(np.mean(ep_spd)) if ep_spd else float("nan"))
        ep_hdg_err_mean.append(float(np.mean(ep_hdg)) if ep_hdg else float("nan"))
        ep_hold_frac.append(float(ep_hold) / float(hold_total) if hold_total > 0 else 0.0)

    print("=" * 60)
    print("STABLE FLIGHT EVAL (world-model)")
    print(f"scenario:   {args.scenario}")
    print(f"checkpoint: {args.checkpoint}")
    print(f"episodes:   {int(args.episodes)} seed: {int(args.seed)}..{int(args.seed) + int(args.episodes) - 1}")
    print(f"action_mode:{args.action_mode} include_visual={bool(args.include_visual)} include_proprio={bool(args.include_proprio)}")
    print(f"tolerances: alt<= {float(args.alt_tol_m):.1f}m, spd<= {float(args.spd_tol_mps):.1f}m/s, hdg<= {float(args.hdg_tol_deg):.1f}deg (warmup={int(args.warmup_steps)} steps)")
    print("-" * 60)
    print(_fmt_stats("episode_reward", ep_rewards))
    print(_fmt_stats("episode_steps", [float(x) for x in ep_steps]))
    print(_fmt_stats("episode_alt_err_mean", ep_alt_err_mean, unit="m"))
    print(_fmt_stats("episode_spd_err_mean", ep_spd_err_mean, unit="m/s"))
    print(_fmt_stats("episode_hdg_err_mean", ep_hdg_err_mean, unit="deg"))
    print(_fmt_stats("episode_hold_frac", ep_hold_frac))
    print("-" * 60)
    print(_fmt_stats("all_alt_err_abs", alt_err_abs, unit="m"))
    print(_fmt_stats("all_spd_err_abs", spd_err_abs, unit="m/s"))
    print(_fmt_stats("all_hdg_err_abs", hdg_err_abs, unit="deg"))
    print(_fmt_stats("all_roll_abs", roll_abs, unit="deg"))
    print(_fmt_stats("all_pitch_abs", pitch_abs, unit="deg"))
    print("-" * 60)
    if crashes > 0:
        print(f"crash_like_terminations: {crashes}/{int(args.episodes)} (heuristic)")
    print("=" * 60)


if __name__ == "__main__":
    main()
