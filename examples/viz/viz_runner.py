import eventlet
eventlet.monkey_patch()

import argparse
import os
import sys
import time

from flask import Flask, render_template
from flask_socketio import SocketIO

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
build_dir = os.path.join(repo_root, "build")

# Prefer the locally built `ef_py` extension when present.
if os.path.isdir(build_dir) and any(fname.startswith("ef_py") and fname.endswith(".so") for fname in os.listdir(build_dir)):
    sys.path.insert(0, build_dir)
sys.path.insert(0, repo_root)

# Import ef_py before numpy/torch-heavy libs
import ef_py
import numpy as np
# Import Universal Env
from gym_envs.universal_env import UniversalEnv, half_to_unit
from python.models.transformer import TransformerExtractor
from python.world_model.features import (
    DEFAULT_ANGLE_DEG_INDICES,
    angle_sincos_features,
    append_angle_sincos_features,
    nav_tracking_features,
)


def _flatten_obs(obs: dict) -> np.ndarray:
    inst = np.asarray(obs["instruments"], dtype=np.float32).reshape(-1)
    mission = np.asarray(obs["mission"], dtype=np.float32).reshape(-1)
    proprio = np.asarray(obs.get("proprio", []), dtype=np.float32).reshape(-1)
    if proprio.size > 0:
        return np.concatenate([inst, mission, proprio], axis=0).astype(np.float32, copy=False)
    return np.concatenate([inst, mission], axis=0).astype(np.float32, copy=False)


def _downsample_visual(visual: np.ndarray, factor: int) -> np.ndarray:
    if factor <= 1:
        return visual
    h, w, c = visual.shape
    if h % factor != 0 or w % factor != 0:
        raise ValueError(f"visual shape {visual.shape} not divisible by downsample factor {factor}")
    nh, nw = h // factor, w // factor
    return visual.reshape(nh, factor, nw, factor, c).mean(axis=(1, 3))


def _unnormalize_action(action: np.ndarray, low: np.ndarray, high: np.ndarray) -> np.ndarray:
    action = np.asarray(action, dtype=np.float32).reshape(-1)
    low = np.asarray(low, dtype=np.float32).reshape(-1)
    high = np.asarray(high, dtype=np.float32).reshape(-1)
    out = low + 0.5 * (action + 1.0) * (high - low)
    return np.clip(out, low, high).astype(np.float32, copy=False)


class _WorldModelPolicy:
    def __init__(self, checkpoint_path: str, *, device: str = "cpu"):
        import torch

        from python.world_model.networks import Actor, GRUActor, WorldModel

        self.device = torch.device(device)
        try:
            ckpt = torch.load(checkpoint_path, map_location=self.device, weights_only=False)
        except TypeError:
            ckpt = torch.load(checkpoint_path, map_location=self.device)

        cfg = ckpt.get("cfg", {}) if isinstance(ckpt, dict) else {}
        if not isinstance(cfg, dict):
            cfg = {}
        self.actor_input = str(cfg.get("actor_input", "rssm"))
        self.angle_deg_indices = DEFAULT_ANGLE_DEG_INDICES
        try:
            self.angle_deg_indices = tuple(int(x) for x in cfg.get("angle_deg_indices", DEFAULT_ANGLE_DEG_INDICES))
        except Exception:
            self.angle_deg_indices = DEFAULT_ANGLE_DEG_INDICES
        self.obs_norm_clip = cfg.get("obs_norm_clip", None)
        self.visual_norm_clip = cfg.get("visual_norm_clip", None)

        spec = ckpt.get("spec", {})
        self.action_dim = int(spec.get("action_dim", 17))
        self.obs_vec_dim = int(spec.get("obs_vec_dim", 46))
        self.visual_shape = spec.get("visual_shape", None)
        if self.visual_shape is not None:
            self.visual_shape = tuple(int(x) for x in self.visual_shape)

        action_low = spec.get("action_low", None)
        action_high = spec.get("action_high", None)
        if action_low is None or action_high is None:
            raise ValueError(
                "World-model checkpoint is missing action_low/action_high; "
                "re-collect the dataset with the updated collector and retrain."
            )
        self.action_low = np.asarray(action_low, dtype=np.float32).reshape(-1)
        self.action_high = np.asarray(action_high, dtype=np.float32).reshape(-1)

        obs_mean = ckpt.get("obs_mean", None)
        obs_std = ckpt.get("obs_std", None)
        if obs_mean is None or obs_std is None:
            raise ValueError("World-model checkpoint missing obs_mean/obs_std.")
        self.obs_mean = torch.as_tensor(obs_mean, device=self.device, dtype=torch.float32).reshape(1, -1)
        self.obs_std = torch.as_tensor(obs_std, device=self.device, dtype=torch.float32).reshape(1, -1)

        self.visual_mean = None
        self.visual_std = None
        if self.visual_shape is not None:
            visual_mean = ckpt.get("visual_mean", None)
            visual_std = ckpt.get("visual_std", None)
            if visual_mean is None or visual_std is None:
                raise ValueError("World-model checkpoint missing visual_mean/visual_std.")
            visual_mean_t = torch.as_tensor(visual_mean, device=self.device, dtype=torch.float32).reshape(-1)
            visual_std_t = torch.as_tensor(visual_std, device=self.device, dtype=torch.float32).reshape(-1)
            self.visual_mean = visual_mean_t.view(1, 1, 1, -1)
            self.visual_std = visual_std_t.view(1, 1, 1, -1)

        self.wm = WorldModel(action_dim=self.action_dim, obs_vec_dim=self.obs_vec_dim, visual_shape=self.visual_shape).to(
            self.device
        )
        self.wm.load_state_dict(ckpt["world_model"])
        self.wm.eval()

        rssm_feat_dim = int(self.wm.rssm.deter_dim + self.wm.rssm.stoch_dim)
        if self.actor_input in ("obs", "obs_gru"):
            actor_feat_dim = int(self.obs_vec_dim)
        elif self.actor_input in ("obs_sincos", "obs_sincos_gru"):
            actor_feat_dim = int(self.obs_vec_dim) + 2 * len(self.angle_deg_indices)
        elif self.actor_input in ("obs_sincos_track", "obs_sincos_track_gru"):
            actor_feat_dim = int(self.obs_vec_dim) + 2 * len(self.angle_deg_indices) + 8
        elif self.actor_input in ("obs_sincos_track_vis", "obs_sincos_track_vis_gru"):
            if self.wm.encoder.visual is None:
                raise ValueError("actor_input='obs_sincos_track_vis*' requires visual input")
            actor_feat_dim = int(self.obs_vec_dim) + 2 * len(self.angle_deg_indices) + 8 + int(
                getattr(self.wm.encoder, "visual_embed_dim", 0)
            )
        elif self.actor_input in ("embed_sincos", "embed_sincos_gru"):
            actor_feat_dim = int(self.wm.encoder.embed_dim) + 2 * len(self.angle_deg_indices)
        elif self.actor_input in ("embed_sincos_track", "embed_sincos_track_gru"):
            actor_feat_dim = int(self.wm.encoder.embed_dim) + 2 * len(self.angle_deg_indices) + 8
        elif self.actor_input in ("embed", "embed_gru"):
            actor_feat_dim = int(self.wm.encoder.embed_dim)
        else:
            actor_feat_dim = rssm_feat_dim
        if self.actor_input in (
            "embed_gru",
            "embed_sincos_gru",
            "embed_sincos_track_gru",
            "obs_gru",
            "obs_sincos_gru",
            "obs_sincos_track_gru",
            "obs_sincos_track_vis_gru",
        ):
            self.actor = GRUActor(input_dim=actor_feat_dim, action_dim=self.action_dim).to(self.device)
        else:
            self.actor = Actor(feat_dim=actor_feat_dim, action_dim=self.action_dim).to(self.device)
        self.actor.load_state_dict(ckpt["actor"])
        self.actor.eval()

        self._factor = None
        self._state = None
        self._last_embed = None
        self._last_obs_t = None
        self._last_obs_raw_t = None
        self._last_action_norm = None
        self._h = None

    def _apply_norm_clip(self, t, clip):
        import torch

        if clip is None:
            return t
        return torch.clamp(t, -float(clip), float(clip))

    def _encode_obs(self, obs: dict, *, need_embed: bool = True):
        import torch

        obs_vec = _flatten_obs(obs)
        obs_raw_t = torch.from_numpy(obs_vec).to(self.device).float().unsqueeze(0)
        obs_t = (obs_raw_t - self.obs_mean) / self.obs_std
        obs_t = self._apply_norm_clip(obs_t, self.obs_norm_clip)
        self._last_obs_t = obs_t
        self._last_obs_raw_t = obs_raw_t

        if self.visual_shape is not None and need_embed:
            visual = np.asarray(obs["visual"], dtype=np.float32)
            if self._factor is None:
                self._factor = self._ensure_visual_factor(visual)
            visual = _downsample_visual(visual, int(self._factor))
            visual = np.clip(visual, -10.0, 10.0).astype(np.float32, copy=False)
            vis_t = torch.from_numpy(visual).to(self.device).float().unsqueeze(0)
            vis_t = (vis_t - self.visual_mean) / self.visual_std  # type: ignore[operator]
            vis_t = self._apply_norm_clip(vis_t, self.visual_norm_clip)
            vis_t = vis_t.reshape(1, -1)
        else:
            vis_t = None

        if not need_embed:
            return None

        with torch.no_grad():
            return self.wm.encoder(obs_t, vis_t) if vis_t is not None else self.wm.encoder(obs_t)

    def _ensure_visual_factor(self, visual: np.ndarray) -> int:
        if self.visual_shape is None:
            return 1
        h, w, c = self.visual_shape
        if visual.shape[0] % h != 0 or visual.shape[1] % w != 0:
            raise ValueError(f"Cannot downsample env visual {visual.shape} -> {self.visual_shape}")
        factor_h = visual.shape[0] // h
        factor_w = visual.shape[1] // w
        if factor_h != factor_w:
            raise ValueError(f"Non-uniform visual downsample factors: h={factor_h}, w={factor_w}")
        if int(visual.shape[2]) != int(c):
            raise ValueError(f"Visual channel mismatch: env C={visual.shape[2]}, expected {c}")
        return int(factor_h)

    def reset(self, obs: dict) -> None:
        import torch

        embed0 = None
        if self.actor_input in (
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
            embed0 = self._encode_obs(obs, need_embed=True)
            self._last_embed = embed0
        else:
            self._encode_obs(obs, need_embed=False)
            self._last_embed = None

        self._state = None
        if self.actor_input == "rssm":
            assert embed0 is not None
            with torch.no_grad():
                self._state, _ = self.wm.rssm.observe_init(embed0)
        self._last_action_norm = None
        self._h = None
        if self.actor_input in (
            "embed_gru",
            "embed_sincos_gru",
            "embed_sincos_track_gru",
            "obs_gru",
            "obs_sincos_gru",
            "obs_sincos_track_gru",
            "obs_sincos_track_vis_gru",
        ):
            self._h = self.actor.init_h(batch_size=1, device=self.device)  # type: ignore[union-attr]

    def predict(self, obs: dict, *, deterministic: bool = True):
        import torch

        if self.actor_input == "obs":
            self._encode_obs(obs, need_embed=False)
            feat = self._last_obs_t
            if feat is None:
                self.reset(obs)
                feat = self._last_obs_t
        elif self.actor_input == "obs_gru":
            self._encode_obs(obs, need_embed=False)
            feat = self._last_obs_t
            if feat is None:
                self.reset(obs)
                feat = self._last_obs_t
        elif self.actor_input == "obs_sincos":
            self._encode_obs(obs, need_embed=False)
            if self._last_obs_t is None or self._last_obs_raw_t is None:
                self.reset(obs)
            feat = append_angle_sincos_features(
                obs_raw_deg=self._last_obs_raw_t,
                obs_norm=self._last_obs_t,
                angle_deg_indices=self.angle_deg_indices,
            )
        elif self.actor_input == "obs_sincos_gru":
            self._encode_obs(obs, need_embed=False)
            if self._last_obs_t is None or self._last_obs_raw_t is None:
                self.reset(obs)
            feat = append_angle_sincos_features(
                obs_raw_deg=self._last_obs_raw_t,
                obs_norm=self._last_obs_t,
                angle_deg_indices=self.angle_deg_indices,
            )
        elif self.actor_input == "obs_sincos_track":
            self._encode_obs(obs, need_embed=False)
            if self._last_obs_t is None or self._last_obs_raw_t is None:
                self.reset(obs)
            base = append_angle_sincos_features(
                obs_raw_deg=self._last_obs_raw_t,
                obs_norm=self._last_obs_t,
                angle_deg_indices=self.angle_deg_indices,
            )
            track = nav_tracking_features(self._last_obs_raw_t)
            feat = torch.cat([base, track], dim=-1)
        elif self.actor_input == "obs_sincos_track_gru":
            self._encode_obs(obs, need_embed=False)
            if self._last_obs_t is None or self._last_obs_raw_t is None:
                self.reset(obs)
            base = append_angle_sincos_features(
                obs_raw_deg=self._last_obs_raw_t,
                obs_norm=self._last_obs_t,
                angle_deg_indices=self.angle_deg_indices,
            )
            track = nav_tracking_features(self._last_obs_raw_t)
            feat = torch.cat([base, track], dim=-1)
        elif self.actor_input == "obs_sincos_track_vis":
            embed = self._encode_obs(obs, need_embed=True)
            self._last_embed = embed
            if self._last_obs_t is None or self._last_obs_raw_t is None or embed is None:
                self.reset(obs)
                embed = self._last_embed
            base = append_angle_sincos_features(
                obs_raw_deg=self._last_obs_raw_t,
                obs_norm=self._last_obs_t,
                angle_deg_indices=self.angle_deg_indices,
            )
            track = nav_tracking_features(self._last_obs_raw_t)
            vis_dim = int(getattr(self.wm.encoder, "visual_embed_dim", 0))
            if vis_dim <= 0:
                raise ValueError("actor_input='obs_sincos_track_vis' requires visual embedding")
            vis_embed = embed[:, -vis_dim:]
            feat = torch.cat([base, track, vis_embed], dim=-1)
        elif self.actor_input == "obs_sincos_track_vis_gru":
            embed = self._encode_obs(obs, need_embed=True)
            self._last_embed = embed
            if self._last_obs_t is None or self._last_obs_raw_t is None or embed is None:
                self.reset(obs)
                embed = self._last_embed
            base = append_angle_sincos_features(
                obs_raw_deg=self._last_obs_raw_t,
                obs_norm=self._last_obs_t,
                angle_deg_indices=self.angle_deg_indices,
            )
            track = nav_tracking_features(self._last_obs_raw_t)
            vis_dim = int(getattr(self.wm.encoder, "visual_embed_dim", 0))
            if vis_dim <= 0:
                raise ValueError("actor_input='obs_sincos_track_vis_gru' requires visual embedding")
            vis_embed = embed[:, -vis_dim:]
            feat = torch.cat([base, track, vis_embed], dim=-1)
        elif self.actor_input in ("embed", "embed_gru"):
            feat = self._encode_obs(obs, need_embed=True)
            self._last_embed = feat
        elif self.actor_input in ("embed_sincos", "embed_sincos_gru"):
            embed = self._encode_obs(obs, need_embed=True)
            self._last_embed = embed
            if self._last_obs_raw_t is None:
                self.reset(obs)
                embed = self._last_embed
            ang = angle_sincos_features(self._last_obs_raw_t, angle_deg_indices=self.angle_deg_indices)
            feat = torch.cat([embed, ang], dim=-1)
        elif self.actor_input in ("embed_sincos_track", "embed_sincos_track_gru"):
            embed = self._encode_obs(obs, need_embed=True)
            self._last_embed = embed
            if self._last_obs_raw_t is None:
                self.reset(obs)
                embed = self._last_embed
            ang = angle_sincos_features(self._last_obs_raw_t, angle_deg_indices=self.angle_deg_indices)
            track = nav_tracking_features(self._last_obs_raw_t)
            feat = torch.cat([embed, ang, track], dim=-1)
        else:
            if self._state is None:
                self.reset(obs)
            feat = self.wm.feat(self._state)
        with torch.no_grad():
            if deterministic:
                if self.actor_input in (
                    "embed_gru",
                    "embed_sincos_gru",
                    "embed_sincos_track_gru",
                    "obs_gru",
                    "obs_sincos_gru",
                    "obs_sincos_track_gru",
                    "obs_sincos_track_vis_gru",
                ):
                    mean, _std, self._h = self.actor.step(feat, self._h)  # type: ignore[union-attr]
                    action_norm = torch.tanh(mean)
                else:
                    mean, _std = self.actor(feat)  # type: ignore[union-attr]
                    action_norm = torch.tanh(mean)
            else:
                if self.actor_input in (
                    "embed_gru",
                    "embed_sincos_gru",
                    "embed_sincos_track_gru",
                    "obs_gru",
                    "obs_sincos_gru",
                    "obs_sincos_track_gru",
                    "obs_sincos_track_vis_gru",
                ):
                    action_norm, _logp, self._h = self.actor.sample_step(feat, self._h)  # type: ignore[union-attr]
                else:
                    action_norm, _logp = self.actor.sample(feat)  # type: ignore[union-attr]
        action_np = action_norm.squeeze(0).detach().cpu().numpy().astype(np.float32, copy=False)
        self._last_action_norm = action_np
        action_env = _unnormalize_action(action_np, self.action_low, self.action_high)
        return action_env, None

    def observe(self, obs: dict) -> None:
        if self.actor_input in (
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
        ):
            # No RSSM roll-forward needed for reactive embedding policies.
            return
        if self._state is None or self._last_action_norm is None:
            self.reset(obs)
            return

        import torch

        embed_next = self._encode_obs(obs, need_embed=True)
        with torch.no_grad():
            a_t = torch.from_numpy(self._last_action_norm).to(self.device).float().unsqueeze(0)
            self._state, _prior, _post = self.wm.rssm.obs_step(self._state, a_t, embed_next)

# Setup Web Server
base_dir = os.path.abspath(os.path.dirname(__file__))
# We will use the generic 'index.html' (2D) as default, but allow switching
template_dir = os.path.join(base_dir, "web_viz/templates")
static_dir = os.path.join(base_dir, "web_viz/static")

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Globals
simulation_running = False
simulation_paused = False
env = None
model = None
episode_return = 0.0
episode_return = 0.0
args = None
map_data = None
nav_data = None

@socketio.on('connect')
def handle_connect():
    print("Client Connected")
    global map_data
    if map_data:
        print(f"Sending cached map data ({len(map_data['zones'])} zones) to new client")
        socketio.emit('map_setup', map_data)
    global nav_data
    if nav_data:
        socketio.emit("nav_setup", nav_data)

@socketio.on('start_sim')
def handle_start_sim():
    global simulation_running, simulation_paused
    print("Start Signal Received")
    simulation_running = True
    simulation_paused = False

@socketio.on('pause_sim')
def handle_pause_sim():
    global simulation_paused
    print("Pause Signal Received")
    simulation_paused = True

@socketio.on('resume_sim')
def handle_resume_sim():
    global simulation_paused
    print("Resume Signal Received")
    simulation_paused = False

@app.route('/')
def index():
    # Universal 3D Viewer
    return render_template('index.html')

def simulation_loop():
    global simulation_running, simulation_paused, env, model, episode_return, args, nav_data
    
    # Load Model if provided
    if args.model and os.path.exists(args.model):
        try:
            model_path = args.model
            if model_path.endswith((".pt", ".pth")):
                print(f"Loading world-model policy from {model_path}...")
                model = _WorldModelPolicy(model_path, device="cpu")
            else:
                print(f"Loading PPO model from {model_path}...")
                from stable_baselines3 import PPO

                if model_path.endswith(".zip"):
                    model_path = model_path[:-4]
                model = PPO.load(model_path, device="cpu")
        except Exception as e:
            print(f"Error loading model: {e}")
            model = None
    else:
        print("No model loaded. Running with random/noop actions.")
        model = None

    action_mode = args.action_mode
    if action_mode == "auto":
        act_dim = None
        if model is not None:
            act_dim = getattr(model, "action_dim", None)
            if act_dim is None:
                act_space = getattr(model, "action_space", None)
                act_shape = getattr(act_space, "shape", None)
                act_dim = int(act_shape[0]) if act_shape and len(act_shape) == 1 else None
        if act_dim == 2:
            action_mode = "takeoff2"
        elif act_dim == 4:
            action_mode = "takeoff4"
        else:
            action_mode = "full"

    print(f"Initializing Universal Environment with scenario: {args.scenario} (action_mode={action_mode})")
    env = UniversalEnv(
        args.scenario,
        action_mode=action_mode,
        include_visual=True,
        include_proprio=bool(getattr(args, "include_proprio", False)),
    )

    print("Server ready. Waiting for start...")
    if args.seed is not None:
        obs, _ = env.reset(seed=int(args.seed))
    else:
        obs, _ = env.reset()
    if isinstance(model, _WorldModelPolicy):
        model.reset(obs)
    episode_return = 0.0

    def _update_nav_markers(obs_now: dict) -> None:
        """
        Emit a set of human-only navigation markers to help visually judge
        cruise tracking. This does NOT affect training or observations.
        """
        nonlocal action_mode
        global nav_data
        try:
            mission = np.asarray(obs_now.get("mission", []), dtype=np.float32).reshape(-1)
            if mission.size < 4:
                nav_data = None
                return
            cmd_code = int(float(mission[0]))
            tgt_hdg = float(mission[1])
            tgt_alt = float(mission[2])
            tgt_spd = float(mission[3])

            # Waypoint cruise: show the actual mission waypoints (steerpoints), not a straight "heading ray".
            if cmd_code == 3 and hasattr(env, "loader") and getattr(env.loader, "waypoints", None):
                wps = list(getattr(env.loader, "waypoints", []))
                idx = int(getattr(env.loader, "waypoint_idx", 0))
                idx = max(0, min(idx, len(wps)))

                markers = []
                for i, wp in enumerate(wps):
                    is_active = (i == idx)
                    markers.append(
                        {
                            "name": f"WP_{i+1}",
                            "x": float(wp.get("x", 0.0)),
                            "y": float(wp.get("y", 0.0)),
                            "z": float(wp.get("z", tgt_alt)),
                            "radius_m": 6.0 if is_active else 4.0,
                            "color": 0x00FF00 if is_active else 0xFFFF00,
                        }
                    )

                new_nav = {
                    "markers": markers,
                    "mission": {
                        "command_code": cmd_code,
                        "waypoint_index": idx,
                        "waypoint_total": int(len(wps)),
                        "target_altitude": tgt_alt,
                        "target_speed": tgt_spd,
                    },
                    "action_mode": str(action_mode),
                }
                # Emit only if waypoint index changed (avoid spamming the socket).
                if nav_data is None or nav_data.get("mission", {}).get("waypoint_index") != idx:
                    nav_data = new_nav
                    socketio.emit("nav_setup", nav_data)
                return

            # Heading-hold (stable flight): keep a short "course line" for quick inspection.
            pos0 = env.sim.get_unit_position(env.agent_id)
            x0, y0, _z0 = float(pos0[0]), float(pos0[1]), float(pos0[2])
            rad = np.deg2rad(tgt_hdg)
            dx = float(np.sin(rad))
            dy = float(np.cos(rad))

            markers = []
            step_m = 2000.0
            for i in range(1, 6):
                dist = step_m * float(i)
                markers.append(
                    {
                        "name": f"CRUISE_{i}",
                        "x": x0 + dist * dx,
                        "y": y0 + dist * dy,
                        "z": tgt_alt,
                        "radius_m": 10.0,
                        "color": 0xFFFF00,
                    }
                )

            nav_data = {
                "markers": markers,
                "mission": {
                    "command_code": cmd_code,
                    "target_heading": tgt_hdg,
                    "target_altitude": tgt_alt,
                    "target_speed": tgt_spd,
                },
                "action_mode": str(action_mode),
            }
            socketio.emit("nav_setup", nav_data)
        except Exception:
            nav_data = None

    _update_nav_markers(obs)
    
    hz = 30
    dt_wall = 1.0 / float(hz)
    dt_wall = 1.0 / float(hz)
    dt_wall = 1.0 / float(hz)
    sim_time = 0.0
    
    # --- Map Setup ---
    global map_data
    zones = env.loader.scenario_data.get("environment", {}).get("zones", [])
    map_data = {"zones": zones}
    print(f"=" * 60)
    print(f"MAP DATA SENT TO VIZ:")
    for z in zones:
        print(f"  Zone '{z.get('name')}': x={z.get('x')}, y={z.get('y')}, "
              f"width={z.get('width')}, length={z.get('length')}, heading={z.get('heading')}")
    print(f"=" * 60)
    socketio.emit('map_setup', map_data)
    
    while True:
        try:
            eventlet.sleep(dt_wall)
            
            if not simulation_running:
                continue

            if simulation_paused:
                continue
                
            # Predict
            if args.fixed_action is not None:
                action = np.asarray(args.fixed_action, dtype=np.float32).reshape(-1)
            elif model:
                # We need to map the env observation to what the model expects
                # UniversalEnv returns a Dict observation. SB3 PPO handles Dict if trained on it.
                action, _ = model.predict(obs, deterministic=True)
                if action.shape != env.action_space.shape:
                    raise ValueError(
                        f"Action shape mismatch: model produced {action.shape} but env expects {env.action_space.shape} "
                        f"(hint: set --action_mode to match the training action space)."
                    )
                if sim_time < 2.0:
                    print(f"Action: {action}")
            else:
                # No model: Do nothing (zeros)
                action = np.zeros(env.action_space.shape, dtype=np.float32)

            next_obs, reward, terminated, truncated, info = env.step(action)
            episode_return += float(reward)
            sim_time += env.sim.get_time_step() # Use internal sim step
            if isinstance(model, _WorldModelPolicy):
                model.observe(next_obs)
            obs = next_obs

            # Waypoint cruise: update markers when advancing waypoints (cheap; emits only on index change).
            try:
                m0 = np.asarray(obs.get("mission", []), dtype=np.float32).reshape(-1)
                if m0.size >= 1 and int(float(m0[0])) == 3:
                    _update_nav_markers(obs)
            except Exception:
                pass
            
            # --- Universal State Extraction ---
            # Instead of specific hardcoded fields, we extract all entities in the loader
            
            units_data = []
            
            # Helper to get safe unit data
            def get_unit_data(eid, name):
                if not env.sim.is_unit_active(eid):
                    return None
                    
                pos = env.sim.get_unit_position(eid) # list [x, y, z]
                hdg = env.sim.get_unit_heading(eid)
                # UniversalEnv helper or direct sim access for more details?
                # SimulationKernel doesn't expose generic "get_all_properties" easily in python 
                # without the specialized struct binding.
                # But 'get_agent_observation' returns a rich struct. 
                # Let's try to use basic info we have.
                
                # We need velocity/speed for viz
                # Currently C++ side: get_unit_velocity is not bound? 
                # We can check universal_env usage. It calls get_unit_position.
                # It calls get_agent_observation for THE agent.
                
                # Implementation Detail: 
                # Getting rich state for NON-agents might be limited in current bindings 
                # unless we use `get_detections` or similar.
                # However, for Visualization, we often want "Ground Truth".
                # Let's assume we can get basic Pos/Hdg.
                
                return {
                    "id": eid,
                    "name": name,
                    "side": "Blue", 
                    "type": "Aircraft" if "F16" in name or "Aircraft" in name else "Facility", 
                    "x": pos[0],
                    "y": pos[1],
                    # Physics Z is CG. Visual Model Origin is approx at wheels. 
                    # Subtract gear height (~2.0m) to align visuals.
                    "z": pos[2] - 2.0 if "Aircraft" in name or "F16" in name else pos[2],
                    "heading": hdg,
                    "pitch": 0.0, # TODO: Get Pitch/Roll if possible
                    "roll": 0.0,
                    "speed": 0.0, 
                    "hp": 100.0,
                    "max_hp": 100.0,
                }

            # Iterate ALL entities known to loader
            for name, eid in env.loader.entities.items():
                u = get_unit_data(eid, name)
                if u:
                    # Enrich with Agent data if it's the agent (has more info)
                    if eid == env.agent_id:
                        # DEBUG: Print position of agent to debug drift - FORCE FLUSH
                        # DEBUG: Print position of agent to debug drift - FORCE FLUSH
                        if sim_time < 5.0: 
                            raw = env.sim.get_agent_observation(eid)
                            try:
                                inst_now = env.sim.get_instrument_state(eid)
                            except Exception:
                                inst_now = None

                            runway_cross_m = info.get("runway_cross_m") if isinstance(info, dict) else None
                            on_runway_geom = info.get("on_runway_geom") if isinstance(info, dict) else None

                            rud_cmd = None
                            thr_cmd = None
                            brake_cmd = None
                            if isinstance(action, np.ndarray) and action.ndim == 1:
                                if env.action_mode == "full" and action.size >= 9:
                                    rud_cmd = float(action[2])
                                    thr_cmd = float(action[3])
                                    brake_cmd = float(half_to_unit(float(max(action[7], action[8]))))
                                elif env.action_mode == "takeoff4" and action.size >= 4:
                                    rud_cmd = float(action[2])
                                    thr_cmd = float(action[3])
                                elif env.action_mode == "takeoff2" and action.size >= 2:
                                    thr_cmd = float(action[1])

                            wind_str = "n/a"
                            if inst_now is not None:
                                wind_str = f"{float(inst_now.wind_speed):.2f}@{float(inst_now.wind_dir):.1f}"

                            cross_str = "n/a" if runway_cross_m is None else f"{float(runway_cross_m):.1f}"
                            onrw_str = (
                                "n/a"
                                if on_runway_geom is None
                                else str(int(float(on_runway_geom) > 0.5))
                            )
                            thr_str = "n/a" if thr_cmd is None else f"{thr_cmd:.2f}"
                            rud_str = "n/a" if rud_cmd is None else f"{rud_cmd:.2f}"
                            brk_str = "n/a" if brake_cmd is None else f"{brake_cmd:.2f}"

                            print(
                                f"Viz Frame T={sim_time:.2f} | {name} "
                                f"Pos: ({u['x']:.2f}, {u['y']:.2f}, {u['z']:.2f}) "
                                f"Hdg: {raw.heading:.1f} Trk: {float(getattr(inst_now, 'ground_track', 0.0)):.1f} "
                                f"IAS: {float(getattr(inst_now, 'ias', 0.0)):.1f} Wind: {wind_str} "
                                f"Cross: {cross_str} OnRw: {onrw_str} "
                                f"Act(thr={thr_str}, rud={rud_str}, brk={brk_str}) "
                                f"ThrPos: {float(getattr(inst_now, 'throttle_pos', 0.0)):.2f}"
                            )
                            sys.stdout.flush()
                        u.update({
                            "speed": float(raw.speed),
                            "roll": float(raw.roll),
                            "throttle": float(raw.throttle),
                            "pitch": float(raw.pitch),
                            "hp": float(raw.health),
                            "side": "Blue" # Agent is usually Blue
                        })
                    
                    units_data.append(u)
            
            state = {
                "tick": sim_time,
                "units": units_data
            }
            
            socketio.emit('state_update', state)
            
            if terminated or truncated:
                print(f"Episode Done. Return: {episode_return:.2f}")
                if args.seed is not None:
                    obs, _ = env.reset(seed=int(args.seed))
                else:
                    obs, _ = env.reset()
                if isinstance(model, _WorldModelPolicy):
                    model.reset(obs)
                _update_nav_markers(obs)
                episode_return = 0.0
                
        except Exception as e:
            print(f"Viz Loop Error: {e}")
            import traceback
            traceback.print_exc()
            break

def main():
    global args, app
    parser = argparse.ArgumentParser(description="Universal Visualization Runner")
    parser.add_argument("--scenario", type=str, required=True, help="Path to scenario JSON")
    parser.add_argument("--model", type=str, help="Path to trained model (.zip SB3 PPO or .pt world-model checkpoint)")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=None, help="Deterministic env.reset seed for reproducible wind/yaw.")
    parser.add_argument(
        "--include_proprio",
        action="store_true",
        help="Include previous-action proprioception in observations (must match how the model was trained).",
    )
    parser.add_argument(
        "--action_mode",
        type=str,
        default="auto",
        choices=["auto", "full", "takeoff2", "takeoff4"],
        help="Action space mode; use 'auto' to infer from the model action dimension.",
    )
    parser.add_argument(
        "--fixed_action",
        type=str,
        default=None,
        help="Comma-separated action vector to apply every step (overrides model), e.g. '0,0,0,1' for takeoff4.",
    )
    args = parser.parse_args()

    if args.fixed_action is not None:
        toks = [t.strip() for t in str(args.fixed_action).split(",") if t.strip()]
        if not toks:
            raise ValueError("--fixed_action provided but empty")
        args.fixed_action = np.asarray([float(t) for t in toks], dtype=np.float32)
    
    app.config['SECRET_KEY'] = 'universal_viz_secret'
    
    socketio.start_background_task(simulation_loop)
    print(f"Running Universal Viz on http://localhost:{args.port}")
    socketio.run(app, host='0.0.0.0', port=args.port, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    main()
