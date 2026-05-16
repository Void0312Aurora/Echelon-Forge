from __future__ import annotations

import argparse
import unittest

import torch as th
from gymnasium import spaces

from python.testing.runtime import ensure_repo_imports

ensure_repo_imports()

from python.rl.policy_algo.policies import HierarchicalMoEExecutionPolicy
from train import maybe_initialize_hmoe_from_shared


class _ConstantSchedule:
    def __call__(self, progress_remaining: float) -> float:
        return 3.0e-4


class _DummyModel:
    def __init__(self, policy) -> None:
        self.policy = policy


class HMoETrainBootstrapTests(unittest.TestCase):
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

    def test_maybe_initialize_hmoe_from_shared_bootstraps_when_enabled(self) -> None:
        policy = self._make_policy()
        with th.no_grad():
            policy.action_net.weight.fill_(0.2)
            policy.action_net.bias.fill_(0.05)
        model = _DummyModel(policy)
        args = argparse.Namespace(resume_path=None, init_from=None)
        cfg = {"hmoe": {"bootstrap_from_shared_action_head": "auto"}}

        changed = maybe_initialize_hmoe_from_shared(model, train_config=cfg, args=args)

        self.assertTrue(changed)
        for head in policy.hmoe_head_bank.family_heads:
            self.assertTrue(th.allclose(head.weight.detach(), th.zeros_like(head.weight)))
            self.assertTrue(th.allclose(head.bias.detach(), th.zeros_like(head.bias)))

    def test_maybe_initialize_hmoe_from_shared_skips_resume(self) -> None:
        policy = self._make_policy()
        model = _DummyModel(policy)
        args = argparse.Namespace(resume_path="/tmp/model.zip", init_from=None)
        cfg = {"hmoe": {"bootstrap_from_shared_action_head": "auto"}}

        changed = maybe_initialize_hmoe_from_shared(model, train_config=cfg, args=args)

        self.assertFalse(changed)


if __name__ == "__main__":
    unittest.main()
