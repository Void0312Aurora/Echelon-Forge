from __future__ import annotations

import unittest
from unittest import mock

import numpy as np
import torch as th
from gymnasium import spaces

from python.testing.runtime import ensure_repo_imports

ensure_repo_imports()

from python.models.transformer import (
    TemporalTransformerExtractor,
    TransformerExtractor,
    preprocess_mission_tensor,
    preprocess_transformer_observations,
)
from gym_envs.universal_env_parts import make_action_space
from python.mission_obs_taxonomy import mission_observation_dim, mission_observation_field_index
from python.rl.policy_algo.policies import (
    HierarchicalMoEExecutionPolicy,
    SquashedMultiInputPolicy,
    _HybridActionDistribution,
    _normalize_hybrid_action_layout,
)
from python.rl.support.nonfinite_probe import NonFiniteTrainingProbe
from train import apply_safe_action_bias


class _ConstantSchedule:
    def __call__(self, progress_remaining: float) -> float:
        return 3.0e-4


class HMoEPolicyTests(unittest.TestCase):
    def _make_air_combat_hybrid_distribution(
        self,
        params: th.Tensor,
        *,
        fire_mask: th.Tensor | None = None,
    ) -> _HybridActionDistribution:
        action_space = make_action_space("air_combat_hybrid_v1")
        layout = _normalize_hybrid_action_layout("air_combat_hybrid_v1", action_space)
        assert layout is not None
        return _HybridActionDistribution(
            layout=layout,
            params=params,
            log_std=th.zeros((6,), dtype=params.dtype, device=params.device),
            action_low=action_space.low,
            action_high=action_space.high,
            fire_event_mask=fire_mask,
        )

    def _make_policy(self) -> HierarchicalMoEExecutionPolicy:
        observation_space = spaces.Dict(
            {
                "image": spaces.Box(low=0.0, high=1.0, shape=(1, 8, 8), dtype=float),
                "instruments": spaces.Box(low=-1.0, high=1.0, shape=(26,), dtype=float),
                "mission": spaces.Box(low=-1.0e6, high=1.0e6, shape=(21,), dtype=float),
                "prev_action": spaces.Box(low=-1.0, high=1.0, shape=(17,), dtype=float),
            }
        )
        action_space = spaces.Box(low=-1.0, high=1.0, shape=(17,), dtype=float)
        return HierarchicalMoEExecutionPolicy(
            observation_space,
            action_space,
            _ConstantSchedule(),
            net_arch={"pi": [32], "vf": [32]},
        )

    def _make_air_combat_hybrid_observation_space(self, mission_dim: int = 20) -> spaces.Dict:
        return spaces.Dict(
            {
                "instruments": spaces.Box(low=-1.0, high=1.0, shape=(42,), dtype=float),
                "contacts": spaces.Box(low=-1.0, high=1.0, shape=(10, 5), dtype=float),
                "rwr": spaces.Box(low=-1.0, high=1.0, shape=(4, 4), dtype=float),
                "mission": spaces.Box(low=-1.0e6, high=1.0e6, shape=(mission_dim,), dtype=float),
                "proprio": spaces.Box(low=-1.0, high=7.0, shape=(12,), dtype=float),
            }
        )

    def _make_air_combat_hybrid_policy(self, **policy_kwargs) -> HierarchicalMoEExecutionPolicy:
        return HierarchicalMoEExecutionPolicy(
            self._make_air_combat_hybrid_observation_space(),
            make_action_space("air_combat_hybrid_v1"),
            _ConstantSchedule(),
            features_extractor_class=TransformerExtractor,
            features_extractor_kwargs={"features_dim": 32, "n_heads": 4, "n_layers": 1, "use_checkpointing": False},
            net_arch={"pi": [32], "vf": [32]},
            hybrid_action_spec="air_combat_hybrid_v1",
            **policy_kwargs,
        )

    def _make_authorized_fire_obs(self, batch_size: int) -> dict[str, th.Tensor]:
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

    def test_optimizer_includes_hmoe_head_parameters(self) -> None:
        policy = self._make_policy()
        head_param_ids = {id(param) for param in policy.hmoe_head_bank.parameters()}
        optimizer_param_ids = {
            id(param)
            for group in policy.optimizer.param_groups
            for param in group.get("params", [])
        }
        self.assertTrue(head_param_ids)
        self.assertTrue(head_param_ids.issubset(optimizer_param_ids))

    def test_optimizer_uses_lower_lr_for_hmoe_heads(self) -> None:
        policy = self._make_policy()
        self.assertEqual(len(policy.optimizer.param_groups), 2)
        shared_group, hmoe_group = policy.optimizer.param_groups
        self.assertEqual(shared_group.get("name"), "shared")
        self.assertEqual(hmoe_group.get("name"), "hmoe")
        self.assertAlmostEqual(float(shared_group.get("lr_scale", 0.0)), 1.0, places=6)
        self.assertAlmostEqual(float(hmoe_group.get("lr_scale", 0.0)), 0.35, places=6)
        self.assertAlmostEqual(float(shared_group["lr"]), 3.0e-4, places=10)
        self.assertAlmostEqual(float(hmoe_group["lr"]), 3.0e-4 * 0.35, places=10)

    def test_hybrid_event_head_gets_dedicated_optimizer_lane(self) -> None:
        observation_space = spaces.Dict(
            {
                "instruments": spaces.Box(low=-1.0, high=1.0, shape=(42,), dtype=float),
                "contacts": spaces.Box(low=-1.0, high=1.0, shape=(10, 5), dtype=float),
                "rwr": spaces.Box(low=-1.0, high=1.0, shape=(4, 4), dtype=float),
                "mission": spaces.Box(low=-1.0e6, high=1.0e6, shape=(20,), dtype=float),
                "proprio": spaces.Box(low=-1.0, high=7.0, shape=(12,), dtype=float),
            }
        )
        policy = HierarchicalMoEExecutionPolicy(
            observation_space,
            make_action_space("air_combat_hybrid_v1"),
            _ConstantSchedule(),
            features_extractor_class=TransformerExtractor,
            features_extractor_kwargs={"features_dim": 32, "n_heads": 4, "n_layers": 1, "use_checkpointing": False},
            net_arch={"pi": [32], "vf": [32]},
            hybrid_action_spec="air_combat_hybrid_v1",
            hybrid_event_head_lr_scale=8.0,
        )

        self.assertIsNotNone(policy.hybrid_event_head)
        assert policy.hybrid_event_head is not None
        self.assertTrue(th.allclose(policy.hybrid_event_head.weight.detach(), th.zeros_like(policy.hybrid_event_head.weight)))
        self.assertTrue(th.allclose(policy.hybrid_event_head.bias.detach(), th.zeros_like(policy.hybrid_event_head.bias)))
        self.assertEqual([group.get("name") for group in policy.optimizer.param_groups], ["shared", "hybrid_event_head", "hmoe"])
        self.assertAlmostEqual(float(policy.optimizer.param_groups[1].get("lr_scale", 0.0)), 8.0, places=6)
        self.assertAlmostEqual(float(policy.optimizer.param_groups[1]["lr"]), 3.0e-4 * 8.0, places=10)

        with th.no_grad():
            policy.action_net.weight.zero_()
            policy.action_net.bias.zero_()
            policy.action_net.bias[9] = -5.0
            policy.action_net.bias[11] = 0.0
        obs = {
            "instruments": th.zeros((2, 42), dtype=th.float32),
            "contacts": th.zeros((2, 10, 5), dtype=th.float32),
            "rwr": th.zeros((2, 4, 4), dtype=th.float32),
            "mission": th.zeros((2, 20), dtype=th.float32),
            "proprio": th.zeros((2, 12), dtype=th.float32),
        }
        obs["mission"][:, 5] = 2.0
        obs["mission"][:, 6] = 1.0
        obs["mission"][:, 14] = 2.0
        obs["mission"][:, 15] = 1.0
        obs["mission"][:, 16] = 1.0
        obs["mission"][:, 19] = 1.0

        with th.no_grad():
            delta = policy.get_distribution(obs).fire_event_logit_delta()

        self.assertIsNotNone(delta)
        assert delta is not None
        self.assertTrue(th.allclose(delta, th.full_like(delta, -5.0)))
        stats = policy.get_hmoe_route_stats()
        self.assertEqual(float(stats["a6/event_head_enabled"]), 1.0)
        self.assertAlmostEqual(float(stats["a6/event_head_delta_abs_mean"]), 0.0, places=6)

    def test_hybrid_event_credit_head_is_disabled_by_default(self) -> None:
        policy = self._make_air_combat_hybrid_policy()

        self.assertIsNone(policy.hybrid_event_credit_head)
        self.assertEqual([group.get("name") for group in policy.optimizer.param_groups], ["shared", "hmoe"])
        self.assertAlmostEqual(
            float(policy._get_constructor_parameters().get("hybrid_event_credit_head_lr_scale", -1.0)),
            0.0,
            places=6,
        )
        obs = self._make_authorized_fire_obs(batch_size=2)

        with th.no_grad():
            distribution = policy.get_distribution(obs)
            credit = policy.get_hybrid_event_credit(obs)
            q_values = distribution.fire_event_q_values()
            advantage = distribution.fire_event_advantage()

        self.assertIsNone(credit)
        self.assertIsNone(q_values)
        self.assertIsNone(advantage)
        stats = policy.get_hmoe_route_stats()
        self.assertEqual(float(stats["a7/event_credit_head_enabled"]), 0.0)
        self.assertAlmostEqual(float(stats["a7/event_credit_head_lr_scale"]), 0.0, places=6)

    def test_hybrid_event_credit_head_gets_dedicated_optimizer_lane_and_zero_outputs(self) -> None:
        observation_space = spaces.Dict(
            {
                "instruments": spaces.Box(low=-1.0, high=1.0, shape=(42,), dtype=float),
                "contacts": spaces.Box(low=-1.0, high=1.0, shape=(10, 5), dtype=float),
                "rwr": spaces.Box(low=-1.0, high=1.0, shape=(4, 4), dtype=float),
                "mission": spaces.Box(low=-1.0e6, high=1.0e6, shape=(20,), dtype=float),
                "proprio": spaces.Box(low=-1.0, high=7.0, shape=(12,), dtype=float),
            }
        )
        policy = HierarchicalMoEExecutionPolicy(
            observation_space,
            make_action_space("air_combat_hybrid_v1"),
            _ConstantSchedule(),
            features_extractor_class=TransformerExtractor,
            features_extractor_kwargs={"features_dim": 32, "n_heads": 4, "n_layers": 1, "use_checkpointing": False},
            net_arch={"pi": [32], "vf": [32]},
            hybrid_action_spec="air_combat_hybrid_v1",
            hybrid_event_credit_head_lr_scale=6.0,
        )

        self.assertIsNotNone(policy.hybrid_event_credit_head)
        assert policy.hybrid_event_credit_head is not None
        self.assertTrue(
            th.allclose(
                policy.hybrid_event_credit_head.weight.detach(),
                th.zeros_like(policy.hybrid_event_credit_head.weight),
            )
        )
        self.assertTrue(
            th.allclose(
                policy.hybrid_event_credit_head.bias.detach(),
                th.zeros_like(policy.hybrid_event_credit_head.bias),
            )
        )
        self.assertEqual([group.get("name") for group in policy.optimizer.param_groups], ["shared", "hybrid_event_credit_head", "hmoe"])
        self.assertAlmostEqual(float(policy.optimizer.param_groups[1].get("lr_scale", 0.0)), 6.0, places=6)
        self.assertAlmostEqual(float(policy.optimizer.param_groups[1]["lr"]), 3.0e-4 * 6.0, places=10)
        self.assertAlmostEqual(
            float(policy._get_constructor_parameters().get("hybrid_event_credit_head_lr_scale", 0.0)),
            6.0,
            places=6,
        )

        with th.no_grad():
            policy.action_net.weight.zero_()
            policy.action_net.bias.zero_()
            policy.action_net.bias[9] = -5.0
            policy.action_net.bias[11] = 0.0
        obs = {
            "instruments": th.zeros((2, 42), dtype=th.float32),
            "contacts": th.zeros((2, 10, 5), dtype=th.float32),
            "rwr": th.zeros((2, 4, 4), dtype=th.float32),
            "mission": th.zeros((2, 20), dtype=th.float32),
            "proprio": th.zeros((2, 12), dtype=th.float32),
        }
        obs["mission"][:, 5] = 2.0
        obs["mission"][:, 6] = 1.0
        obs["mission"][:, 14] = 2.0
        obs["mission"][:, 15] = 1.0
        obs["mission"][:, 16] = 1.0
        obs["mission"][:, 19] = 1.0

        with th.no_grad():
            distribution = policy.get_distribution(obs)
            credit = policy.get_hybrid_event_credit(obs)
            delta = distribution.fire_event_logit_delta()
            q_values = distribution.fire_event_q_values()
            advantage = distribution.fire_event_advantage()

        self.assertIsNotNone(credit)
        self.assertIsNotNone(delta)
        self.assertIsNotNone(q_values)
        self.assertIsNotNone(advantage)
        assert credit is not None
        assert delta is not None
        assert q_values is not None
        assert advantage is not None
        self.assertTrue(th.allclose(delta, th.full_like(delta, -5.0)))
        self.assertEqual(tuple(q_values.shape), (2, 2))
        self.assertTrue(th.allclose(q_values, th.zeros_like(q_values)))
        self.assertTrue(th.allclose(advantage, th.zeros_like(advantage)))
        self.assertTrue(th.allclose(credit.q_hold, th.zeros_like(credit.q_hold)))
        self.assertTrue(th.allclose(credit.q_fire_once, th.zeros_like(credit.q_fire_once)))
        self.assertTrue(th.allclose(credit.event_advantage, th.zeros_like(credit.event_advantage)))
        stats = policy.get_hmoe_route_stats()
        self.assertEqual(float(stats["a7/event_credit_head_enabled"]), 1.0)
        self.assertAlmostEqual(float(stats["a7/event_credit_head_lr_scale"]), 6.0, places=6)
        self.assertAlmostEqual(float(stats["a7/event_credit_advantage_abs_mean"]), 0.0, places=6)

    def test_hybrid_event_credit_head_coexists_with_event_logit_head(self) -> None:
        policy = self._make_air_combat_hybrid_policy(
            hybrid_event_head_lr_scale=8.0,
            hybrid_event_credit_head_lr_scale=6.0,
        )

        self.assertIsNotNone(policy.hybrid_event_head)
        self.assertIsNotNone(policy.hybrid_event_credit_head)
        self.assertEqual(
            [group.get("name") for group in policy.optimizer.param_groups],
            ["shared", "hybrid_event_head", "hybrid_event_credit_head", "hmoe"],
        )
        assert policy.hybrid_event_head is not None
        assert policy.hybrid_event_credit_head is not None
        with th.no_grad():
            policy.action_net.weight.zero_()
            policy.action_net.bias.zero_()
            policy.action_net.bias[9] = -2.0
            policy.action_net.bias[11] = 0.5
            policy.hybrid_event_head.weight.zero_()
            policy.hybrid_event_head.bias.copy_(th.tensor([0.25, 1.25], dtype=th.float32))
            policy.hybrid_event_credit_head.weight.zero_()
            policy.hybrid_event_credit_head.bias.copy_(th.tensor([2.0, 5.0], dtype=th.float32))
        obs = self._make_authorized_fire_obs(batch_size=4)

        with th.no_grad():
            distribution = policy.get_distribution(obs)
            credit = policy.get_hybrid_event_credit(obs)
            delta = distribution.fire_event_logit_delta()
            q_values = distribution.fire_event_q_values()
            advantage = distribution.fire_event_advantage()

        self.assertIsNotNone(credit)
        assert credit is not None
        assert delta is not None
        assert q_values is not None
        assert advantage is not None
        self.assertTrue(th.allclose(delta, th.full((4,), -1.5)))
        self.assertTrue(th.allclose(q_values[:, 0], th.full((4,), 2.0)))
        self.assertTrue(th.allclose(q_values[:, 1], th.full((4,), 5.0)))
        self.assertTrue(th.allclose(advantage, th.full((4,), 3.0)))
        self.assertTrue(th.allclose(credit.event_advantage, th.full((4,), 3.0)))
        stats = policy.get_hmoe_route_stats()
        self.assertEqual(float(stats["a6/event_head_enabled"]), 1.0)
        self.assertEqual(float(stats["a7/event_credit_head_enabled"]), 1.0)

    def test_hybrid_event_credit_head_exposes_hold_fire_values_without_changing_event_logits(self) -> None:
        observation_space = spaces.Dict(
            {
                "instruments": spaces.Box(low=-1.0, high=1.0, shape=(42,), dtype=float),
                "contacts": spaces.Box(low=-1.0, high=1.0, shape=(10, 5), dtype=float),
                "rwr": spaces.Box(low=-1.0, high=1.0, shape=(4, 4), dtype=float),
                "mission": spaces.Box(low=-1.0e6, high=1.0e6, shape=(20,), dtype=float),
                "proprio": spaces.Box(low=-1.0, high=7.0, shape=(12,), dtype=float),
            }
        )
        policy = HierarchicalMoEExecutionPolicy(
            observation_space,
            make_action_space("air_combat_hybrid_v1"),
            _ConstantSchedule(),
            features_extractor_class=TransformerExtractor,
            features_extractor_kwargs={"features_dim": 32, "n_heads": 4, "n_layers": 1, "use_checkpointing": False},
            net_arch={"pi": [32], "vf": [32]},
            hybrid_action_spec="air_combat_hybrid_v1",
            hybrid_event_credit_head_lr_scale=6.0,
        )
        assert policy.hybrid_event_credit_head is not None
        with th.no_grad():
            policy.action_net.weight.zero_()
            policy.action_net.bias.zero_()
            policy.action_net.bias[9] = -2.0
            policy.action_net.bias[11] = 0.5
            policy.hybrid_event_credit_head.weight.zero_()
            policy.hybrid_event_credit_head.bias.copy_(th.tensor([1.25, -0.75], dtype=th.float32))
        obs = {
            "instruments": th.zeros((3, 42), dtype=th.float32),
            "contacts": th.zeros((3, 10, 5), dtype=th.float32),
            "rwr": th.zeros((3, 4, 4), dtype=th.float32),
            "mission": th.zeros((3, 20), dtype=th.float32),
            "proprio": th.zeros((3, 12), dtype=th.float32),
        }
        obs["mission"][:, 5] = 2.0
        obs["mission"][:, 6] = 1.0
        obs["mission"][:, 14] = 2.0
        obs["mission"][:, 15] = 1.0
        obs["mission"][:, 16] = 1.0
        obs["mission"][:, 19] = 1.0

        with th.no_grad():
            distribution = policy.get_distribution(obs)
            credit = policy.get_hybrid_event_credit(obs)
            delta = distribution.fire_event_logit_delta()
            q_values = distribution.fire_event_q_values()
            advantage = distribution.fire_event_advantage()

        self.assertIsNotNone(credit)
        assert credit is not None
        assert delta is not None
        assert q_values is not None
        assert advantage is not None
        self.assertTrue(th.allclose(delta, th.full_like(delta, -2.5)))
        self.assertTrue(th.allclose(q_values[:, 0], th.full((3,), 1.25)))
        self.assertTrue(th.allclose(q_values[:, 1], th.full((3,), -0.75)))
        self.assertTrue(th.allclose(advantage, th.full((3,), -2.0)))
        self.assertTrue(th.allclose(credit.q_hold, th.full((3,), 1.25)))
        self.assertTrue(th.allclose(credit.q_fire_once, th.full((3,), -0.75)))
        self.assertTrue(th.allclose(credit.event_advantage, th.full((3,), -2.0)))
        stats = policy.get_hmoe_route_stats()
        self.assertAlmostEqual(float(stats["a7/event_credit_q_hold_mean"]), 1.25, places=6)
        self.assertAlmostEqual(float(stats["a7/event_credit_q_fire_mean"]), -0.75, places=6)
        self.assertAlmostEqual(float(stats["a7/event_credit_advantage_mean"]), -2.0, places=6)

    def test_hybrid_event_credit_head_state_dict_load_smoke(self) -> None:
        source = self._make_air_combat_hybrid_policy(hybrid_event_credit_head_lr_scale=6.0)
        target = self._make_air_combat_hybrid_policy(hybrid_event_credit_head_lr_scale=6.0)
        assert source.hybrid_event_credit_head is not None
        with th.no_grad():
            source.hybrid_event_credit_head.weight.zero_()
            source.hybrid_event_credit_head.bias.copy_(th.tensor([0.5, 3.5], dtype=th.float32))

        target.load_state_dict({key: value.detach().clone() for key, value in source.state_dict().items()})
        obs = self._make_authorized_fire_obs(batch_size=2)

        with th.no_grad():
            credit = target.get_hybrid_event_credit(obs)

        self.assertIsNotNone(credit)
        assert credit is not None
        self.assertTrue(th.allclose(credit.q_hold, th.full((2,), 0.5)))
        self.assertTrue(th.allclose(credit.q_fire_once, th.full((2,), 3.5)))
        self.assertTrue(th.allclose(credit.event_advantage, th.full((2,), 3.0)))

    def test_route_stats_follow_mission_semantics(self) -> None:
        policy = self._make_policy()
        obs = {
            "image": th.zeros((2, 1, 8, 8), dtype=th.float32),
            "instruments": th.zeros((2, 26), dtype=th.float32),
            "prev_action": th.zeros((2, 17), dtype=th.float32),
            "mission": th.tensor(
                [
                    [2.0, 33.0, 1333.0, 177.0, 1.0, 0.0, 1000.0, 10.0, 100.0, 0.1, 2.0, 5000.0, 0.0, 0.0, 120.0, -45.0, 30.0, 21.0, 1.0, 11.0, 0.0],
                    [3.0, 33.0, 1333.0, 177.0, 1.0, 0.0, 1000.0, 10.0, 100.0, 0.1, 2.0, 5000.0, 0.0, 0.0, 120.0, -45.0, 30.0, 22.0, 2.0, 12.0, 11.0],
                ],
                dtype=th.float32,
            ),
        }
        with th.no_grad():
            actions, values, log_prob = policy.forward(obs, deterministic=True)

        self.assertEqual(tuple(actions.shape), (2, 17))
        self.assertEqual(tuple(values.shape), (2, 1))
        self.assertEqual(tuple(log_prob.shape), (2,))

        stats = policy.get_hmoe_route_stats()
        self.assertAlmostEqual(stats["hmoe/fam/form"], 1.0, places=6)
        self.assertAlmostEqual(stats["hmoe/sub/form/lead"], 0.5, places=6)
        self.assertAlmostEqual(stats["hmoe/sub/form/wingman"], 0.5, places=6)

    def test_predict_path_uses_observation_aware_routing(self) -> None:
        policy = self._make_policy()
        obs = {
            "image": th.zeros((1, 1, 8, 8), dtype=th.float32),
            "instruments": th.zeros((1, 26), dtype=th.float32),
            "prev_action": th.zeros((1, 17), dtype=th.float32),
            "mission": th.tensor(
                [[3.0, 33.0, 1333.0, 177.0, 1.0, 0.0, 1000.0, 10.0, 100.0, 0.1, 2.0, 5000.0, 0.0, 0.0, 120.0, -45.0, 30.0, 22.0, 2.0, 12.0, 11.0]],
                dtype=th.float32,
            ),
        }
        with th.no_grad():
            dist = policy.get_distribution(obs)
            actions = dist.get_actions(deterministic=True)

        self.assertEqual(tuple(actions.shape), (1, 17))
        stats = policy.get_hmoe_route_stats()
        self.assertAlmostEqual(stats["hmoe/fam/form"], 1.0, places=6)
        self.assertAlmostEqual(stats["hmoe/sub/form/wingman"], 1.0, places=6)

    def test_air_combat_c2_roe_route_stats_use_combat_weapons_family(self) -> None:
        observation_space = spaces.Dict(
            {
                "image": spaces.Box(low=0.0, high=1.0, shape=(1, 8, 8), dtype=float),
                "instruments": spaces.Box(low=-1.0, high=1.0, shape=(26,), dtype=float),
                "mission": spaces.Box(low=-1.0e6, high=1.0e6, shape=(20,), dtype=float),
                "prev_action": spaces.Box(low=-1.0, high=1.0, shape=(17,), dtype=float),
            }
        )
        policy = HierarchicalMoEExecutionPolicy(
            observation_space,
            spaces.Box(low=-1.0, high=1.0, shape=(17,), dtype=float),
            _ConstantSchedule(),
            net_arch={"pi": [32], "vf": [32]},
        )
        obs = {
            "image": th.zeros((3, 1, 8, 8), dtype=th.float32),
            "instruments": th.zeros((3, 26), dtype=th.float32),
            "prev_action": th.zeros((3, 17), dtype=th.float32),
            "mission": th.tensor(
                [
                    [2.0, 0.0, 7000.0, 230.0, 2.0, 2.0, 1.0, 101.0, 9001.0, 301.0, 301.0, 0.0, 12.5, 3.0, 2.0, 1.0, 1.0, 0.0, 0.0, 1.0],
                    [2.0, 0.0, 7000.0, 230.0, 2.0, 1.0, 1.0, 101.0, 9001.0, 301.0, 301.0, 0.0, 12.5, 3.0, 3.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                    [2.0, 0.0, 7000.0, 230.0, 2.0, 2.0, 1.0, 101.0, 9001.0, 301.0, 301.0, 0.0, 12.5, 3.0, 2.0, 1.0, 0.0, 1.0, 1.0, 1.0],
                ],
                dtype=th.float32,
            ),
        }

        with th.no_grad():
            actions, values, log_prob = policy.forward(obs, deterministic=True)

        self.assertEqual(tuple(actions.shape), (3, 17))
        self.assertEqual(tuple(values.shape), (3, 1))
        self.assertEqual(tuple(log_prob.shape), (3,))
        stats = policy.get_hmoe_route_stats()
        self.assertAlmostEqual(stats["hmoe/fam/combat"], 1.0, places=6)
        self.assertAlmostEqual(stats["hmoe/sub/combat/first_shot"], 1.0 / 3.0, places=6)
        self.assertAlmostEqual(stats["hmoe/sub/combat/hold"], 1.0 / 3.0, places=6)
        self.assertAlmostEqual(stats["hmoe/sub/combat/assess"], 1.0 / 3.0, places=6)

    def test_nonfinite_probe_preserves_observation_aware_routing(self) -> None:
        policy = self._make_policy()
        probe = NonFiniteTrainingProbe(report_path="/tmp/hmoe_nonfinite_probe_test.json", enabled=True)

        class _Model:
            def __init__(self, policy) -> None:
                self.policy = policy
                self.device = th.device("cpu")
                self.policy_kwargs = {}
                self._excluded_save_params = lambda: []

        probe._patch_policy(_Model(policy).policy)
        obs = {
            "image": th.zeros((1, 1, 8, 8), dtype=th.float32),
            "instruments": th.zeros((1, 26), dtype=th.float32),
            "prev_action": th.zeros((1, 17), dtype=th.float32),
            "mission": th.tensor(
                [[3.0, 33.0, 1333.0, 177.0, 1.0, 0.0, 1000.0, 10.0, 100.0, 0.1, 2.0, 5000.0, 0.0, 0.0, 120.0, -45.0, 30.0, 22.0, 2.0, 12.0, 11.0]],
                dtype=th.float32,
            ),
        }

        with th.no_grad():
            dist = policy.get_distribution(obs)
            actions = dist.get_actions(deterministic=True)

        self.assertEqual(tuple(actions.shape), (1, 17))
        stats = policy.get_hmoe_route_stats()
        self.assertAlmostEqual(stats["hmoe/fam/form"], 1.0, places=6)
        self.assertAlmostEqual(stats["hmoe/sub/form/wingman"], 1.0, places=6)

    def test_hmoe_heads_start_as_zero_residuals(self) -> None:
        policy = self._make_policy()
        for head in policy.hmoe_head_bank.family_heads:
            self.assertTrue(th.allclose(head.weight.detach(), th.zeros_like(head.weight)))
            self.assertTrue(th.allclose(head.bias.detach(), th.zeros_like(head.bias)))
        for family_subheads in policy.hmoe_head_bank.subexpert_heads:
            for head in family_subheads:
                self.assertTrue(th.allclose(head.weight.detach(), th.zeros_like(head.weight)))
                self.assertTrue(th.allclose(head.bias.detach(), th.zeros_like(head.bias)))

    def test_residual_gate_warms_up_from_zero(self) -> None:
        policy = self._make_policy()
        self.assertAlmostEqual(policy._hmoe_residual_gate, 0.0, places=6)
        policy.set_hmoe_training_progress(1.0)
        self.assertAlmostEqual(policy._hmoe_residual_gate, 0.0, places=6)

        policy.set_hmoe_training_progress(0.925)
        self.assertAlmostEqual(policy._hmoe_residual_gate, 0.5, places=6)

        policy.set_hmoe_training_progress(0.85)
        self.assertAlmostEqual(policy._hmoe_residual_gate, 1.0, places=6)

    def test_safe_action_bias_keeps_hmoe_residual_heads_zero(self) -> None:
        policy = self._make_policy()

        class _Model:
            pass

        model = _Model()
        model.policy = policy
        apply_safe_action_bias(model, "full", "scenarios/combined/cruise_to_landing_continuous_train_v1.json")

        # Shared action head keeps the realistic initialization bias.
        self.assertGreater(float(policy.action_net.bias[3].detach().cpu().item()), 0.0)

        # Routed residual heads stay neutral so they do not amplify the initial policy.
        for head in policy.hmoe_head_bank.family_heads:
            self.assertTrue(th.allclose(head.bias.detach(), th.zeros_like(head.bias)))
        for family_subheads in policy.hmoe_head_bank.subexpert_heads:
            for head in family_subheads:
                self.assertTrue(th.allclose(head.bias.detach(), th.zeros_like(head.bias)))

    def test_safe_action_bias_zeroes_naval_station_action_head(self) -> None:
        observation_space = spaces.Dict(
            {
                "instruments": spaces.Box(low=-1.0, high=1.0, shape=(42,), dtype=float),
                "contacts": spaces.Box(low=-1.0, high=1.0, shape=(10, 5), dtype=float),
                "rwr": spaces.Box(low=-1.0, high=1.0, shape=(4, 4), dtype=float),
                "mission": spaces.Box(low=-1.0e6, high=1.0e6, shape=(23,), dtype=float),
                "proprio": spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=float),
            }
        )
        action_space = spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=float)
        policy = SquashedMultiInputPolicy(
            observation_space,
            action_space,
            _ConstantSchedule(),
            features_extractor_class=TransformerExtractor,
            features_extractor_kwargs={"features_dim": 32, "n_heads": 4, "n_layers": 1, "use_checkpointing": False},
            net_arch={"pi": [32], "vf": [32]},
        )
        with th.no_grad():
            policy.action_net.weight.fill_(0.25)
            policy.action_net.bias.fill_(0.1)

        class _Model:
            pass

        model = _Model()
        model.policy = policy
        apply_safe_action_bias(model, "naval_station3", "scenarios/naval/ddg51_take1_screen_threat_roe_v1.json")

        self.assertTrue(th.allclose(policy.action_net.weight.detach(), th.zeros_like(policy.action_net.weight)))
        self.assertTrue(th.allclose(policy.action_net.bias.detach(), th.zeros_like(policy.action_net.bias)))

    def test_air_combat_hybrid_policy_uses_mixed_distribution_over_flat_transport(self) -> None:
        observation_space = spaces.Dict(
            {
                "instruments": spaces.Box(low=-1.0, high=1.0, shape=(42,), dtype=float),
                "contacts": spaces.Box(low=-1.0, high=1.0, shape=(10, 5), dtype=float),
                "rwr": spaces.Box(low=-1.0, high=1.0, shape=(4, 4), dtype=float),
                "mission": spaces.Box(low=-1.0e6, high=1.0e6, shape=(21,), dtype=float),
                "proprio": spaces.Box(low=-1.0, high=7.0, shape=(12,), dtype=float),
            }
        )
        action_space = make_action_space("air_combat_hybrid_v1")
        policy = HierarchicalMoEExecutionPolicy(
            observation_space,
            action_space,
            _ConstantSchedule(),
            features_extractor_class=TransformerExtractor,
            features_extractor_kwargs={"features_dim": 32, "n_heads": 4, "n_layers": 1, "use_checkpointing": False},
            net_arch={"pi": [32], "vf": [32]},
            hybrid_action_spec="air_combat_hybrid_v1",
            log_std_init=-1.2,
        )
        obs = {
            "instruments": th.zeros((2, 42), dtype=th.float32),
            "contacts": th.zeros((2, 10, 5), dtype=th.float32),
            "rwr": th.zeros((2, 4, 4), dtype=th.float32),
            "mission": th.zeros((2, 21), dtype=th.float32),
            "proprio": th.zeros((2, 12), dtype=th.float32),
        }

        with th.no_grad():
            actions, values, log_prob = policy.forward(obs, deterministic=True)
            eval_values, eval_log_prob, entropy = policy.evaluate_actions(obs, actions)

        self.assertEqual(int(policy.action_net.out_features), 20)
        self.assertEqual(int(policy.log_std.shape[0]), 6)
        self.assertTrue(th.allclose(policy.log_std.detach(), th.full_like(policy.log_std.detach(), -1.2)))
        self.assertEqual(tuple(actions.shape), (2, 12))
        self.assertEqual(tuple(values.shape), (2, 1))
        self.assertEqual(tuple(log_prob.shape), (2,))
        self.assertEqual(tuple(eval_values.shape), (2, 1))
        self.assertEqual(tuple(eval_log_prob.shape), (2,))
        self.assertTrue(th.isfinite(actions).all())
        self.assertTrue(th.isfinite(log_prob).all())
        self.assertTrue(th.isfinite(eval_log_prob).all())
        self.assertIsNotNone(entropy)
        self.assertEqual(tuple(entropy.shape), (2,))
        self.assertTrue(th.isfinite(entropy).all())
        self.assertTrue(th.all(entropy > 0.0))
        for idx in (6, 7, 8, 9, 10):
            self.assertTrue(th.all((actions[:, idx] == 0.0) | (actions[:, idx] == 1.0)))
        self.assertTrue(th.all(actions[:, 11] == th.round(actions[:, 11])))
        self.assertTrue(th.all(actions[:, 11] >= 0.0))
        self.assertTrue(th.all(actions[:, 11] <= 7.0))

    def test_air_combat_hybrid_fire_event_mask_blocks_deterministic_and_stochastic_fire(self) -> None:
        params = th.zeros((4, 20), dtype=th.float32)
        params[:, 9] = 8.0
        params[:, 11] = -2.0
        dist = self._make_air_combat_hybrid_distribution(params, fire_mask=th.zeros((4,), dtype=th.bool))

        deterministic_actions = dist.get_actions(deterministic=True)
        stochastic_actions = dist.get_actions(deterministic=False)

        self.assertTrue(th.all(deterministic_actions[:, 9] == 0.0))
        self.assertTrue(th.all(stochastic_actions[:, 9] == 0.0))

    def test_air_combat_hybrid_fire_event_logprob_and_entropy_are_finite_when_masked(self) -> None:
        params = th.zeros((2, 20), dtype=th.float32)
        params[:, 9] = 8.0
        params[:, 11] = -2.0
        dist = self._make_air_combat_hybrid_distribution(params, fire_mask=th.zeros((2,), dtype=th.bool))
        hold_actions = th.zeros((2, 12), dtype=th.float32)
        fire_actions = hold_actions.clone()
        fire_actions[:, 9] = 1.0

        hold_log_prob = dist.log_prob(hold_actions)
        fire_log_prob = dist.log_prob(fire_actions)
        entropy = dist.entropy()

        self.assertTrue(th.isfinite(hold_log_prob).all())
        self.assertTrue(th.isfinite(fire_log_prob).all())
        self.assertTrue(th.isfinite(entropy).all())
        self.assertTrue(th.all(fire_log_prob < hold_log_prob - 1.0e6))

    def test_air_combat_hybrid_fire_event_deterministic_uses_hold_fire_argmax(self) -> None:
        params = th.zeros((1, 20), dtype=th.float32)
        params[:, 9] = 0.25
        params[:, 11] = 2.0
        dist = self._make_air_combat_hybrid_distribution(params, fire_mask=th.ones((1,), dtype=th.bool))

        actions = dist.get_actions(deterministic=True)

        self.assertEqual(float(actions[0, 9]), 0.0)

    def test_air_combat_hybrid_non_event_binary_heads_still_use_bernoulli_semantics(self) -> None:
        params = th.zeros((1, 20), dtype=th.float32)
        params[:, 6] = -1.0
        params[:, 7] = 1.0
        params[:, 8] = 2.0
        params[:, 9] = -3.0
        params[:, 10] = -2.0
        params[:, 11] = 0.0
        dist = self._make_air_combat_hybrid_distribution(params, fire_mask=th.ones((1,), dtype=th.bool))

        actions = dist.get_actions(deterministic=True)

        self.assertEqual(float(actions[0, 6]), 0.0)
        self.assertEqual(float(actions[0, 7]), 1.0)
        self.assertEqual(float(actions[0, 8]), 1.0)
        self.assertEqual(float(actions[0, 10]), 0.0)

    def test_air_combat_c2_roe_mission_mask_plumbs_into_policy_distribution(self) -> None:
        observation_space = spaces.Dict(
            {
                "instruments": spaces.Box(low=-1.0, high=1.0, shape=(42,), dtype=float),
                "contacts": spaces.Box(low=-1.0, high=1.0, shape=(10, 5), dtype=float),
                "rwr": spaces.Box(low=-1.0, high=1.0, shape=(4, 4), dtype=float),
                "mission": spaces.Box(low=-1.0e6, high=1.0e6, shape=(20,), dtype=float),
                "proprio": spaces.Box(low=-1.0, high=7.0, shape=(12,), dtype=float),
            }
        )
        policy = HierarchicalMoEExecutionPolicy(
            observation_space,
            make_action_space("air_combat_hybrid_v1"),
            _ConstantSchedule(),
            features_extractor_class=TransformerExtractor,
            features_extractor_kwargs={"features_dim": 32, "n_heads": 4, "n_layers": 1, "use_checkpointing": False},
            net_arch={"pi": [32], "vf": [32]},
            hybrid_action_spec="air_combat_hybrid_v1",
        )
        with th.no_grad():
            policy.action_net.weight.zero_()
            policy.action_net.bias.zero_()
            policy.action_net.bias[9] = 8.0
            policy.action_net.bias[11] = -2.0
        mission = th.zeros((2, 20), dtype=th.float32)
        mission[1, 5] = 2.0
        mission[1, 6] = 1.0
        mission[1, 14] = 2.0
        mission[1, 15] = 1.0
        mission[1, 16] = 1.0
        mission[1, 19] = 1.0
        obs = {
            "instruments": th.zeros((2, 42), dtype=th.float32),
            "contacts": th.zeros((2, 10, 5), dtype=th.float32),
            "rwr": th.zeros((2, 4, 4), dtype=th.float32),
            "mission": mission,
            "proprio": th.zeros((2, 12), dtype=th.float32),
        }

        with th.no_grad():
            actions = policy.get_distribution(obs).get_actions(deterministic=True)

        self.assertEqual(float(actions[0, 9]), 0.0)
        self.assertEqual(float(actions[1, 9]), 1.0)

    def test_air_combat_c2_roe_v2_explicit_fire_mask_plumbs_into_policy_distribution(self) -> None:
        mode = "air_combat_c2_roe_v2"
        mission_dim = mission_observation_dim(mode)
        observation_space = spaces.Dict(
            {
                "instruments": spaces.Box(low=-1.0, high=1.0, shape=(42,), dtype=float),
                "contacts": spaces.Box(low=-1.0, high=1.0, shape=(10, 5), dtype=float),
                "rwr": spaces.Box(low=-1.0, high=1.0, shape=(4, 4), dtype=float),
                "mission": spaces.Box(low=-1.0e6, high=1.0e6, shape=(mission_dim,), dtype=float),
                "proprio": spaces.Box(low=-1.0, high=7.0, shape=(12,), dtype=float),
            }
        )
        policy = HierarchicalMoEExecutionPolicy(
            observation_space,
            make_action_space("air_combat_hybrid_v1"),
            _ConstantSchedule(),
            features_extractor_class=TransformerExtractor,
            features_extractor_kwargs={"features_dim": 32, "n_heads": 4, "n_layers": 1, "use_checkpointing": False},
            net_arch={"pi": [32], "vf": [32]},
            hybrid_action_spec="air_combat_hybrid_v1",
        )
        with th.no_grad():
            policy.action_net.weight.zero_()
            policy.action_net.bias.zero_()
            policy.action_net.bias[9] = 8.0
            policy.action_net.bias[11] = -2.0
        mission = th.zeros((2, mission_dim), dtype=th.float32)
        mission[1, mission_observation_field_index(mode, "fire_mask_open")] = 1.0
        obs = {
            "instruments": th.zeros((2, 42), dtype=th.float32),
            "contacts": th.zeros((2, 10, 5), dtype=th.float32),
            "rwr": th.zeros((2, 4, 4), dtype=th.float32),
            "mission": mission,
            "proprio": th.zeros((2, 12), dtype=th.float32),
        }

        with th.no_grad():
            actions = policy.get_distribution(obs).get_actions(deterministic=True)

        self.assertEqual(float(actions[0, 9]), 0.0)
        self.assertEqual(float(actions[1, 9]), 1.0)

    def test_safe_action_bias_initializes_air_combat_hybrid_switch_logits(self) -> None:
        observation_space = spaces.Dict(
            {
                "instruments": spaces.Box(low=-1.0, high=1.0, shape=(42,), dtype=float),
                "contacts": spaces.Box(low=-1.0, high=1.0, shape=(10, 5), dtype=float),
                "rwr": spaces.Box(low=-1.0, high=1.0, shape=(4, 4), dtype=float),
                "mission": spaces.Box(low=-1.0e6, high=1.0e6, shape=(21,), dtype=float),
                "proprio": spaces.Box(low=-1.0, high=7.0, shape=(12,), dtype=float),
            }
        )
        policy = HierarchicalMoEExecutionPolicy(
            observation_space,
            make_action_space("air_combat_hybrid_v1"),
            _ConstantSchedule(),
            features_extractor_class=TransformerExtractor,
            features_extractor_kwargs={"features_dim": 32, "n_heads": 4, "n_layers": 1, "use_checkpointing": False},
            net_arch={"pi": [32], "vf": [32]},
            hybrid_action_spec="air_combat_hybrid_v1",
        )
        with th.no_grad():
            policy.action_net.weight.fill_(0.25)
            policy.action_net.bias.fill_(0.1)

        class _Model:
            pass

        model = _Model()
        model.policy = policy
        apply_safe_action_bias(
            model,
            "air_combat_hybrid_v1",
            "scenarios/air_combat/1v1/air_combat_1v1_stage1_bvr_nonmaneuvering_target_v1.json",
        )

        bias = policy.action_net.bias.detach().cpu()
        self.assertTrue(th.allclose(policy.action_net.weight.detach(), th.zeros_like(policy.action_net.weight)))
        self.assertGreater(float(bias[6]), 0.0)
        self.assertGreater(float(bias[8]), 0.0)
        self.assertLess(float(bias[7]), -3.0)
        self.assertLess(float(bias[9]), -5.0)
        self.assertLess(float(bias[9]), 0.0)
        self.assertLess(float(bias[10]), 0.0)
        self.assertGreater(float(bias[11]), float(bias[9]))
        self.assertGreater(float(bias[13]), float(bias[12]))
        for head in policy.hmoe_head_bank.family_heads:
            self.assertTrue(th.allclose(head.bias.detach(), th.zeros_like(head.bias)))

    def test_initialize_hmoe_from_shared_action_head_preserves_zero_residual_bootstrap(self) -> None:
        policy = self._make_policy()
        with th.no_grad():
            policy.action_net.weight.fill_(0.25)
            policy.action_net.bias.fill_(0.1)
            policy.hmoe_head_bank.family_heads[0].weight.fill_(1.0)
            policy.hmoe_head_bank.family_heads[0].bias.fill_(1.0)
            policy.hmoe_head_bank.subexpert_heads[0][0].weight.fill_(1.0)
            policy.hmoe_head_bank.subexpert_heads[0][0].bias.fill_(1.0)

        policy.initialize_hmoe_from_shared_action_head()

        for head in policy.hmoe_head_bank.family_heads:
            self.assertTrue(th.allclose(head.weight.detach(), th.zeros_like(head.weight)))
            self.assertTrue(th.allclose(head.bias.detach(), th.zeros_like(head.bias)))
        for family_subheads in policy.hmoe_head_bank.subexpert_heads:
            for head in family_subheads:
                self.assertTrue(th.allclose(head.weight.detach(), th.zeros_like(head.weight)))
                self.assertTrue(th.allclose(head.bias.detach(), th.zeros_like(head.bias)))

    def test_initialize_hmoe_from_shared_action_head_zeroes_hybrid_event_credit_head(self) -> None:
        policy = self._make_air_combat_hybrid_policy(hybrid_event_credit_head_lr_scale=6.0)
        assert policy.hybrid_event_credit_head is not None
        with th.no_grad():
            policy.hybrid_event_credit_head.weight.fill_(1.0)
            policy.hybrid_event_credit_head.bias.fill_(1.0)

        policy.initialize_hmoe_from_shared_action_head()

        self.assertTrue(
            th.allclose(
                policy.hybrid_event_credit_head.weight.detach(),
                th.zeros_like(policy.hybrid_event_credit_head.weight),
            )
        )
        self.assertTrue(
            th.allclose(
                policy.hybrid_event_credit_head.bias.detach(),
                th.zeros_like(policy.hybrid_event_credit_head.bias),
            )
        )

    def test_hmoe_parameter_stats_report_nonzero_fraction(self) -> None:
        policy = self._make_policy()
        stats = policy.get_hmoe_parameter_stats()
        self.assertAlmostEqual(stats["hmoe_params/family/nonzero_frac"], 0.0, places=6)
        self.assertAlmostEqual(stats["hmoe_params/sub/nonzero_frac"], 0.0, places=6)

        with th.no_grad():
            policy.hmoe_head_bank.family_heads[0].weight.fill_(0.5)
            policy.hmoe_head_bank.subexpert_heads[0][0].weight.fill_(0.5)
        stats = policy.get_hmoe_parameter_stats()
        self.assertGreater(stats["hmoe_params/family/nonzero_frac"], 0.0)
        self.assertGreater(stats["hmoe_params/sub/nonzero_frac"], 0.0)

    def test_transformer_extractor_prefers_bf16_when_supported(self) -> None:
        observation_space = spaces.Dict(
            {
                "instruments": spaces.Box(low=-1.0, high=1.0, shape=(26,), dtype=float),
                "contacts": spaces.Box(low=-1.0, high=1.0, shape=(10, 5), dtype=float),
                "rwr": spaces.Box(low=-1.0, high=1.0, shape=(4, 4), dtype=float),
                "mission": spaces.Box(low=-1.0, high=1.0, shape=(21,), dtype=float),
                "proprio": spaces.Box(low=-1.0, high=1.0, shape=(17,), dtype=float),
            }
        )
        extractor = TransformerExtractor(
            observation_space,
            features_dim=32,
            n_heads=4,
            n_layers=1,
            use_amp=True,
            use_checkpointing=False,
        )

        with mock.patch("torch.cuda.is_available", return_value=True), mock.patch(
            "torch.cuda.is_bf16_supported", return_value=True
        ):
            self.assertTrue(extractor._autocast_enabled_for_forward())
            self.assertEqual(extractor._autocast_dtype(), th.bfloat16)

        extractor_fp16 = TransformerExtractor(
            observation_space,
            features_dim=32,
            n_heads=4,
            n_layers=1,
            use_amp=True,
            amp_dtype="fp16",
            use_checkpointing=False,
        )
        self.assertEqual(extractor_fp16._autocast_dtype(), th.float16)

    def test_transformer_observation_preprocessing_compresses_large_scales(self) -> None:
        observations = {
            "instruments": th.tensor(
                [[
                    180.0, 0.7, 6800.0, 240.0, -12.0, 8.0, 2.0, 5.0, -15.0, 270.0,
                    1.2, 0.8, 12.0, -4.0, 6.0, 92.0, 4200.0, 34708.0, 1.0, 0.2,
                    0.1, 185.0, 7200.0, 170.0, 31.2, 121.4, 110.0, 90.0, -4.0, 145.0,
                    268.0, 12.0, 300.0, 24.0, 1.0, 35.0, 1.0, 4.0, 0.3, -0.2, 1.0, 7200.0,
                ]],
                dtype=th.float32,
            ),
            "contacts": th.tensor(
                [[[34055.0, 190.0, 12.0, -320.0, 3.5]] * 10],
                dtype=th.float32,
            ),
            "rwr": th.tensor(
                [[[270.0, 8.0, 1.0, 0.0]] * 4],
                dtype=th.float32,
            ),
            "mission": th.tensor(
                [[
                    3.0, 275.0, 7600.0, 175.0, 2.0, 1.0, 17423.0, -135.0, -1700.0, 0.8,
                    28.0, 17423.0, 35.0, 9200.0, 2.0, 1.0, 30.0, 2.0, 120.0, -80.0,
                    35.0, 21.0, 2.0, 12.0, 11.0,
                ]],
                dtype=th.float32,
            ),
            "proprio": th.tensor([[0.2] * 17], dtype=th.float32),
        }

        processed = preprocess_transformer_observations(observations)
        self.assertTrue(th.isfinite(processed["instruments"]).all())
        self.assertTrue(th.isfinite(processed["contacts"]).all())
        self.assertTrue(th.isfinite(processed["rwr"]).all())
        self.assertTrue(th.isfinite(processed["mission"]).all())

        self.assertLess(float(processed["instruments"].abs().max().item()), 6.0)
        self.assertLess(float(processed["contacts"].abs().max().item()), 6.0)
        self.assertLess(float(processed["rwr"].abs().max().item()), 6.0)
        self.assertLess(float(processed["mission"].abs().max().item()), 6.0)

        self.assertAlmostEqual(float(processed["instruments"][0, 17].item()), float(th.log1p(th.tensor(34.708)).item()), places=5)
        self.assertAlmostEqual(float(processed["contacts"][0, 0, 0].item()), float(th.log1p(th.tensor(34.055)).item()), places=5)
        self.assertAlmostEqual(float(processed["mission"][0, 6].item()), float(th.log1p(th.tensor(17.423)).item()), places=5)
        self.assertAlmostEqual(float(processed["rwr"][0, 0, 1].item()), 4.0, places=6)

    def test_transformer_preprocesses_naval_screen_station_mission_by_domain_fields(self) -> None:
        mode = "naval_screen_station_v1"
        mission = th.zeros((1, 23), dtype=th.float32)
        mission[0, mission_observation_field_index(mode, "command_code")] = 3.0
        mission[0, mission_observation_field_index(mode, "target_heading_deg")] = 90.0
        mission[0, mission_observation_field_index(mode, "target_speed_mps")] = 10.29
        mission[0, mission_observation_field_index(mode, "station_radius_m")] = 14816.0
        mission[0, mission_observation_field_index(mode, "station_bearing_deg")] = 90.0
        mission[0, mission_observation_field_index(mode, "station_error_m")] = 4040.0
        mission[0, mission_observation_field_index(mode, "station_error_norm")] = 0.306
        mission[0, mission_observation_field_index(mode, "screen_separation_m")] = 14816.0
        mission[0, mission_observation_field_index(mode, "screen_separation_error_m")] = 1618.0
        mission[0, mission_observation_field_index(mode, "target_contact_present")] = 1.0
        mission[0, mission_observation_field_index(mode, "support_track_present")] = 1.0
        mission[0, mission_observation_field_index(mode, "report_chain_seen")] = 0.5
        mission[0, mission_observation_field_index(mode, "roe_state")] = 1.0
        mission[0, mission_observation_field_index(mode, "assigned_target_id")] = 580.0

        processed = preprocess_mission_tensor(mission)

        self.assertTrue(th.isfinite(processed).all())
        self.assertLess(float(processed.abs().max().item()), 6.0)
        self.assertAlmostEqual(
            float(processed[0, mission_observation_field_index(mode, "station_bearing_deg")].item()),
            0.5,
            places=6,
        )
        self.assertAlmostEqual(
            float(processed[0, mission_observation_field_index(mode, "station_radius_m")].item()),
            float(th.log1p(th.tensor(14.816)).item()),
            places=5,
        )
        self.assertAlmostEqual(
            float(processed[0, mission_observation_field_index(mode, "station_error_m")].item()),
            float(th.log1p(th.tensor(4.04)).item()),
            places=5,
        )
        self.assertAlmostEqual(
            float(processed[0, mission_observation_field_index(mode, "station_error_norm")].item()),
            0.306,
            places=6,
        )
        self.assertAlmostEqual(
            float(processed[0, mission_observation_field_index(mode, "target_contact_present")].item()),
            1.0,
            places=6,
        )
        self.assertAlmostEqual(
            float(processed[0, mission_observation_field_index(mode, "report_chain_seen")].item()),
            0.5,
            places=6,
        )

    def test_transformer_extractor_forward_stays_finite_on_large_observations(self) -> None:
        observation_space = spaces.Dict(
            {
                "instruments": spaces.Box(low=-1.0e6, high=1.0e6, shape=(42,), dtype=float),
                "contacts": spaces.Box(low=-1.0e6, high=1.0e6, shape=(10, 5), dtype=float),
                "rwr": spaces.Box(low=-1.0e6, high=1.0e6, shape=(4, 4), dtype=float),
                "mission": spaces.Box(low=-1.0e6, high=1.0e6, shape=(25,), dtype=float),
                "proprio": spaces.Box(low=-1.0, high=1.0, shape=(17,), dtype=float),
            }
        )
        extractor = TransformerExtractor(
            observation_space,
            features_dim=32,
            n_heads=4,
            n_layers=1,
            use_amp=False,
            use_checkpointing=False,
        )
        observations = {
            "instruments": th.full((2, 42), 25000.0, dtype=th.float32),
            "contacts": th.full((2, 10, 5), 34055.0, dtype=th.float32),
            "rwr": th.full((2, 4, 4), 270.0, dtype=th.float32),
            "mission": th.full((2, 25), 17423.0, dtype=th.float32),
            "proprio": th.zeros((2, 17), dtype=th.float32),
        }

        with th.no_grad():
            features = extractor(observations)

        self.assertEqual(tuple(features.shape), (2, 32))
        self.assertTrue(th.isfinite(features).all())

    def test_temporal_transformer_extractor_forward_is_finite(self) -> None:
        history_len = 4
        observation_space = spaces.Dict(
            {
                "instruments": spaces.Box(low=-np.inf, high=np.inf, shape=(42,), dtype=np.float32),
                "contacts": spaces.Box(low=-np.inf, high=np.inf, shape=(10, 5), dtype=np.float32),
                "rwr": spaces.Box(low=-np.inf, high=np.inf, shape=(4, 4), dtype=np.float32),
                "mission": spaces.Box(low=-np.inf, high=np.inf, shape=(21,), dtype=np.float32),
                "proprio": spaces.Box(low=-1.0, high=1.0, shape=(17,), dtype=np.float32),
                "instruments_history": spaces.Box(
                    low=-np.inf,
                    high=np.inf,
                    shape=(history_len, 42),
                    dtype=np.float32,
                ),
                "contacts_history": spaces.Box(
                    low=-np.inf,
                    high=np.inf,
                    shape=(history_len, 10, 5),
                    dtype=np.float32,
                ),
                "rwr_history": spaces.Box(
                    low=-np.inf,
                    high=np.inf,
                    shape=(history_len, 4, 4),
                    dtype=np.float32,
                ),
                "mission_history": spaces.Box(
                    low=-np.inf,
                    high=np.inf,
                    shape=(history_len, 21),
                    dtype=np.float32,
                ),
                "proprio_history": spaces.Box(
                    low=-np.inf,
                    high=np.inf,
                    shape=(history_len, 17),
                    dtype=np.float32,
                ),
            }
        )
        extractor = TemporalTransformerExtractor(
            observation_space,
            features_dim=32,
            n_heads=4,
            n_layers=1,
            temporal_n_layers=1,
            use_checkpointing=False,
        )
        observations = {
            "instruments_history": th.randn((2, history_len, 42), dtype=th.float32),
            "contacts_history": th.randn((2, history_len, 10, 5), dtype=th.float32),
            "rwr_history": th.randn((2, history_len, 4, 4), dtype=th.float32),
            "mission_history": th.randn((2, history_len, 21), dtype=th.float32),
            "proprio_history": th.randn((2, history_len, 17), dtype=th.float32),
        }

        features = extractor(observations)

        self.assertEqual(tuple(features.shape), (2, 32))
        self.assertTrue(th.isfinite(features).all())


if __name__ == "__main__":
    unittest.main()
