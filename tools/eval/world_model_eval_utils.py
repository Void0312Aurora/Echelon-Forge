from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import torch

from tools.eval.eval_utils import bootstrap_repo_imports

bootstrap_repo_imports()

from python.world_model.features import (  # noqa: E402
    DEFAULT_ANGLE_DEG_INDICES,
    angle_sincos_features,
    append_angle_sincos_features,
    nav_tracking_features,
)
from python.world_model.networks import Actor, GRUActor, WorldModel  # noqa: E402
from python.world_model.utils import DeviceConfig  # noqa: E402

import world_model_train as wmt  # noqa: E402


RAW_OBS_ACTOR_INPUTS = {
    "obs",
    "obs_gru",
    "obs_sincos",
    "obs_sincos_gru",
    "obs_sincos_track",
    "obs_sincos_track_gru",
}
OBS_VISUAL_EMBED_INPUTS = {"obs_sincos_track_vis", "obs_sincos_track_vis_gru"}


@dataclass
class WorldModelEvalBundle:
    device: torch.device
    ckpt: dict[str, Any]
    cfg: dict[str, Any]
    spec: dict[str, Any]
    wm: WorldModel
    actor: Any
    actor_input: str
    actor_is_gru: bool
    action_dim: int
    obs_vec_dim: int
    action_low: np.ndarray
    action_high: np.ndarray
    visual_shape: tuple[int, int, int] | None
    angle_deg_indices: tuple[int, ...]
    obs_mean: torch.Tensor
    obs_std: torch.Tensor
    obs_norm_clip: float | None
    visual_norm_clip: float | None
    visual_mean_t: torch.Tensor | None
    visual_std_t: torch.Tensor | None


def load_world_model_eval_bundle(checkpoint: str, *, device: str, include_visual: bool) -> WorldModelEvalBundle:
    torch_device = DeviceConfig(device).torch_device()
    try:
        ckpt = torch.load(checkpoint, map_location=torch_device, weights_only=False)
    except TypeError:
        ckpt = torch.load(checkpoint, map_location=torch_device)

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
    actor_is_gru = bool(actor_input.endswith("_gru"))
    angle_deg_indices = DEFAULT_ANGLE_DEG_INDICES
    if isinstance(cfg, dict):
        try:
            angle_deg_indices = tuple(int(x) for x in cfg.get("angle_deg_indices", DEFAULT_ANGLE_DEG_INDICES))
        except Exception:
            angle_deg_indices = DEFAULT_ANGLE_DEG_INDICES

    wm = WorldModel(action_dim=action_dim, obs_vec_dim=obs_vec_dim, visual_shape=visual_shape).to(torch_device)
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

    if actor_is_gru:
        actor = GRUActor(input_dim=actor_feat_dim, action_dim=action_dim).to(torch_device)
    else:
        actor = Actor(feat_dim=actor_feat_dim, action_dim=action_dim).to(torch_device)
    actor.load_state_dict(ckpt["actor"])
    actor.eval()

    obs_mean = ckpt.get("obs_mean", None)
    obs_std = ckpt.get("obs_std", None)
    if obs_mean is None or obs_std is None:
        raise ValueError("Checkpoint missing obs_mean/obs_std")
    obs_mean_t = torch.as_tensor(obs_mean, device=torch_device, dtype=torch.float32).reshape(1, -1)
    obs_std_t = torch.as_tensor(obs_std, device=torch_device, dtype=torch.float32).reshape(1, -1)

    obs_norm_clip = cfg.get("obs_norm_clip", None) if isinstance(cfg, dict) else None
    visual_norm_clip = cfg.get("visual_norm_clip", None) if isinstance(cfg, dict) else None

    if visual_shape is not None and not bool(include_visual) and actor_input not in RAW_OBS_ACTOR_INPUTS:
        raise ValueError("This checkpoint expects ARB visual input; rerun with --include_visual.")

    visual_mean_t = None
    visual_std_t = None
    if visual_shape is not None:
        visual_mean = ckpt.get("visual_mean", None)
        visual_std = ckpt.get("visual_std", None)
        if visual_mean is None or visual_std is None:
            raise ValueError("Checkpoint missing visual_mean/visual_std")
        visual_mean_t = torch.as_tensor(visual_mean, device=torch_device, dtype=torch.float32).reshape(1, 1, 1, -1)
        visual_std_t = torch.as_tensor(visual_std, device=torch_device, dtype=torch.float32).reshape(1, 1, 1, -1)

    return WorldModelEvalBundle(
        device=torch_device,
        ckpt=ckpt,
        cfg=cfg,
        spec=spec,
        wm=wm,
        actor=actor,
        actor_input=actor_input,
        actor_is_gru=actor_is_gru,
        action_dim=action_dim,
        obs_vec_dim=obs_vec_dim,
        action_low=action_low,
        action_high=action_high,
        visual_shape=visual_shape,
        angle_deg_indices=angle_deg_indices,
        obs_mean=obs_mean_t,
        obs_std=obs_std_t,
        obs_norm_clip=obs_norm_clip,
        visual_norm_clip=visual_norm_clip,
        visual_mean_t=visual_mean_t,
        visual_std_t=visual_std_t,
    )


class WorldModelPolicyRunner:
    def __init__(self, checkpoint: str, *, device: str, include_visual: bool) -> None:
        self.bundle = load_world_model_eval_bundle(checkpoint, device=device, include_visual=include_visual)
        self.device = self.bundle.device
        self.wm = self.bundle.wm
        self.actor = self.bundle.actor
        self.actor_input = self.bundle.actor_input
        self.actor_is_gru = self.bundle.actor_is_gru
        self.angle_deg_indices = self.bundle.angle_deg_indices
        self.obs_raw_t: torch.Tensor | None = None
        self.obs_t: torch.Tensor | None = None
        self.vis_t: torch.Tensor | None = None
        self.embed: torch.Tensor | None = None
        self.state = None
        self.actor_h: torch.Tensor | None = None
        self.deterministic_state = True
        self._last_action_norm: torch.Tensor | None = None

    def _needs_embed(self) -> bool:
        return self.actor_input not in RAW_OBS_ACTOR_INPUTS or self.actor_input in OBS_VISUAL_EMBED_INPUTS

    def _preprocess_visual(self, obs: dict[str, Any]) -> torch.Tensor | None:
        visual_shape = self.bundle.visual_shape
        if visual_shape is None:
            return None
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
        vis_t = torch.from_numpy(visual).to(self.device).float().unsqueeze(0)
        vis_t = (vis_t - self.bundle.visual_mean_t) / self.bundle.visual_std_t  # type: ignore[operator]
        vis_t = wmt._apply_norm_clip(vis_t, self.bundle.visual_norm_clip)
        return vis_t.reshape(1, -1)

    def _set_obs(self, obs: dict[str, Any]) -> None:
        obs_vec = wmt._flatten_obs(obs)
        if obs_vec.shape[0] != self.bundle.obs_vec_dim:
            raise ValueError(f"obs_vec_dim mismatch: got {obs_vec.shape[0]}, expected {self.bundle.obs_vec_dim}")
        self.obs_raw_t = torch.from_numpy(obs_vec).to(self.device).float().unsqueeze(0)
        self.obs_t = (self.obs_raw_t - self.bundle.obs_mean) / self.bundle.obs_std
        self.obs_t = wmt._apply_norm_clip(self.obs_t, self.bundle.obs_norm_clip)
        self.vis_t = self._preprocess_visual(obs)
        if self._needs_embed():
            self.embed = self.wm.encoder(self.obs_t, self.vis_t) if self.vis_t is not None else self.wm.encoder(self.obs_t)
        else:
            self.embed = None

    def reset_episode(self, obs: dict[str, Any], *, deterministic_state: bool) -> None:
        self.deterministic_state = bool(deterministic_state)
        self._set_obs(obs)
        self.state = None
        if self.actor_input == "rssm":
            assert self.embed is not None
            self.state, _ = self.wm.rssm.observe_init(self.embed, deterministic=self.deterministic_state)
        self.actor_h = self.actor.init_h(batch_size=1, device=self.device) if self.actor_is_gru else None
        self._last_action_norm = None

    def _build_feat(self) -> torch.Tensor:
        assert self.obs_raw_t is not None and self.obs_t is not None
        if self.actor_input in ("obs", "obs_gru"):
            return self.obs_t
        if self.actor_input in ("obs_sincos", "obs_sincos_gru"):
            return append_angle_sincos_features(
                obs_raw_deg=self.obs_raw_t,
                obs_norm=self.obs_t,
                angle_deg_indices=self.angle_deg_indices,
            )
        if self.actor_input in ("obs_sincos_track", "obs_sincos_track_gru"):
            feat = append_angle_sincos_features(
                obs_raw_deg=self.obs_raw_t,
                obs_norm=self.obs_t,
                angle_deg_indices=self.angle_deg_indices,
            )
            track = nav_tracking_features(self.obs_raw_t)
            return torch.cat([feat, track], dim=-1)
        if self.actor_input in ("obs_sincos_track_vis", "obs_sincos_track_vis_gru"):
            assert self.embed is not None
            feat = append_angle_sincos_features(
                obs_raw_deg=self.obs_raw_t,
                obs_norm=self.obs_t,
                angle_deg_indices=self.angle_deg_indices,
            )
            track = nav_tracking_features(self.obs_raw_t)
            vis_dim = int(getattr(self.wm.encoder, "visual_embed_dim", 0))
            if vis_dim <= 0:
                raise ValueError(f"actor_input={self.actor_input!r} requires visual embedding")
            vis_embed = self.embed[:, -vis_dim:]
            return torch.cat([feat, track, vis_embed], dim=-1)
        if self.actor_input in ("embed", "embed_gru"):
            assert self.embed is not None
            return self.embed
        if self.actor_input in ("embed_sincos", "embed_sincos_gru"):
            assert self.embed is not None
            ang = angle_sincos_features(self.obs_raw_t, angle_deg_indices=self.angle_deg_indices)
            return torch.cat([self.embed, ang], dim=-1)
        if self.actor_input in ("embed_sincos_track", "embed_sincos_track_gru"):
            assert self.embed is not None
            ang = angle_sincos_features(self.obs_raw_t, angle_deg_indices=self.angle_deg_indices)
            track = nav_tracking_features(self.obs_raw_t)
            return torch.cat([self.embed, ang, track], dim=-1)
        assert self.state is not None
        return self.wm.feat(self.state)

    def act_env(self) -> np.ndarray:
        feat = self._build_feat()
        with torch.no_grad():
            if self.actor_is_gru:
                mean, _std, self.actor_h = self.actor.step(feat, self.actor_h)  # type: ignore[union-attr]
            else:
                mean, _std = self.actor(feat)  # type: ignore[union-attr]
            action_norm = torch.tanh(mean)
        self._last_action_norm = action_norm.detach()
        return wmt._unnormalize_action(
            action_norm.squeeze(0).cpu().numpy().astype(np.float32, copy=False),
            self.bundle.action_low,
            self.bundle.action_high,
        )

    def observe(self, next_obs: dict[str, Any]) -> None:
        prev_state = self.state
        action_norm = self._last_action_norm
        self._set_obs(next_obs)
        if prev_state is not None:
            assert self.embed is not None and action_norm is not None
            self.state, _, _ = self.wm.rssm.obs_step(
                prev_state,
                action_norm,
                self.embed,
                deterministic=self.deterministic_state,
            )
