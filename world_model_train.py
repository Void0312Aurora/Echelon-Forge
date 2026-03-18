import argparse
import os
import sys
from dataclasses import asdict
from datetime import datetime

import numpy as np
import torch

# Prefer the locally built `ef_py` extension when present.
_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
_BUILD_DIR = os.path.join(_REPO_ROOT, "build")
if os.path.isdir(_BUILD_DIR):
    for _name in ("ef_py", "ef_py.cpython-313-x86_64-linux-gnu.so"):
        if os.path.exists(os.path.join(_BUILD_DIR, _name)) or any(
            fname.startswith("ef_py") and fname.endswith(".so") for fname in os.listdir(_BUILD_DIR)
        ):
            sys.path.insert(0, _BUILD_DIR)
            break
sys.path.insert(0, _REPO_ROOT)

from gym_envs.universal_env import UniversalEnv  # noqa: E402
from python.rl.scripted_takeoff import ScriptedTakeoffController, scripted_takeoff_action  # noqa: E402
from python.rl.scripted_stable_flight import ScriptedStableFlightController  # noqa: E402
from python.world_model.dreamer import DreamerConfig, DreamerTrainer  # noqa: E402
from python.world_model.features import (  # noqa: E402
    DEFAULT_ANGLE_DEG_INDICES,
    angle_sincos_features,
    append_angle_sincos_features,
    nav_tracking_features,
)
from python.world_model.replay import DatasetSpec, Episode, EpisodeDataset, EpisodeStore  # noqa: E402
from python.world_model.networks import Actor, GRUActor, WorldModel  # noqa: E402
from python.world_model.utils import DeviceConfig, ensure_dir, set_seed  # noqa: E402


def _apply_preset(args: argparse.Namespace) -> None:
    preset = getattr(args, "preset", "default")
    if preset in (None, "", "default"):
        return
    if preset == "takeoff_stable":
        # Tuned to reduce return variance and critic blow-ups on takeoff tasks with large negative penalties.
        # Keeps realism intact (no observation leakage), only changes learning-side scalings.
        args.horizon = 10
        args.reward_symlog_clip = 3.0
        args.seq_len = 64
        if getattr(args, "bc_scale", None) is not None and float(args.bc_scale) <= 0.0:
            args.bc_scale = 0.1
        if getattr(args, "bc_teacher_prob", None) is not None:
            args.bc_teacher_prob = min(float(args.bc_teacher_prob), 0.7)
        if getattr(args, "log_compact", None) is not None:
            args.log_compact = True
        return
    raise ValueError(f"Unknown preset: {preset}")


def _format_metrics(metrics: dict[str, float], *, compact: bool) -> str:
    if not compact:
        items = sorted(metrics.items())
        return " ".join(f"{k}={v:.4f}" for k, v in items)

    keys = [
        "wm/total",
        "wm/kl",
        "wm/obs",
        "wm/visual",
        "wm/cont",
        "ac/return_mean",
        "ac/return_std",
        "ac/value_raw_mse",
        "ac/bc",
    ]
    items = [(k, float(metrics[k])) for k in keys if k in metrics]
    return " ".join(f"{k}={v:.4f}" for k, v in items)


def _no_randomization_overrides() -> dict:
    # Deterministic baseline: remove wind and world-yaw randomization.
    # This does NOT leak privileged information; it only fixes environment conditions.
    return {
        "world_yaw_range": [0.0, 0.0],
        # Global wind sampling
        "wind_speed_range": [0.0, 0.0],
        "wind_dir_from_range": [0.0, 0.0],
        # Runway-relative wind sampling (takeoff/landing scenarios)
        "wind_headwind_range": [0.0, 0.0],
        "wind_crosswind_range": [0.0, 0.0],
        "wind_tailwind_max_mps": 0.0,
        # Shear (both modes share this key)
        "wind_shear_range": [0.0, 0.0],
    }


def _apply_env_overrides(env: UniversalEnv, args: argparse.Namespace) -> None:
    if bool(getattr(args, "no_randomization", False)):
        env.set_randomization_overrides(_no_randomization_overrides())


def _load_curriculum(path: str) -> list[dict]:
    import json

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and isinstance(data.get("stages", None), list):
        stages = data["stages"]
    elif isinstance(data, list):
        stages = data
    else:
        raise ValueError("curriculum must be a JSON list or an object with a 'stages' list")
    if not stages:
        raise ValueError("curriculum stages list is empty")
    return [dict(s) for s in stages if isinstance(s, dict)]


def _select_curriculum_stage(stages: list[dict], t: int, *, key: str) -> int:
    for idx, st in enumerate(stages):
        until = st.get(key, None)
        if until is None:
            return idx
        if t < int(until):
            return idx
    return len(stages) - 1


def _get_stage_overrides(stage: dict) -> dict:
    overrides = stage.get("randomization_overrides", stage.get("randomization", {}))
    if overrides is None:
        overrides = {}
    if not isinstance(overrides, dict):
        raise TypeError(f"curriculum stage overrides must be a dict, got {type(overrides)}")
    return dict(overrides)


def _downsample_visual(visual: np.ndarray, factor: int) -> np.ndarray:
    if factor <= 1:
        return visual
    h, w, c = visual.shape
    if h % factor != 0 or w % factor != 0:
        raise ValueError(f"visual shape {visual.shape} not divisible by downsample factor {factor}")
    nh, nw = h // factor, w // factor
    return visual.reshape(nh, factor, nw, factor, c).mean(axis=(1, 3))


def _flatten_obs(obs: dict) -> np.ndarray:
    # Strict realism: only include pilot-observable avionics + mission command.
    # Do NOT include contacts/rwr arrays here until they are implemented as real sensor fusion outputs.
    inst = np.asarray(obs["instruments"], dtype=np.float32).reshape(-1)
    mission = np.asarray(obs["mission"], dtype=np.float32).reshape(-1)
    proprio = np.asarray(obs.get("proprio", []), dtype=np.float32).reshape(-1)
    if proprio.size > 0:
        return np.concatenate([inst, mission, proprio], axis=0).astype(np.float32, copy=False)
    return np.concatenate([inst, mission], axis=0).astype(np.float32, copy=False)


def _normalize_action(action: np.ndarray, low: np.ndarray, high: np.ndarray) -> np.ndarray:
    action = np.asarray(action, dtype=np.float32).reshape(-1)
    low = np.asarray(low, dtype=np.float32).reshape(-1)
    high = np.asarray(high, dtype=np.float32).reshape(-1)
    denom = high - low
    denom = np.where(np.abs(denom) < 1e-8, 1.0, denom)
    out = 2.0 * (action - low) / denom - 1.0
    return np.clip(out, -1.0, 1.0).astype(np.float32, copy=False)


def _unnormalize_action(action: np.ndarray, low: np.ndarray, high: np.ndarray) -> np.ndarray:
    action = np.asarray(action, dtype=np.float32).reshape(-1)
    low = np.asarray(low, dtype=np.float32).reshape(-1)
    high = np.asarray(high, dtype=np.float32).reshape(-1)
    out = low + 0.5 * (action + 1.0) * (high - low)
    return np.clip(out, low, high).astype(np.float32, copy=False)


def _apply_norm_clip(t: torch.Tensor, clip: float | None) -> torch.Tensor:
    if clip is None:
        return t
    return torch.clamp(t, -float(clip), float(clip))


def _parse_angle_deg_indices(value: str | None) -> tuple[int, ...]:
    if value is None:
        return DEFAULT_ANGLE_DEG_INDICES
    s = str(value).strip()
    if not s:
        return DEFAULT_ANGLE_DEG_INDICES
    parts = [p.strip() for p in s.split(",") if p.strip()]
    return tuple(int(p) for p in parts)


def _resolve_visual_encoder_settings(
    *,
    args: argparse.Namespace | None = None,
    ckpt_cfg: dict | None = None,
) -> tuple[str, int]:
    if isinstance(ckpt_cfg, dict):
        enc_type = str(ckpt_cfg.get("visual_encoder_type", "mlp")).strip().lower()
        channels = int(ckpt_cfg.get("visual_cnn_channels", 64))
    else:
        enc_type = str(getattr(args, "visual_encoder_type", "cnn")).strip().lower()
        channels = int(getattr(args, "visual_cnn_channels", 64))
    if enc_type not in ("cnn", "mlp"):
        raise ValueError(f"Unknown visual_encoder_type: {enc_type!r}")
    return enc_type, max(16, channels)


def _build_world_model(
    *,
    action_dim: int,
    obs_vec_dim: int,
    visual_shape: tuple[int, int, int] | None,
    visual_encoder_type: str,
    visual_cnn_channels: int,
) -> WorldModel:
    return WorldModel(
        action_dim=action_dim,
        obs_vec_dim=obs_vec_dim,
        visual_shape=visual_shape,
        visual_encoder_type=str(visual_encoder_type),
        visual_cnn_channels=int(visual_cnn_channels),
    )


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

    if str(args.policy) in ("dagger_scripted_takeoff", "dagger_scripted_stable_flight", "dagger_scripted_waypoint"):
        if not getattr(args, "student_checkpoint", None):
            raise ValueError("--student_checkpoint is required for DAgger policies")
        if spec.action_low is None or spec.action_high is None:
            raise ValueError("DAgger policy requires env.action_space low/high to be defined")

        student_device = DeviceConfig(getattr(args, "device", "cpu")).torch_device()
        try:
            ckpt = torch.load(str(args.student_checkpoint), map_location=student_device, weights_only=False)
        except TypeError:
            ckpt = torch.load(str(args.student_checkpoint), map_location=student_device)
        if not isinstance(ckpt, dict):
            raise ValueError("student_checkpoint must be a dict-like checkpoint")
        ckpt_spec = ckpt.get("spec", {}) if isinstance(ckpt.get("spec", {}), dict) else {}
        ckpt_action_dim = int(ckpt_spec.get("action_dim", spec.action_dim))
        ckpt_obs_vec_dim = int(ckpt_spec.get("obs_vec_dim", spec.obs_vec_dim))
        if ckpt_action_dim != int(spec.action_dim):
            raise ValueError(f"student_checkpoint action_dim={ckpt_action_dim} does not match env action_dim={spec.action_dim}")
        if ckpt_obs_vec_dim != int(spec.obs_vec_dim):
            raise ValueError(f"student_checkpoint obs_vec_dim={ckpt_obs_vec_dim} does not match env obs_vec_dim={spec.obs_vec_dim}")
        ckpt_visual_shape = ckpt_spec.get("visual_shape", None)
        if args.include_visual:
            if ckpt_visual_shape is None:
                raise ValueError("student_checkpoint was trained without visual, but --include_visual is set")
            # Validate downsample factor matches the checkpoint visual shape.
            v0_raw = np.asarray(obs["visual"], dtype=np.float32)
            v0_ds = _downsample_visual(v0_raw, int(args.visual_downsample))
            if tuple(int(x) for x in v0_ds.shape) != tuple(int(x) for x in np.asarray(ckpt_visual_shape).reshape(-1).tolist()):
                raise ValueError(
                    f"--visual_downsample={int(args.visual_downsample)} yields visual_shape={tuple(int(x) for x in v0_ds.shape)}, "
                    f"but student_checkpoint expects visual_shape={tuple(int(x) for x in np.asarray(ckpt_visual_shape).reshape(-1).tolist())}. "
                    "Use the same downsample factor as the checkpoint training dataset."
                )
        else:
            if ckpt_visual_shape is not None and tuple(int(x) for x in np.asarray(ckpt_visual_shape).reshape(-1).tolist())[0] >= 0:
                raise ValueError("student_checkpoint expects visual, but --include_visual is not set")

        cfg = ckpt.get("cfg", {}) if isinstance(ckpt.get("cfg", {}), dict) else {}
        student_actor_input = str(cfg.get("actor_input", "rssm"))
        student_deterministic_state = bool(cfg.get("bc_deterministic_state", True))
        student_obs_norm_clip = cfg.get("obs_norm_clip", None)
        student_visual_norm_clip = cfg.get("visual_norm_clip", None)
        student_visual_encoder_type, student_visual_cnn_channels = _resolve_visual_encoder_settings(ckpt_cfg=cfg)
        try:
            student_angle_deg_indices = tuple(int(x) for x in cfg.get("angle_deg_indices", DEFAULT_ANGLE_DEG_INDICES))
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
                raise ValueError("student_checkpoint actor_input='obs_sincos_track_vis*' requires visual")
            actor_feat_dim = int(spec.obs_vec_dim) + 2 * len(student_angle_deg_indices) + 8 + int(
                getattr(student_wm.encoder, "visual_embed_dim", 0)
            )
        elif student_actor_input in ("embed_sincos", "embed_sincos_gru"):
            actor_feat_dim = int(student_wm.encoder.embed_dim) + 2 * len(student_angle_deg_indices)
        elif student_actor_input in ("embed_sincos_track", "embed_sincos_track_gru"):
            actor_feat_dim = int(student_wm.encoder.embed_dim) + 2 * len(student_angle_deg_indices) + 8
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
            student_actor = GRUActor(input_dim=actor_feat_dim, action_dim=spec.action_dim).to(student_device)
        else:
            student_actor = Actor(feat_dim=actor_feat_dim, action_dim=spec.action_dim).to(student_device)
        if "actor" not in ckpt:
            raise ValueError("student_checkpoint missing 'actor' weights")
        student_actor.load_state_dict(ckpt["actor"])
        student_actor.eval()

        obs_mean = ckpt.get("obs_mean", None)
        obs_std = ckpt.get("obs_std", None)
        if obs_mean is None or obs_std is None:
            raise ValueError("student_checkpoint missing obs_mean/obs_std (required for inference)")
        student_obs_mean = obs_mean.to(student_device).float() if isinstance(obs_mean, torch.Tensor) else torch.from_numpy(
            np.asarray(obs_mean, dtype=np.float32)
        ).to(student_device)
        student_obs_std = obs_std.to(student_device).float() if isinstance(obs_std, torch.Tensor) else torch.from_numpy(
            np.asarray(obs_std, dtype=np.float32)
        ).to(student_device)

        if args.include_visual:
            vmean = ckpt.get("visual_mean", None)
            vstd = ckpt.get("visual_std", None)
            if vmean is None or vstd is None:
                raise ValueError("student_checkpoint missing visual_mean/visual_std (required when --include_visual)")
            student_visual_mean = (
                vmean.to(student_device).float() if isinstance(vmean, torch.Tensor) else torch.from_numpy(np.asarray(vmean, dtype=np.float32)).to(student_device)
            )
            student_visual_std = (
                vstd.to(student_device).float() if isinstance(vstd, torch.Tensor) else torch.from_numpy(np.asarray(vstd, dtype=np.float32)).to(student_device)
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
        if str(args.policy) in ("dagger_scripted_takeoff", "dagger_scripted_stable_flight", "dagger_scripted_waypoint"):
            assert student_device is not None
            assert student_wm is not None
            assert student_actor is not None
            assert student_obs_mean is not None
            assert student_obs_std is not None
            vec0 = obs_vecs[-1]
            obs_t = torch.from_numpy(np.asarray(vec0, dtype=np.float32)).to(student_device).float().unsqueeze(0)
            obs_t = (obs_t - student_obs_mean.view(1, -1)) / student_obs_std.view(1, -1)
            obs_t = _apply_norm_clip(obs_t, student_obs_norm_clip)
            if args.include_visual:
                assert student_visual_mean is not None and student_visual_std is not None
                v0 = np.asarray(obs["visual"], dtype=np.float32)
                v0 = _downsample_visual(v0, int(args.visual_downsample))
                v0 = np.clip(v0, -10.0, 10.0).astype(np.float32, copy=False)
                vis_t = torch.from_numpy(v0).to(student_device).float().unsqueeze(0)  # (1,H,W,C)
                vis_t = (vis_t - student_visual_mean.view(1, 1, 1, -1)) / student_visual_std.view(1, 1, 1, -1)
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
                    student_embed0 = student_wm.encoder(obs_t, vis_t) if vis_t is not None else student_wm.encoder(obs_t)
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
                elif str(student_actor_input) in ("obs_gru", "obs_sincos_gru", "obs_sincos_track_gru"):
                    student_h = student_actor.init_h(batch_size=1, device=student_device)  # type: ignore[union-attr]

        max_steps = int(args.max_steps) if args.max_steps is not None else 10**9
        if str(args.policy) in ("scripted_stable_flight", "dagger_scripted_stable_flight", "scripted_waypoint", "dagger_scripted_waypoint"):
            stable_ctrl = ScriptedStableFlightController(
                action_dim=int(spec.action_dim), dt=float(getattr(env.sim, "get_time_step", lambda: 0.05)())
            )
            stable_ctrl.reset(obs)
        if str(args.policy) in ("scripted_takeoff", "dagger_scripted_takeoff"):
            takeoff_ctrl = ScriptedTakeoffController(
                action_dim=int(spec.action_dim), dt=float(getattr(env.sim, "get_time_step", lambda: 0.05)())
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
                    teacher_action_env = scripted_takeoff_action(obs, action_dim=int(spec.action_dim))
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
            elif str(args.policy) in ("dagger_scripted_takeoff", "dagger_scripted_stable_flight", "dagger_scripted_waypoint"):
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
                    obs_raw = torch.from_numpy(np.asarray(vec_cur, dtype=np.float32)).to(student_device).float().unsqueeze(0)
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
                    if str(student_actor_input) in ("obs_sincos_track_vis", "obs_sincos_track_vis_gru"):
                        assert student_embed0 is not None
                        vis_dim = int(getattr(student_wm.encoder, "visual_embed_dim", 0))
                        if vis_dim <= 0:
                            raise ValueError("student_actor_input='obs_sincos_track_vis*' requires a visual encoder")
                        vis_embed = student_embed0[:, -vis_dim:]
                        feat = torch.cat([feat, vis_embed], dim=-1)
                elif str(student_actor_input) in ("embed_sincos", "embed_sincos_gru"):
                    assert student_embed0 is not None
                    vec_cur = obs_vecs[-1]
                    obs_raw = torch.from_numpy(np.asarray(vec_cur, dtype=np.float32)).to(student_device).float().unsqueeze(0)
                    ang = angle_sincos_features(obs_raw, angle_deg_indices=student_angle_deg_indices)
                    feat = torch.cat([student_embed0, ang], dim=-1)
                elif str(student_actor_input) in ("embed_sincos_track", "embed_sincos_track_gru"):
                    assert student_embed0 is not None
                    vec_cur = obs_vecs[-1]
                    obs_raw = torch.from_numpy(np.asarray(vec_cur, dtype=np.float32)).to(student_device).float().unsqueeze(0)
                    ang = angle_sincos_features(obs_raw, angle_deg_indices=student_angle_deg_indices)
                    track = nav_tracking_features(obs_raw)
                    feat = torch.cat([student_embed0, ang, track], dim=-1)
                else:
                    assert student_embed0 is not None
                    feat = student_embed0
                with torch.no_grad():
                    if student_stochastic:
                        if str(student_actor_input) in ("embed_gru", "embed_sincos_gru", "embed_sincos_track_gru"):
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
                        if str(student_actor_input) in ("embed_gru", "embed_sincos_gru", "embed_sincos_track_gru"):
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
                student_action_norm = a_norm_t.squeeze(0).detach().cpu().numpy().astype(np.float32, copy=False)
                student_action_env = _unnormalize_action(student_action_norm, spec.action_low, spec.action_high)
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

            if teacher_action_env is not None and spec.action_low is not None and spec.action_high is not None:
                expert_action = _normalize_action(teacher_action_env, spec.action_low, spec.action_high)
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
                        max_abs_runway_cross_m = max(max_abs_runway_cross_m, abs(float(info.get("runway_cross_m", 0.0))))
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
            if str(args.policy) in ("dagger_scripted_takeoff", "dagger_scripted_stable_flight", "dagger_scripted_waypoint"):
                assert student_device is not None
                assert student_wm is not None
                assert student_obs_mean is not None and student_obs_std is not None
                next_vec = obs_vecs[-1]
                obs_t = torch.from_numpy(np.asarray(next_vec, dtype=np.float32)).to(student_device).float().unsqueeze(0)
                obs_t = (obs_t - student_obs_mean.view(1, -1)) / student_obs_std.view(1, -1)
                obs_t = _apply_norm_clip(obs_t, student_obs_norm_clip)
                if args.include_visual:
                    assert student_visual_mean is not None and student_visual_std is not None
                    v1 = np.asarray(next_obs["visual"], dtype=np.float32)
                    v1 = _downsample_visual(v1, int(args.visual_downsample))
                    v1 = np.clip(v1, -10.0, 10.0).astype(np.float32, copy=False)
                    vis_t = torch.from_numpy(v1).to(student_device).float().unsqueeze(0)
                    vis_t = (vis_t - student_visual_mean.view(1, 1, 1, -1)) / student_visual_std.view(1, 1, 1, -1)
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
                        embed_next = student_wm.encoder(obs_t, vis_t) if vis_t is not None else student_wm.encoder(obs_t)
                        if str(student_actor_input) == "rssm":
                            assert student_state is not None
                            a_t = torch.from_numpy(exec_action).to(student_device).float().unsqueeze(0)
                            student_state, _prior, _post = student_wm.rssm.obs_step(
                                student_state, a_t, embed_next, deterministic=student_deterministic_state
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
            if int(spec.get("obs_vec_dim", dataset.spec.obs_vec_dim)) != int(dataset.spec.obs_vec_dim):
                raise ValueError("Checkpoint obs_vec_dim does not match dataset spec")
        ckpt_cfg = ckpt.get("cfg", {}) if isinstance(ckpt, dict) else {}
    visual_encoder_type, visual_cnn_channels = _resolve_visual_encoder_settings(args=args, ckpt_cfg=ckpt_cfg)
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
        ckpt_actor_input = str(ckpt_cfg.get("actor_input", "rssm")) if isinstance(ckpt_cfg, dict) else "rssm"
        if bool(getattr(args, "reset_actor", False)):
            print(f"[train] reset actor weights (not loading from checkpoint): {ckpt_path}")
        elif "actor" in ckpt:
            if str(cfg.actor_input) == ckpt_actor_input:
                try:
                    trainer.actor.load_state_dict(ckpt["actor"])
                except RuntimeError:
                    # Backward compatibility: allow extending *_sincos inputs by changing angle_deg_indices.
                    # This only changes the actor feature representation (sin/cos channels), not the env.
                    try:
                        src = ckpt["actor"]
                        dst = trainer.actor.state_dict()
                        first_w = "net.net.0.weight"
                        if first_w in src and first_w in dst:
                            w_src = src[first_w]
                            w_dst = dst[first_w]
                            if (
                                isinstance(w_src, torch.Tensor)
                                and isinstance(w_dst, torch.Tensor)
                                and w_src.ndim == 2
                                and w_dst.ndim == 2
                                and w_src.shape[0] == w_dst.shape[0]
                                and w_dst.shape[1] >= w_src.shape[1]
                            ):
                                w_new = w_dst.clone()
                                w_new.zero_()
                                w_new[:, : w_src.shape[1]] = w_src
                                dst[first_w] = w_new
                                for k, v in src.items():
                                    if k == first_w:
                                        continue
                                    if k in dst and isinstance(v, torch.Tensor) and dst[k].shape == v.shape:
                                        dst[k] = v
                                trainer.actor.load_state_dict(dst)
                                print(
                                    f"[train] padded actor weights: {ckpt_actor_input} "
                                    f"(in={w_src.shape[1]} -> {w_dst.shape[1]})"
                                )
                            else:
                                raise RuntimeError("Cannot pad actor weights: incompatible first-layer shapes")
                        else:
                            raise RuntimeError("Cannot pad actor weights: missing first-layer key")
                    except Exception:
                        raise
            else:
                # Backward-compatible fine-tuning: allow extending the actor input with
                # extra engineered-but-realism-safe features while reusing a stable base policy.
                #
                # Example: embed -> embed_sincos (append sin/cos features). We copy all matching
                # parameters and pad the first linear layer with zeros for the new inputs, so the
                # initial behavior is identical to the base policy.
                if ckpt_actor_input == "embed" and str(cfg.actor_input) == "embed_sincos":
                    try:
                        src = ckpt["actor"]
                        dst = trainer.actor.state_dict()
                        first_w = "net.net.0.weight"
                        if first_w in src and first_w in dst:
                            w_src = src[first_w]
                            w_dst = dst[first_w]
                            if (
                                isinstance(w_src, torch.Tensor)
                                and isinstance(w_dst, torch.Tensor)
                                and w_src.ndim == 2
                                and w_dst.ndim == 2
                                and w_src.shape[0] == w_dst.shape[0]
                                and w_dst.shape[1] >= w_src.shape[1]
                            ):
                                w_new = w_dst.clone()
                                w_new.zero_()
                                w_new[:, : w_src.shape[1]] = w_src
                                dst[first_w] = w_new
                                # Copy remaining parameters when shapes match.
                                for k, v in src.items():
                                    if k == first_w:
                                        continue
                                    if k in dst and isinstance(v, torch.Tensor) and dst[k].shape == v.shape:
                                        dst[k] = v
                                trainer.actor.load_state_dict(dst)
                                print(
                                    f"[train] padded actor weights: {ckpt_actor_input} -> {cfg.actor_input} "
                                    f"(in={w_src.shape[1]} -> {w_dst.shape[1]})"
                                )
                    except Exception:
                        pass
                if ckpt_actor_input == "embed_sincos" and str(cfg.actor_input) == "embed_sincos_track":
                    try:
                        src = ckpt["actor"]
                        dst = trainer.actor.state_dict()
                        first_w = "net.net.0.weight"
                        if first_w in src and first_w in dst:
                            w_src = src[first_w]
                            w_dst = dst[first_w]
                            if (
                                isinstance(w_src, torch.Tensor)
                                and isinstance(w_dst, torch.Tensor)
                                and w_src.ndim == 2
                                and w_dst.ndim == 2
                                and w_src.shape[0] == w_dst.shape[0]
                                and w_dst.shape[1] >= w_src.shape[1]
                            ):
                                w_new = w_dst.clone()
                                w_new.zero_()
                                w_new[:, : w_src.shape[1]] = w_src
                                dst[first_w] = w_new
                                for k, v in src.items():
                                    if k == first_w:
                                        continue
                                    if k in dst and isinstance(v, torch.Tensor) and dst[k].shape == v.shape:
                                        dst[k] = v
                                trainer.actor.load_state_dict(dst)
                                print(
                                    f"[train] padded actor weights: {ckpt_actor_input} -> {cfg.actor_input} "
                                    f"(in={w_src.shape[1]} -> {w_dst.shape[1]})"
                                )
                    except Exception:
                        pass
        if "value" in ckpt:
            trainer.value.load_state_dict(ckpt["value"])
        # IMPORTANT: The world model encoder is trained on normalized observations.
        # If we resume from a checkpoint but use a different dataset (with different stats),
        # the checkpoint weights become incompatible and rollouts can fail catastrophically.
        #
        # Default behavior: reuse the checkpoint's normalization stats unless the user
        # explicitly requests a recomputation via --recompute_stats.
        if not bool(getattr(args, "recompute_stats", False)):
            try:
                obs_mean = ckpt.get("obs_mean", None)
                obs_std = ckpt.get("obs_std", None)
                if obs_mean is not None and obs_std is not None:
                    obs_mean_t = torch.as_tensor(obs_mean, device=device, dtype=torch.float32).reshape(-1)
                    obs_std_t = torch.as_tensor(obs_std, device=device, dtype=torch.float32).reshape(-1)
                    if trainer.obs_mean is not None and trainer.obs_std is not None:
                        if obs_mean_t.shape == trainer.obs_mean.shape and obs_std_t.shape == trainer.obs_std.shape:
                            trainer.obs_mean = obs_mean_t
                            trainer.obs_std = torch.maximum(obs_std_t, torch.as_tensor(cfg.obs_min_std, device=device))

                if dataset.spec.visual_shape is not None:
                    visual_mean = ckpt.get("visual_mean", None)
                    visual_std = ckpt.get("visual_std", None)
                    if visual_mean is not None and visual_std is not None:
                        visual_mean_t = torch.as_tensor(visual_mean, device=device, dtype=torch.float32).reshape(-1)
                        visual_std_t = torch.as_tensor(visual_std, device=device, dtype=torch.float32).reshape(-1)
                        if trainer.visual_mean is not None and trainer.visual_std is not None:
                            if (
                                visual_mean_t.shape == trainer.visual_mean.shape
                                and visual_std_t.shape == trainer.visual_std.shape
                            ):
                                trainer.visual_mean = visual_mean_t
                                trainer.visual_std = torch.maximum(
                                    visual_std_t, torch.as_tensor(cfg.visual_min_std, device=device)
                                )
            except Exception:
                pass
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
                "visual_mean": (trainer.visual_mean.detach().cpu() if trainer.visual_mean is not None else None),
                "visual_std": (trainer.visual_std.detach().cpu() if trainer.visual_std is not None else None),
                "cfg": asdict(cfg),
                "spec": asdict(dataset.spec),
            }
            torch.save(ckpt, os.path.join(args.run_dir, "checkpoint.pt"))


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
    visual_encoder_type, visual_cnn_channels = _resolve_visual_encoder_settings(args=args, ckpt_cfg=ckpt_cfg)

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
        ckpt_actor_input = str(ckpt_cfg.get("actor_input", "rssm")) if isinstance(ckpt_cfg, dict) else "rssm"
        if "actor" in ckpt and str(cfg.actor_input) == ckpt_actor_input:
            try:
                trainer.actor.load_state_dict(ckpt["actor"])
            except RuntimeError:
                try:
                    src = ckpt["actor"]
                    dst = trainer.actor.state_dict()
                    first_w = "net.net.0.weight"
                    if first_w in src and first_w in dst:
                        w_src = src[first_w]
                        w_dst = dst[first_w]
                        if (
                            isinstance(w_src, torch.Tensor)
                            and isinstance(w_dst, torch.Tensor)
                            and w_src.ndim == 2
                            and w_dst.ndim == 2
                            and w_src.shape[0] == w_dst.shape[0]
                            and w_dst.shape[1] >= w_src.shape[1]
                        ):
                            w_new = w_dst.clone()
                            w_new.zero_()
                            w_new[:, : w_src.shape[1]] = w_src
                            dst[first_w] = w_new
                            for k, v in src.items():
                                if k == first_w:
                                    continue
                                if k in dst and isinstance(v, torch.Tensor) and dst[k].shape == v.shape:
                                    dst[k] = v
                            trainer.actor.load_state_dict(dst)
                            print(
                                f"[online] padded actor weights: {ckpt_actor_input} "
                                f"(in={w_src.shape[1]} -> {w_dst.shape[1]})"
                            )
                        else:
                            raise RuntimeError("Cannot pad actor weights: incompatible first-layer shapes")
                    else:
                        raise RuntimeError("Cannot pad actor weights: missing first-layer key")
                except Exception:
                    raise
        if "value" in ckpt:
            trainer.value.load_state_dict(ckpt["value"])
        # See train_world_model(): keep checkpoint normalization stats by default, otherwise
        # the resumed encoder can become incompatible with the new dataset stats.
        if not bool(getattr(args, "recompute_stats", False)):
            try:
                obs_mean = ckpt.get("obs_mean", None)
                obs_std = ckpt.get("obs_std", None)
                if obs_mean is not None and obs_std is not None:
                    obs_mean_t = torch.as_tensor(obs_mean, device=device, dtype=torch.float32).reshape(-1)
                    obs_std_t = torch.as_tensor(obs_std, device=device, dtype=torch.float32).reshape(-1)
                    if trainer.obs_mean is not None and trainer.obs_std is not None:
                        if obs_mean_t.shape == trainer.obs_mean.shape and obs_std_t.shape == trainer.obs_std.shape:
                            trainer.obs_mean = obs_mean_t
                            trainer.obs_std = torch.maximum(obs_std_t, torch.as_tensor(cfg.obs_min_std, device=device))

                if dataset.spec.visual_shape is not None:
                    visual_mean = ckpt.get("visual_mean", None)
                    visual_std = ckpt.get("visual_std", None)
                    if visual_mean is not None and visual_std is not None:
                        visual_mean_t = torch.as_tensor(visual_mean, device=device, dtype=torch.float32).reshape(-1)
                        visual_std_t = torch.as_tensor(visual_std, device=device, dtype=torch.float32).reshape(-1)
                        if trainer.visual_mean is not None and trainer.visual_std is not None:
                            if (
                                visual_mean_t.shape == trainer.visual_mean.shape
                                and visual_std_t.shape == trainer.visual_std.shape
                            ):
                                trainer.visual_mean = visual_mean_t
                                trainer.visual_std = torch.maximum(
                                    visual_std_t, torch.as_tensor(cfg.visual_min_std, device=device)
                                )
            except Exception:
                pass
        print(f"[online] loaded checkpoint {ckpt_path}")

    include_visual = dataset.spec.visual_shape is not None
    env = UniversalEnv(
        args.scenario,
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
            raise ValueError(f"Cannot downsample env visual {env_visual_shape} -> {dataset.spec.visual_shape}")
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
            vis_t = (vis_t - trainer.visual_mean.view(1, 1, 1, -1)) / trainer.visual_std.view(1, 1, 1, -1)
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
                embed0 = trainer.wm.encoder(obs_t, vis_t) if vis_t is not None else trainer.wm.encoder(obs_t)
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
                dt = float(env.sim.get_time_step())
            except Exception:
                dt = 0.05
            if expert_labels == "scripted_takeoff":
                expert_ctrl = ScriptedTakeoffController(action_dim=int(dataset.spec.action_dim), dt=dt)
                expert_ctrl.reset(obs)
            elif expert_labels == "scripted_stable_flight":
                expert_ctrl = ScriptedStableFlightController(action_dim=int(dataset.spec.action_dim), dt=dt)
                expert_ctrl.reset(obs)
            elif expert_labels == "scripted_waypoint":
                # Waypoint navigation uses the same realism-first controller: it tracks the mission heading/alt/speed,
                # and for command_code==3 the ScenarioLoader updates the mission heading to "bearing-to-waypoint".
                expert_ctrl = ScriptedStableFlightController(action_dim=int(dataset.spec.action_dim), dt=dt)
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
                        raise ValueError("actor_input='obs_sincos_track_vis' requires a visual encoder")
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
                        raise ValueError("actor_input='obs_sincos_track_vis_gru' requires a visual encoder")
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
                    ang = angle_sincos_features(obs_raw_t, angle_deg_indices=trainer.angle_deg_indices)
                    feat = torch.cat([embed0, ang], dim=-1)
                    if args.deterministic:
                        mean, _std = trainer.actor(feat)  # type: ignore[union-attr]
                        action_norm = torch.tanh(mean)
                    else:
                        action_norm, _logp = trainer.actor.sample(feat)  # type: ignore[union-attr]
                elif actor_input == "embed_sincos_track":
                    assert embed0 is not None
                    ang = angle_sincos_features(obs_raw_t, angle_deg_indices=trainer.angle_deg_indices)
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
                    ang = angle_sincos_features(obs_raw_t, angle_deg_indices=trainer.angle_deg_indices)
                    feat = torch.cat([embed0, ang], dim=-1)
                    if args.deterministic:
                        mean, _std, actor_h = trainer.actor.step(feat, actor_h)  # type: ignore[union-attr]
                        action_norm = torch.tanh(mean)
                    else:
                        action_norm, _logp, actor_h = trainer.actor.sample_step(feat, actor_h)  # type: ignore[union-attr]
                elif actor_input == "embed_sincos_track_gru":
                    assert embed0 is not None
                    ang = angle_sincos_features(obs_raw_t, angle_deg_indices=trainer.angle_deg_indices)
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
                vis_next = (vis_next - trainer.visual_mean.view(1, 1, 1, -1)) / trainer.visual_std.view(1, 1, 1, -1)
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
                    embed_next = trainer.wm.encoder(next_t, vis_next) if vis_next is not None else trainer.wm.encoder(next_t)

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
            actions=np.stack(actions, axis=0) if actions else np.zeros((0, dataset.spec.action_dim), dtype=np.float32),
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
                "visual_mean": (trainer.visual_mean.detach().cpu() if trainer.visual_mean is not None else None),
                "visual_std": (trainer.visual_std.detach().cpu() if trainer.visual_std is not None else None),
                "cfg": asdict(cfg),
                "spec": asdict(dataset.spec),
            }
            torch.save(ckpt, os.path.join(args.run_dir, "checkpoint.pt"))


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
        raise ValueError("Checkpoint is missing action_low/action_high; re-collect dataset with the updated collector.")
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
            raise ValueError("This checkpoint expects ARB visual input; run rollout with --include_visual.")
        if visual_mean is None or visual_std is None:
            raise ValueError("Checkpoint missing visual_mean/visual_std; retrain with updated trainer.")
        visual_mean_t = torch.as_tensor(visual_mean, device=device, dtype=torch.float32).reshape(1, 1, 1, -1)
        visual_std_t = torch.as_tensor(visual_std, device=device, dtype=torch.float32).reshape(1, 1, 1, -1)
    else:
        visual_mean_t = None
        visual_std_t = None

    env = UniversalEnv(
        args.scenario,
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
            raise ValueError(f"obs_vec_dim mismatch: got {obs_vec.shape[0]}, expected {obs_vec_dim}")

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
                raise ValueError(f"Unexpected env visual shape {visual.shape}, expected {env_visual_shape}")
            h, w, c = visual_shape
            if visual.shape[0] % h != 0 or visual.shape[1] % w != 0:
                raise ValueError(f"Cannot downsample env visual {visual.shape} -> {visual_shape}")
            factor_h = visual.shape[0] // h
            factor_w = visual.shape[1] // w
            if factor_h != factor_w:
                raise ValueError(f"Non-uniform visual downsample factors: h={factor_h}, w={factor_w}")
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
                    max_abs_cross_m = max(max_abs_cross_m, abs(float(last_info.get("runway_cross_m", 0.0))))
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
                embed_next = wm.encoder(next_t, vis_next) if vis_next is not None else wm.encoder(next_t)
                if actor_input == "rssm":
                    assert state is not None
                    a_t = torch.from_numpy(action_np).to(device).float().unsqueeze(0)
                    state, _prior, _post = wm.rssm.obs_step(state, a_t, embed_next, deterministic=deterministic_state)
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
        print(f"[rollout] ep={ep} steps={steps} ep_rew={ep_rew:.2f}{inst_str}{peak_str}{metric_str}{runway_str}{outcome_str}{ms_str}")

    if total_rewards:
        arr = np.asarray(total_rewards, dtype=np.float32)
        print(f"[rollout] mean={arr.mean():.2f} std={arr.std():.2f} min={arr.min():.2f} max={arr.max():.2f}")
        if int(args.episodes) > 0:
            known = successes + failures
            if known > 0:
                print(f"[rollout] success_rate={successes}/{int(args.episodes)} known={known}")


def main() -> None:
    p = argparse.ArgumentParser(description="Initial world-model (Dreamer-style) training for CMO")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_collect = sub.add_parser("collect", help="Collect an offline dataset from the env")
    p_collect.add_argument("--scenario", required=True)
    p_collect.add_argument("--out_dir", required=True)
    p_collect.add_argument("--episodes", type=int, default=10)
    p_collect.add_argument("--max_steps", type=int, default=None)
    p_collect.add_argument("--seed", type=int, default=0)
    p_collect.add_argument("--action_mode", type=str, default="full", choices=["full", "takeoff2", "takeoff4"])
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
    p_collect.add_argument("--no_randomization", action="store_true", help="Disable wind/world-yaw randomization")
    p_collect.add_argument("--curriculum", type=str, default=None, help="Path to randomization curriculum JSON")
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

    p_train = sub.add_parser("train", help="Train world model (and optionally the policy) from a dataset")
    p_train.add_argument("--dataset_dir", required=True)
    p_train.add_argument("--run_dir", required=True)
    p_train.add_argument("--checkpoint", type=str, default=None, help="Optional checkpoint.pt to resume from")
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
    p_train.add_argument("--bc_scale", type=float, default=0.0, help="Behavior cloning regularizer for offline stability")
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
    p_train.add_argument("--preset", type=str, default="default", choices=["default", "takeoff_stable"])
    p_train.add_argument("--log_compact", action="store_true")
    p_train.add_argument(
        "--recompute_stats",
        action="store_true",
        help="Recompute dataset normalization stats and overwrite stats.npz (use after appending new episodes).",
    )
    p_train.add_argument("--log_every", type=int, default=50)
    p_train.add_argument("--save_every", type=int, default=500)

    p_online = sub.add_parser("online", help="Online training: interleave env rollouts with training")
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
    p_online.add_argument("--action_mode", type=str, default="full", choices=["full", "takeoff2", "takeoff4"])
    p_online.add_argument(
        "--include_proprio",
        action="store_true",
        help="Include previous action (proprioception) in observations; must match how the dataset was collected.",
    )
    p_online.add_argument("--preset", type=str, default="default", choices=["default", "takeoff_stable"])
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
    p_online.add_argument("--no_randomization", action="store_true", help="Disable wind/world-yaw randomization")
    p_online.add_argument("--curriculum", type=str, default=None, help="Path to randomization curriculum JSON")
    p_online.add_argument("--log_every", type=int, default=50)
    p_online.add_argument("--save_every", type=int, default=500)

    p_roll = sub.add_parser("rollout", help="Roll out a trained world-model policy in the real env")
    p_roll.add_argument("--scenario", required=True)
    p_roll.add_argument("--checkpoint", required=True)
    p_roll.add_argument("--episodes", type=int, default=3)
    p_roll.add_argument("--max_steps", type=int, default=2000)
    p_roll.add_argument("--seed", type=int, default=0)
    p_roll.add_argument("--device", type=str, default="cuda")
    p_roll.add_argument("--action_mode", type=str, default="full", choices=["full", "takeoff2", "takeoff4"])
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
    p_roll.add_argument("--no_randomization", action="store_true", help="Disable wind/world-yaw randomization")

    args = p.parse_args()
    if args.cmd == "collect":
        collect_dataset(args)
    elif args.cmd == "train":
        train_world_model(args)
    elif args.cmd == "online":
        online_train(args)
    elif args.cmd == "rollout":
        rollout_policy(args)
    else:  # pragma: no cover
        raise ValueError(args.cmd)


if __name__ == "__main__":
    main()
