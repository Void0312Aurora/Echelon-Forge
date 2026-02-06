import argparse
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


def _percentile(xs: list[float], q: float) -> float:
    if not xs:
        return float("nan")
    return float(np.percentile(np.asarray(xs, dtype=np.float64), q))


def _fmt_stats(name: str, xs: list[float], *, unit: str = "") -> str:
    if not xs:
        return f"{name}: <empty>"
    arr = np.asarray(xs, dtype=np.float64)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return f"{name}: <all_nan>"
    mean = float(np.mean(arr))
    std = float(np.std(arr))
    p50 = float(np.percentile(arr, 50))
    p90 = float(np.percentile(arr, 90))
    mn = float(np.min(arr))
    mx = float(np.max(arr))
    suffix = f" {unit}" if unit else ""
    return (
        f"{name}: mean={mean:.3f}{suffix} std={std:.3f}{suffix} "
        f"p50={p50:.3f}{suffix} p90={p90:.3f}{suffix} min={mn:.3f}{suffix} max={mx:.3f}{suffix}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate waypoint navigation for a world-model checkpoint")
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--episodes", type=int, default=10)
    parser.add_argument("--max_steps", type=int, default=6000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--action_mode", type=str, default="full", choices=["full", "takeoff2", "takeoff4"])
    parser.add_argument("--include_visual", action="store_true")
    parser.add_argument("--include_proprio", action="store_true")
    parser.add_argument("--stochastic_state", action="store_true")
    parser.add_argument("--no_randomization", action="store_true")
    args = parser.parse_args()

    repo_root = _repo_root()
    _prepend_local_ef_py(repo_root)
    sys.path.insert(0, repo_root)

    from gym_envs.universal_env import UniversalEnv  # noqa: E402
    from python.world_model.features import (  # noqa: E402
        DEFAULT_ANGLE_DEG_INDICES,
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

    ep_success: list[float] = []
    ep_steps: list[int] = []
    ep_rewards: list[float] = []
    ep_final_wp_idx: list[int] = []
    ep_min_dist: list[float] = []
    ep_final_dist: list[float] = []
    ep_wp_min_last: list[float] = []
    ep_wp_min_max: list[float] = []
    crashes = 0
    failures = 0

    for ep in range(int(args.episodes)):
        obs, _ = env.reset(seed=int(args.seed) + ep)
        obs_vec = wmt._flatten_obs(obs)
        if obs_vec.shape[0] != obs_vec_dim:
            raise ValueError(f"obs_vec_dim mismatch: got {obs_vec.shape[0]}, expected {obs_vec_dim}")

        obs_raw_t = torch.from_numpy(obs_vec).to(device).float().unsqueeze(0)
        obs_t = (obs_raw_t - obs_mean) / obs_std
        obs_t = wmt._apply_norm_clip(obs_t, obs_norm_clip)

        vis_t = None
        if visual_shape is not None:
            visual = np.asarray(obs["visual"], dtype=np.float32)
            env_visual_shape = (48, 96, 10)
            if tuple(visual.shape) != env_visual_shape:
                raise ValueError(f"Unexpected env visual shape {tuple(visual.shape)}, expected {env_visual_shape}")
            h, w, _c = visual_shape
            if visual.shape[0] % h != 0 or visual.shape[1] % w != 0:
                raise ValueError(f"Cannot downsample env visual {tuple(visual.shape)} -> {visual_shape}")
            factor_h = visual.shape[0] // h
            factor_w = visual.shape[1] // w
            if factor_h != factor_w:
                raise ValueError(f"Non-uniform visual downsample factors: h={factor_h}, w={factor_w}")
            visual = wmt._downsample_visual(visual, int(factor_h))
            visual = np.clip(visual, -10.0, 10.0).astype(np.float32, copy=False)
            vis_t = torch.from_numpy(visual).to(device).float().unsqueeze(0)
            vis_t = (vis_t - visual_mean_t) / visual_std_t  # type: ignore[operator]
            vis_t = wmt._apply_norm_clip(vis_t, visual_norm_clip)
            vis_t = vis_t.reshape(1, -1)

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
        dists: list[float] = []
        last_ms = None
        wps = list(getattr(getattr(env, "loader", None), "waypoints", []) or [])
        wp_min_d = [float("inf")] * int(len(wps))

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
                elif actor_input in ("embed", "embed_gru", "embed_sincos", "embed_sincos_gru", "embed_sincos_track", "embed_sincos_track_gru"):
                    assert embed is not None
                    feat = embed
                    if "sincos" in actor_input:
                        feat = append_angle_sincos_features(
                            obs_raw_deg=obs_raw_t,
                            obs_norm=feat,
                            angle_deg_indices=angle_deg_indices,
                        )
                    if "track" in actor_input:
                        track = nav_tracking_features(obs_raw_t)
                        feat = torch.cat([feat, track], dim=-1)
                    if actor_input.endswith("_gru"):
                        mean, _std, actor_h = actor.step(feat, actor_h)  # type: ignore[union-attr]
                    else:
                        mean, _std = actor(feat)  # type: ignore[union-attr]
                    action_norm = torch.tanh(mean)
                else:
                    # rssm / rssm-gru actor
                    assert state is not None
                    feat = wm.rssm.get_feat(state)
                    if actor_input.endswith("_gru"):
                        mean, _std, actor_h = actor.step(feat, actor_h)  # type: ignore[union-attr]
                    else:
                        mean, _std = actor(feat)  # type: ignore[union-attr]
                    action_norm = torch.tanh(mean)

            action = wmt._unnormalize_action(action_norm.squeeze(0).cpu().numpy(), action_low, action_high)
            next_obs, rew, terminated, truncated, info = env.step(action)
            total_rew += float(rew)

            # Per-waypoint min pass distance (geometry-only, for realism-aligned accuracy).
            if wp_min_d:
                try:
                    truth = env.sim.get_agent_observation(env.agent_id)
                    x = float(getattr(truth, "x", 0.0))
                    y = float(getattr(truth, "y", 0.0))
                    for i, wp in enumerate(wps):
                        dx = float(wp.get("x", 0.0)) - x
                        dy = float(wp.get("y", 0.0)) - y
                        d = float(np.hypot(dx, dy))
                        if d < wp_min_d[i]:
                            wp_min_d[i] = d
                except Exception:
                    pass

            ms = info.get("mission_status", None) if isinstance(info, dict) else None
            if ms is not None:
                ms = np.asarray(ms, dtype=np.float32).reshape(-1)
                last_ms = ms
                if ms.size >= 1:
                    # Avoid polluting distance stats on explicit failure: on crash/failfast,
                    # mission_status[0] can be left at the default 0.0 (not a real waypoint distance).
                    if ms.size >= 4 and float(ms[3]) < -0.5:
                        pass
                    else:
                        d = float(ms[0])
                        if np.isfinite(d):
                            dists.append(d)

            obs = next_obs
            obs_vec = wmt._flatten_obs(obs)
            obs_raw_t = torch.from_numpy(obs_vec).to(device).float().unsqueeze(0)
            obs_t = (obs_raw_t - obs_mean) / obs_std
            obs_t = wmt._apply_norm_clip(obs_t, obs_norm_clip)

            if visual_shape is not None:
                visual = np.asarray(obs["visual"], dtype=np.float32)
                env_visual_shape = (48, 96, 10)
                if tuple(visual.shape) != env_visual_shape:
                    raise ValueError(f"Unexpected env visual shape {tuple(visual.shape)}, expected {env_visual_shape}")
                h, w, _c = visual_shape
                factor_h = visual.shape[0] // h
                factor_w = visual.shape[1] // w
                if factor_h != factor_w:
                    raise ValueError(f"Non-uniform visual downsample factors: h={factor_h}, w={factor_w}")
                visual = wmt._downsample_visual(visual, int(factor_h))
                visual = np.clip(visual, -10.0, 10.0).astype(np.float32, copy=False)
                visual_t = torch.from_numpy(visual).to(device).float().unsqueeze(0)
                visual_t = (visual_t - visual_mean_t) / visual_std_t  # type: ignore[operator]
                visual_t = wmt._apply_norm_clip(visual_t, visual_norm_clip)
                vis_t = visual_t.reshape(1, -1)

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
                if state is not None:
                    assert embed is not None
                    act_t = torch.from_numpy(wmt._normalize_action(action, action_low, action_high)).to(device).float().unsqueeze(0)
                    state, _prior, _post = wm.rssm.obs_step(state, act_t, embed, deterministic=deterministic_state)

            steps += 1
            done = bool(terminated or truncated or steps >= int(args.max_steps))

        # Episode summary
        success = False
        failed = False
        wp_idx = 0
        dist_final = float("nan")
        if last_ms is not None and last_ms.size >= 4:
            success = bool(float(last_ms[3]) > 0.5)
            failed = bool(float(last_ms[3]) < -0.5)
            wp_idx = int(float(last_ms[1])) if last_ms.size >= 2 else 0
            if failed:
                dist_final = float("nan")
            else:
                dist_final = float(last_ms[0]) if last_ms.size >= 1 else float("nan")

        # Count explicit failures (crash/invalid/terminated-by-failfast). Avoid using return-based heuristics:
        # waypoint tasks can accumulate large negative shaping returns without crashing.
        if failed:
            failures += 1
            crashes += 1

        ep_success.append(1.0 if success else 0.0)
        ep_steps.append(int(steps))
        ep_rewards.append(float(total_rew))
        ep_final_wp_idx.append(int(wp_idx))
        ep_min_dist.append(float(np.min(dists)) if dists else float("nan"))
        ep_final_dist.append(float(dist_final))
        if wp_min_d:
            ep_wp_min_last.append(float(wp_min_d[-1]))
            ep_wp_min_max.append(float(np.max(np.asarray(wp_min_d, dtype=np.float64))))
        else:
            ep_wp_min_last.append(float("nan"))
            ep_wp_min_max.append(float("nan"))

        print(
            f"[ep {ep+1}/{int(args.episodes)}] success={success} failed={failed} steps={steps} "
            f"final_wp_idx={wp_idx} min_dist={ep_min_dist[-1]:.1f}m final_dist={dist_final:.1f}m "
            f"wp_min_last={ep_wp_min_last[-1]:.1f}m wp_min_max={ep_wp_min_max[-1]:.1f}m return={total_rew:.1f}"
        )

    print("=" * 60)
    print(
        f"success_rate: {float(np.mean(ep_success)):.3f}  "
        f"failures: {failures}/{int(args.episodes)}  crashes: {crashes}/{int(args.episodes)}"
    )
    print(_fmt_stats("steps", ep_steps))
    print(_fmt_stats("return", ep_rewards))
    print(_fmt_stats("final_wp_idx", ep_final_wp_idx))
    print(_fmt_stats("min_dist", ep_min_dist, unit="m"))
    print(_fmt_stats("final_dist", ep_final_dist, unit="m"))
    print(_fmt_stats("wp_min_last", ep_wp_min_last, unit="m"))
    print(_fmt_stats("wp_min_max", ep_wp_min_max, unit="m"))


if __name__ == "__main__":
    main()
