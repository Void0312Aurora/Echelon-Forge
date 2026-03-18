from __future__ import annotations

from dataclasses import dataclass
import os
import time

import numpy as np
import torch
import torch.nn.functional as F

from python.world_model.features import (
    DEFAULT_ANGLE_DEG_INDICES,
    angle_sincos_features,
    append_angle_sincos_features,
    nav_tracking_features,
)
from python.world_model.networks import Actor, GRUActor, RSSMState, Value, WorldModel, kl_divergence, lambda_return
from python.world_model.replay import EpisodeDataset
from python.world_model.utils import symlog, symexp


@dataclass(frozen=True)
class DreamerConfig:
    seed: int = 0
    batch_size: int = 16
    seq_len: int = 50
    wm_lr: float = 3e-4
    actor_lr: float = 3e-4
    value_lr: float = 3e-4
    grad_clip: float = 100.0
    free_nats: float = 1.0
    kl_scale: float = 1.0
    obs_scale: float = 1.0
    reward_scale: float = 1.0
    cont_scale: float = 1.0
    visual_scale: float = 1.0
    horizon: int = 15
    gamma: float = 0.99
    lambda_: float = 0.95
    entropy_scale: float = 1e-3
    reward_symlog_clip: float | None = 6.0
    bc_scale: float = 0.0
    # Behavior cloning stability: when training the actor with BC, feed a mixture of
    # teacher actions and actor actions into the RSSM so the policy is robust in closed loop.
    # 1.0 = pure teacher forcing (offline), 0.0 = pure student forcing.
    bc_teacher_prob: float = 1.0
    # Policy input mode:
    # - "rssm": actor consumes RSSM latent features (Dreamer-style)
    # - "embed": actor consumes per-step observation embeddings (stable BC baseline)
    # - "embed_gru": actor is a GRU over observation embeddings (history-capable BC)
    # - "embed_sincos": like "embed" but appends sin/cos features for key degree-valued angles
    # - "embed_sincos_gru": like "embed_gru" but appends sin/cos features
    # - "embed_sincos_track": like "embed_sincos" but appends realism-safe tracking error features
    # - "embed_sincos_track_gru": like "embed_sincos_gru" but appends tracking error features
    # - "obs": actor consumes normalized obs_vec directly (BC only; avoids encoder compression)
    # - "obs_gru": actor is a GRU over normalized obs_vec directly (BC only; history-capable)
    # - "obs_sincos": like "obs" but appends sin/cos features for key degree-valued angles
    # - "obs_sincos_gru": like "obs_gru" but appends sin/cos features
    # - "obs_sincos_track": like "obs_sincos" but appends tracking error features (8d)
    # - "obs_sincos_track_gru": GRU over obs_sincos_track features
    # - "obs_sincos_track_vis": like "obs_sincos_track" but also appends *visual* embedding (keeps full-observation training)
    # - "obs_sincos_track_vis_gru": GRU over obs_sincos_track_vis features
    actor_input: str = "rssm"
    # Indices in obs_vec (raw degrees) to be encoded as sin/cos features when using *_sincos actor inputs.
    # Keep this configurable for backward compatibility across checkpoints when we add new angle channels.
    angle_deg_indices: tuple[int, ...] = DEFAULT_ANGLE_DEG_INDICES
    # Startup / normalization
    verbose: bool = True
    visual_stats_episodes: int = 16
    visual_stats_frames_per_episode: int = 20
    stats_cache: bool = True
    # Ignore cached stats.npz (if present) and recompute normalization stats from the dataset.
    # When stats_cache is True, the recomputed stats will overwrite stats.npz.
    stats_force_recompute: bool = False
    obs_min_std: float = 0.1
    obs_norm_clip: float | None = 10.0
    visual_min_std: float = 0.1
    visual_norm_clip: float | None = 10.0
    visual_encoder_type: str = "cnn"
    visual_cnn_channels: int = 64
    # Behavior cloning stability: roll in the RSSM using the actor's own actions
    # (DAgger-style) to reduce covariate shift at deployment.
    bc_rollin_prob: float = 0.0  # 0=teacher forcing, 1=fully closed-loop roll-in
    # Recurrent BC: optional "burn-in" steps. When >0 and using a *_gru actor_input,
    # we sample random subsequences of length (seq_len + burn_in) and compute the loss
    # only on the last `seq_len` steps. This helps GRU policies learn long-horizon tasks
    # without being restricted to the first seq_len steps of each episode.
    bc_gru_burn_in: int = 0
    # Non-recurrent BC: probability of sampling sequences starting at t=0.
    #
    # Many aviation tasks have important transients near reset (e.g., capturing a new commanded heading),
    # while most of the episode is steady-state trim with near-zero actions. Pure uniform sampling over
    # long episodes can under-sample those transients, causing BC policies to ignore mission commands.
    bc_start_at_zero_prob: float = 0.0
    # Use posterior mean (deterministic) RSSM state for BC roll-in/targets.
    # This reduces action noise caused by stochastic latent sampling during evaluation.
    bc_deterministic_state: bool = True
    # Optional BC reweighting: emphasize matching expert rudder when the expert commands a large correction.
    # This helps runway tracking under crosswind without changing observations or adding privileged info.
    bc_rudder_mag_weight: float = 0.0
    # Optional BC reweighting: constant weight on rudder error (applies even when expert rudder is small).
    # This reduces compounding drift from tiny per-step rudder errors during long ground rolls.
    bc_rudder_weight: float = 1.0
    # Optional BC reweighting for pitch (stick_pitch, action dim 0): emphasize rotation/climb-out behavior.
    # This remains realism-safe: it only changes learning-side loss scaling, not observations.
    bc_pitch_mag_weight: float = 0.0
    bc_pitch_weight: float = 1.0
    # Optional BC reweighting for roll (stick_roll, action dim 1): emphasize bank/heading capture accuracy.
    # Small roll errors can integrate into large heading drift over long horizons.
    bc_roll_mag_weight: float = 0.0
    bc_roll_weight: float = 1.0
    # Optional BC reweighting for throttle (index 3 in full/takeoff4 action layouts).
    # Helps prevent speed runaway due to small systematic throttle bias.
    bc_throttle_mag_weight: float = 0.0
    bc_throttle_weight: float = 1.0
    # Optional BC step-weighting: emphasize ground-roll control (runway tracking) vs airborne trim.
    # This does NOT leak privileged information: it uses radar altitude (a pilot-observable signal)
    # already present in obs_vec.
    bc_ground_alt_threshold: float = 5.0
    bc_ground_weight: float = 1.0
    bc_airborne_weight: float = 1.0
    # Optional BC step-weighting by ILS localizer deviation magnitude (focus on recovery steps).
    # loc_dev is already part of the observation (ILS instrument), so this remains realism-safe.
    bc_loc_weight: float = 0.0
    # Optional BC step-weighting by mission heading error magnitude (emphasize capture/transients).
    # Uses only mission command + heading instrument, so it remains realism-safe.
    bc_hdg_weight: float = 0.0
    bc_hdg_norm_deg: float = 30.0


class DreamerTrainer:
    def __init__(self, *, dataset: EpisodeDataset, world_model: WorldModel, device: torch.device, cfg: DreamerConfig):
        self.dataset = dataset
        self.wm = world_model.to(device)
        self.device = device
        self.cfg = cfg
        self.verbose = bool(cfg.verbose)
        self.rng = np.random.default_rng(cfg.seed)
        try:
            self.angle_deg_indices = tuple(int(x) for x in getattr(cfg, "angle_deg_indices", DEFAULT_ANGLE_DEG_INDICES))
        except Exception:
            self.angle_deg_indices = DEFAULT_ANGLE_DEG_INDICES

        rssm_feat_dim = self.wm.rssm.deter_dim + self.wm.rssm.stoch_dim
        actor_input = str(getattr(cfg, "actor_input", "rssm"))
        if actor_input in ("obs", "obs_gru"):
            actor_feat_dim = int(dataset.spec.obs_vec_dim)
        elif actor_input in ("obs_sincos", "obs_sincos_gru"):
            actor_feat_dim = int(dataset.spec.obs_vec_dim) + 2 * len(self.angle_deg_indices)
        elif actor_input in ("obs_sincos_track", "obs_sincos_track_gru"):
            actor_feat_dim = int(dataset.spec.obs_vec_dim) + 2 * len(self.angle_deg_indices) + 8
        elif actor_input in ("obs_sincos_track_vis", "obs_sincos_track_vis_gru"):
            if self.wm.encoder.visual is None:
                raise ValueError("actor_input='obs_sincos_track_vis*' requires a visual-capable world model/dataset")
            actor_feat_dim = int(dataset.spec.obs_vec_dim) + 2 * len(self.angle_deg_indices) + 8 + int(
                getattr(self.wm.encoder, "visual_embed_dim", 0)
            )
        elif actor_input in ("embed_sincos", "embed_sincos_gru"):
            actor_feat_dim = int(self.wm.encoder.embed_dim) + 2 * len(self.angle_deg_indices)
        elif actor_input in ("embed_sincos_track", "embed_sincos_track_gru"):
            actor_feat_dim = int(self.wm.encoder.embed_dim) + 2 * len(self.angle_deg_indices) + 8
        elif actor_input in ("embed", "embed_gru"):
            actor_feat_dim = int(self.wm.encoder.embed_dim)
        else:
            actor_feat_dim = int(rssm_feat_dim)
        if actor_input in (
            "embed_gru",
            "embed_sincos_gru",
            "embed_sincos_track_gru",
            "obs_gru",
            "obs_sincos_gru",
            "obs_sincos_track_gru",
            "obs_sincos_track_vis_gru",
        ):
            self.actor = GRUActor(input_dim=actor_feat_dim, action_dim=dataset.spec.action_dim).to(device)
        else:
            self.actor = Actor(feat_dim=actor_feat_dim, action_dim=dataset.spec.action_dim).to(device)
        self.value = Value(feat_dim=rssm_feat_dim).to(device)

        self.opt_wm = torch.optim.Adam(self.wm.parameters(), lr=cfg.wm_lr)
        self.opt_actor = torch.optim.Adam(self.actor.parameters(), lr=cfg.actor_lr)
        self.opt_value = torch.optim.Adam(self.value.parameters(), lr=cfg.value_lr)

        self.visual_mean = None
        self.visual_std = None
        self.obs_mean = None
        self.obs_std = None

        force_recompute = bool(getattr(cfg, "stats_force_recompute", False))
        if not (bool(cfg.stats_cache) and (not force_recompute) and self._try_load_cached_stats()):
            self.obs_mean, self.obs_std = self._compute_obs_stats_full()
            if dataset.spec.visual_shape is not None:
                self.visual_mean, self.visual_std = self._compute_visual_stats_fast(
                    max_episodes=int(cfg.visual_stats_episodes),
                    frames_per_episode=int(cfg.visual_stats_frames_per_episode),
                )
            if bool(cfg.stats_cache):
                self._save_cached_stats()

        if self.obs_mean is None or self.obs_std is None:
            raise RuntimeError("Failed to initialize obs_mean/obs_std")

    def _to_torch(self, batch: dict[str, np.ndarray]) -> dict[str, torch.Tensor]:
        out: dict[str, torch.Tensor] = {}
        for k, v in batch.items():
            if v.dtype == np.bool_:
                out[k] = torch.from_numpy(v.astype(np.float32)).to(self.device)
            else:
                out[k] = torch.from_numpy(v).to(self.device)
        return out

    def _try_load_cached_stats(self) -> bool:
        stats_path = os.path.join(self.dataset.root_dir, "stats.npz")
        if not os.path.exists(stats_path):
            return False
        try:
            data = np.load(stats_path, allow_pickle=False)
            obs_mean = np.asarray(data["obs_mean"], dtype=np.float32).reshape(-1)
            obs_std = np.asarray(data["obs_std"], dtype=np.float32).reshape(-1)
            if obs_mean.shape[0] != int(self.dataset.spec.obs_vec_dim):
                return False
            if obs_std.shape[0] != int(self.dataset.spec.obs_vec_dim):
                return False
            obs_std = np.maximum(obs_std, float(self.cfg.obs_min_std))
            self.obs_mean = torch.from_numpy(obs_mean).to(self.device)
            self.obs_std = torch.from_numpy(obs_std).to(self.device)

            if self.dataset.spec.visual_shape is not None:
                visual_mean = np.asarray(data["visual_mean"], dtype=np.float32).reshape(-1)
                visual_std = np.asarray(data["visual_std"], dtype=np.float32).reshape(-1)
                c = int(self.dataset.spec.visual_shape[2])
                if visual_mean.shape[0] != c or visual_std.shape[0] != c:
                    return False
                visual_std = np.maximum(visual_std, float(self.cfg.visual_min_std))
                self.visual_mean = torch.from_numpy(visual_mean).to(self.device)
                self.visual_std = torch.from_numpy(visual_std).to(self.device)

            if self.verbose:
                print(f"[init] loaded normalization stats from {stats_path}")
            return True
        except Exception:
            return False

    def _save_cached_stats(self) -> None:
        stats_path = os.path.join(self.dataset.root_dir, "stats.npz")
        try:
            payload = {
                "obs_mean": self.obs_mean.detach().cpu().numpy().astype(np.float32, copy=False),
                "obs_std": self.obs_std.detach().cpu().numpy().astype(np.float32, copy=False),
                "obs_vec_dim": np.asarray([int(self.dataset.spec.obs_vec_dim)], dtype=np.int32),
            }
            if self.dataset.spec.visual_shape is not None and self.visual_mean is not None and self.visual_std is not None:
                payload["visual_mean"] = self.visual_mean.detach().cpu().numpy().astype(np.float32, copy=False)
                payload["visual_std"] = self.visual_std.detach().cpu().numpy().astype(np.float32, copy=False)
                payload["visual_shape"] = np.asarray(self.dataset.spec.visual_shape, dtype=np.int32)
            np.savez_compressed(stats_path, **payload)
            if self.verbose:
                print(f"[init] saved normalization stats to {stats_path}")
        except Exception:
            return

    def _compute_obs_stats_full(self) -> tuple[torch.Tensor, torch.Tensor]:
        d = int(self.dataset.spec.obs_vec_dim)
        total_paths = len(self.dataset.episode_paths)
        sum_ = np.zeros((d,), dtype=np.float64)
        sum_sq = np.zeros((d,), dtype=np.float64)
        count = 0

        if self.verbose:
            print(f"[init] computing obs stats (scan {total_paths} episodes; no visual decode)")
        t0 = time.time()
        for i, path in enumerate(self.dataset.episode_paths):
            try:
                with np.load(path, allow_pickle=False) as data:
                    obs = np.asarray(data["obs_vec"], dtype=np.float32)
            except Exception:
                continue
            obs = obs.reshape(-1, d).astype(np.float64, copy=False)
            sum_ += obs.sum(axis=0)
            sum_sq += (obs * obs).sum(axis=0)
            count += int(obs.shape[0])
            if self.verbose and (i + 1) % max(1, total_paths // 10) == 0:
                print(f"[init] obs stats progress: {i+1}/{total_paths} episodes")

        if count <= 0:
            raise RuntimeError("No valid obs_vec samples found while computing obs stats")
        mean = sum_ / float(count)
        var = sum_sq / float(count) - mean * mean
        std = np.sqrt(np.maximum(var, 1e-6))
        std = np.maximum(std, float(self.cfg.obs_min_std))
        if self.verbose:
            print(f"[init] obs stats done: samples={count} elapsed={time.time()-t0:.1f}s")
        mean_t = torch.from_numpy(mean.astype(np.float32)).to(self.device)
        std_t = torch.from_numpy(std.astype(np.float32)).to(self.device)
        return mean_t, std_t

    def _compute_visual_stats_fast(self, *, max_episodes: int, frames_per_episode: int) -> tuple[torch.Tensor, torch.Tensor]:
        if self.dataset.spec.visual_shape is None:
            raise ValueError("Dataset has no visual_shape")
        c = int(self.dataset.spec.visual_shape[2])
        max_episodes = int(max_episodes)
        frames_per_episode = int(frames_per_episode)
        if max_episodes <= 0:
            max_episodes = len(self.dataset.episode_paths)
        if frames_per_episode <= 0:
            frames_per_episode = 1

        n_eps_total = len(self.dataset.episode_paths)
        n_eps = min(max_episodes, n_eps_total)
        ep_indices = self.rng.choice(n_eps_total, size=n_eps, replace=False)

        sum_ = np.zeros((c,), dtype=np.float64)
        sum_sq = np.zeros((c,), dtype=np.float64)
        count = 0

        if self.verbose:
            print(
                f"[init] computing visual stats (episodes={n_eps}/{n_eps_total}, frames_per_episode={frames_per_episode})"
            )
        t0 = time.time()
        for i, ep_idx in enumerate(ep_indices):
            path = self.dataset.episode_paths[int(ep_idx)]
            try:
                with np.load(path, allow_pickle=False) as data:
                    if "visual" not in data.files:
                        continue
                    visual = np.asarray(data["visual"], dtype=np.float32)
            except Exception:
                continue

            visual = np.clip(visual, -10.0, 10.0)
            T = int(visual.shape[0])
            if T <= 0:
                continue
            k = min(frames_per_episode, T)
            if k == T:
                sample = visual
            else:
                frame_idx = self.rng.choice(T, size=k, replace=False)
                sample = visual[frame_idx]

            flat = sample.reshape(-1, c).astype(np.float64, copy=False)
            sum_ += flat.sum(axis=0)
            sum_sq += (flat * flat).sum(axis=0)
            count += int(flat.shape[0])

            if self.verbose and (i + 1) % max(1, n_eps // 4) == 0:
                print(f"[init] visual stats progress: {i+1}/{n_eps} episodes, samples={count}")

        if count <= 0:
            raise RuntimeError("No valid visual samples found while computing visual stats")

        mean = sum_ / float(count)
        var = sum_sq / float(count) - mean * mean
        std = np.sqrt(np.maximum(var, 1e-6))
        std = np.maximum(std, float(self.cfg.visual_min_std))
        if self.verbose:
            print(f"[init] visual stats done: samples={count} elapsed={time.time()-t0:.1f}s")
        mean_t = torch.from_numpy(mean.astype(np.float32)).to(self.device)
        std_t = torch.from_numpy(std.astype(np.float32)).to(self.device)
        return mean_t, std_t

    def _norm_obs(self, obs_vec: torch.Tensor) -> torch.Tensor:
        x = (obs_vec - self.obs_mean) / self.obs_std
        clip = self.cfg.obs_norm_clip
        if clip is not None:
            x = torch.clamp(x, -float(clip), float(clip))
        return x

    def _norm_visual(self, visual: torch.Tensor) -> torch.Tensor:
        if self.visual_mean is None or self.visual_std is None:
            return visual
        mean = self.visual_mean.view(1, 1, 1, 1, -1)
        std = self.visual_std.view(1, 1, 1, 1, -1)
        x = (visual - mean) / std
        clip = self.cfg.visual_norm_clip
        if clip is not None:
            x = torch.clamp(x, -float(clip), float(clip))
        return x

    def train_world_model(self) -> dict[str, float]:
        batch_np = self.dataset.sample_batch(self.cfg.batch_size, self.cfg.seq_len, self.rng)
        batch = self._to_torch(batch_np)
        obs_vec = batch["obs_vec"]  # (B, L+1, D)
        visual = batch.get("visual", None)  # (B, L+1, H, W, C) or None
        actions = batch["actions"]  # (B, L, A)
        rewards = batch["rewards"]  # (B, L)
        dones = batch["dones"]  # (B, L) float {0,1}

        B, Lp1, D = obs_vec.shape
        L = Lp1 - 1

        obs_vec = obs_vec.float()
        actions = actions.float()
        rewards = rewards.float()
        dones = dones.float()

        obs_vec = self._norm_obs(obs_vec)
        if visual is not None:
            visual = visual.float()
            visual = torch.clamp(visual, -10.0, 10.0)
            visual = self._norm_visual(visual)

        # Encode all observations.
        obs_flat = obs_vec.reshape(B * (L + 1), D)
        if visual is not None:
            vis_flat = visual.reshape(B * (L + 1), -1)
            embeds = self.wm.encoder(obs_flat, vis_flat).reshape(B, L + 1, -1)
        else:
            embeds = self.wm.encoder(obs_flat).reshape(B, L + 1, -1)

        # Initialize state from the first observation.
        state, (post_mean0, post_std0) = self.wm.rssm.observe_init(embeds[:, 0])
        states = [state]

        kl_terms = []
        for t in range(L):
            state, (prior_mean, prior_std), (post_mean, post_std) = self.wm.rssm.obs_step(state, actions[:, t], embeds[:, t + 1])
            states.append(state)
            kl_terms.append(kl_divergence(post_mean, post_std, prior_mean, prior_std))

        # Stack features for prediction (use states[1:] aligned to transitions).
        feats = torch.stack([self.wm.feat(s) for s in states[1:]], dim=1)  # (B, L, F)
        pred_obs = self.wm.decoder(feats.reshape(B * L, -1)).reshape(B, L, D)
        pred_visual = None
        if visual is not None and self.wm.visual_decoder is not None:
            pred_visual = self.wm.visual_decoder(feats.reshape(B * L, -1)).reshape(B, L, -1)
        pred_rew = self.wm.reward(feats.reshape(B * L, -1)).reshape(B, L)
        pred_cont_logits = self.wm.cont(feats.reshape(B * L, -1)).reshape(B, L)

        # Losses (reward uses symlog for stability).
        obs_loss = F.mse_loss(pred_obs, obs_vec[:, 1:], reduction="mean")
        visual_loss = torch.tensor(0.0, device=self.device)
        if pred_visual is not None and visual is not None:
            target_vis = visual[:, 1:].reshape(B, L, -1)
            visual_loss = F.mse_loss(pred_visual, target_vis, reduction="mean")
        rew_loss = F.mse_loss(pred_rew, symlog(rewards), reduction="mean")
        cont_targets = 1.0 - dones
        cont_loss = F.binary_cross_entropy_with_logits(pred_cont_logits, cont_targets, reduction="mean")

        kl = torch.stack(kl_terms, dim=1)  # (B, L)
        free = float(self.cfg.free_nats)
        kl_loss = torch.mean(torch.clamp(kl - free, min=0.0))

        loss = (
            self.cfg.obs_scale * obs_loss
            + self.cfg.visual_scale * visual_loss
            + self.cfg.reward_scale * rew_loss
            + self.cfg.cont_scale * cont_loss
            + self.cfg.kl_scale * kl_loss
        )

        self.opt_wm.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.wm.parameters(), self.cfg.grad_clip)
        self.opt_wm.step()

        return {
            "wm/total": float(loss.detach().cpu().item()),
            "wm/obs": float(obs_loss.detach().cpu().item()),
            "wm/visual": float(visual_loss.detach().cpu().item()),
            "wm/reward": float(rew_loss.detach().cpu().item()),
            "wm/cont": float(cont_loss.detach().cpu().item()),
            "wm/kl": float(kl_loss.detach().cpu().item()),
        }

    @torch.no_grad()
    def _infer_state_from_batch(self, obs_vec: torch.Tensor, actions: torch.Tensor, visual: torch.Tensor | None = None) -> RSSMState:
        B, Lp1, D = obs_vec.shape
        L = Lp1 - 1
        obs_vec = self._norm_obs(obs_vec)
        obs_flat = obs_vec.reshape(B * (L + 1), D)
        if visual is not None:
            visual = visual.float()
            visual = torch.clamp(visual, -10.0, 10.0)
            visual = self._norm_visual(visual)
            vis_flat = visual.reshape(B * (L + 1), -1)
            embeds = self.wm.encoder(obs_flat, vis_flat).reshape(B, L + 1, -1)
        else:
            embeds = self.wm.encoder(obs_flat).reshape(B, L + 1, -1)
        state, _ = self.wm.rssm.observe_init(embeds[:, 0])
        for t in range(L):
            state, _, _ = self.wm.rssm.obs_step(state, actions[:, t], embeds[:, t + 1])
        return state

    def _imagine(
        self, start: RSSMState, horizon: int, *, grad: bool
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Returns:
          feats:    (H, B, F) latent features at each step (post-transition)
          rewards:  (H, B) predicted rewards (original scale)
          discount: (H, B) discount factors (gamma * continue_prob)
          logp:     (H, B) approximate action log-prob (pre-tanh Gaussian)
        """
        state = RSSMState(deter=start.deter, stoch=start.stoch)
        feats = []
        rewards = []
        discounts = []
        logps = []

        for _ in range(int(horizon)):
            feat = self.wm.feat(state)
            actor_input = str(getattr(self.cfg, "actor_input", "rssm"))
            if actor_input == "rssm":
                act_in = feat
            elif actor_input == "embed":
                # Reactive actor: derive an "imagined observation" from the latent and re-encode it.
                # This keeps the actor input consistent with real rollouts (encoder(obs)), while still
                # allowing Dreamer-style imagined rollouts in RSSM space.
                # NOTE: The world model is trained in *normalized* observation space:
                # - obs_vec is normalized (and optionally clipped) before encoding
                # - decoder predicts that normalized obs_vec directly
                # So we must NOT apply _norm_obs() again here (would double-normalize).
                pred_obs_norm = self.wm.decoder(feat)  # (B, obs_vec_dim) normalized
                clip = self.cfg.obs_norm_clip
                if clip is not None:
                    pred_obs_norm = torch.clamp(pred_obs_norm, -float(clip), float(clip))
                if self.dataset.spec.visual_shape is None:
                    act_in = self.wm.encoder(pred_obs_norm)
                else:
                    if self.wm.visual_decoder is None:
                        raise RuntimeError("actor_input='embed' with visual requires a visual_decoder in the world model")
                    h, w, c = (int(self.dataset.spec.visual_shape[0]), int(self.dataset.spec.visual_shape[1]), int(self.dataset.spec.visual_shape[2]))
                    pred_vis_norm = self.wm.visual_decoder(feat).reshape(feat.shape[0], h, w, c)  # normalized
                    vclip = self.cfg.visual_norm_clip
                    if vclip is not None:
                        pred_vis_norm = torch.clamp(pred_vis_norm, -float(vclip), float(vclip))
                    act_in = self.wm.encoder(pred_obs_norm, pred_vis_norm.reshape(feat.shape[0], -1))
            else:
                raise ValueError(f"unknown actor_input: {actor_input!r}")

            if grad:
                action, logp = self.actor.sample(act_in)
            else:
                with torch.no_grad():
                    action, logp = self.actor.sample(act_in)

            state, _ = self.wm.rssm.imagine_step(state, action)
            next_feat = self.wm.feat(state)
            rew_symlog = self.wm.reward(next_feat)
            clip = self.cfg.reward_symlog_clip
            if clip is not None:
                rew_symlog = torch.clamp(rew_symlog, -float(clip), float(clip))
            rew = symexp(rew_symlog)
            cont = torch.sigmoid(self.wm.cont(next_feat))

            feats.append(next_feat)
            rewards.append(rew)
            discounts.append(cont * float(self.cfg.gamma))
            logps.append(logp)

        return (
            torch.stack(feats, dim=0),
            torch.stack(rewards, dim=0),
            torch.stack(discounts, dim=0),
            torch.stack(logps, dim=0),
        )

    def train_actor_value(self) -> dict[str, float]:
        actor_input = str(getattr(self.cfg, "actor_input", "rssm"))
        if actor_input in (
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
            raise NotImplementedError(
                f"actor_input={actor_input!r} is only supported with BC (policy_mode=bc)."
            )
        batch_np = self.dataset.sample_batch(self.cfg.batch_size, self.cfg.seq_len, self.rng)
        batch = self._to_torch(batch_np)
        obs_vec = batch["obs_vec"].float()
        visual = batch.get("visual", None)
        actions = batch["actions"].float()
        targets = batch.get("expert_actions", actions).float()

        bc_scale = float(self.cfg.bc_scale)
        bc_loss = torch.tensor(0.0, device=self.device)
        if bc_scale > 0.0:
            B, L, A = actions.shape
            with torch.no_grad():
                obs_norm = self._norm_obs(obs_vec)
                obs_flat = obs_norm.reshape(B * (L + 1), -1)
                if visual is not None:
                    visual_norm = visual.float()
                    visual_norm = torch.clamp(visual_norm, -10.0, 10.0)
                    visual_norm = self._norm_visual(visual_norm)
                    vis_flat = visual_norm.reshape(B * (L + 1), -1)
                    embeds = self.wm.encoder(obs_flat, vis_flat).reshape(B, L + 1, -1)
                else:
                    embeds = self.wm.encoder(obs_flat).reshape(B, L + 1, -1)

                if actor_input == "rssm":
                    deterministic_state = bool(getattr(self.cfg, "bc_deterministic_state", False))
                    state, _ = self.wm.rssm.observe_init(embeds[:, 0], deterministic=deterministic_state)
                    states = [state]
                    for t in range(L):
                        state, _, _ = self.wm.rssm.obs_step(
                            state, actions[:, t], embeds[:, t + 1], deterministic=deterministic_state
                        )
                        states.append(state)
                    feats_pre = torch.stack([self.wm.feat(s) for s in states[:-1]], dim=1)  # (B, L, F)
                    actor_feats = feats_pre
                elif actor_input == "embed":
                    actor_feats = embeds[:, :L]  # (B, L, E)
                else:
                    raise ValueError(f"unknown actor_input: {actor_input!r}")

            mean, _std = self.actor(actor_feats.reshape(B * L, -1))
            pred = torch.tanh(mean).reshape(B, L, A)
            rudder_w = float(getattr(self.cfg, "bc_rudder_mag_weight", 0.0))
            rudder_base = float(getattr(self.cfg, "bc_rudder_weight", 1.0))
            if (rudder_w > 0.0 or rudder_base != 1.0) and A > 2:
                err = (pred - targets) ** 2
                scale = rudder_base * (1.0 + rudder_w * torch.abs(targets[:, :, 2]))
                err[:, :, 2] = err[:, :, 2] * scale
                bc_loss = err.mean()
            else:
                bc_loss = F.mse_loss(pred, targets, reduction="mean")

        # Start imagination from posterior state at end of batch sequence.
        with torch.no_grad():
            start_state = self._infer_state_from_batch(obs_vec, actions, visual=visual)

        H = int(self.cfg.horizon)

        # --- Value update: targets computed under no_grad (world model and actor are frozen here) ---
        with torch.no_grad():
            feats_ng, rewards_ng, discounts_ng, _logps_ng = self._imagine(start_state, H, grad=False)
            feat0_ng = self.wm.feat(start_state)
            values_next_ng = self.value(feats_ng).detach()  # (H, B) = V(s_{t+1})
            values_boot = torch.cat([torch.zeros_like(values_next_ng[:1]), values_next_ng], dim=0)  # (H+1, B)
            returns_tgt = lambda_return(rewards_ng, values_boot, discounts_ng, self.cfg.lambda_)  # returns for s_t

        feats_states = torch.cat([feat0_ng.unsqueeze(0), feats_ng[:-1]], dim=0)  # (H, B, F) = s_t
        value_pred = self.value(feats_states)  # (H, B)
        # Critic stability: optimize a robust loss in symlog-space (Dreamer-style),
        # but keep raw-scale diagnostics for interpretability.
        value_loss_raw = F.mse_loss(value_pred, returns_tgt, reduction="mean")
        value_loss = F.smooth_l1_loss(symlog(value_pred), symlog(returns_tgt), reduction="mean")
        self.opt_value.zero_grad(set_to_none=True)
        value_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.value.parameters(), self.cfg.grad_clip)
        self.opt_value.step()
        returns_tgt_mean = returns_tgt.mean()
        returns_tgt_std = returns_tgt.std()
        value_pred_mean = value_pred.mean()
        value_pred_std = value_pred.std()

        # --- Actor update: gradients flow through actor + world model, but not through value network ---
        feats_g, rewards_g, discounts_g, logps_g = self._imagine(start_state, H, grad=True)
        with torch.no_grad():
            values_next_g = self.value(feats_g)  # (H, B)
        values_boot_g = torch.cat([torch.zeros_like(values_next_g[:1]), values_next_g], dim=0)  # (H+1, B)
        returns_g = lambda_return(rewards_g, values_boot_g, discounts_g, self.cfg.lambda_)

        entropy = (-logps_g).mean()
        returns_mean = returns_g.mean()
        returns_std = returns_g.std()
        actor_loss = -(returns_mean + float(self.cfg.entropy_scale) * entropy) + bc_scale * bc_loss
        self.opt_actor.zero_grad(set_to_none=True)
        actor_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.actor.parameters(), self.cfg.grad_clip)
        self.opt_actor.step()

        return {
            "ac/actor": float(actor_loss.detach().cpu().item()),
            "ac/value": float(value_loss.detach().cpu().item()),
            "ac/value_raw_mse": float(value_loss_raw.detach().cpu().item()),
            "ac/entropy": float(entropy.detach().cpu().item()),
            "ac/return_mean": float(returns_mean.detach().cpu().item()),
            "ac/return_std": float(returns_std.detach().cpu().item()),
            "ac/target_mean": float(returns_tgt_mean.detach().cpu().item()),
            "ac/target_std": float(returns_tgt_std.detach().cpu().item()),
            "ac/value_pred_mean": float(value_pred_mean.detach().cpu().item()),
            "ac/value_pred_std": float(value_pred_std.detach().cpu().item()),
            "ac/bc": float(bc_loss.detach().cpu().item()),
        }

    def train_actor_bc(self) -> dict[str, float]:
        """
        Pure behavior cloning update for the actor.

        This is used as a stable baseline to avoid offline world-model exploitation:
        the learned policy stays close to the demonstration data while the world model
        can still be trained for later RL fine-tuning.
        """
        actor_input = str(getattr(self.cfg, "actor_input", "rssm"))
        is_recurrent = actor_input in (
            "embed_gru",
            "embed_sincos_gru",
            "embed_sincos_track_gru",
            "obs_gru",
            "obs_sincos_gru",
            "obs_sincos_track_gru",
            "obs_sincos_track_vis_gru",
        )
        burn_in = int(getattr(self.cfg, "bc_gru_burn_in", 0) or 0)
        burn_in = max(0, burn_in)
        # Default behavior (burn_in=0): align sequences to episode starts so the hidden state
        # matches deployment (h=0 at reset).
        #
        # When burn_in>0: sample random subsequences and ignore the first `burn_in` steps in the loss.
        # This allows training on later parts of long episodes (crucial for stable flight / cruise).
        start_at_zero = bool(is_recurrent) and burn_in <= 0
        seq_len = int(self.cfg.seq_len) + (burn_in if is_recurrent else 0)
        start_at_zero_prob = None
        if not bool(is_recurrent):
            try:
                p0 = float(getattr(self.cfg, "bc_start_at_zero_prob", 0.0))
            except Exception:
                p0 = 0.0
            p0 = float(np.clip(p0, 0.0, 1.0))
            if p0 > 0.0:
                start_at_zero_prob = p0
        batch_np = self.dataset.sample_batch(
            self.cfg.batch_size,
            seq_len,
            self.rng,
            start_at_zero=start_at_zero,
            start_at_zero_prob=start_at_zero_prob,
        )
        batch = self._to_torch(batch_np)
        obs_vec = batch["obs_vec"].float()
        visual = batch.get("visual", None)
        actions = batch["actions"].float()
        targets = batch.get("expert_actions", actions).float()
        dones = batch.get("dones", None)
        if dones is None:
            # Back-compat: treat all steps as valid.
            dones = torch.zeros((actions.shape[0], actions.shape[1]), device=self.device, dtype=torch.float32)
        dones = dones.float()

        B, L, A = actions.shape
        teacher_prob = float(getattr(self.cfg, "bc_teacher_prob", 1.0))
        teacher_prob = float(np.clip(teacher_prob, 0.0, 1.0))

        # Mask out padded timesteps after episode termination. This is critical when seq_len is large
        # and the dataset pads short episodes: otherwise the loss is dominated by post-terminal zeros,
        # and the policy can ignore the early takeoff dynamics that matter for runway tracking.
        #
        # Keep the terminal transition itself (first done=True) included; mask only after it.
        done_cum = torch.cumsum((dones > 0.5).float(), dim=1)  # (B, L) in {0,1,2,...}
        valid = (done_cum <= 1.0).float()  # (B, L)
        weights = valid
        if is_recurrent and burn_in > 0:
            # Mask out burn-in steps from the loss while still allowing the GRU
            # to update its hidden state based on preceding context.
            weights[:, :burn_in] = 0.0

        # Optional step weights: focus BC capacity on ground-roll directional control.
        # Note: obs_vec includes mission/proprio; the radar alt index (3) lives in the instruments prefix.
        ground_thr = float(getattr(self.cfg, "bc_ground_alt_threshold", 5.0))
        ground_w = float(getattr(self.cfg, "bc_ground_weight", 1.0))
        airborne_w = float(getattr(self.cfg, "bc_airborne_weight", 1.0))
        if (ground_w != 1.0 or airborne_w != 1.0) and obs_vec.shape[-1] > 3:
            alt_radar = obs_vec[:, :L, 3]
            on_ground = (alt_radar < ground_thr).float()
            step_w = on_ground * ground_w + (1.0 - on_ground) * airborne_w
            weights = weights * step_w

        # Optional weight by ILS localizer deviation magnitude (stronger gradients when far off-center).
        # Current obs layout: instruments (38) + ILS(4) + mission(4) => loc_dev at index 39.
        loc_w = float(getattr(self.cfg, "bc_loc_weight", 0.0))
        if loc_w > 0.0 and obs_vec.shape[-1] > 39:
            loc_dev = torch.abs(obs_vec[:, :L, 39])
            step_w = 1.0 + loc_w * loc_dev
            weights = weights * step_w

        # Optional weight by heading command tracking error (capture phases / recovery steps).
        # obs layout: instruments (42) + mission(4) => heading at 9, ground_track at 30,
        # target_heading at 43, command_code at 42.
        #
        # For waypoint navigation (command_code==3), the mission target_heading is a ground-referenced
        # track bug (LNAV). In that case we weight by *track* error (target_track - ground_track),
        # not air-referenced heading error (which would penalize correct crab in crosswind).
        hdg_w = float(getattr(self.cfg, "bc_hdg_weight", 0.0))
        if hdg_w > 0.0 and obs_vec.shape[-1] > 43:
            heading = obs_vec[:, :L, 9]
            ground_track = obs_vec[:, :L, 30] if obs_vec.shape[-1] > 30 else heading
            tgt_hdg = obs_vec[:, :L, 43]
            diff_heading = torch.remainder((tgt_hdg - heading) + 180.0, 360.0) - 180.0
            if obs_vec.shape[-1] > 42:
                cmd = obs_vec[:, :L, 42]
                is_wp = (cmd > 2.5) & (cmd < 3.5)
                diff_track = torch.remainder((tgt_hdg - ground_track) + 180.0, 360.0) - 180.0
                diff = torch.where(is_wp, diff_track, diff_heading)
            else:
                diff = diff_heading
            diff = torch.abs(diff)
            norm = float(getattr(self.cfg, "bc_hdg_norm_deg", 30.0))
            if norm <= 1.0e-6:
                norm = 30.0
            step_w = 1.0 + hdg_w * (diff / norm)
            weights = weights * step_w

        weights_a = weights.unsqueeze(-1)  # (B, L, 1)

        pitch_w = float(getattr(self.cfg, "bc_pitch_mag_weight", 0.0))
        pitch_base = float(getattr(self.cfg, "bc_pitch_weight", 1.0))
        roll_w = float(getattr(self.cfg, "bc_roll_mag_weight", 0.0))
        roll_base = float(getattr(self.cfg, "bc_roll_weight", 1.0))
        thr_w = float(getattr(self.cfg, "bc_throttle_mag_weight", 0.0))
        thr_base = float(getattr(self.cfg, "bc_throttle_weight", 1.0))
        # Normalize observations once. For embed/rssm we will also compute embeddings
        # (no gradients through the world model for BC).
        obs_norm = self._norm_obs(obs_vec)
        embeds = None
        vis_embeds = None
        if actor_input in (
            "embed",
            "embed_gru",
            "embed_sincos",
            "embed_sincos_gru",
            "embed_sincos_track",
            "embed_sincos_track_gru",
            "rssm",
        ):
            with torch.no_grad():
                obs_flat = obs_norm.reshape(B * (L + 1), -1)
                if visual is not None:
                    visual_norm = visual.float()
                    visual_norm = torch.clamp(visual_norm, -10.0, 10.0)
                    visual_norm = self._norm_visual(visual_norm)
                    vis_flat = visual_norm.reshape(B * (L + 1), -1)
                    embeds = self.wm.encoder(obs_flat, vis_flat).reshape(B, L + 1, -1)
                else:
                    embeds = self.wm.encoder(obs_flat).reshape(B, L + 1, -1)
        if actor_input in ("obs_sincos_track_vis", "obs_sincos_track_vis_gru"):
            if visual is None or self.wm.encoder.visual is None:
                raise ValueError("actor_input='obs_sincos_track_vis*' requires visual observations in the dataset")
            with torch.no_grad():
                visual_norm = visual.float()
                visual_norm = torch.clamp(visual_norm, -10.0, 10.0)
                visual_norm = self._norm_visual(visual_norm)
                vis_flat = visual_norm.reshape(B * (L + 1), -1)
                vis_embeds = self.wm.encoder.visual(vis_flat).reshape(B, L + 1, -1)

        if actor_input == "obs":
            feats = obs_norm[:, :L]  # (B, L, D)
            mean, _std = self.actor(feats.reshape(B * L, -1))
            pred = torch.tanh(mean).reshape(B, L, A)
            rudder_w = float(getattr(self.cfg, "bc_rudder_mag_weight", 0.0))
            rudder_base = float(getattr(self.cfg, "bc_rudder_weight", 1.0))
            err = (pred - targets) ** 2
            if (pitch_w > 0.0 or pitch_base != 1.0) and A > 0:
                scale = pitch_base * (1.0 + pitch_w * torch.abs(targets[:, :, 0]))
                err[:, :, 0] = err[:, :, 0] * scale
            if (roll_w > 0.0 or roll_base != 1.0) and A > 1:
                scale = roll_base * (1.0 + roll_w * torch.abs(targets[:, :, 1]))
                err[:, :, 1] = err[:, :, 1] * scale
            if (thr_w > 0.0 or thr_base != 1.0) and A > 3:
                scale = thr_base * (1.0 + thr_w * torch.abs(targets[:, :, 3]))
                err[:, :, 3] = err[:, :, 3] * scale
            if (rudder_w > 0.0 or rudder_base != 1.0) and A > 2:
                scale = rudder_base * (1.0 + rudder_w * torch.abs(targets[:, :, 2]))
                err[:, :, 2] = err[:, :, 2] * scale
            err = err * weights_a
            denom = float(weights.sum().clamp_min(1.0).item()) * float(A)
            bc_loss = err.sum() / denom
        elif actor_input == "obs_gru":
            feats = obs_norm[:, :L]  # (B, L, D)
            mean, _std, _hN = self.actor(feats, h0=None)  # type: ignore[misc]
            pred = torch.tanh(mean)
            rudder_w = float(getattr(self.cfg, "bc_rudder_mag_weight", 0.0))
            rudder_base = float(getattr(self.cfg, "bc_rudder_weight", 1.0))
            err = (pred - targets) ** 2
            if (pitch_w > 0.0 or pitch_base != 1.0) and A > 0:
                scale = pitch_base * (1.0 + pitch_w * torch.abs(targets[:, :, 0]))
                err[:, :, 0] = err[:, :, 0] * scale
            if (roll_w > 0.0 or roll_base != 1.0) and A > 1:
                scale = roll_base * (1.0 + roll_w * torch.abs(targets[:, :, 1]))
                err[:, :, 1] = err[:, :, 1] * scale
            if (thr_w > 0.0 or thr_base != 1.0) and A > 3:
                scale = thr_base * (1.0 + thr_w * torch.abs(targets[:, :, 3]))
                err[:, :, 3] = err[:, :, 3] * scale
            if (rudder_w > 0.0 or rudder_base != 1.0) and A > 2:
                scale = rudder_base * (1.0 + rudder_w * torch.abs(targets[:, :, 2]))
                err[:, :, 2] = err[:, :, 2] * scale
            err = err * weights_a
            denom = float(weights.sum().clamp_min(1.0).item()) * float(A)
            bc_loss = err.sum() / denom
        elif actor_input == "obs_sincos":
            feats = append_angle_sincos_features(
                obs_raw_deg=obs_vec[:, :L],
                obs_norm=obs_norm[:, :L],
                angle_deg_indices=self.angle_deg_indices,
            )
            mean, _std = self.actor(feats.reshape(B * L, -1))
            pred = torch.tanh(mean).reshape(B, L, A)
            rudder_w = float(getattr(self.cfg, "bc_rudder_mag_weight", 0.0))
            rudder_base = float(getattr(self.cfg, "bc_rudder_weight", 1.0))
            err = (pred - targets) ** 2
            if (pitch_w > 0.0 or pitch_base != 1.0) and A > 0:
                scale = pitch_base * (1.0 + pitch_w * torch.abs(targets[:, :, 0]))
                err[:, :, 0] = err[:, :, 0] * scale
            if (roll_w > 0.0 or roll_base != 1.0) and A > 1:
                scale = roll_base * (1.0 + roll_w * torch.abs(targets[:, :, 1]))
                err[:, :, 1] = err[:, :, 1] * scale
            if (thr_w > 0.0 or thr_base != 1.0) and A > 3:
                scale = thr_base * (1.0 + thr_w * torch.abs(targets[:, :, 3]))
                err[:, :, 3] = err[:, :, 3] * scale
            if (rudder_w > 0.0 or rudder_base != 1.0) and A > 2:
                scale = rudder_base * (1.0 + rudder_w * torch.abs(targets[:, :, 2]))
                err[:, :, 2] = err[:, :, 2] * scale
            err = err * weights_a
            denom = float(weights.sum().clamp_min(1.0).item()) * float(A)
            bc_loss = err.sum() / denom
        elif actor_input == "obs_sincos_gru":
            feats = append_angle_sincos_features(
                obs_raw_deg=obs_vec[:, :L],
                obs_norm=obs_norm[:, :L],
                angle_deg_indices=self.angle_deg_indices,
            )
            mean, _std, _hN = self.actor(feats, h0=None)  # type: ignore[misc]
            pred = torch.tanh(mean)
            rudder_w = float(getattr(self.cfg, "bc_rudder_mag_weight", 0.0))
            rudder_base = float(getattr(self.cfg, "bc_rudder_weight", 1.0))
            err = (pred - targets) ** 2
            if (pitch_w > 0.0 or pitch_base != 1.0) and A > 0:
                scale = pitch_base * (1.0 + pitch_w * torch.abs(targets[:, :, 0]))
                err[:, :, 0] = err[:, :, 0] * scale
            if (roll_w > 0.0 or roll_base != 1.0) and A > 1:
                scale = roll_base * (1.0 + roll_w * torch.abs(targets[:, :, 1]))
                err[:, :, 1] = err[:, :, 1] * scale
            if (thr_w > 0.0 or thr_base != 1.0) and A > 3:
                scale = thr_base * (1.0 + thr_w * torch.abs(targets[:, :, 3]))
                err[:, :, 3] = err[:, :, 3] * scale
            if (rudder_w > 0.0 or rudder_base != 1.0) and A > 2:
                scale = rudder_base * (1.0 + rudder_w * torch.abs(targets[:, :, 2]))
                err[:, :, 2] = err[:, :, 2] * scale
            err = err * weights_a
            denom = float(weights.sum().clamp_min(1.0).item()) * float(A)
            bc_loss = err.sum() / denom
        elif actor_input == "obs_sincos_track":
            feats = append_angle_sincos_features(
                obs_raw_deg=obs_vec[:, :L],
                obs_norm=obs_norm[:, :L],
                angle_deg_indices=self.angle_deg_indices,
            )
            track = nav_tracking_features(obs_vec[:, :L])
            feats = torch.cat([feats, track], dim=-1)
            mean, _std = self.actor(feats.reshape(B * L, -1))
            pred = torch.tanh(mean).reshape(B, L, A)
            rudder_w = float(getattr(self.cfg, "bc_rudder_mag_weight", 0.0))
            rudder_base = float(getattr(self.cfg, "bc_rudder_weight", 1.0))
            err = (pred - targets) ** 2
            if (pitch_w > 0.0 or pitch_base != 1.0) and A > 0:
                scale = pitch_base * (1.0 + pitch_w * torch.abs(targets[:, :, 0]))
                err[:, :, 0] = err[:, :, 0] * scale
            if (roll_w > 0.0 or roll_base != 1.0) and A > 1:
                scale = roll_base * (1.0 + roll_w * torch.abs(targets[:, :, 1]))
                err[:, :, 1] = err[:, :, 1] * scale
            if (thr_w > 0.0 or thr_base != 1.0) and A > 3:
                scale = thr_base * (1.0 + thr_w * torch.abs(targets[:, :, 3]))
                err[:, :, 3] = err[:, :, 3] * scale
            if (rudder_w > 0.0 or rudder_base != 1.0) and A > 2:
                scale = rudder_base * (1.0 + rudder_w * torch.abs(targets[:, :, 2]))
                err[:, :, 2] = err[:, :, 2] * scale
            err = err * weights_a
            denom = float(weights.sum().clamp_min(1.0).item()) * float(A)
            bc_loss = err.sum() / denom
        elif actor_input == "obs_sincos_track_gru":
            feats = append_angle_sincos_features(
                obs_raw_deg=obs_vec[:, :L],
                obs_norm=obs_norm[:, :L],
                angle_deg_indices=self.angle_deg_indices,
            )
            track = nav_tracking_features(obs_vec[:, :L])
            feats = torch.cat([feats, track], dim=-1)
            mean, _std, _hN = self.actor(feats, h0=None)  # type: ignore[misc]
            pred = torch.tanh(mean)
            rudder_w = float(getattr(self.cfg, "bc_rudder_mag_weight", 0.0))
            rudder_base = float(getattr(self.cfg, "bc_rudder_weight", 1.0))
            err = (pred - targets) ** 2
            if (pitch_w > 0.0 or pitch_base != 1.0) and A > 0:
                scale = pitch_base * (1.0 + pitch_w * torch.abs(targets[:, :, 0]))
                err[:, :, 0] = err[:, :, 0] * scale
            if (roll_w > 0.0 or roll_base != 1.0) and A > 1:
                scale = roll_base * (1.0 + roll_w * torch.abs(targets[:, :, 1]))
                err[:, :, 1] = err[:, :, 1] * scale
            if (thr_w > 0.0 or thr_base != 1.0) and A > 3:
                scale = thr_base * (1.0 + thr_w * torch.abs(targets[:, :, 3]))
                err[:, :, 3] = err[:, :, 3] * scale
            if (rudder_w > 0.0 or rudder_base != 1.0) and A > 2:
                scale = rudder_base * (1.0 + rudder_w * torch.abs(targets[:, :, 2]))
                err[:, :, 2] = err[:, :, 2] * scale
            err = err * weights_a
            denom = float(weights.sum().clamp_min(1.0).item()) * float(A)
            bc_loss = err.sum() / denom
        elif actor_input == "obs_sincos_track_vis":
            if vis_embeds is None:
                raise RuntimeError("vis_embeds not initialized for obs_sincos_track_vis")
            feats = append_angle_sincos_features(
                obs_raw_deg=obs_vec[:, :L],
                obs_norm=obs_norm[:, :L],
                angle_deg_indices=self.angle_deg_indices,
            )
            track = nav_tracking_features(obs_vec[:, :L])
            feats = torch.cat([feats, track, vis_embeds[:, :L]], dim=-1)
            mean, _std = self.actor(feats.reshape(B * L, -1))
            pred = torch.tanh(mean).reshape(B, L, A)
            rudder_w = float(getattr(self.cfg, "bc_rudder_mag_weight", 0.0))
            rudder_base = float(getattr(self.cfg, "bc_rudder_weight", 1.0))
            err = (pred - targets) ** 2
            if (pitch_w > 0.0 or pitch_base != 1.0) and A > 0:
                scale = pitch_base * (1.0 + pitch_w * torch.abs(targets[:, :, 0]))
                err[:, :, 0] = err[:, :, 0] * scale
            if (roll_w > 0.0 or roll_base != 1.0) and A > 1:
                scale = roll_base * (1.0 + roll_w * torch.abs(targets[:, :, 1]))
                err[:, :, 1] = err[:, :, 1] * scale
            if (thr_w > 0.0 or thr_base != 1.0) and A > 3:
                scale = thr_base * (1.0 + thr_w * torch.abs(targets[:, :, 3]))
                err[:, :, 3] = err[:, :, 3] * scale
            if (rudder_w > 0.0 or rudder_base != 1.0) and A > 2:
                scale = rudder_base * (1.0 + rudder_w * torch.abs(targets[:, :, 2]))
                err[:, :, 2] = err[:, :, 2] * scale
            err = err * weights_a
            denom = float(weights.sum().clamp_min(1.0).item()) * float(A)
            bc_loss = err.sum() / denom
        elif actor_input == "obs_sincos_track_vis_gru":
            if vis_embeds is None:
                raise RuntimeError("vis_embeds not initialized for obs_sincos_track_vis_gru")
            feats = append_angle_sincos_features(
                obs_raw_deg=obs_vec[:, :L],
                obs_norm=obs_norm[:, :L],
                angle_deg_indices=self.angle_deg_indices,
            )
            track = nav_tracking_features(obs_vec[:, :L])
            feats = torch.cat([feats, track, vis_embeds[:, :L]], dim=-1)
            mean, _std, _hN = self.actor(feats, h0=None)  # type: ignore[misc]
            pred = torch.tanh(mean)
            rudder_w = float(getattr(self.cfg, "bc_rudder_mag_weight", 0.0))
            rudder_base = float(getattr(self.cfg, "bc_rudder_weight", 1.0))
            err = (pred - targets) ** 2
            if (pitch_w > 0.0 or pitch_base != 1.0) and A > 0:
                scale = pitch_base * (1.0 + pitch_w * torch.abs(targets[:, :, 0]))
                err[:, :, 0] = err[:, :, 0] * scale
            if (roll_w > 0.0 or roll_base != 1.0) and A > 1:
                scale = roll_base * (1.0 + roll_w * torch.abs(targets[:, :, 1]))
                err[:, :, 1] = err[:, :, 1] * scale
            if (thr_w > 0.0 or thr_base != 1.0) and A > 3:
                scale = thr_base * (1.0 + thr_w * torch.abs(targets[:, :, 3]))
                err[:, :, 3] = err[:, :, 3] * scale
            if (rudder_w > 0.0 or rudder_base != 1.0) and A > 2:
                scale = rudder_base * (1.0 + rudder_w * torch.abs(targets[:, :, 2]))
                err[:, :, 2] = err[:, :, 2] * scale
            err = err * weights_a
            denom = float(weights.sum().clamp_min(1.0).item()) * float(A)
            bc_loss = err.sum() / denom
        elif actor_input == "embed_sincos":
            assert embeds is not None
            ang = angle_sincos_features(obs_vec[:, :L], angle_deg_indices=self.angle_deg_indices)
            feats = torch.cat([embeds[:, :L], ang], dim=-1)
            mean, _std = self.actor(feats.reshape(B * L, -1))
            pred = torch.tanh(mean).reshape(B, L, A)
            rudder_w = float(getattr(self.cfg, "bc_rudder_mag_weight", 0.0))
            rudder_base = float(getattr(self.cfg, "bc_rudder_weight", 1.0))
            err = (pred - targets) ** 2
            if (pitch_w > 0.0 or pitch_base != 1.0) and A > 0:
                scale = pitch_base * (1.0 + pitch_w * torch.abs(targets[:, :, 0]))
                err[:, :, 0] = err[:, :, 0] * scale
            if (roll_w > 0.0 or roll_base != 1.0) and A > 1:
                scale = roll_base * (1.0 + roll_w * torch.abs(targets[:, :, 1]))
                err[:, :, 1] = err[:, :, 1] * scale
            if (thr_w > 0.0 or thr_base != 1.0) and A > 3:
                scale = thr_base * (1.0 + thr_w * torch.abs(targets[:, :, 3]))
                err[:, :, 3] = err[:, :, 3] * scale
            if (rudder_w > 0.0 or rudder_base != 1.0) and A > 2:
                scale = rudder_base * (1.0 + rudder_w * torch.abs(targets[:, :, 2]))
                err[:, :, 2] = err[:, :, 2] * scale
            err = err * weights_a
            denom = float(weights.sum().clamp_min(1.0).item()) * float(A)
            bc_loss = err.sum() / denom
        elif actor_input == "embed_sincos_track":
            assert embeds is not None
            ang = angle_sincos_features(obs_vec[:, :L], angle_deg_indices=self.angle_deg_indices)
            track = nav_tracking_features(obs_vec[:, :L])
            feats = torch.cat([embeds[:, :L], ang, track], dim=-1)
            mean, _std = self.actor(feats.reshape(B * L, -1))
            pred = torch.tanh(mean).reshape(B, L, A)
            rudder_w = float(getattr(self.cfg, "bc_rudder_mag_weight", 0.0))
            rudder_base = float(getattr(self.cfg, "bc_rudder_weight", 1.0))
            err = (pred - targets) ** 2
            if (pitch_w > 0.0 or pitch_base != 1.0) and A > 0:
                scale = pitch_base * (1.0 + pitch_w * torch.abs(targets[:, :, 0]))
                err[:, :, 0] = err[:, :, 0] * scale
            if (roll_w > 0.0 or roll_base != 1.0) and A > 1:
                scale = roll_base * (1.0 + roll_w * torch.abs(targets[:, :, 1]))
                err[:, :, 1] = err[:, :, 1] * scale
            if (thr_w > 0.0 or thr_base != 1.0) and A > 3:
                scale = thr_base * (1.0 + thr_w * torch.abs(targets[:, :, 3]))
                err[:, :, 3] = err[:, :, 3] * scale
            if (rudder_w > 0.0 or rudder_base != 1.0) and A > 2:
                scale = rudder_base * (1.0 + rudder_w * torch.abs(targets[:, :, 2]))
                err[:, :, 2] = err[:, :, 2] * scale
            err = err * weights_a
            denom = float(weights.sum().clamp_min(1.0).item()) * float(A)
            bc_loss = err.sum() / denom
        elif actor_input == "embed_sincos_gru":
            assert embeds is not None
            ang = angle_sincos_features(obs_vec[:, :L], angle_deg_indices=self.angle_deg_indices)
            feats = torch.cat([embeds[:, :L], ang], dim=-1)
            mean, _std, _hN = self.actor(feats, h0=None)  # type: ignore[misc]
            pred = torch.tanh(mean)
            rudder_w = float(getattr(self.cfg, "bc_rudder_mag_weight", 0.0))
            rudder_base = float(getattr(self.cfg, "bc_rudder_weight", 1.0))
            err = (pred - targets) ** 2
            if (pitch_w > 0.0 or pitch_base != 1.0) and A > 0:
                scale = pitch_base * (1.0 + pitch_w * torch.abs(targets[:, :, 0]))
                err[:, :, 0] = err[:, :, 0] * scale
            if (roll_w > 0.0 or roll_base != 1.0) and A > 1:
                scale = roll_base * (1.0 + roll_w * torch.abs(targets[:, :, 1]))
                err[:, :, 1] = err[:, :, 1] * scale
            if (thr_w > 0.0 or thr_base != 1.0) and A > 3:
                scale = thr_base * (1.0 + thr_w * torch.abs(targets[:, :, 3]))
                err[:, :, 3] = err[:, :, 3] * scale
            if (rudder_w > 0.0 or rudder_base != 1.0) and A > 2:
                scale = rudder_base * (1.0 + rudder_w * torch.abs(targets[:, :, 2]))
                err[:, :, 2] = err[:, :, 2] * scale
            err = err * weights_a
            denom = float(weights.sum().clamp_min(1.0).item()) * float(A)
            bc_loss = err.sum() / denom
        elif actor_input == "embed_sincos_track_gru":
            assert embeds is not None
            ang = angle_sincos_features(obs_vec[:, :L], angle_deg_indices=self.angle_deg_indices)
            track = nav_tracking_features(obs_vec[:, :L])
            feats = torch.cat([embeds[:, :L], ang, track], dim=-1)
            mean, _std, _hN = self.actor(feats, h0=None)  # type: ignore[misc]
            pred = torch.tanh(mean)
            rudder_w = float(getattr(self.cfg, "bc_rudder_mag_weight", 0.0))
            rudder_base = float(getattr(self.cfg, "bc_rudder_weight", 1.0))
            err = (pred - targets) ** 2
            if (pitch_w > 0.0 or pitch_base != 1.0) and A > 0:
                scale = pitch_base * (1.0 + pitch_w * torch.abs(targets[:, :, 0]))
                err[:, :, 0] = err[:, :, 0] * scale
            if (roll_w > 0.0 or roll_base != 1.0) and A > 1:
                scale = roll_base * (1.0 + roll_w * torch.abs(targets[:, :, 1]))
                err[:, :, 1] = err[:, :, 1] * scale
            if (thr_w > 0.0 or thr_base != 1.0) and A > 3:
                scale = thr_base * (1.0 + thr_w * torch.abs(targets[:, :, 3]))
                err[:, :, 3] = err[:, :, 3] * scale
            if (rudder_w > 0.0 or rudder_base != 1.0) and A > 2:
                scale = rudder_base * (1.0 + rudder_w * torch.abs(targets[:, :, 2]))
                err[:, :, 2] = err[:, :, 2] * scale
            err = err * weights_a
            denom = float(weights.sum().clamp_min(1.0).item()) * float(A)
            bc_loss = err.sum() / denom
        elif actor_input == "embed":
            # Reactive BC baseline: predict actions directly from the current observation embedding.
            # This avoids recurrent covariate shift on takeoff tasks (rudder sign flips were caused by RSSM roll-in).
            assert embeds is not None
            feats = embeds[:, :L]  # (B, L, E) aligned with actions[:, t]
            mean, _std = self.actor(feats.reshape(B * L, -1))
            pred = torch.tanh(mean).reshape(B, L, A)
            rudder_w = float(getattr(self.cfg, "bc_rudder_mag_weight", 0.0))
            rudder_base = float(getattr(self.cfg, "bc_rudder_weight", 1.0))
            err = (pred - targets) ** 2
            if (pitch_w > 0.0 or pitch_base != 1.0) and A > 0:
                scale = pitch_base * (1.0 + pitch_w * torch.abs(targets[:, :, 0]))
                err[:, :, 0] = err[:, :, 0] * scale
            if (roll_w > 0.0 or roll_base != 1.0) and A > 1:
                scale = roll_base * (1.0 + roll_w * torch.abs(targets[:, :, 1]))
                err[:, :, 1] = err[:, :, 1] * scale
            if (thr_w > 0.0 or thr_base != 1.0) and A > 3:
                scale = thr_base * (1.0 + thr_w * torch.abs(targets[:, :, 3]))
                err[:, :, 3] = err[:, :, 3] * scale
            if (rudder_w > 0.0 or rudder_base != 1.0) and A > 2:
                # Weight the rudder dimension:
                # - a constant factor (rudder_base) to reduce compounding drift
                # - an extra factor based on expert magnitude for large crosswind corrections
                scale = rudder_base * (1.0 + rudder_w * torch.abs(targets[:, :, 2]))
                err[:, :, 2] = err[:, :, 2] * scale
            err = err * weights_a
            denom = float(weights.sum().clamp_min(1.0).item()) * float(A)
            bc_loss = err.sum() / denom
        elif actor_input == "embed_gru":
            # History-capable BC over embeddings: the GRU hidden state can represent
            # integral-like behavior needed for runway tracking under wind.
            assert embeds is not None
            feats = embeds[:, :L]  # (B, L, E)
            mean, _std, _hN = self.actor(feats, h0=None)  # type: ignore[misc]
            pred = torch.tanh(mean)
            rudder_w = float(getattr(self.cfg, "bc_rudder_mag_weight", 0.0))
            rudder_base = float(getattr(self.cfg, "bc_rudder_weight", 1.0))
            err = (pred - targets) ** 2
            if (pitch_w > 0.0 or pitch_base != 1.0) and A > 0:
                scale = pitch_base * (1.0 + pitch_w * torch.abs(targets[:, :, 0]))
                err[:, :, 0] = err[:, :, 0] * scale
            if (thr_w > 0.0 or thr_base != 1.0) and A > 3:
                scale = thr_base * (1.0 + thr_w * torch.abs(targets[:, :, 3]))
                err[:, :, 3] = err[:, :, 3] * scale
            if (rudder_w > 0.0 or rudder_base != 1.0) and A > 2:
                scale = rudder_base * (1.0 + rudder_w * torch.abs(targets[:, :, 2]))
                err[:, :, 2] = err[:, :, 2] * scale
            err = err * weights_a
            denom = float(weights.sum().clamp_min(1.0).item()) * float(A)
            bc_loss = err.sum() / denom
        elif actor_input == "rssm":
            # RSSM-conditioned BC: roll the RSSM forward with a mixture of teacher actions and actor actions.
            assert embeds is not None
            deterministic_state = bool(getattr(self.cfg, "bc_deterministic_state", False))
            state, _ = self.wm.rssm.observe_init(embeds[:, 0], deterministic=deterministic_state)
            bc_losses = []
            rudder_w = float(getattr(self.cfg, "bc_rudder_mag_weight", 0.0))
            rudder_base = float(getattr(self.cfg, "bc_rudder_weight", 1.0))
            for t in range(L):
                feat_t = self.wm.feat(state)
                mean, _std = self.actor(feat_t)
                pred_t = torch.tanh(mean)
                if float(valid[:, t].max().item()) > 0.5:
                    if (rudder_w > 0.0 or rudder_base != 1.0) and A > 2:
                        err = (pred_t - targets[:, t]) ** 2  # (B, A)
                        if (pitch_w > 0.0 or pitch_base != 1.0) and A > 0:
                            scale_p = pitch_base * (1.0 + pitch_w * torch.abs(targets[:, t, 0]))
                            err[:, 0] = err[:, 0] * scale_p
                        if (roll_w > 0.0 or roll_base != 1.0) and A > 1:
                            scale_r = roll_base * (1.0 + roll_w * torch.abs(targets[:, t, 1]))
                            err[:, 1] = err[:, 1] * scale_r
                        if (thr_w > 0.0 or thr_base != 1.0) and A > 3:
                            scale_thr = thr_base * (1.0 + thr_w * torch.abs(targets[:, t, 3]))
                            err[:, 3] = err[:, 3] * scale_thr
                        scale = rudder_base * (1.0 + rudder_w * torch.abs(targets[:, t, 2]))  # (B,)
                        err[:, 2] = err[:, 2] * scale
                        # Mask invalid rows (post-terminal) for this timestep.
                        m = weights[:, t].view(B, 1)
                        err = err * m
                        denom = float(m.sum().clamp_min(1.0).item()) * float(A)
                        bc_losses.append(err.sum() / denom)
                    else:
                        m = weights[:, t].view(B, 1)
                        err = ((pred_t - targets[:, t]) ** 2) * m
                        if (pitch_w > 0.0 or pitch_base != 1.0) and A > 0:
                            scale_p = pitch_base * (1.0 + pitch_w * torch.abs(targets[:, t, 0]))
                            err[:, 0] = err[:, 0] * scale_p
                        if (roll_w > 0.0 or roll_base != 1.0) and A > 1:
                            scale_r = roll_base * (1.0 + roll_w * torch.abs(targets[:, t, 1]))
                            err[:, 1] = err[:, 1] * scale_r
                        if (thr_w > 0.0 or thr_base != 1.0) and A > 3:
                            scale_thr = thr_base * (1.0 + thr_w * torch.abs(targets[:, t, 3]))
                            err[:, 3] = err[:, 3] * scale_thr
                        denom = float(m.sum().clamp_min(1.0).item()) * float(A)
                        bc_losses.append(err.sum() / denom)

                if teacher_prob >= 1.0:
                    act_in = actions[:, t]
                elif teacher_prob <= 0.0:
                    act_in = pred_t.detach()
                else:
                    mask = (torch.rand((B, 1), device=self.device) < teacher_prob).float()
                    act_in = mask * actions[:, t] + (1.0 - mask) * pred_t.detach()
                with torch.no_grad():
                    state, _, _ = self.wm.rssm.obs_step(state, act_in, embeds[:, t + 1], deterministic=deterministic_state)

            if bc_losses:
                bc_loss = torch.stack(bc_losses).mean()
            else:
                bc_loss = torch.tensor(0.0, device=self.device)
        else:
            raise ValueError(f"unknown actor_input: {actor_input!r}")

        scale = float(self.cfg.bc_scale) if float(self.cfg.bc_scale) > 0.0 else 1.0
        actor_loss = bc_loss * scale
        self.opt_actor.zero_grad(set_to_none=True)
        actor_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.actor.parameters(), self.cfg.grad_clip)
        self.opt_actor.step()

        return {
            "ac/actor": float(actor_loss.detach().cpu().item()),
            "ac/bc": float(bc_loss.detach().cpu().item()),
        }
