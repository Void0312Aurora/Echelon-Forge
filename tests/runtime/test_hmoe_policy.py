from __future__ import annotations

import unittest

import torch as th
from gymnasium import spaces

from python.rl.nonfinite_probe import NonFiniteTrainingProbe
from python.rl.policies import HierarchicalMoEExecutionPolicy
from train import apply_safe_action_bias


class _ConstantSchedule:
    def __call__(self, progress_remaining: float) -> float:
        return 3.0e-4


class HMoEPolicyTests(unittest.TestCase):
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

    def test_initialize_hmoe_from_shared_action_head_bootstraps_family_heads(self) -> None:
        policy = self._make_policy()
        with th.no_grad():
            policy.action_net.weight.fill_(0.25)
            policy.action_net.bias.fill_(0.1)
            policy.hmoe_head_bank.family_heads[0].weight.zero_()
            policy.hmoe_head_bank.family_heads[0].bias.zero_()
            policy.hmoe_head_bank.subexpert_heads[0][0].weight.fill_(1.0)
            policy.hmoe_head_bank.subexpert_heads[0][0].bias.fill_(1.0)

        policy.initialize_hmoe_from_shared_action_head()

        for head in policy.hmoe_head_bank.family_heads:
            self.assertTrue(th.allclose(head.weight.detach(), policy.action_net.weight.detach()))
            self.assertTrue(th.allclose(head.bias.detach(), policy.action_net.bias.detach()))
        for family_subheads in policy.hmoe_head_bank.subexpert_heads:
            for head in family_subheads:
                self.assertTrue(th.allclose(head.weight.detach(), th.zeros_like(head.weight)))
                self.assertTrue(th.allclose(head.bias.detach(), th.zeros_like(head.bias)))

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


if __name__ == "__main__":
    unittest.main()
