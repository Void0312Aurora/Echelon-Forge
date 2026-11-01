from __future__ import annotations

import unittest

import numpy as np

from python.training.cooperative_policy_dispatch import (
    CooperativePolicyDispatchError,
    CooperativeRouteLayout,
    CooperativeRoutePolicyDispatcher,
    resolve_cooperative_policy_models,
)


class _FakeEnv:
    def __init__(self, routes):
        self.routes = routes
        self.step_calls = 0
        self.last_actions = None

    def slot_indices_by_policy_route(self):
        return self.routes

    def step(self, actions):
        self.step_calls += 1
        self.last_actions = np.asarray(actions)
        return "obs", np.zeros(self.last_actions.shape[0]), np.zeros(self.last_actions.shape[0], dtype=bool), [{}]


class _FakeModel:
    def __init__(self, value: float):
        self.value = float(value)
        self.calls = []

    def predict(self, obs, deterministic=True):
        array = np.asarray(next(iter(obs.values()))) if isinstance(obs, dict) else np.asarray(obs)
        self.calls.append((array.copy(), bool(deterministic)))
        return np.full((array.shape[0], 2), self.value, dtype=np.float32), None


class CooperativePolicyDispatchTests(unittest.TestCase):
    def test_route_actions_are_scattered_and_world_steps_once(self):
        env = _FakeEnv({"leader": [0], "execution": [1, 2]})
        layout = CooperativeRouteLayout.from_env(env)
        leader = _FakeModel(1.0)
        execution = _FakeModel(2.0)
        dispatcher = CooperativeRoutePolicyDispatcher(
            {"leader": leader, "execution": execution}, layout
        )
        observation = {"state": np.zeros((3, 4), dtype=np.float32)}
        result = dispatcher.step(env, observation)

        self.assertEqual(env.step_calls, 1)
        np.testing.assert_array_equal(
            env.last_actions,
            np.asarray([[1.0, 1.0], [2.0, 2.0], [2.0, 2.0]], dtype=np.float32),
        )
        self.assertEqual(len(leader.calls), 1)
        self.assertEqual(leader.calls[0][0].shape, (1, 4))
        self.assertEqual(len(execution.calls), 1)
        self.assertEqual(execution.calls[0][0].shape, (2, 4))
        self.assertEqual(result[0], "obs")

    def test_route_layout_rejects_overlap_and_missing_slot(self):
        with self.assertRaises(CooperativePolicyDispatchError):
            CooperativeRouteLayout.from_env(_FakeEnv({"a": [0, 1], "b": [1]}))
        with self.assertRaises(CooperativePolicyDispatchError):
            CooperativeRouteLayout.from_env(_FakeEnv({"a": [0], "b": [2]}))

    def test_dispatch_rejects_missing_route_and_bad_action_shape(self):
        env = _FakeEnv({"leader": [0], "execution": [1]})
        layout = CooperativeRouteLayout.from_env(env)
        with self.assertRaises(CooperativePolicyDispatchError):
            CooperativeRoutePolicyDispatcher({"leader": _FakeModel(1.0)}, layout)

        class BadModel:
            def predict(self, obs, deterministic=True):
                return np.zeros((99, 2), dtype=np.float32), None

        dispatcher = CooperativeRoutePolicyDispatcher(
            {"leader": BadModel(), "execution": _FakeModel(2.0)}, layout
        )
        with self.assertRaises(CooperativePolicyDispatchError):
            dispatcher.predict(np.zeros((2, 4), dtype=np.float32))

    def test_policy_model_config_accepts_mapping_and_list(self):
        self.assertEqual(
            resolve_cooperative_policy_models(
                {"cooperative_execution": {"policy_models": {"leader": "a.zip"}}}
            ),
            {"leader": "a.zip"},
        )
        self.assertEqual(
            resolve_cooperative_policy_models(
                {
                    "cooperative_execution": {
                        "policy_models": [
                            {"route": "leader", "model_path": "a.zip"},
                            {"route": "execution", "model_path": "b.zip"},
                        ]
                    }
                }
            ),
            {"leader": "a.zip", "execution": "b.zip"},
        )
        with self.assertRaises(CooperativePolicyDispatchError):
            resolve_cooperative_policy_models(
                {"cooperative_execution": {"policy_models": [{"route": "leader"}]}}
            )


if __name__ == "__main__":
    unittest.main()
