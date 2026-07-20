from __future__ import annotations

import json
import math
import os
import sys
from argparse import Namespace
from types import SimpleNamespace

import eventlet
import numpy as np

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from python.testing.runtime import ensure_repo_imports

ensure_repo_imports()

from gym_envs.leader_env import LeaderTrainingEnv
from gym_envs.universal_env_parts.actions import half_to_unit
from python.rl.control.mission_defs import (
    COMMAND_NAME_TO_CODE,
    CRUISE_PHASE_NAMES,
    LANDING_PHASE_NAMES,
    TAKEOFF_PHASE_NAMES,
    normalize_phase_name,
)
from python.rl.control.scripted_landing import ScriptedLandingController
from python.rl.control.scripted_stable_flight import ScriptedStableFlightController
from python.rl.control.scripted_takeoff import ScriptedTakeoffController
from python.rl.control.wrappers import get_action_wrapper_spec
from python.rl.policy_algo.ppo_adaptive_kl import AdaptiveKLPPO
from python.rl.runtime.cooperative_world_batch_vec_env import CooperativeWorldBatchVecEnv
from python.rl.runtime.world_batch_vec_env import WorldBatchVecEnv
from python.world_model.features import (
    DEFAULT_ANGLE_DEG_INDICES,
    angle_sincos_features,
    append_angle_sincos_features,
    nav_tracking_features,
)
from examples.viz.runtime.environment_overlays import build_environment_overlay_payload
from examples.viz.runtime.illumination import resolve_scenario_illumination
from examples.viz.runtime.unit_semantics import infer_echelon
from examples.viz.runtime.action_utils import normalize_fixed_action


def _format_reward_terms(reward_terms: dict | None, *, limit: int = 8) -> str:
    if not isinstance(reward_terms, dict) or not reward_terms:
        return "none"
    items = []
    for k, v in reward_terms.items():
        try:
            items.append((str(k), float(v)))
        except Exception:
            continue
    if not items:
        return "none"
    items.sort(key=lambda kv: abs(kv[1]), reverse=True)
    return ", ".join(f"{k}={v:.2f}" for k, v in items[: max(1, int(limit))])


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


COMMAND_CODE_TO_NAME = {int(v): str(k).upper() for k, v in COMMAND_NAME_TO_CODE.items()}
GROUND_TASKING_PROFILE_ALIASES = {"army", "ground", "land"}

# Versioned wire contracts. Bump when a consumer-visible field changes shape
# or meaning so old/new frontends and replay tooling can negotiate; additive
# fields do not require a bump.
VIZ_STATE_FRAME_CONTRACT_VERSION = "examples.viz.state_frame.v1"
VIZ_MAP_SETUP_CONTRACT_VERSION = "examples.viz.map_setup.v1"
DEFAULT_C2_TASK_SEQUENCE = [
    "TASK_SCRAMBLE",
    "TASK_CAP",
    "TASK_RTB",
    "TASK_RECOVER_LAND",
]


def _scenario_tasking_profile(scenario_data: object) -> str:
    if not isinstance(scenario_data, dict):
        return ""
    candidates = [scenario_data.get("tasking_profile")]
    for key in ("mission_command", "task_order"):
        section = scenario_data.get(key)
        if isinstance(section, dict):
            candidates.append(section.get("tasking_profile"))
    for candidate in candidates:
        text = str(candidate or "").strip().lower()
        if text:
            return text
    return ""


def _is_ground_tasking_profile(tasking_profile: str | None) -> bool:
    return str(tasking_profile or "").strip().lower() in GROUND_TASKING_PROFILE_ALIASES


def _pretty_label(name: str | None) -> str:
    text = str(name or "").strip()
    if not text:
        return "--"
    if text.startswith("TASK_"):
        text = text[5:]
    return text.replace("_", " ").title()


def _infer_c2_task(phase_name: str | None, *, command_code: int | None = None) -> str:
    phase = normalize_phase_name(phase_name)
    if phase == "rtb":
        return "TASK_RTB"
    if phase in TAKEOFF_PHASE_NAMES:
        return "TASK_SCRAMBLE"
    if phase in LANDING_PHASE_NAMES:
        return "TASK_RECOVER_LAND"
    if phase in CRUISE_PHASE_NAMES:
        return "TASK_CAP"
    try:
        if int(command_code) == 4:
            return "TASK_RECOVER_LAND"
        if int(command_code) == 3:
            return "TASK_CAP"
        if int(command_code) == 1:
            return "TASK_SCRAMBLE"
    except Exception:
        pass
    return "TASK_IDLE"


def _build_mission_status_payload(
    sim_env,
    *,
    sim_time: float,
    history: list[dict],
) -> dict | None:
    loader = getattr(sim_env, "loader", None)
    if loader is None:
        return None

    mission_cmd = getattr(loader, "mission_cmd", {}) or {}
    phase_name = normalize_phase_name(getattr(loader, "mission_phase_name", "idle"))
    try:
        command_code = int(mission_cmd.get("command_code", 0))
    except Exception:
        command_code = 0

    c2_task = str(getattr(loader, "c2_task_name", "") or "").strip().upper()
    if not c2_task:
        c2_task = _infer_c2_task(phase_name, command_code=command_code)
    seq = list(DEFAULT_C2_TASK_SEQUENCE)
    try:
        meta = getattr(loader, "scenario_data", {}).get("meta", {})
        custom_seq = meta.get("demo_task_sequence", None) if isinstance(meta, dict) else None
        if isinstance(custom_seq, list) and custom_seq:
            seq = [str(x).strip() for x in custom_seq if str(x).strip()]
    except Exception:
        pass

    try:
        sequence_index = seq.index(c2_task)
    except ValueError:
        sequence_index = -1

    waypoints = list(getattr(loader, "waypoints", []) or [])
    waypoint_total = int(len(waypoints))
    waypoint_idx = int(getattr(loader, "waypoint_idx", 0) or 0)
    active_waypoint = 0
    if waypoint_total > 0:
        active_waypoint = max(1, min(waypoint_total, waypoint_idx + 1))

    return {
        "sim_time_s": float(sim_time),
        "c2_task": str(c2_task),
        "c2_task_label": _pretty_label(c2_task),
        "phase_name": phase_name or "idle",
        "phase_label": _pretty_label(phase_name),
        "command_code": int(command_code),
        "command_name": COMMAND_CODE_TO_NAME.get(int(command_code), f"CODE_{int(command_code)}"),
        "waypoint_index": int(waypoint_idx),
        "waypoint_total": int(waypoint_total),
        "active_waypoint": int(active_waypoint),
        "task_sequence": seq,
        "task_sequence_index": int(sequence_index),
        "history": list(history),
    }


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
            return
        if self._state is None or self._last_action_norm is None:
            self.reset(obs)
            return

        import torch

        embed_next = self._encode_obs(obs, need_embed=True)
        with torch.no_grad():
            a_t = torch.from_numpy(self._last_action_norm).to(self.device).float().unsqueeze(0)
            self._state, _prior, _post = self.wm.rssm.obs_step(self._state, a_t, embed_next)


class _ScriptedPolicy:
    def __init__(self, mode: str, *, action_dim: int, dt: float = 0.05):
        mode = str(mode).strip().lower()
        self.mode = mode
        self._transition_alt_agl_m = 140.0
        self._active_mode = None
        if mode == "takeoff":
            self.ctrl = ScriptedTakeoffController(action_dim=action_dim, dt=dt)
            self.takeoff_ctrl = self.ctrl
            self.stable_ctrl = None
            self.landing_ctrl = None
        elif mode == "stable_flight":
            self.ctrl = ScriptedStableFlightController(action_dim=action_dim, dt=dt)
            self.takeoff_ctrl = None
            self.stable_ctrl = self.ctrl
            self.landing_ctrl = None
        elif mode == "landing_ils":
            self.ctrl = ScriptedLandingController(action_dim=action_dim, dt=dt)
            self.takeoff_ctrl = None
            self.stable_ctrl = None
            self.landing_ctrl = None
        elif mode == "takeoff_cruise_landing":
            self.takeoff_ctrl = ScriptedTakeoffController(action_dim=action_dim, dt=dt)
            self.stable_ctrl = ScriptedStableFlightController(action_dim=action_dim, dt=dt)
            self.landing_ctrl = ScriptedLandingController(action_dim=action_dim, dt=dt)
            self.ctrl = self.takeoff_ctrl
        else:
            raise ValueError(f"Unknown scripted mode: {mode}")

    def reset(self, obs: dict) -> None:
        if self.mode == "takeoff_cruise_landing":
            self.ctrl = self.takeoff_ctrl
            self._active_mode = "takeoff"
        self.ctrl.reset(obs)

    def _infer_mode(self, obs: dict) -> str:
        if self.mode != "takeoff_cruise_landing":
            return self.mode
        try:
            mission = np.asarray(obs.get("mission", []), dtype=np.float32).reshape(-1)
            if mission.size >= 1 and int(round(float(mission[0]))) == 4:
                return "landing_ils"
            if self._active_mode in ("stable_flight", "landing_ils"):
                return "stable_flight"
        except Exception:
            pass
        try:
            inst = np.asarray(obs.get("instruments", []), dtype=np.float32).reshape(-1)
            if inst.size >= 4:
                return "takeoff" if float(inst[3]) < self._transition_alt_agl_m else "stable_flight"
        except Exception:
            pass
        return self._active_mode or "takeoff"

    def predict(self, obs: dict, deterministic: bool = True):
        if self.mode == "takeoff_cruise_landing":
            desired_mode = self._infer_mode(obs)
            desired_ctrl = (
                self.landing_ctrl if desired_mode == "landing_ils"
                else self.stable_ctrl if desired_mode == "stable_flight"
                else self.takeoff_ctrl
            )
            if desired_mode != self._active_mode:
                desired_ctrl.reset(obs)
            self.ctrl = desired_ctrl
            self._active_mode = desired_mode
        return np.asarray(self.ctrl.step(obs), dtype=np.float32), None


def _load_train_config_for_viz(model_path: str | None, explicit_cfg_path: str | None) -> dict | None:
    cfg_path = None
    if explicit_cfg_path:
        cfg_path = os.path.abspath(explicit_cfg_path)
        if not os.path.exists(cfg_path):
            raise FileNotFoundError(f"Training config not found: {cfg_path}")
    elif model_path:
        abs_model = os.path.abspath(model_path)
        parent_dir = os.path.dirname(abs_model)
        exp_dir = os.path.dirname(parent_dir) if os.path.basename(parent_dir) == "checkpoints" else parent_dir
        candidate = os.path.join(exp_dir, "train_config_backup.json")
        if os.path.exists(candidate):
            cfg_path = candidate

    if cfg_path is None:
        return None

    with open(cfg_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _env_defaults_from_train_config(train_config: dict | None) -> dict:
    if not isinstance(train_config, dict):
        return {}
    env_cfg = train_config.get("env", {})
    return env_cfg if isinstance(env_cfg, dict) else {}


def _is_leader_train_config(train_config: dict | None) -> bool:
    if not isinstance(train_config, dict):
        return False
    return str(train_config.get("agent_layer", "execution")).strip().lower() == "leader"


def _is_cooperative_train_config(train_config: dict | None) -> bool:
    if not isinstance(train_config, dict):
        return False
    return str(train_config.get("agent_layer", "execution")).strip().lower() == "cooperative_execution"


def _model_looks_like_leader(model_obj) -> bool:
    obs_space = getattr(model_obj, "observation_space", None)
    try:
        keys = set(getattr(obs_space, "spaces", {}).keys())
    except Exception:
        keys = set()
    return {"ownship", "task", "navigation", "terminal", "link"}.issubset(keys)


def _infer_visual_downsample(model_obj, requested_factor: int | None) -> int:
    if requested_factor is not None and int(requested_factor) > 0:
        return int(requested_factor)
    obs_space = getattr(model_obj, "observation_space", None)
    visual_space = None
    try:
        visual_space = obs_space.spaces.get("visual") if obs_space is not None else None
    except Exception:
        visual_space = None
    if visual_space is None or len(getattr(visual_space, "shape", ())) != 3:
        return 1
    try:
        h, w, _c = [int(x) for x in visual_space.shape]
    except Exception:
        return 1
    native_h, native_w = 48, 96
    if h <= 0 or w <= 0:
        return 1
    if native_h % h != 0 or native_w % w != 0:
        return 1
    factor_h = native_h // h
    factor_w = native_w // w
    return factor_h if factor_h == factor_w and factor_h > 0 else 1


def _model_expects_proprio(model_obj) -> bool:
    obs_space = getattr(model_obj, "observation_space", None)
    try:
        return bool(obs_space is not None and "proprio" in obs_space.spaces)
    except Exception:
        return False


def _model_expects_visual(model_obj) -> bool:
    obs_space = getattr(model_obj, "observation_space", None)
    try:
        return bool(obs_space is not None and "visual" in obs_space.spaces)
    except Exception:
        return False


def _infer_mission_obs_mode(model_obj, requested_mode: str | None) -> str:
    if requested_mode:
        return str(requested_mode).strip().lower()
    obs_space = getattr(model_obj, "observation_space", None)
    try:
        mission_space = obs_space.spaces.get("mission") if obs_space is not None else None
    except Exception:
        mission_space = None
    if mission_space is None:
        return "basic"
    try:
        dim = int(mission_space.shape[0])
    except Exception:
        return "basic"
    if dim == 21:
        return "nav_v2_formation_role_v1"
    if dim == 25:
        return "nav_v2_cooperative_takeoff_v1"
    if dim == 23:
        return "naval_screen_station_v1"
    if dim == 17:
        return "nav_v2_formation_v1"
    if dim == 14:
        return "nav_v2"
    if dim == 11:
        return "nav_v1"
    return "basic"


def _infer_visual_update_interval(train_config: dict | None, requested_interval: int | None) -> int:
    if requested_interval is not None and int(requested_interval) > 0:
        return int(requested_interval)
    env_cfg = _env_defaults_from_train_config(train_config)
    try:
        value = int(env_cfg.get("visual_update_interval", 1))
    except Exception:
        value = 1
    return max(1, value)


def _cooperative_action_wrapper_kwargs(train_config: dict | None) -> dict | None:
    if not isinstance(train_config, dict):
        return None
    _wrapper_class, wrapper_kwargs = get_action_wrapper_spec(train_config)
    if wrapper_kwargs is None:
        return None
    return dict(wrapper_kwargs)


class VizSession:
    def __init__(self, args: Namespace, socketio, *, status_callback=None) -> None:
        self.args = args
        fixed_action = normalize_fixed_action(getattr(args, "fixed_action", None))
        if fixed_action is not None:
            setattr(self.args, "fixed_action", fixed_action)
        self.socketio = socketio
        self.status_callback = status_callback
        self.scenario = str(getattr(args, "scenario", ""))
        self.simulation_running = False
        self.simulation_paused = False
        self.stop_requested = False
        self.ready = False
        self.env = None
        self.model = None
        self.episode_return = 0.0
        self.map_data = None
        self.nav_data = None
        self.sim_speed = 1.0
        self.last_error = ""

    def _release_runtime_resources(self) -> None:
        env = self.env
        self.env = None
        self.model = None
        if env is None:
            return
        close_fn = getattr(env, "close", None)
        if callable(close_fn):
            try:
                close_fn()
            except Exception as exc:
                print(f"[WARN] Failed to close viz env: {exc}")

    def emit_cached_setup(self) -> None:
        if self.map_data:
            overlay_layers = self.map_data.get("environment_overlays", {}).get("layers", [])
            print(
                "Sending cached map data "
                f"({len(self.map_data.get('zones', []))} zones, {len(overlay_layers)} env layers) "
                "to new client"
            )
            self.socketio.emit("map_setup", self.map_data)
        if self.nav_data:
            self.socketio.emit("nav_setup", self.nav_data)
        self.socketio.emit("speed_update", {"value": float(self.sim_speed)})
        self._notify_status()

    def _notify_status(self) -> None:
        if callable(self.status_callback):
            self.status_callback()
        else:
            self.socketio.emit("viz_session_status", self.status_payload())

    def start(self) -> None:
        print("Start Signal Received")
        self.simulation_running = True
        self.simulation_paused = False

    def pause(self) -> None:
        print("Pause Signal Received")
        self.simulation_paused = True

    def resume(self) -> None:
        print("Resume Signal Received")
        self.simulation_paused = False

    def stop(self) -> None:
        print("Stop Signal Received")
        self.stop_requested = True
        self.simulation_running = False
        self.simulation_paused = False
        self.ready = False
        self.map_data = None
        self.nav_data = None
        self._release_runtime_resources()
        self._notify_status()

    def set_speed(self, data) -> None:
        try:
            value = 1.0
            if isinstance(data, dict):
                value = float(data.get("value", 1.0))
            else:
                value = float(data)
        except Exception:
            value = 1.0
        self.sim_speed = max(0.05, min(16.0, value))
        print(f"Speed Set: {self.sim_speed:g}x")
        self.socketio.emit("speed_update", {"value": float(self.sim_speed)})
        self._notify_status()

    def status_payload(self) -> dict:
        return {
            "scenario": str(self.scenario),
            "running": bool(self.simulation_running),
            "paused": bool(self.simulation_paused),
            "ready": bool(self.ready),
            "stopped": bool(self.stop_requested),
            "speed": float(self.sim_speed),
            "error": str(self.last_error),
        }

    def report_error(self, message: str) -> None:
        self.last_error = str(message)
        try:
            self.socketio.emit("viz_error", {"message": self.last_error, "scenario": str(self.scenario)})
        except Exception:
            pass
        self._notify_status()

    def run_loop(self) -> None:
        try:
            self._run_loop_inner()
        except Exception as exc:
            import traceback

            traceback.print_exc()
            self.ready = False
            self.simulation_running = False
            self.simulation_paused = False
            self.report_error(f"{type(exc).__name__}: {exc}")

    def _run_loop_inner(self) -> None:
        args = self.args
        self.stop_requested = False
        train_config = _load_train_config_for_viz(getattr(args, "model", None), getattr(args, "train_config", None))
        leader_mode = _is_leader_train_config(train_config)
        cooperative_mode = _is_cooperative_train_config(train_config)
        wrapper_class = None
        wrapper_kwargs = None
        cooperative_action_wrapper_kwargs = None
        sim_env = None
        mission_transition_log: list[dict] = []
        last_phase_name = ""
        last_c2_task = ""
        leader_exec_steps_remaining = 0
        leader_decision_pending = False
        coop_last_infos: list[dict] = []
        world_batch_mode = False
        scripted_mode = str(getattr(args, "scripted", "")).strip().lower()
        if scripted_mode in ("", "none", "null", "false", "0"):
            scripted_mode = ""

        if scripted_mode:
            print(f"Using scripted policy mode: {scripted_mode}")
            self.model = None
        elif args.model and os.path.exists(args.model):
            try:
                model_path = args.model
                if model_path.endswith((".pt", ".pth")):
                    print(f"Loading world-model policy from {model_path}...")
                    self.model = _WorldModelPolicy(model_path, device="cpu")
                else:
                    print(f"Loading PPO model from {model_path}...")
                    if model_path.endswith(".zip"):
                        model_path = model_path[:-4]
                    algo_name = str(getattr(args, "algo", "auto")).strip()
                    algo_cls = AdaptiveKLPPO if algo_name in ("auto", "AdaptiveKLPPO", "PPOAdaptiveKL", "PPO_AdaptiveKL") else None
                    load_err = None
                    if algo_cls is not None:
                        try:
                            self.model = algo_cls.load(model_path, device="cpu")
                        except Exception as e:
                            load_err = e
                            self.model = None
                    if self.model is None:
                        from stable_baselines3 import PPO

                        self.model = PPO.load(model_path, device="cpu")
                        if load_err is not None and algo_name != "auto":
                            print(f"[WARN] failed to load with {algo_name}: {load_err}; fell back to PPO")
            except Exception as e:
                print(f"Error loading model: {e}")
                self.model = None
        else:
            print("No model loaded. Running with random/noop actions.")
            self.model = None

        if not leader_mode and not cooperative_mode and self.model is not None and _model_looks_like_leader(self.model):
            leader_mode = True

        if train_config is not None and not leader_mode and not cooperative_mode:
            wrapper_class, wrapper_kwargs = get_action_wrapper_spec(train_config)
            if wrapper_kwargs is not None:
                wrapper_kwargs = dict(wrapper_kwargs)
        elif train_config is not None and cooperative_mode:
            cooperative_action_wrapper_kwargs = _cooperative_action_wrapper_kwargs(train_config)

        if scripted_mode == "takeoff_cruise_landing":
            if wrapper_kwargs is None:
                raise ValueError(
                    "scripted=takeoff_cruise_landing requires a train config with the action wrapper enabled; "
                    "pass --train_config examples/config/training/frozen/execution/p5_continuous_retrain_v1.json"
                )
            wrapper_kwargs["scripted_baseline_mode"] = "takeoff_cruise_landing"
            wrapper_kwargs["scripted_residual_scale"] = 0.0
            wrapper_kwargs["action_rate_penalty_coef"] = 0.0
        elif cooperative_mode and scripted_mode:
            raise ValueError(
                "Cooperative visualization currently does not support --scripted; use a learned checkpoint."
            )

        action_mode = args.action_mode
        env_defaults = _env_defaults_from_train_config(train_config)

        if not leader_mode:
            if action_mode == "auto":
                act_dim = None
                if self.model is not None:
                    act_dim = getattr(self.model, "action_dim", None)
                    if act_dim is None:
                        act_space = getattr(self.model, "action_space", None)
                        act_shape = getattr(act_space, "shape", None)
                        act_dim = int(act_shape[0]) if act_shape and len(act_shape) == 1 else None
                elif scripted_mode:
                    act_dim = 17
                if act_dim == 2:
                    action_mode = "takeoff2"
                elif act_dim == 4:
                    action_mode = "takeoff4"
                else:
                    action_mode = "full"

            include_proprio = bool(getattr(args, "include_proprio", False))
            if self.model is not None and not include_proprio:
                include_proprio = _model_expects_proprio(self.model)
            elif self.model is None and not include_proprio:
                include_proprio = bool(env_defaults.get("include_proprio", False))

            include_visual = False
            if self.model is not None:
                include_visual = _model_expects_visual(self.model)
            else:
                include_visual = True

            if self.model is not None:
                mission_obs_mode = _infer_mission_obs_mode(self.model, getattr(args, "mission_obs_mode", None))
                visual_downsample = _infer_visual_downsample(self.model, getattr(args, "visual_downsample", None))
            else:
                mission_obs_mode = str(
                    getattr(args, "mission_obs_mode", None) or env_defaults.get("mission_obs_mode", "basic")
                ).strip().lower()
                visual_downsample = int(
                    getattr(args, "visual_downsample", None) or env_defaults.get("visual_downsample", 1) or 1
                )
            visual_update_interval = _infer_visual_update_interval(train_config, getattr(args, "visual_update_interval", None))
        else:
            include_proprio = False
            mission_obs_mode = "leader"
            visual_downsample = 1
            visual_update_interval = 1

        if not leader_mode and not cooperative_mode:
            print(
                f"Initializing WorldBatchVecEnv visualization runtime with scenario: {args.scenario} "
                f"(action_mode={action_mode}, include_visual={include_visual}, include_proprio={include_proprio}, "
                f"mission_obs_mode={mission_obs_mode}, visual_downsample={visual_downsample}, "
                f"visual_update_interval={visual_update_interval})"
            )
            runtime_cfg = train_config.get("runtime", {}) if isinstance(train_config, dict) else {}
            if not isinstance(runtime_cfg, dict):
                runtime_cfg = {}
            self.env = WorldBatchVecEnv(
                scenario_path=args.scenario,
                n_envs=1,
                action_mode=action_mode,
                include_visual=include_visual,
                include_proprio=include_proprio,
                mission_obs_mode=mission_obs_mode,
                visual_downsample=visual_downsample,
                visual_update_interval=visual_update_interval,
                temporal_history_len=int(env_defaults.get("temporal_history_len", 1) or 1),
                step_info_mode=str(env_defaults.get("step_info_mode", "full") or "full"),
                execution_step_runtime_mode=str(
                    env_defaults.get("execution_step_runtime_mode", "compiled") or "compiled"
                ),
                flight_shaping_backend=str(env_defaults.get("flight_shaping_backend", "compiled") or "compiled"),
                batch_observation_backend=runtime_cfg.get("batch_observation_backend", "auto"),
                batch_visual_backend=runtime_cfg.get("batch_visual_backend", "auto"),
                action_wrapper_kwargs=wrapper_kwargs,
            )
            if bool(getattr(args, "zero_randomization", False)):
                self.env.env_method(
                    "set_randomization_overrides",
                    {
                        "world_yaw_range": [0.0, 0.0],
                        "wind_speed_range": [0.0, 0.0],
                        "wind_dir_from_range": [0.0, 0.0],
                        "wind_headwind_range": [0.0, 0.0],
                        "wind_crosswind_range": [0.0, 0.0],
                        "wind_tailwind_max_mps": 0.0,
                        "wind_shear_range": [0.0, 0.0],
                    },
                    indices=[0],
                )
            world_batch_mode = True
            if scripted_mode and scripted_mode != "takeoff_cruise_landing":
                self.model = _ScriptedPolicy(
                    scripted_mode,
                    action_dim=int(self.env.action_space.shape[0]),
                    dt=0.05,
                )
        elif cooperative_mode:
            runtime_cfg = train_config.get("runtime", {}) if isinstance(train_config, dict) else {}
            if not isinstance(runtime_cfg, dict):
                runtime_cfg = {}
            print(
                f"Initializing Cooperative Environment with scenario: {args.scenario} "
                f"(action_mode={action_mode}, include_visual={include_visual}, include_proprio={include_proprio}, "
                f"mission_obs_mode={mission_obs_mode}, visual_downsample={visual_downsample}, "
                f"visual_update_interval={visual_update_interval})"
            )
            self.env = CooperativeWorldBatchVecEnv(
                scenario_path=args.scenario,
                n_envs=1,
                include_visual=include_visual,
                include_proprio=include_proprio,
                action_mode=action_mode,
                mission_obs_mode=mission_obs_mode,
                visual_downsample=visual_downsample,
                visual_update_interval=visual_update_interval,
                batch_observation_backend=runtime_cfg.get("batch_observation_backend", "auto"),
                batch_visual_backend=runtime_cfg.get("batch_visual_backend", "auto"),
                action_wrapper_kwargs=cooperative_action_wrapper_kwargs,
            )
            if bool(getattr(args, "zero_randomization", False)):
                self.env.set_randomization_overrides(
                    {
                        "world_yaw_range": [0.0, 0.0],
                        "wind_speed_range": [0.0, 0.0],
                        "wind_dir_from_range": [0.0, 0.0],
                        "wind_headwind_range": [0.0, 0.0],
                        "wind_crosswind_range": [0.0, 0.0],
                        "wind_tailwind_max_mps": 0.0,
                        "wind_shear_range": [0.0, 0.0],
                    }
                )
            sim_env = None
        else:
            leader_cfg = dict(train_config.get("leader_env", {}) or {}) if isinstance(train_config, dict) else {}
            if not leader_cfg:
                raise ValueError("Leader visualization requires a leader train config with a 'leader_env' section.")
            execution_train_config = leader_cfg.get("execution_train_config", None)
            execution_model_path = leader_cfg.get("execution_model_path", None)
            if execution_train_config:
                execution_train_config = os.path.abspath(os.path.join(repo_root, str(execution_train_config)))
            if execution_model_path:
                execution_model_path = os.path.abspath(os.path.join(repo_root, str(execution_model_path)))
            print(
                f"Initializing Leader Environment with scenario: {args.scenario} "
                f"(decision_interval_steps={int(leader_cfg.get('decision_interval_steps', 20))}, "
                f"execution_backend={str(leader_cfg.get('execution_backend', 'scripted'))})"
            )
            self.env = LeaderTrainingEnv(
                args.scenario,
                decision_interval_steps=int(leader_cfg.get("decision_interval_steps", 20)),
                execution_backend=str(leader_cfg.get("execution_backend", "scripted")),
                execution_train_config=execution_train_config,
                execution_model_path=execution_model_path,
                execution_algo=str(leader_cfg.get("execution_algo", "auto")),
                scripted_transition_alt_agl_m=float(leader_cfg.get("scripted_transition_alt_agl_m", 140.0)),
                heading_bias_limit_deg=float(leader_cfg.get("heading_bias_limit_deg", 45.0)),
                altitude_bias_limit_m=float(leader_cfg.get("altitude_bias_limit_m", 800.0)),
                speed_bias_limit_mps=float(leader_cfg.get("speed_bias_limit_mps", 40.0)),
                command_change_penalty=float(leader_cfg.get("command_change_penalty", 0.0)),
                teacher_keep_deadband=float(leader_cfg.get("teacher_keep_deadband", 0.20)),
                invalid_phase_penalty=float(leader_cfg.get("invalid_phase_penalty", 0.0)),
                premature_approach_penalty=float(leader_cfg.get("premature_approach_penalty", 0.0)),
                baseline_deviation_penalty=float(leader_cfg.get("baseline_deviation_penalty", 0.0)),
                mode_change_penalty=float(leader_cfg.get("mode_change_penalty", 0.0)),
                approach_gate_distance_m=float(leader_cfg.get("approach_gate_distance_m", 18000.0)),
                approach_gate_cross_m=float(leader_cfg.get("approach_gate_cross_m", 3500.0)),
                approach_gate_heading_error_deg=float(leader_cfg.get("approach_gate_heading_error_deg", 85.0)),
            )
            if bool(getattr(args, "zero_randomization", False)):
                self.env.set_randomization_overrides(
                    {
                        "world_yaw_range": [0.0, 0.0],
                        "wind_speed_range": [0.0, 0.0],
                        "wind_dir_from_range": [0.0, 0.0],
                        "wind_headwind_range": [0.0, 0.0],
                        "wind_crosswind_range": [0.0, 0.0],
                        "wind_tailwind_max_mps": 0.0,
                        "wind_shear_range": [0.0, 0.0],
                    }
                )
            sim_env = self.env.unwrapped
            action_mode = str(getattr(sim_env, "action_mode", "full"))
            if scripted_mode:
                print("[WARN] scripted visual controllers are only supported for execution-env mode; ignoring --scripted for leader mode.")
                scripted_mode = ""

        def _cooperative_slot_states() -> list:
            if not cooperative_mode or self.env is None:
                return []
            return [slot_state for slot_state in list(getattr(self.env, "_slots", []) or []) if slot_state is not None]

        def _refresh_cooperative_adapter() -> None:
            nonlocal sim_env
            if not cooperative_mode:
                return
            slot_states = _cooperative_slot_states()
            if not slot_states:
                sim_env = None
                return
            primary_slot = slot_states[0]
            sim_env = SimpleNamespace(
                loader=primary_slot.loader,
                sim=primary_slot.loader.sim,
                agent_id=int(primary_slot.entity_id),
                action_mode=str(getattr(self.env, "action_mode", "full")),
                _last_inst=primary_slot.last_inst,
                _last_truth=primary_slot.last_truth,
            )

        def _refresh_world_batch_adapter() -> None:
            nonlocal sim_env
            if not world_batch_mode:
                return
            handles = list(getattr(self.env, "_handles", []) or [])
            if not handles:
                sim_env = None
                return
            handle = handles[0]
            sim_env = SimpleNamespace(
                loader=handle.loader,
                sim=handle.loader.sim,
                agent_id=int(handle.agent_id) if handle.agent_id is not None else 0,
                action_mode=str(getattr(self.env, "action_mode", "full")),
                _last_inst=handle.last_inst,
                _last_truth=handle.last_truth,
            )

        def _single_obs_from_vec(obs_now: dict):
            if not world_batch_mode or not isinstance(obs_now, dict):
                return obs_now
            display_obs = {}
            for key, value in obs_now.items():
                arr = np.asarray(value)
                if arr.ndim >= 1 and arr.shape[0] == 1:
                    display_obs[key] = arr[0]
                else:
                    display_obs[key] = value
            return display_obs

        def _reset_env_for_viz(seed_override: int | None = None):
            nonlocal coop_last_infos
            if cooperative_mode:
                if seed_override is not None and hasattr(self.env, "seed"):
                    self.env.seed(int(seed_override))
                obs_now = self.env.reset()
                coop_last_infos = []
                _refresh_cooperative_adapter()
                return obs_now
            if world_batch_mode:
                if seed_override is not None and hasattr(self.env, "seed"):
                    self.env.seed(int(seed_override))
                obs_now = self.env.reset()
                _refresh_world_batch_adapter()
                return _single_obs_from_vec(obs_now)
            if seed_override is not None:
                obs_now, _ = self.env.reset(seed=int(seed_override))
            else:
                obs_now, _ = self.env.reset()
            return obs_now

        def _display_obs(obs_now: dict):
            if not cooperative_mode or not isinstance(obs_now, dict):
                return obs_now
            slot_count = max(0, int(getattr(self.env, "num_envs", 0)))
            if slot_count <= 0:
                return obs_now
            display_obs = {}
            for key, value in obs_now.items():
                arr = np.asarray(value)
                if arr.ndim >= 1 and arr.shape[0] == slot_count:
                    display_obs[key] = arr[0]
                else:
                    display_obs[key] = value
            return display_obs

        print("Server ready. Waiting for start...")
        obs = _reset_env_for_viz(int(args.seed) if args.seed is not None else None)
        if isinstance(self.model, (_WorldModelPolicy, _ScriptedPolicy)):
            self.model.reset(obs)
        self.episode_return = 0.0
        self.ready = True
        self._notify_status()

        def _reset_mission_status_tracking() -> None:
            nonlocal mission_transition_log, last_phase_name, last_c2_task
            mission_transition_log = []
            last_phase_name = ""
            last_c2_task = ""

        def _capture_mission_status(sim_time_now: float) -> dict | None:
            nonlocal mission_transition_log, last_phase_name, last_c2_task
            status = _build_mission_status_payload(
                sim_env,
                sim_time=float(sim_time_now),
                history=mission_transition_log,
            )
            if not isinstance(status, dict):
                return None

            phase_name = str(status.get("phase_name", "")).strip().lower()
            c2_task = str(status.get("c2_task", "")).strip().upper()
            if phase_name != last_phase_name or c2_task != last_c2_task:
                mission_transition_log.append(
                    {
                        "time_s": float(sim_time_now),
                        "phase_name": phase_name or "idle",
                        "phase_label": str(status.get("phase_label", "--")),
                        "c2_task": c2_task or "TASK_IDLE",
                        "c2_task_label": str(status.get("c2_task_label", "--")),
                        "command_code": int(status.get("command_code", 0)),
                        "waypoint_text": (
                            f"{int(status.get('active_waypoint', 0))}/{int(status.get('waypoint_total', 0))}"
                            if int(status.get("waypoint_total", 0)) > 0
                            else "--"
                        ),
                    }
                )
                mission_transition_log = mission_transition_log[-8:]
                last_phase_name = phase_name
                last_c2_task = c2_task
                status["history"] = list(mission_transition_log)
            return status

        _reset_mission_status_tracking()
        _capture_mission_status(0.0)

        def _update_nav_markers(obs_now: dict) -> None:
            nonlocal action_mode
            try:
                obs_display = _display_obs(obs_now)
                mission = np.asarray(obs_display.get("mission", []), dtype=np.float32).reshape(-1)
                if mission.size < 4:
                    self.nav_data = None
                    return
                cmd_code = int(float(mission[0]))
                tgt_hdg = float(mission[1])
                tgt_alt = float(mission[2])
                tgt_spd = float(mission[3])

                if cmd_code == 4 and hasattr(sim_env, "loader"):
                    try:
                        beacons = list(getattr(sim_env.loader, "ils_beacons", []) or [])
                    except Exception:
                        beacons = []

                    if beacons:
                        beacon = None
                        ref_runway = None
                        try:
                            ref_runway = str(getattr(sim_env.loader, "mission_cmd", {}).get("reference_runway", "")).strip().lower()
                        except Exception:
                            ref_runway = None

                        if ref_runway:
                            for cand in beacons:
                                name = str(cand.get("name", "")).strip().lower()
                                if name == ref_runway:
                                    beacon = cand
                                    break
                            if beacon is None:
                                for cand in beacons:
                                    name = str(cand.get("name", "")).strip().lower()
                                    if ref_runway in name or name in ref_runway:
                                        beacon = cand
                                        break

                        if beacon is None:
                            try:
                                pos0 = sim_env.sim.get_unit_position(sim_env.agent_id)
                                x0, y0 = float(pos0[0]), float(pos0[1])
                                beacon = min(
                                    beacons,
                                    key=lambda b: (float(b.get("thr_x", 0.0)) - x0) ** 2
                                    + (float(b.get("thr_y", 0.0)) - y0) ** 2,
                                )
                            except Exception:
                                beacon = beacons[0]

                        h_rad = np.deg2rad(float(beacon.get("heading", tgt_hdg)))
                        dx = float(np.sin(h_rad))
                        dy = float(np.cos(h_rad))
                        thr_x = float(beacon.get("thr_x", 0.0))
                        thr_y = float(beacon.get("thr_y", 0.0))
                        elev_m = float(beacon.get("elev_m", 0.0))
                        gs_deg = float(beacon.get("glide_slope_deg", 3.0))
                        runway_width_m = max(10.0, float(beacon.get("width", 45.0)))
                        marker_radius_m = max(18.0, runway_width_m * 0.35)
                        mission_cfg = getattr(sim_env.loader, "mission_cmd", {}) or {}
                        thr_cross_h_m = float(mission_cfg.get("threshold_crossing_height_m", 15.0))
                        tdz_from_thr_m = float(mission_cfg.get("touchdown_zone_from_threshold_m", 300.0))
                        tdz_radius_m = max(30.0, float(mission_cfg.get("touchdown_zone_radius_m", 120.0)))
                        rollout_from_thr_m = float(mission_cfg.get("rollout_reference_from_threshold_m", 900.0))

                        tdz_x = thr_x + tdz_from_thr_m * dx
                        tdz_y = thr_y + tdz_from_thr_m * dy
                        rollout_x = thr_x + rollout_from_thr_m * dx
                        rollout_y = thr_y + rollout_from_thr_m * dy

                        markers = [
                            {
                                "name": f"{beacon.get('name', 'RWY')} THR CROSS",
                                "x": thr_x,
                                "y": thr_y,
                                "z": elev_m + thr_cross_h_m,
                                "arrival_radius_m": marker_radius_m,
                                "waypoint_mode": "flyover",
                                "is_active": False,
                            },
                            {
                                "name": f"{beacon.get('name', 'RWY')} TDZ",
                                "x": tdz_x,
                                "y": tdz_y,
                                "z": elev_m,
                                "arrival_radius_m": tdz_radius_m,
                                "waypoint_mode": "flyby",
                                "is_active": True,
                            },
                            {
                                "name": f"{beacon.get('name', 'RWY')} ROLLOUT",
                                "x": rollout_x,
                                "y": rollout_y,
                                "z": elev_m,
                                "arrival_radius_m": max(40.0, runway_width_m * 0.6),
                                "waypoint_mode": "flyby",
                                "is_active": False,
                            },
                        ]

                        for idx, dist_m in enumerate((1500.0, 3000.0, 4500.0, 6000.0), start=1):
                            markers.append(
                                {
                                    "name": f"GS_{idx}",
                                    "x": thr_x - dist_m * dx,
                                    "y": thr_y - dist_m * dy,
                                    "z": elev_m + dist_m * float(np.tan(np.deg2rad(gs_deg))),
                                    "arrival_radius_m": marker_radius_m,
                                    "waypoint_mode": "flyby",
                                    "is_active": False,
                                }
                            )

                        self.nav_data = {
                            "markers": list(reversed(markers)),
                            "mission": {
                                "command_code": cmd_code,
                                "reference_runway": str(beacon.get("name", "")),
                                "target_altitude": tgt_alt,
                                "target_speed": tgt_spd,
                                "glide_slope_deg": gs_deg,
                                "threshold_crossing_height_m": thr_cross_h_m,
                                "touchdown_zone_from_threshold_m": tdz_from_thr_m,
                                "touchdown_zone_radius_m": tdz_radius_m,
                            },
                            "action_mode": str(action_mode),
                        }
                        self.socketio.emit("nav_setup", self.nav_data)
                        return

                if cmd_code == 3 and hasattr(sim_env, "loader") and getattr(sim_env.loader, "waypoints", None):
                    viz = None
                    try:
                        viz = sim_env.loader.get_waypoint_visualization_products()
                    except Exception:
                        viz = None

                    wps = list(getattr(sim_env.loader, "waypoints", []))
                    idx = int(getattr(sim_env.loader, "waypoint_idx", 0))
                    idx = max(0, min(idx, len(wps)))

                    markers = []
                    if isinstance(viz, dict) and isinstance(viz.get("markers"), list):
                        markers = list(viz.get("markers", []))
                    else:
                        for i, wp in enumerate(wps):
                            is_active = i == idx
                            markers.append(
                                {
                                    "name": f"WP_{i + 1}",
                                    "x": float(wp.get("x", 0.0)),
                                    "y": float(wp.get("y", 0.0)),
                                    "z": float(wp.get("z", tgt_alt)),
                                    "arrival_radius_m": float(wp.get("radius_m", 1000.0)),
                                    "waypoint_mode": "flyby",
                                    "is_active": bool(is_active),
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
                        "active": viz.get("active") if isinstance(viz, dict) else None,
                        "action_mode": str(action_mode),
                    }
                    prev_idx = self.nav_data.get("mission", {}).get("waypoint_index") if isinstance(self.nav_data, dict) else None
                    prev_gate = None
                    if isinstance(self.nav_data, dict):
                        prev_active = self.nav_data.get("active")
                        if isinstance(prev_active, dict):
                            prev_gate = prev_active.get("sequence_gate_m")
                    next_gate = None
                    if isinstance(new_nav.get("active"), dict):
                        next_gate = new_nav["active"].get("sequence_gate_m")
                    gate_changed = False
                    if prev_gate is None and next_gate is not None:
                        gate_changed = True
                    elif prev_gate is not None and next_gate is None:
                        gate_changed = True
                    elif prev_gate is not None and next_gate is not None and abs(float(prev_gate) - float(next_gate)) > 100.0:
                        gate_changed = True

                    if self.nav_data is None or prev_idx != idx or gate_changed:
                        self.nav_data = new_nav
                        self.socketio.emit("nav_setup", self.nav_data)
                    return

                tasking_profile = _scenario_tasking_profile(getattr(sim_env.loader, "scenario_data", None))
                if _is_ground_tasking_profile(tasking_profile):
                    self.nav_data = {
                        "markers": [],
                        "mission": {
                            "command_code": cmd_code,
                            "tasking_profile": tasking_profile,
                        },
                        "action_mode": str(action_mode),
                    }
                    self.socketio.emit("nav_setup", self.nav_data)
                    return

                pos0 = sim_env.sim.get_unit_position(sim_env.agent_id)
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

                self.nav_data = {
                    "markers": markers,
                    "mission": {
                        "command_code": cmd_code,
                        "target_heading": tgt_hdg,
                        "target_altitude": tgt_alt,
                        "target_speed": tgt_spd,
                    },
                    "action_mode": str(action_mode),
                }
                self.socketio.emit("nav_setup", self.nav_data)
            except Exception:
                self.nav_data = None

        _update_nav_markers(obs)

        hz = 30
        dt_wall = 1.0 / float(hz)
        sim_time = 0.0
        episode_debug_next_t = 0.0
        episode_max_ias = 0.0
        episode_max_gs = 0.0
        episode_max_agl = 0.0

        scenario_data = sim_env.loader.scenario_data
        env_block = scenario_data.get("environment") if isinstance(scenario_data, dict) else None
        env_block_stripped = not isinstance(env_block, dict) or not (
            "zones" in env_block or "illumination" in env_block
        )
        if env_block_stripped:
            # World-batch loader shims keep only a reduced environment block
            # ({max_steps, time_step}); fall back to the scenario file so
            # zones, overlays, and illumination still reach the viz.
            scenario_path = str(getattr(args, "scenario", "") or "")
            if scenario_path and os.path.isfile(scenario_path):
                try:
                    with open(scenario_path, "r", encoding="utf-8") as fh:
                        scenario_data = json.load(fh)
                except Exception:
                    scenario_data = sim_env.loader.scenario_data
        zones = scenario_data.get("environment", {}).get("zones", [])
        environment_overlays = build_environment_overlay_payload(scenario_data)
        illumination = resolve_scenario_illumination(scenario_data, sim=sim_env.sim)
        self.map_data = {
            "contract_version": VIZ_MAP_SETUP_CONTRACT_VERSION,
            "zones": zones,
            "environment_overlays": environment_overlays,
            "illumination": illumination,
        }
        print("=" * 60)
        print("MAP DATA SENT TO VIZ:")
        for z in zones:
            print(
                f"  Zone '{z.get('name')}': x={z.get('x')}, y={z.get('y')}, "
                f"width={z.get('width')}, length={z.get('length')}, heading={z.get('heading')}"
            )
        print(f"  Environment overlay layers: {len(environment_overlays.get('layers', []))}")
        print("=" * 60)
        self.socketio.emit("map_setup", self.map_data)
        self.socketio.emit("speed_update", {"value": float(self.sim_speed)})

        while True:
            try:
                if self.stop_requested:
                    break
                speed = max(0.05, float(self.sim_speed))
                if speed >= 1.0:
                    eventlet.sleep(dt_wall)
                else:
                    eventlet.sleep(dt_wall / speed)

                if not self.simulation_running:
                    continue

                if self.simulation_paused:
                    continue

                substeps = max(1, int(speed)) if speed >= 1.0 else 1
                terminated = False
                truncated = False
                info = {}
                action = None

                if leader_mode:
                    for _ in range(substeps):
                        if not leader_decision_pending:
                            if args.fixed_action is not None:
                                action = np.asarray(args.fixed_action, dtype=np.float32).reshape(-1)
                            elif self.model:
                                action, _ = self.model.predict(obs, deterministic=True)
                                if action.shape != self.env.action_space.shape:
                                    raise ValueError(
                                        f"Leader action shape mismatch: model produced {action.shape} but env expects {self.env.action_space.shape}"
                                    )
                            else:
                                action = np.zeros(self.env.action_space.shape, dtype=np.float32)
                            self.env.begin_batched_leader_step(action)
                            leader_decision_pending = True
                            leader_exec_steps_remaining = int(getattr(self.env, "decision_interval_steps", 1))
                            if sim_time < 2.0:
                                print(f"Leader Action: {action}")

                        if self.env.has_pending_execution_step() and leader_exec_steps_remaining > 0:
                            exec_obs = self.env.current_execution_observation()
                            exec_action = self.env._predict_execution_action(exec_obs)
                            self.env.step_execution_once(exec_action)
                            leader_exec_steps_remaining -= 1
                            sim_time += sim_env.sim.get_time_step()
                            info = {}
                            try:
                                pending_state = getattr(self.env, "_pending_leader_state", None)
                                if pending_state is not None:
                                    info = dict(getattr(pending_state, "last_info", {}) or {})
                            except Exception:
                                info = {}
                            try:
                                inst_step = sim_env._last_inst if getattr(sim_env, "_last_inst", None) is not None else sim_env.sim.get_instrument_state(sim_env.agent_id)
                                truth_step = sim_env._last_truth if getattr(sim_env, "_last_truth", None) is not None else sim_env.sim.get_agent_observation(sim_env.agent_id)
                                episode_max_ias = max(episode_max_ias, float(getattr(inst_step, "ias", 0.0)))
                                episode_max_gs = max(episode_max_gs, float(getattr(truth_step, "speed", 0.0)))
                                episode_max_agl = max(episode_max_agl, float(getattr(inst_step, "alt_radar", 0.0)))
                            except Exception:
                                pass

                        if leader_decision_pending and (
                            leader_exec_steps_remaining <= 0 or not self.env.has_pending_execution_step()
                        ):
                            obs, reward, terminated, truncated, info = self.env.finish_batched_leader_step()
                            leader_decision_pending = False
                            leader_exec_steps_remaining = 0
                            self.episode_return += float(reward)
                            if terminated or truncated:
                                break
                elif cooperative_mode:
                    for _ in range(substeps):
                        if args.fixed_action is not None:
                            fixed_action = np.asarray(args.fixed_action, dtype=np.float32).reshape(-1)
                            act_dim = int(self.env.action_space.shape[0])
                            slot_count = int(getattr(self.env, "num_envs", 1))
                            if fixed_action.size == act_dim:
                                action = np.repeat(fixed_action.reshape(1, -1), slot_count, axis=0)
                            elif fixed_action.size == slot_count * act_dim:
                                action = fixed_action.reshape(slot_count, act_dim)
                            else:
                                raise ValueError(
                                    f"Cooperative fixed_action expects {act_dim} or {slot_count * act_dim} values, got {fixed_action.size}"
                                )
                        elif self.model:
                            action, _ = self.model.predict(obs, deterministic=True)
                            action = np.asarray(action, dtype=np.float32)
                            if action.ndim == 1:
                                action = action.reshape(1, -1)
                            expected_shape = (int(getattr(self.env, "num_envs", 1)), int(self.env.action_space.shape[0]))
                            if action.shape != expected_shape:
                                raise ValueError(
                                    f"Cooperative action shape mismatch: model produced {action.shape} but env expects {expected_shape}"
                                )
                            if sim_time < 2.0:
                                print(f"Cooperative Action[0]: {action[0]}")
                        else:
                            action = np.zeros(
                                (int(getattr(self.env, "num_envs", 1)), int(self.env.action_space.shape[0])),
                                dtype=np.float32,
                            )

                        next_obs, rewards, dones, infos = self.env.step(action)
                        coop_last_infos = list(infos)
                        self.episode_return += float(np.mean(np.asarray(rewards, dtype=np.float32)))
                        slot_states = _cooperative_slot_states()
                        dt_sim = 0.05
                        if slot_states:
                            try:
                                dt_sim = float(slot_states[0].loader.sim.get_time_step())
                            except Exception:
                                dt_sim = 0.05
                        sim_time += float(dt_sim)
                        try:
                            for slot_state in slot_states:
                                inst_step = slot_state.last_inst
                                truth_step = slot_state.last_truth
                                if inst_step is None or truth_step is None:
                                    continue
                                episode_max_ias = max(episode_max_ias, float(getattr(inst_step, "ias", 0.0)))
                                episode_max_gs = max(episode_max_gs, float(getattr(truth_step, "speed", 0.0)))
                                episode_max_agl = max(episode_max_agl, float(getattr(inst_step, "alt_radar", 0.0)))
                        except Exception:
                            pass
                        obs = next_obs
                        _refresh_cooperative_adapter()
                        terminated = bool(np.any(np.asarray(dones, dtype=bool)))
                        truncated = False
                        info = infos[0] if infos else {}
                        if terminated:
                            break
                else:
                    for _ in range(substeps):
                        if args.fixed_action is not None:
                            action = np.asarray(args.fixed_action, dtype=np.float32).reshape(-1)
                        elif self.model:
                            action, _ = self.model.predict(obs, deterministic=True)
                            if action.shape != self.env.action_space.shape:
                                raise ValueError(
                                    f"Action shape mismatch: model produced {action.shape} but env expects {self.env.action_space.shape} "
                                    f"(hint: set --action_mode to match the training action space)."
                                )
                            if sim_time < 2.0:
                                print(f"Action: {action}")
                        else:
                            action = np.zeros(self.env.action_space.shape, dtype=np.float32)

                        if world_batch_mode:
                            batched_action = np.asarray(action, dtype=np.float32).reshape(1, -1)
                            next_obs_batch, rewards, dones, infos = self.env.step(batched_action)
                            reward = float(np.asarray(rewards, dtype=np.float32).reshape(-1)[0])
                            terminated = bool(np.asarray(dones, dtype=bool).reshape(-1)[0])
                            truncated = False
                            info = dict(infos[0]) if infos and isinstance(infos[0], dict) else {}
                            _refresh_world_batch_adapter()
                            next_obs = _single_obs_from_vec(next_obs_batch)
                        else:
                            next_obs, reward, terminated, truncated, info = self.env.step(action)
                        self.episode_return += float(reward)
                        sim_time += sim_env.sim.get_time_step()
                        try:
                            inst_step = sim_env._last_inst if getattr(sim_env, "_last_inst", None) is not None else sim_env.sim.get_instrument_state(sim_env.agent_id)
                            truth_step = sim_env._last_truth if getattr(sim_env, "_last_truth", None) is not None else sim_env.sim.get_agent_observation(sim_env.agent_id)
                            episode_max_ias = max(episode_max_ias, float(getattr(inst_step, "ias", 0.0)))
                            episode_max_gs = max(episode_max_gs, float(getattr(truth_step, "speed", 0.0)))
                            episode_max_agl = max(episode_max_agl, float(getattr(inst_step, "alt_radar", 0.0)))
                        except Exception:
                            pass
                        if isinstance(self.model, _WorldModelPolicy):
                            self.model.observe(next_obs)
                        obs = next_obs
                        if terminated or truncated:
                            break

                try:
                    m0 = np.asarray(_display_obs(obs).get("mission", []), dtype=np.float32).reshape(-1)
                    if m0.size >= 1 and int(float(m0[0])) == 3:
                        _update_nav_markers(obs)
                except Exception:
                    pass

                units_data = []
                tactical_overlays = {
                    "sensor_rings": [],
                    "datalinks": [],
                    "tracks": [],
                    "nav": self.nav_data if isinstance(self.nav_data, dict) else None,
                    "weapons": [],
                }
                coop_slot_state_by_entity_id = {}
                coop_info_by_entity_id = {}
                if cooperative_mode:
                    slot_states = _cooperative_slot_states()
                    for idx, slot_state in enumerate(slot_states):
                        coop_slot_state_by_entity_id[int(slot_state.entity_id)] = slot_state
                        coop_info_by_entity_id[int(slot_state.entity_id)] = (
                            coop_last_infos[idx]
                            if idx < len(coop_last_infos) and isinstance(coop_last_infos[idx], dict)
                            else {}
                        )

                scenario_entities_cfg = {}
                try:
                    loader_scenario_data = getattr(sim_env.loader, "scenario_data", None)
                    loader_has_entities = (
                        isinstance(loader_scenario_data, dict)
                        and isinstance(loader_scenario_data.get("entities"), list)
                        and len(loader_scenario_data.get("entities")) > 0
                    )
                    if not loader_has_entities:
                        # World-batch loaders keep an empty scenario dict on the
                        # compatibility shim; fall back to the scenario file so
                        # the viz still gets side/type metadata for units.
                        scenario_path = str(getattr(args, "scenario", "") or "")
                        if scenario_path and os.path.isfile(scenario_path):
                            with open(scenario_path, "r", encoding="utf-8") as fh:
                                loader_scenario_data = json.load(fh)
                    if isinstance(loader_scenario_data, dict):
                        raw_entities_cfg = loader_scenario_data.get("entities", [])
                        if isinstance(raw_entities_cfg, list):
                            for ent_cfg in raw_entities_cfg:
                                if not isinstance(ent_cfg, dict):
                                    continue
                                ent_name = str(ent_cfg.get("name", "")).strip()
                                if ent_name:
                                    scenario_entities_cfg[ent_name] = ent_cfg
                except Exception:
                    scenario_entities_cfg = {}

                def get_unit_data(eid, name):
                    if not sim_env.sim.is_unit_active(eid):
                        return None

                    pos = sim_env.sim.get_unit_position(eid)
                    try:
                        hdg = sim_env.sim.get_unit_heading(eid)
                    except AttributeError:
                        # World-batch adapter shims expose observations but not
                        # the legacy per-unit heading accessor.
                        obs_now = sim_env.sim.get_agent_observation(eid)
                        hdg = float(getattr(obs_now, "heading", 0.0) or 0.0)
                    ent_cfg = scenario_entities_cfg.get(str(name), {})
                    type_name = str(ent_cfg.get("type", "")).strip()
                    type_name_upper = type_name.upper()
                    name_upper = str(name).upper()
                    aircraft_tokens = (
                        "F-16",
                        "F16",
                        "AIRCRAFT",
                        "MQ-9",
                        "MQ9",
                        "REAPER",
                        "UAV",
                        "DRONE",
                        "SHAHED",
                        "GERAN",
                    )
                    is_aircraft = any(
                        token in type_name_upper or token in name_upper
                        for token in aircraft_tokens
                    )
                    is_ship = (
                        "DDG-51" in type_name_upper
                        or "ARLEIGH_BURKE" in type_name_upper
                        or "T-AKE-1" in type_name_upper
                        or "LEWIS_AND_CLARK" in type_name_upper
                        or "SHIP" == type_name_upper
                        or "SHIP" in type_name_upper
                        or "DDG-51" in name_upper
                        or "TAKE1" in name_upper
                        or "T-AKE" in name_upper
                        or "HVU" in name_upper
                    )
                    ground_tokens = ("GROUND", "PLATOON", "INFANTRY", "VEHICLE", "TANK", "IFV", "APC")
                    is_ground = any(
                        token in type_name_upper or token in name_upper
                        for token in ground_tokens
                    )
                    if is_aircraft:
                        viz_type = "Aircraft"
                    elif is_ship:
                        viz_type = "Ship"
                    elif is_ground:
                        viz_type = "Ground"
                    else:
                        viz_type = "Facility"

                    return {
                        "id": eid,
                        "name": name,
                        "side": str(ent_cfg.get("side", "Unknown")),
                        "type": viz_type,
                        "platform_type": type_name,
                        # Echelon seed for operational/strategic aggregation;
                        # inferred from naming until the engine models it.
                        "echelon": infer_echelon(type_name, name),
                        "x": pos[0],
                        "y": pos[1],
                        "z": pos[2] - 2.0 if is_aircraft else pos[2],
                        "heading": hdg,
                        "pitch": 0.0,
                        "roll": 0.0,
                        "speed": 0.0,
                        "hp": 100.0,
                        "max_hp": 100.0,
                    }

                def get_runtime_unit_data(runtime_unit, known_entity_ids):
                    try:
                        eid = int(getattr(runtime_unit, "id"))
                    except Exception:
                        return None
                    if eid in known_entity_ids:
                        return None
                    try:
                        unit_type = int(getattr(runtime_unit, "type", 0))
                    except Exception:
                        unit_type = 0
                    # Runtime UnitType values: Aircraft=1, Ship=2, Missile=3, Facility=4.
                    if unit_type != 3:
                        return None
                    try:
                        missile_state = sim_env.sim.debug_get_missile_runtime_state(eid)
                    except Exception:
                        missile_state = {}
                    try:
                        velocity = sim_env.sim.get_unit_velocity(eid)
                    except Exception:
                        velocity = (0.0, 0.0, 0.0)
                    vx = float(velocity[0]) if len(velocity) > 0 else 0.0
                    vy = float(velocity[1]) if len(velocity) > 1 else 0.0
                    vz = float(velocity[2]) if len(velocity) > 2 else 0.0
                    speed = float(math.sqrt(vx * vx + vy * vy + vz * vz))
                    side_code = int(getattr(runtime_unit, "side", 0) or 0)
                    side = "Blue" if side_code == 1 else "Red" if side_code == 2 else "Neutral" if side_code == 3 else "Unknown"
                    service_profile = "BlueAir" if side == "Blue" else "RedAir" if side == "Red" else ""
                    return {
                        "id": eid,
                        "name": f"Missile_{eid}",
                        "side": side,
                        "type": "Missile",
                        "platform_type": "Missile",
                        "echelon": "",
                        "service_profile": service_profile,
                        "x": float(getattr(runtime_unit, "x", 0.0)),
                        "y": float(getattr(runtime_unit, "y", 0.0)),
                        "z": float(getattr(runtime_unit, "z", 0.0)),
                        "heading": float(getattr(runtime_unit, "heading", 0.0)),
                        "pitch": 0.0,
                        "roll": 0.0,
                        "speed": speed,
                        "ias": speed,
                        "hp": 100.0,
                        "max_hp": 100.0,
                        "attacker_id": int(missile_state.get("attacker_id", 0)) if isinstance(missile_state, dict) else 0,
                        "target_id": int(missile_state.get("target_id", 0)) if isinstance(missile_state, dict) else 0,
                    }

                for name, eid in sim_env.loader.entities.items():
                    u = get_unit_data(eid, name)
                    if u:
                        unit_side = str(u.get("side", "Unknown"))
                        ent_cfg = scenario_entities_cfg.get(str(name), {})
                        type_name = str(ent_cfg.get("type", "")).strip()
                        type_name_upper = type_name.upper()
                        is_ship_unit = (
                            u.get("type") == "Ship"
                            or "SHIP" in type_name_upper
                            or "DDG-51" in type_name_upper
                            or "T-AKE-1" in type_name_upper
                        )
                        slot_state = coop_slot_state_by_entity_id.get(int(eid)) if cooperative_mode else None
                        if slot_state is not None or eid == sim_env.agent_id:
                            if slot_state is not None:
                                raw = slot_state.last_truth if slot_state.last_truth is not None else sim_env.sim.get_agent_observation(eid)
                                try:
                                    inst_now = slot_state.last_inst if slot_state.last_inst is not None else sim_env.sim.get_instrument_state(eid)
                                except Exception:
                                    inst_now = None
                                slot_info = coop_info_by_entity_id.get(int(eid), {})
                                act_for_display = slot_state.last_action
                            else:
                                raw = sim_env.sim.get_agent_observation(eid)
                                try:
                                    inst_now = sim_env.sim.get_instrument_state(eid)
                                except Exception:
                                    inst_now = None
                                slot_info = info if isinstance(info, dict) else {}
                                eff_action = None
                                if isinstance(slot_info, dict):
                                    ea = slot_info.get("effective_action")
                                    if isinstance(ea, np.ndarray):
                                        eff_action = ea
                                    elif isinstance(ea, (list, tuple)):
                                        try:
                                            eff_action = np.asarray(ea, dtype=np.float32).reshape(-1)
                                        except Exception:
                                            eff_action = None
                                act_for_display = eff_action if isinstance(eff_action, np.ndarray) and eff_action.ndim == 1 else action

                            runway_cross_m = slot_info.get("runway_cross_m") if isinstance(slot_info, dict) else None
                            on_runway_geom = slot_info.get("on_runway_geom") if isinstance(slot_info, dict) else None

                            rud_cmd = None
                            thr_cmd = None
                            brake_cmd = None
                            if isinstance(act_for_display, np.ndarray):
                                act_flat = np.asarray(act_for_display, dtype=np.float32).reshape(-1)
                                if sim_env.action_mode == "full" and act_flat.size >= 9:
                                    rud_cmd = float(act_flat[2])
                                    thr_cmd = float(act_flat[3])
                                    brake_cmd = float(half_to_unit(float(max(act_flat[7], act_flat[8]))))
                                elif sim_env.action_mode == "takeoff4" and act_flat.size >= 4:
                                    rud_cmd = float(act_flat[2])
                                    thr_cmd = float(act_flat[3])
                                elif sim_env.action_mode == "takeoff2" and act_flat.size >= 2:
                                    thr_cmd = float(act_flat[1])

                            wind_str = "n/a"
                            if inst_now is not None:
                                wind_str = f"{float(inst_now.wind_speed):.2f}@{float(inst_now.wind_dir):.1f}"

                            if sim_time + 1.0e-6 >= episode_debug_next_t:
                                cross_str = "n/a" if runway_cross_m is None else f"{float(runway_cross_m):.1f}"
                                onrw_str = "n/a" if on_runway_geom is None else str(int(float(on_runway_geom) > 0.5))
                                thr_str = "n/a" if thr_cmd is None else f"{thr_cmd:.2f}"
                                rud_str = "n/a" if rud_cmd is None else f"{rud_cmd:.2f}"
                                brk_str = "n/a" if brake_cmd is None else f"{brake_cmd:.2f}"

                                print(
                                    f"Viz Frame T={sim_time:.2f} | {name} "
                                    f"Pos: ({u['x']:.2f}, {u['y']:.2f}, {u['z']:.2f}) "
                                    f"Hdg: {float(getattr(raw, 'heading', 0.0)):.1f} Trk: {float(getattr(inst_now, 'ground_track', 0.0)):.1f} "
                                    f"IAS: {float(getattr(inst_now, 'ias', 0.0)):.1f} Wind: {wind_str} "
                                    f"Cross: {cross_str} OnRw: {onrw_str} "
                                    f"EffAct(thr={thr_str}, rud={rud_str}, brk={brk_str}) "
                                    f"ThrPos: {float(getattr(inst_now, 'throttle_pos', 0.0)):.2f}"
                                )
                                sys.stdout.flush()
                                episode_debug_next_t += 0.5
                            u.update(
                                {
                                    "speed": float(getattr(raw, "speed", 0.0)),
                                    "ias": float(getattr(inst_now, "ias", float(getattr(raw, "speed", 0.0)))) if inst_now is not None else float(getattr(raw, "speed", 0.0)),
                                    "roll": float(getattr(raw, "roll", 0.0)),
                                    "throttle": float(getattr(raw, "throttle", 0.0)),
                                    "pitch": float(getattr(raw, "pitch", 0.0)),
                                    "hp": float(getattr(raw, "health", 100.0)),
                                    "side": unit_side,
                                }
                            )

                        if is_ship_unit:
                            radar_range_m = None
                            if "DDG-51" in type_name_upper or "ARLEIGH_BURKE" in type_name_upper or "DDG" in str(name).upper():
                                radar_range_m = 46300.0
                            elif "T-AKE-1" in type_name_upper or "LEWIS_AND_CLARK" in type_name_upper or "TAKE" in str(name).upper():
                                radar_range_m = 36300.0
                            if radar_range_m is not None:
                                tactical_overlays["sensor_rings"].append(
                                    {
                                        "entity_id": int(eid),
                                        "name": str(name),
                                        "side": unit_side,
                                        "platform_type": str(type_name),
                                        "service_profile": str(ent_cfg.get("service_profile", "")),
                                        "x": float(u["x"]),
                                        "y": float(u["y"]),
                                        "range_m": float(radar_range_m),
                                    }
                                )

                        if u.get("type") == "Ship" and unit_side.lower() == "blue":
                            for other_name, other_eid in sim_env.loader.entities.items():
                                if int(other_eid) == int(eid):
                                    continue
                                other_cfg = scenario_entities_cfg.get(str(other_name), {})
                                other_side = str(other_cfg.get("side", "Unknown"))
                                other_type = str(other_cfg.get("type", "")).strip().upper()
                                if other_side.lower() == "blue" and (
                                    "SHIP" in other_type or "DDG-51" in other_type or "T-AKE-1" in other_type
                                ):
                                    other_pos = sim_env.sim.get_unit_position(other_eid)
                                    tactical_overlays["datalinks"].append(
                                        {
                                            "from_id": int(eid),
                                            "to_id": int(other_eid),
                                            "from_x": float(u["x"]),
                                            "from_y": float(u["y"]),
                                            "to_x": float(other_pos[0]),
                                            "to_y": float(other_pos[1]),
                                        }
                                    )

                        try:
                            ship_obs = sim_env.sim.get_agent_observation(eid)
                        except Exception:
                            ship_obs = None
                        if ship_obs is not None:
                            for track in getattr(ship_obs, "contacts", []):
                                try:
                                    track_id = int(getattr(track, "id", 0))
                                    track_range = float(getattr(track, "range", 0.0))
                                    track_az = float(getattr(track, "azimuth", 0.0))
                                    track_source = int(getattr(track, "source", 0))
                                except Exception:
                                    continue
                                bearing_deg = float(u["heading"]) + track_az
                                bearing_rad = math.radians(90.0 - bearing_deg)
                                tx = float(u["x"]) + track_range * math.cos(bearing_rad)
                                ty = float(u["y"]) + track_range * math.sin(bearing_rad)
                                tactical_overlays["tracks"].append(
                                    {
                                        "observer_id": int(eid),
                                        "observer_name": str(name),
                                        "observer_side": unit_side,
                                        "target_id": int(track_id),
                                        "x0": float(u["x"]),
                                        "y0": float(u["y"]),
                                        "x1": float(tx),
                                        "y1": float(ty),
                                        "source": int(track_source),
                                    }
                                )

                        units_data.append(u)

                known_entity_ids = {int(v) for v in sim_env.loader.entities.values()}
                try:
                    runtime_units = list(sim_env.sim.get_all_units())
                except Exception:
                    runtime_units = []
                for runtime_unit in runtime_units:
                    u = get_runtime_unit_data(runtime_unit, known_entity_ids)
                    if u:
                        tactical_overlays["weapons"].append(
                            {
                                "entity_id": int(u["id"]),
                                "name": str(u["name"]),
                                "side": str(u["side"]),
                                "type": str(u["type"]),
                                "x": float(u["x"]),
                                "y": float(u["y"]),
                                "z": float(u["z"]),
                                "heading": float(u["heading"]),
                                "speed_mps": float(u["speed"]),
                                "attacker_id": int(u.get("attacker_id", 0) or 0),
                                "target_id": int(u.get("target_id", 0) or 0),
                            }
                        )
                        units_data.append(u)

                state = {
                    "contract_version": VIZ_STATE_FRAME_CONTRACT_VERSION,
                    "tick": sim_time,
                    "units": units_data,
                    "mission_status": _capture_mission_status(sim_time),
                    "tactical": tactical_overlays,
                }

                self.socketio.emit("state_update", state)

                if terminated or truncated:
                    term_reason = None
                    reward_terms = None
                    try:
                        if isinstance(info, dict):
                            term_reason = info.get("termination_reason")
                            reward_terms = info.get("reward_terms")
                    except Exception:
                        term_reason = None
                        reward_terms = None
                    if isinstance(term_reason, str) and term_reason:
                        print(
                            "Episode Done. "
                            f"Return: {self.episode_return:.2f} | Reason: {term_reason} | "
                            f"MaxIAS: {episode_max_ias:.1f} | MaxGS: {episode_max_gs:.1f} | MaxAGL: {episode_max_agl:.1f} | "
                            f"RewardTerms: {_format_reward_terms(reward_terms)}"
                        )
                    else:
                        print(
                            "Episode Done. "
                            f"Return: {self.episode_return:.2f} | MaxIAS: {episode_max_ias:.1f} | "
                            f"MaxGS: {episode_max_gs:.1f} | MaxAGL: {episode_max_agl:.1f} | "
                            f"RewardTerms: {_format_reward_terms(reward_terms)}"
                        )
                    if getattr(args, "pause_on_done", False):
                        self.simulation_paused = True
                        print("Simulation paused on terminal state (--pause_on_done).")
                    else:
                        obs = _reset_env_for_viz(int(args.seed) if args.seed is not None else None)
                        leader_decision_pending = False
                        leader_exec_steps_remaining = 0
                        if isinstance(self.model, (_WorldModelPolicy, _ScriptedPolicy)):
                            self.model.reset(obs)
                        _reset_mission_status_tracking()
                        _capture_mission_status(0.0)
                        _update_nav_markers(obs)
                        self.episode_return = 0.0
                        episode_debug_next_t = 0.0
                        episode_max_ias = 0.0
                        episode_max_gs = 0.0
                        episode_max_agl = 0.0

            except Exception as e:
                print(f"Viz Loop Error: {e}")
                import traceback

                traceback.print_exc()
                break

        self.ready = False
        self._release_runtime_resources()
        self._notify_status()
