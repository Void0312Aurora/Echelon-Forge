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


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate runway centerline deviation for a world-model checkpoint")
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--max_steps", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=140)
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--action_mode", type=str, default="takeoff4", choices=["full", "takeoff2", "takeoff4"])
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

    successes = 0
    failures = 0
    total_rewards: list[float] = []

    ep_max_abs_cross: list[float] = []
    ep_mean_abs_cross: list[float] = []
    ep_on_runway_geom_frac: list[float] = []
    all_abs_cross: list[float] = []

    deterministic_state = not bool(args.stochastic_state)

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
        ep_rew = 0.0
        ep_cross: list[float] = []
        ground_steps = 0
        on_runway_geom_steps = 0
        last_info = {}

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

            next_obs, reward, terminated, truncated, info = env.step(action_env)
            done = bool(terminated or truncated or (steps + 1) >= int(args.max_steps))
            last_info = dict(info) if isinstance(info, dict) else {}
            ep_rew += float(reward)

            try:
                if float(last_info.get("on_ground", 0.0)) > 0.5 and "runway_cross_m" in last_info:
                    cross = abs(float(last_info["runway_cross_m"]))
                    ep_cross.append(cross)
                    all_abs_cross.append(cross)
                    ground_steps += 1
                    if float(last_info.get("on_runway_geom", 0.0)) > 0.5:
                        on_runway_geom_steps += 1
            except Exception:
                pass

            next_vec = wmt._flatten_obs(next_obs)
            next_raw = torch.from_numpy(next_vec).to(device).float().unsqueeze(0)
            next_t = (next_raw - obs_mean) / obs_std
            next_t = wmt._apply_norm_clip(next_t, obs_norm_clip)
            if visual_shape is not None:
                visual = np.asarray(next_obs["visual"], dtype=np.float32)
                visual = wmt._downsample_visual(visual, int(factor_h))
                visual = np.clip(visual, -10.0, 10.0).astype(np.float32, copy=False)
                vis_next = torch.from_numpy(visual).to(device).float().unsqueeze(0)
                vis_next = (vis_next - visual_mean_t) / visual_std_t
                vis_next = wmt._apply_norm_clip(vis_next, visual_norm_clip)
                vis_next = vis_next.reshape(1, -1)
            else:
                vis_next = None

            with torch.no_grad():
                if actor_input in ("obs", "obs_gru", "obs_sincos", "obs_sincos_gru"):
                    embed_next = None
                else:
                    embed_next = wm.encoder(next_t, vis_next) if vis_next is not None else wm.encoder(next_t)
                if actor_input == "rssm":
                    assert state is not None
                    assert embed_next is not None
                    a_t = torch.from_numpy(action_np).to(device).float().unsqueeze(0)
                    state, _, _ = wm.rssm.obs_step(state, a_t, embed_next, deterministic=deterministic_state)
                if actor_input not in ("obs", "obs_gru"):
                    embed = embed_next

            obs = next_obs
            obs_raw_t = next_raw
            obs_t = next_t
            steps += 1

        total_rewards.append(float(ep_rew))

        ms = last_info.get("mission_status", None)
        if ms is not None:
            try:
                ms_arr = np.asarray(ms, dtype=np.float32).reshape(-1)
                if ms_arr.size >= 4:
                    if float(ms_arr[3]) > 0.5:
                        successes += 1
                    elif float(ms_arr[3]) < -0.5:
                        failures += 1
            except Exception:
                pass

        if ep_cross:
            ep_max_abs_cross.append(float(np.max(ep_cross)))
            ep_mean_abs_cross.append(float(np.mean(ep_cross)))
        else:
            ep_max_abs_cross.append(0.0)
            ep_mean_abs_cross.append(0.0)

        if ground_steps > 0:
            ep_on_runway_geom_frac.append(float(on_runway_geom_steps) / float(ground_steps))
        else:
            ep_on_runway_geom_frac.append(0.0)

    def _q(arr: list[float], qs: list[float]) -> dict[str, float]:
        x = np.asarray(arr, dtype=np.float64)
        if x.size == 0:
            return {}
        out = {}
        for q in qs:
            out[f"p{int(q*100):02d}"] = float(np.quantile(x, q))
        out["max"] = float(np.max(x))
        out["mean"] = float(np.mean(x))
        return out

    print("== Summary ==")
    print(f"episodes={int(args.episodes)} seed_base={int(args.seed)} action_mode={args.action_mode} include_visual={bool(args.include_visual)}")
    if total_rewards:
        tr = np.asarray(total_rewards, dtype=np.float64)
        print(f"reward_mean={float(tr.mean()):.2f} reward_std={float(tr.std()):.2f} reward_min={float(tr.min()):.2f} reward_max={float(tr.max()):.2f}")
    known = successes + failures
    if known > 0:
        print(f"success_rate={successes}/{int(args.episodes)} known={known}")

    print("== Centerline (on_ground) ==")
    print(f"episode_max_abs_cross_m: {_q(ep_max_abs_cross, [0.50, 0.90, 0.95, 0.99])}")
    print(f"episode_mean_abs_cross_m: {_q(ep_mean_abs_cross, [0.50, 0.90, 0.95, 0.99])}")
    print(f"all_steps_abs_cross_m: {_q(all_abs_cross, [0.50, 0.90, 0.95, 0.99])}")
    print(f"episode_on_runway_geom_frac: {_q(ep_on_runway_geom_frac, [0.50, 0.90, 0.95, 0.99])}")


if __name__ == "__main__":
    main()
