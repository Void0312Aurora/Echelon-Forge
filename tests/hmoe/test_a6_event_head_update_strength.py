from __future__ import annotations

import unittest

import torch as th
from gymnasium import spaces

from python.testing.runtime import ensure_repo_imports

ensure_repo_imports()

from gym_envs.universal_env_parts import make_action_space
from python.models.transformer import TransformerExtractor
from python.rl.policy_algo.first_event_hazard import (
    compute_first_event_credit_loss,
    compute_first_event_hazard_loss,
    compute_first_event_policy_margin_loss,
)
from python.rl.policy_algo.policies import HierarchicalMoEExecutionPolicy


class _ConstantSchedule:
    def __init__(self, lr: float) -> None:
        self.lr = float(lr)

    def __call__(self, progress_remaining: float) -> float:
        return self.lr


def _grad_norm(params) -> float:
    total = 0.0
    for param in params:
        if param.grad is not None:
            total += float(param.grad.detach().pow(2).sum().cpu().item())
    return total**0.5


class A6EventHeadUpdateStrengthTests(unittest.TestCase):
    def _observation_space(self) -> spaces.Dict:
        return spaces.Dict(
            {
                "instruments": spaces.Box(low=-1.0, high=1.0, shape=(42,), dtype=float),
                "contacts": spaces.Box(low=-1.0, high=1.0, shape=(10, 5), dtype=float),
                "rwr": spaces.Box(low=-1.0, high=1.0, shape=(4, 4), dtype=float),
                "mission": spaces.Box(low=-1.0e6, high=1.0e6, shape=(20,), dtype=float),
                "proprio": spaces.Box(low=-1.0, high=7.0, shape=(12,), dtype=float),
            }
        )

    def _open_first_shot_obs(self, batch_size: int = 16) -> dict[str, th.Tensor]:
        mission = th.zeros((batch_size, 20), dtype=th.float32)
        mission[:, 5] = 2.0
        mission[:, 6] = 1.0
        mission[:, 14] = 2.0
        mission[:, 15] = 1.0
        mission[:, 16] = 1.0
        mission[:, 19] = 1.0
        return {
            "instruments": th.zeros((batch_size, 42), dtype=th.float32),
            "contacts": th.zeros((batch_size, 10, 5), dtype=th.float32),
            "rwr": th.zeros((batch_size, 4, 4), dtype=th.float32),
            "mission": mission,
            "proprio": th.zeros((batch_size, 12), dtype=th.float32),
        }

    def _make_policy(
        self,
        lr: float,
        *,
        hybrid_event_head_lr_scale: float = 0.0,
        hybrid_event_credit_head_lr_scale: float = 0.0,
    ) -> HierarchicalMoEExecutionPolicy:
        th.manual_seed(123)
        policy = HierarchicalMoEExecutionPolicy(
            self._observation_space(),
            make_action_space("air_combat_hybrid_v1"),
            _ConstantSchedule(lr),
            features_extractor_class=TransformerExtractor,
            features_extractor_kwargs={
                "features_dim": 32,
                "n_heads": 4,
                "n_layers": 1,
                "use_checkpointing": False,
            },
            net_arch={"pi": [32], "vf": [32]},
            hybrid_action_spec="air_combat_hybrid_v1",
            hmoe_residual_scale=0.18,
            hmoe_head_lr_scale=0.35,
            hmoe_residual_warmup_fraction=0.3,
            hmoe_residual_start_factor=0.25,
            hybrid_event_head_lr_scale=hybrid_event_head_lr_scale,
            hybrid_event_credit_head_lr_scale=hybrid_event_credit_head_lr_scale,
        )
        policy.set_hmoe_training_progress(0.0)
        policy.apply_optimizer_learning_rate(float(lr), lr_mult=1.0)
        with th.no_grad():
            policy.action_net.weight.zero_()
            policy.action_net.bias.zero_()
            policy.action_net.bias[9] = -5.3
            policy.action_net.bias[11] = 0.0
            for param in policy.hmoe_head_bank.parameters():
                param.zero_()
            if policy.hybrid_event_head is not None:
                policy.hybrid_event_head.weight.zero_()
                policy.hybrid_event_head.bias.zero_()
            if policy.hybrid_event_credit_head is not None:
                policy.hybrid_event_credit_head.weight.zero_()
                policy.hybrid_event_credit_head.bias.zero_()
        return policy

    def _hazard_loss(self, policy: HierarchicalMoEExecutionPolicy, obs: dict[str, th.Tensor]):
        distribution = policy.get_distribution(obs)
        event_delta = distribution.fire_event_logit_delta()
        self.assertIsNotNone(event_delta)
        assert event_delta is not None
        target = th.ones_like(event_delta)
        active = th.ones_like(event_delta, dtype=th.bool)
        weight = th.ones_like(event_delta)
        return compute_first_event_hazard_loss(event_delta, target, active, weight, coef=0.3).loss

    def _delta_mean(self, policy: HierarchicalMoEExecutionPolicy, obs: dict[str, th.Tensor]) -> float:
        with th.no_grad():
            delta = policy.get_distribution(obs).fire_event_logit_delta()
        self.assertIsNotNone(delta)
        assert delta is not None
        return float(delta.detach().mean().cpu().item())

    def test_a6_hazard_gradient_reaches_shared_and_hmoe_event_heads(self) -> None:
        policy = self._make_policy(3.0e-5)
        obs = self._open_first_shot_obs()

        loss = self._hazard_loss(policy, obs)
        loss.backward()

        stats = policy.get_hmoe_route_stats()
        self.assertAlmostEqual(stats["hmoe/fam/combat"], 1.0, places=6)
        self.assertAlmostEqual(stats["hmoe/sub/combat/first_shot"], 1.0, places=6)
        self.assertAlmostEqual(stats["hmoe/resid_effective_scale"], 0.18, places=6)
        self.assertLess(float(policy.action_net.bias.grad[9].detach().cpu().item()), 0.0)
        self.assertGreater(float(policy.action_net.bias.grad[11].detach().cpu().item()), 0.0)
        self.assertGreater(_grad_norm(policy.hmoe_head_bank.parameters()), 0.0)
        self.assertEqual([group.get("name") for group in policy.optimizer.param_groups], ["shared", "hmoe"])
        self.assertAlmostEqual(float(policy.optimizer.param_groups[0]["lr"]), 3.0e-5, places=10)
        self.assertAlmostEqual(float(policy.optimizer.param_groups[1]["lr"]), 3.0e-5 * 0.35, places=10)

    def _hazard_only_delta_move(self, lr: float, *, steps: int = 8) -> float:
        policy = self._make_policy(lr)
        obs = self._open_first_shot_obs()
        before = self._delta_mean(policy, obs)
        for _ in range(int(steps)):
            policy.optimizer.zero_grad()
            loss = self._hazard_loss(policy, obs)
            loss.backward()
            th.nn.utils.clip_grad_norm_(policy.parameters(), 0.5)
            policy.optimizer.step()
        return self._delta_mean(policy, obs) - before

    def test_a6_current_short_train_lr_moves_event_delta_slowly(self) -> None:
        current_lr_move = self._hazard_only_delta_move(3.0e-5, steps=8)
        ten_x_lr_move = self._hazard_only_delta_move(3.0e-4, steps=8)

        self.assertGreater(current_lr_move, 0.0)
        self.assertLess(current_lr_move, 0.03)
        self.assertGreater(ten_x_lr_move, current_lr_move * 5.0)

    def test_a6_event_head_lane_accelerates_delta_with_same_base_lr(self) -> None:
        baseline_move = self._hazard_only_delta_move(3.0e-5, steps=8)

        policy = self._make_policy(3.0e-5, hybrid_event_head_lr_scale=10.0)
        obs = self._open_first_shot_obs()
        before = self._delta_mean(policy, obs)
        self.assertEqual([group.get("name") for group in policy.optimizer.param_groups], ["shared", "hybrid_event_head", "hmoe"])
        self.assertAlmostEqual(float(policy.optimizer.param_groups[1]["lr"]), 3.0e-5 * 10.0, places=10)
        for _ in range(8):
            policy.optimizer.zero_grad()
            loss = self._hazard_loss(policy, obs)
            loss.backward()
            th.nn.utils.clip_grad_norm_(policy.parameters(), 0.5)
            policy.optimizer.step()
        event_head_move = self._delta_mean(policy, obs) - before
        stats = policy.get_hmoe_route_stats()

        self.assertGreater(event_head_move, baseline_move * 5.0)
        self.assertEqual(float(stats["a6/event_head_enabled"]), 1.0)
        self.assertGreater(float(stats["a6/event_head_delta_abs_mean"]), 0.0)

    def test_a7_credit_value_loss_reaches_credit_head_without_event_logit_update(self) -> None:
        policy = self._make_policy(3.0e-5, hybrid_event_credit_head_lr_scale=10.0)
        obs = self._open_first_shot_obs()
        distribution = policy.get_distribution(obs)
        q_values = distribution.fire_event_q_values()
        self.assertIsNotNone(q_values)
        assert q_values is not None
        target = th.ones((int(q_values.shape[0]),), dtype=th.float32)
        active = th.ones_like(target, dtype=th.bool)
        weight = th.ones_like(target)

        loss = compute_first_event_credit_loss(
            q_values,
            target,
            active,
            weight,
            value_coef=0.3,
            delta_align_coef=0.0,
        ).loss
        loss.backward()

        assert policy.hybrid_event_credit_head is not None
        self.assertGreater(_grad_norm(policy.hybrid_event_credit_head.parameters()), 0.0)
        self.assertIsNone(policy.action_net.bias.grad)
        self.assertIsNone(policy.hybrid_event_head)

    def test_a7_delta_align_loss_reaches_event_logits_not_credit_head(self) -> None:
        policy = self._make_policy(
            3.0e-5,
            hybrid_event_head_lr_scale=10.0,
            hybrid_event_credit_head_lr_scale=10.0,
        )
        assert policy.hybrid_event_head is not None
        assert policy.hybrid_event_credit_head is not None
        with th.no_grad():
            policy.hybrid_event_credit_head.bias.copy_(th.tensor([0.0, 2.0], dtype=th.float32))
        obs = self._open_first_shot_obs()
        distribution = policy.get_distribution(obs)
        q_values = distribution.fire_event_q_values()
        event_delta = distribution.fire_event_logit_delta()
        self.assertIsNotNone(q_values)
        self.assertIsNotNone(event_delta)
        assert q_values is not None
        assert event_delta is not None
        target = th.ones((int(q_values.shape[0]),), dtype=th.float32)
        active = th.ones_like(target, dtype=th.bool)
        weight = th.ones_like(target)

        loss = compute_first_event_credit_loss(
            q_values,
            target,
            active,
            weight,
            event_logit_delta=event_delta,
            value_coef=0.0,
            delta_align_coef=0.3,
            delta_align_clip=4.0,
        ).loss
        loss.backward()

        self.assertAlmostEqual(_grad_norm(policy.hybrid_event_credit_head.parameters()), 0.0, places=8)
        self.assertGreater(_grad_norm(policy.hybrid_event_head.parameters()), 0.0)
        self.assertIsNotNone(policy.action_net.bias.grad)
        assert policy.action_net.bias.grad is not None
        self.assertGreater(float(policy.action_net.bias.grad[9].detach().abs().cpu().item()), 0.0)
        self.assertGreater(float(policy.action_net.bias.grad[11].detach().abs().cpu().item()), 0.0)

    def test_a7_policy_margin_loss_pushes_positive_up_and_negative_down(self) -> None:
        delta = th.tensor([0.0, 0.0], dtype=th.float32, requires_grad=True)
        target = th.tensor([1.0, 0.0], dtype=th.float32)
        active = th.ones_like(target, dtype=th.bool)
        weight = th.ones_like(target)

        loss = compute_first_event_policy_margin_loss(
            delta,
            target,
            active,
            weight,
            coef=1.0,
            margin=2.0,
        ).loss
        loss.backward()

        self.assertIsNotNone(delta.grad)
        assert delta.grad is not None
        self.assertLess(float(delta.grad[0].detach().cpu().item()), 0.0)
        self.assertGreater(float(delta.grad[1].detach().cpu().item()), 0.0)

    def test_a7_policy_margin_loss_reaches_event_policy_path_not_credit_head(self) -> None:
        policy = self._make_policy(
            3.0e-5,
            hybrid_event_head_lr_scale=10.0,
            hybrid_event_credit_head_lr_scale=10.0,
        )
        assert policy.hybrid_event_head is not None
        assert policy.hybrid_event_credit_head is not None
        with th.no_grad():
            policy.action_net.weight[9].fill_(0.01)
            policy.action_net.weight[11].fill_(-0.01)
        obs = self._open_first_shot_obs()
        distribution = policy.get_distribution(obs)
        event_delta = distribution.fire_event_logit_delta()
        self.assertIsNotNone(event_delta)
        assert event_delta is not None
        target = th.ones_like(event_delta)
        active = th.ones_like(event_delta, dtype=th.bool)
        weight = th.ones_like(event_delta)

        loss = compute_first_event_policy_margin_loss(
            event_delta,
            target,
            active,
            weight,
            coef=0.3,
            margin=2.0,
        ).loss
        loss.backward()

        self.assertGreater(_grad_norm(policy.action_net.parameters()), 0.0)
        self.assertGreater(_grad_norm(policy.hybrid_event_head.parameters()), 0.0)
        self.assertGreater(_grad_norm(policy.mlp_extractor.policy_net.parameters()), 0.0)
        self.assertAlmostEqual(_grad_norm(policy.hybrid_event_credit_head.parameters()), 0.0, places=8)


if __name__ == "__main__":
    unittest.main()
