from __future__ import annotations

import unittest
from unittest import mock

import torch as th
from gymnasium import spaces

from python.testing.runtime import ensure_repo_imports

ensure_repo_imports()

from python.models.transformer import TransformerExtractor, preprocess_transformer_observations
from python.rl.policy_algo.policies import HierarchicalMoEExecutionPolicy
from python.rl.support.nonfinite_probe import NonFiniteTrainingProbe
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


if __name__ == "__main__":
    unittest.main()
