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
    mean = float(np.mean(xs))
    std = float(np.std(xs))
    p50 = _percentile(xs, 50)
    p90 = _percentile(xs, 90)
    p95 = _percentile(xs, 95)
    mn = float(np.min(xs))
    mx = float(np.max(xs))
    suffix = f" {unit}" if unit else ""
    return (
        f"{name}: mean={mean:.2f}{suffix} std={std:.2f}{suffix} "
        f"p50={p50:.2f}{suffix} p90={p90:.2f}{suffix} p95={p95:.2f}{suffix} "
        f"min={mn:.2f}{suffix} max={mx:.2f}{suffix}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate takeoff ground-roll distance for a world-model checkpoint")
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--max_steps", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=140)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--action_mode", type=str, default="takeoff4", choices=["full", "takeoff2", "takeoff4"])
    parser.add_argument("--include_visual", action="store_true")
    parser.add_argument("--include_proprio", action="store_true")
    parser.add_argument("--stochastic_state", action="store_true")
    parser.add_argument("--no_randomization", action="store_true")
    parser.add_argument(
        "--wheel_off_alt_threshold",
        type=float,
        default=None,
        help="Override wheel-off altitude threshold (AGL). Default uses scenario on_ground_alt_threshold.",
    )
    parser.add_argument(
        "--liftoff_alt_threshold",
        type=float,
        default=None,
        help="Override liftoff altitude threshold (AGL). Default uses scenario liftoff_alt_threshold.",
    )
    parser.add_argument(
        "--liftoff_ias_threshold",
        type=float,
        default=None,
        help="Override liftoff IAS threshold. Default uses scenario liftoff_speed_threshold.",
    )
    args = parser.parse_args()

    repo_root = _repo_root()
    _prepend_local_ef_py(repo_root)
    sys.path.insert(0, repo_root)

    from gym_envs.universal_env import UniversalEnv  # noqa: E402
    from python.world_model.features import (  # noqa: E402
        DEFAULT_ANGLE_DEG_INDICES,
        angle_sincos_features,
        append_angle_sincos_features,
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
    elif actor_input in ("embed_sincos", "embed_sincos_gru"):
        actor_feat_dim = int(wm.encoder.embed_dim) + 2 * len(angle_deg_indices)
    elif actor_input in ("embed", "embed_gru"):
        actor_feat_dim = int(wm.encoder.embed_dim)
    else:
        actor_feat_dim = int(wm.rssm.deter_dim + wm.rssm.stoch_dim)
    if actor_input in ("embed_gru", "embed_sincos_gru", "obs_gru", "obs_sincos_gru"):
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

    wheel_off_dist_m: list[float] = []
    wheel_off_time_s: list[float] = []
    wheel_off_ias_mps: list[float] = []

    liftoff_dist_m: list[float] = []
    liftoff_time_s: list[float] = []
    liftoff_ias_mps: list[float] = []
    failures = 0

    for ep in range(int(args.episodes)):
        obs, _ = env.reset(seed=int(args.seed) + ep)
        dt = float(env.sim.get_time_step())
        max_steps = min(int(args.max_steps), int(env.max_steps))

        # Liftoff thresholds follow scenario rewards config (realism-first).
        rcfg = {}
        try:
            rcfg = dict(env.loader.get_rewards_config())
        except Exception:
            rcfg = {}
        default_on_ground_alt_threshold = float(rcfg.get("on_ground_alt_threshold", 2.5))
        default_liftoff_alt_threshold = float(rcfg.get("liftoff_alt_threshold", 5.0))
        default_liftoff_speed_threshold = float(rcfg.get("liftoff_speed_threshold", 80.0))

        wheel_off_alt_threshold = float(
            default_on_ground_alt_threshold if args.wheel_off_alt_threshold is None else args.wheel_off_alt_threshold
        )
        liftoff_alt_threshold = float(
            default_liftoff_alt_threshold if args.liftoff_alt_threshold is None else args.liftoff_alt_threshold
        )
        liftoff_speed_threshold = float(
            default_liftoff_speed_threshold if args.liftoff_ias_threshold is None else args.liftoff_ias_threshold
        )

        # Start runway coordinate at t=0 (no step integration error).
        start_along = None
        try:
            truth0 = env.sim.get_agent_observation(env.agent_id)
            valid_rf, along0, _cross0, rw_len, rw_wid = env.loader.get_runway_local_frame(float(truth0.x), float(truth0.y))
            if bool(valid_rf) and float(rw_len) > 1.0 and float(rw_wid) > 1.0:
                start_along = float(along0)
        except Exception:
            start_along = None

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
            h, w, _c = visual_shape
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
            if actor_input not in ("obs", "obs_gru", "obs_sincos", "obs_sincos_gru"):
                embed = wm.encoder(obs_t, vis_t) if vis_t is not None else wm.encoder(obs_t)
            if actor_input == "rssm":
                assert embed is not None
                state, _ = wm.rssm.observe_init(embed, deterministic=deterministic_state)
        actor_h = None
        if actor_input in ("embed_gru", "embed_sincos_gru", "obs_gru", "obs_sincos_gru"):
            actor_h = actor.init_h(batch_size=1, device=device)  # type: ignore[union-attr]

        done = False
        steps = 0
        got_wheel_off = False
        wheel_off_along = None
        wheel_off_ias = None
        wheel_off_time = None

        got_liftoff = False
        liftoff_along = None
        liftoff_ias = None
        liftoff_time = None

        while not done and steps < max_steps:
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
                elif actor_input == "embed_sincos_gru":
                    assert embed is not None
                    ang = angle_sincos_features(obs_raw_t, angle_deg_indices=angle_deg_indices)
                    feat = torch.cat([embed, ang], dim=-1)
                    mean, _std, actor_h = actor.step(feat, actor_h)  # type: ignore[union-attr]
                    action_norm = torch.tanh(mean)
                else:
                    assert state is not None
                    feat = wm.feat(state)
                    mean, _std = actor(feat)  # type: ignore[union-attr]
                    action_norm = torch.tanh(mean)

            action_np = action_norm.squeeze(0).cpu().numpy().astype(np.float32, copy=False)
            action_env = wmt._unnormalize_action(action_np, action_low, action_high)

            next_obs, _reward, terminated, truncated, info = env.step(action_env)
            done = bool(terminated or truncated or (steps + 1) >= max_steps)

            try:
                inst = np.asarray(next_obs["instruments"], dtype=np.float32).reshape(-1)
                ias_mps = float(inst[0])
                alt_agl = float(inst[3])
            except Exception:
                ias_mps = float("nan")
                alt_agl = float("nan")

            if np.isfinite(ias_mps) and np.isfinite(alt_agl):
                if (not got_wheel_off) and alt_agl > wheel_off_alt_threshold and ias_mps >= liftoff_speed_threshold:
                    got_wheel_off = True
                    wheel_off_time = (steps + 1) * dt
                    wheel_off_ias = ias_mps
                    try:
                        if isinstance(info, dict) and "runway_along_m" in info:
                            wheel_off_along = float(info["runway_along_m"])
                    except Exception:
                        wheel_off_along = None
                    if wheel_off_along is None:
                        try:
                            truth = env.sim.get_agent_observation(env.agent_id)
                            valid_rf, along_m, _cross_m, rw_len, rw_wid = env.loader.get_runway_local_frame(
                                float(truth.x), float(truth.y)
                            )
                            if bool(valid_rf) and float(rw_len) > 1.0 and float(rw_wid) > 1.0:
                                wheel_off_along = float(along_m)
                        except Exception:
                            wheel_off_along = None

                if (not got_liftoff) and alt_agl >= liftoff_alt_threshold and ias_mps >= liftoff_speed_threshold:
                    got_liftoff = True
                    liftoff_time = (steps + 1) * dt
                    liftoff_ias = ias_mps
                    try:
                        if isinstance(info, dict) and "runway_along_m" in info:
                            liftoff_along = float(info["runway_along_m"])
                    except Exception:
                        liftoff_along = None
                    if liftoff_along is None:
                        try:
                            truth = env.sim.get_agent_observation(env.agent_id)
                            valid_rf, along_m, _cross_m, rw_len, rw_wid = env.loader.get_runway_local_frame(
                                float(truth.x), float(truth.y)
                            )
                            if bool(valid_rf) and float(rw_len) > 1.0 and float(rw_wid) > 1.0:
                                liftoff_along = float(along_m)
                        except Exception:
                            liftoff_along = None

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
                if actor_input not in ("obs", "obs_gru", "obs_sincos", "obs_sincos_gru"):
                    embed = wm.encoder(obs_t, vis_t) if vis_t is not None else wm.encoder(obs_t)
                if actor_input == "rssm":
                    assert state is not None and embed is not None
                    state, _ = wm.rssm.observe_step(state, embed, deterministic=deterministic_state)

            steps += 1

        if (
            start_along is None
            or (not got_wheel_off)
            or wheel_off_along is None
            or wheel_off_time is None
            or wheel_off_ias is None
            or (not got_liftoff)
            or liftoff_along is None
            or liftoff_time is None
            or liftoff_ias is None
        ):
            failures += 1
            continue
        wheel_off_dist_m.append(float(wheel_off_along - start_along))
        wheel_off_time_s.append(float(wheel_off_time))
        wheel_off_ias_mps.append(float(wheel_off_ias))

        liftoff_dist_m.append(float(liftoff_along - start_along))
        liftoff_time_s.append(float(liftoff_time))
        liftoff_ias_mps.append(float(liftoff_ias))

    total_eps = int(args.episodes)
    succ = total_eps - failures
    print("=" * 60)
    print("TAKEOFF ROLL EVAL (world-model)")
    print(f"scenario:   {args.scenario}")
    print(f"checkpoint: {args.checkpoint}")
    print(f"episodes:   {total_eps} (success={succ}, fail={failures})")
    print(f"seed:       {args.seed}..{args.seed + total_eps - 1}")
    print(f"action_mode:{args.action_mode}")
    print(f"thresholds: wheel_off_alt>{args.wheel_off_alt_threshold} (default 2.5), liftoff_alt>={args.liftoff_alt_threshold} (default 5.0), ias>={args.liftoff_ias_threshold} (default 80.0)")
    print("-" * 60)
    print(_fmt_stats("wheel_off_distance", wheel_off_dist_m, unit="m"))
    print(_fmt_stats("wheel_off_time", wheel_off_time_s, unit="s"))
    print(_fmt_stats("wheel_off_ias", wheel_off_ias_mps, unit="m/s"))
    print("-" * 60)
    print(_fmt_stats("liftoff_distance", liftoff_dist_m, unit="m"))
    print(_fmt_stats("liftoff_time", liftoff_time_s, unit="s"))
    print(_fmt_stats("liftoff_ias", liftoff_ias_mps, unit="m/s"))
    print("=" * 60)


if __name__ == "__main__":
    main()
