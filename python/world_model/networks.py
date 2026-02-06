from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import torch
import torch.nn as nn
import torch.nn.functional as F


class MLP(nn.Module):
    def __init__(self, in_dim: int, hidden: Sequence[int], out_dim: int, *, layer_norm: bool = False):
        super().__init__()
        dims = [int(in_dim), *[int(h) for h in hidden], int(out_dim)]
        layers: list[nn.Module] = []
        for i in range(len(dims) - 2):
            layers.append(nn.Linear(dims[i], dims[i + 1]))
            if layer_norm:
                layers.append(nn.LayerNorm(dims[i + 1]))
            layers.append(nn.SiLU())
        layers.append(nn.Linear(dims[-2], dims[-1]))
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


@dataclass
class RSSMState:
    deter: torch.Tensor  # (B, deter_dim)
    stoch: torch.Tensor  # (B, stoch_dim)


class RSSM(nn.Module):
    def __init__(self, *, action_dim: int, embed_dim: int, deter_dim: int = 512, stoch_dim: int = 64):
        super().__init__()
        self.action_dim = int(action_dim)
        self.embed_dim = int(embed_dim)
        self.deter_dim = int(deter_dim)
        self.stoch_dim = int(stoch_dim)

        self.gru = nn.GRUCell(self.action_dim + self.stoch_dim, self.deter_dim)
        self.prior_net = MLP(self.deter_dim, [512], self.stoch_dim * 2, layer_norm=True)
        self.post_net = MLP(self.deter_dim + self.embed_dim, [512], self.stoch_dim * 2, layer_norm=True)

    def init_state(self, batch_size: int, device: torch.device) -> RSSMState:
        deter = torch.zeros((batch_size, self.deter_dim), device=device)
        stoch = torch.zeros((batch_size, self.stoch_dim), device=device)
        return RSSMState(deter=deter, stoch=stoch)

    def _dist_params(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        mean, log_std = torch.chunk(x, 2, dim=-1)
        log_std = torch.clamp(log_std, -5.0, 2.0)
        std = torch.exp(log_std)
        return mean, std

    def _sample(self, mean: torch.Tensor, std: torch.Tensor, *, deterministic: bool) -> torch.Tensor:
        if deterministic:
            return mean
        eps = torch.randn_like(mean)
        return mean + eps * std

    def observe_init(
        self, embed0: torch.Tensor, *, deterministic: bool = False
    ) -> tuple[RSSMState, tuple[torch.Tensor, torch.Tensor]]:
        deter0 = torch.zeros((embed0.shape[0], self.deter_dim), device=embed0.device)
        stats = self.post_net(torch.cat([deter0, embed0], dim=-1))
        mean, std = self._dist_params(stats)
        stoch0 = self._sample(mean, std, deterministic=bool(deterministic))
        return RSSMState(deter=deter0, stoch=stoch0), (mean, std)

    def obs_step(
        self, prev: RSSMState, action: torch.Tensor, embed: torch.Tensor, *, deterministic: bool = False
    ) -> tuple[RSSMState, tuple[torch.Tensor, torch.Tensor], tuple[torch.Tensor, torch.Tensor]]:
        x = torch.cat([prev.stoch, action], dim=-1)
        deter = self.gru(x, prev.deter)

        prior_stats = self.prior_net(deter)
        prior_mean, prior_std = self._dist_params(prior_stats)

        post_stats = self.post_net(torch.cat([deter, embed], dim=-1))
        post_mean, post_std = self._dist_params(post_stats)
        stoch = self._sample(post_mean, post_std, deterministic=bool(deterministic))
        return RSSMState(deter=deter, stoch=stoch), (prior_mean, prior_std), (post_mean, post_std)

    def imagine_step(
        self, prev: RSSMState, action: torch.Tensor, *, deterministic: bool = False
    ) -> tuple[RSSMState, tuple[torch.Tensor, torch.Tensor]]:
        x = torch.cat([prev.stoch, action], dim=-1)
        deter = self.gru(x, prev.deter)
        prior_stats = self.prior_net(deter)
        prior_mean, prior_std = self._dist_params(prior_stats)
        stoch = self._sample(prior_mean, prior_std, deterministic=bool(deterministic))
        return RSSMState(deter=deter, stoch=stoch), (prior_mean, prior_std)


class ObservationEncoder(nn.Module):
    def __init__(self, *, obs_vec_dim: int, embed_dim: int = 256):
        super().__init__()
        self.obs_vec_dim = int(obs_vec_dim)
        self.embed_dim = int(embed_dim)
        self.vec = MLP(self.obs_vec_dim, [512, 512], self.embed_dim, layer_norm=True)

    def forward(self, obs_vec: torch.Tensor) -> torch.Tensor:
        return self.vec(obs_vec)


class VisualEncoder(nn.Module):
    def __init__(self, *, visual_dim: int, embed_dim: int = 256):
        super().__init__()
        self.visual_dim = int(visual_dim)
        self.embed_dim = int(embed_dim)
        hidden = [1024, 1024] if self.visual_dim <= 5000 else [512, 512]
        self.net = MLP(self.visual_dim, hidden, self.embed_dim, layer_norm=True)

    def forward(self, visual: torch.Tensor) -> torch.Tensor:
        if visual.ndim > 2:
            visual = visual.reshape(visual.shape[0], -1)
        return self.net(visual)


class MultiModalEncoder(nn.Module):
    def __init__(
        self,
        *,
        obs_vec_dim: int,
        vec_embed_dim: int = 256,
        visual_dim: int | None = None,
        visual_embed_dim: int = 256,
    ):
        super().__init__()
        self.obs_vec_dim = int(obs_vec_dim)
        self.vec_embed_dim = int(vec_embed_dim)
        self.visual_dim = None if visual_dim is None else int(visual_dim)
        self.visual_embed_dim = int(visual_embed_dim)

        self.vec = ObservationEncoder(obs_vec_dim=self.obs_vec_dim, embed_dim=self.vec_embed_dim)
        self.visual = None
        if self.visual_dim is not None:
            self.visual = VisualEncoder(visual_dim=self.visual_dim, embed_dim=self.visual_embed_dim)

    @property
    def embed_dim(self) -> int:
        if self.visual is None:
            return self.vec_embed_dim
        return self.vec_embed_dim + self.visual_embed_dim

    def forward(self, obs_vec: torch.Tensor, visual: torch.Tensor | None = None) -> torch.Tensor:
        vec = self.vec(obs_vec)
        if self.visual is None:
            return vec
        if visual is None:
            raise ValueError("MultiModalEncoder expected visual input but got None")
        vis = self.visual(visual)
        return torch.cat([vec, vis], dim=-1)


class ObservationDecoder(nn.Module):
    def __init__(self, *, feat_dim: int, obs_vec_dim: int):
        super().__init__()
        self.net = MLP(int(feat_dim), [512, 512], int(obs_vec_dim), layer_norm=True)

    def forward(self, feat: torch.Tensor) -> torch.Tensor:
        return self.net(feat)


class VisualDecoder(nn.Module):
    def __init__(self, *, feat_dim: int, visual_dim: int):
        super().__init__()
        self.visual_dim = int(visual_dim)
        hidden = [1024, 1024] if self.visual_dim <= 5000 else [512, 512]
        self.net = MLP(int(feat_dim), hidden, self.visual_dim, layer_norm=True)

    def forward(self, feat: torch.Tensor) -> torch.Tensor:
        return self.net(feat)


class RewardHead(nn.Module):
    def __init__(self, *, feat_dim: int):
        super().__init__()
        self.net = MLP(int(feat_dim), [256, 256], 1, layer_norm=True)

    def forward(self, feat: torch.Tensor) -> torch.Tensor:
        return self.net(feat).squeeze(-1)


class ContinueHead(nn.Module):
    def __init__(self, *, feat_dim: int):
        super().__init__()
        self.net = MLP(int(feat_dim), [256, 256], 1, layer_norm=True)

    def forward(self, feat: torch.Tensor) -> torch.Tensor:
        logits = self.net(feat).squeeze(-1)
        return logits


class WorldModel(nn.Module):
    def __init__(
        self,
        *,
        action_dim: int,
        obs_vec_dim: int,
        visual_shape: tuple[int, int, int] | None = None,
        vec_embed_dim: int = 256,
        visual_embed_dim: int = 256,
        deter_dim: int = 512,
        stoch_dim: int = 64,
    ):
        super().__init__()
        visual_dim = None
        if visual_shape is not None:
            h, w, c = (int(visual_shape[0]), int(visual_shape[1]), int(visual_shape[2]))
            visual_dim = h * w * c

        self.encoder = MultiModalEncoder(
            obs_vec_dim=obs_vec_dim,
            vec_embed_dim=vec_embed_dim,
            visual_dim=visual_dim,
            visual_embed_dim=visual_embed_dim,
        )
        self.rssm = RSSM(action_dim=action_dim, embed_dim=self.encoder.embed_dim, deter_dim=deter_dim, stoch_dim=stoch_dim)
        feat_dim = deter_dim + stoch_dim
        self.decoder = ObservationDecoder(feat_dim=feat_dim, obs_vec_dim=obs_vec_dim)
        self.visual_decoder = None
        if visual_dim is not None:
            self.visual_decoder = VisualDecoder(feat_dim=feat_dim, visual_dim=visual_dim)
        self.reward = RewardHead(feat_dim=feat_dim)
        self.cont = ContinueHead(feat_dim=feat_dim)

    def feat(self, state: RSSMState) -> torch.Tensor:
        return torch.cat([state.deter, state.stoch], dim=-1)


class Actor(nn.Module):
    def __init__(self, *, feat_dim: int, action_dim: int):
        super().__init__()
        self.action_dim = int(action_dim)
        self.net = MLP(int(feat_dim), [512, 512], self.action_dim * 2, layer_norm=True)

    def forward(self, feat: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        mean, log_std = torch.chunk(self.net(feat), 2, dim=-1)
        # Limit exploration noise. A very large std quickly saturates tanh() actions and causes
        # runaway ground-control behavior (especially yaw) during takeoff roll.
        log_std = torch.clamp(log_std, -5.0, 0.5)
        std = torch.exp(log_std)
        return mean, std

    def sample(self, feat: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        mean, std = self(feat)
        eps = torch.randn_like(mean)
        pre_tanh = mean + eps * std
        action = torch.tanh(pre_tanh)
        # Approx log-prob (ignoring tanh correction for initial baseline).
        logp = (-0.5 * ((pre_tanh - mean) / (std + 1e-8)) ** 2 - torch.log(std + 1e-8) - 0.5 * torch.log(torch.tensor(2.0 * torch.pi, device=feat.device))).sum(-1)
        return action, logp


class GRUActor(nn.Module):
    """
    Recurrent actor over observation embeddings (history-capable policy).

    This is used for realism-first takeoff tasks where a purely reactive policy (MLP on per-step embeddings)
    struggles to emulate integral-like behavior under crosswind.
    """

    def __init__(self, *, input_dim: int, action_dim: int, hidden_dim: int = 256):
        super().__init__()
        self.input_dim = int(input_dim)
        self.action_dim = int(action_dim)
        self.hidden_dim = int(hidden_dim)
        self.gru = nn.GRU(self.input_dim, self.hidden_dim, batch_first=True)
        self.head = MLP(self.hidden_dim, [512, 512], self.action_dim * 2, layer_norm=True)

    def init_h(self, batch_size: int, device: torch.device) -> torch.Tensor:
        # GRU hidden state: (num_layers=1, B, H)
        return torch.zeros((1, int(batch_size), self.hidden_dim), device=device)

    def forward(self, emb_seq: torch.Tensor, h0: torch.Tensor | None = None) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        emb_seq: (B, L, E)
        h0: (1, B, H) or None
        returns: mean (B, L, A), std (B, L, A), hN (1, B, H)
        """
        if emb_seq.ndim != 3:
            raise ValueError(f"GRUActor.forward expects (B,L,E), got {tuple(emb_seq.shape)}")
        out, hN = self.gru(emb_seq, h0)
        B, L, H = out.shape
        stats = self.head(out.reshape(B * L, H)).reshape(B, L, self.action_dim * 2)
        mean, log_std = torch.chunk(stats, 2, dim=-1)
        log_std = torch.clamp(log_std, -5.0, 0.5)
        std = torch.exp(log_std)
        return mean, std, hN

    def step(self, emb: torch.Tensor, h: torch.Tensor | None) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Single-step inference.
        emb: (B, E)
        h: (1, B, H) or None
        returns: mean (B, A), std (B, A), hN (1, B, H)
        """
        if emb.ndim != 2:
            raise ValueError(f"GRUActor.step expects (B,E), got {tuple(emb.shape)}")
        out, hN = self.gru(emb.unsqueeze(1), h)
        out = out.squeeze(1)
        mean, log_std = torch.chunk(self.head(out), 2, dim=-1)
        log_std = torch.clamp(log_std, -5.0, 0.5)
        std = torch.exp(log_std)
        return mean, std, hN

    def sample_step(self, emb: torch.Tensor, h: torch.Tensor | None) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        mean, std, hN = self.step(emb, h)
        eps = torch.randn_like(mean)
        pre_tanh = mean + eps * std
        action = torch.tanh(pre_tanh)
        logp = (
            -0.5 * ((pre_tanh - mean) / (std + 1e-8)) ** 2
            - torch.log(std + 1e-8)
            - 0.5 * torch.log(torch.tensor(2.0 * torch.pi, device=emb.device))
        ).sum(-1)
        return action, logp, hN


class Value(nn.Module):
    def __init__(self, *, feat_dim: int):
        super().__init__()
        self.net = MLP(int(feat_dim), [512, 512], 1, layer_norm=True)

    def forward(self, feat: torch.Tensor) -> torch.Tensor:
        return self.net(feat).squeeze(-1)


def kl_divergence(mean_q: torch.Tensor, std_q: torch.Tensor, mean_p: torch.Tensor, std_p: torch.Tensor) -> torch.Tensor:
    # KL(N(q)||N(p)) for diagonal Gaussians
    var_q = std_q**2
    var_p = std_p**2
    return 0.5 * (
        torch.log(var_p / (var_q + 1e-8) + 1e-8)
        + (var_q + (mean_q - mean_p) ** 2) / (var_p + 1e-8)
        - 1.0
    ).sum(-1)


def lambda_return(reward: torch.Tensor, value: torch.Tensor, discount: torch.Tensor, lambda_: float) -> torch.Tensor:
    """
    reward:   (H, B)
    value:    (H+1, B)  value[t] is V(s_t)
    discount: (H, B)
    returns:  (H, B)
    """
    lambda_ = float(lambda_)
    H = reward.shape[0]
    ret = value[-1]
    outs = []
    for t in reversed(range(H)):
        ret = reward[t] + discount[t] * ((1.0 - lambda_) * value[t + 1] + lambda_ * ret)
        outs.append(ret)
    outs.reverse()
    return torch.stack(outs, dim=0)
