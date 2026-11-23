from __future__ import annotations

import unittest
from types import SimpleNamespace

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


class _EntryEnv(_FakeEnv):
    def __init__(self):
        super().__init__({"leader": [0], "execution": [1, 2]})
        self._slots = [SimpleNamespace(control_slot=None, max_steps=1) for _ in range(3)]
        self.closed = False

    def seed(self, seed):
        self.last_seed = seed

    def reset(self):
        return {"state": np.zeros((3, 4), dtype=np.float32)}

    def step(self, actions):
        super().step(actions)
        return self.reset(), np.zeros(3), np.ones(3, dtype=bool), [{} for _ in range(3)]

    def slot_control_slots(self):
        return [None] * 3

    def close(self):
        self.closed = True


def test_train_test_only_accepts_route_models_without_shared_checkpoint(tmp_path, monkeypatch):
    import train

    config = {
        "cooperative_execution": {
            "policy_models": {"leader": "leader.zip", "execution": "execution.zip"}
        }
    }
    bootstrap = SimpleNamespace(
        train_config=config,
        agent_layer="cooperative_execution",
        env_settings={},
        scenario_path="scene.json",
        train_cfg_path=str(tmp_path / "config.json"),
        exp_dir=str(tmp_path),
        run_name="routes",
        ckpt_dir=str(tmp_path),
        log_dir=str(tmp_path),
        training_seed=1,
        n_envs=1,
    )
    args = SimpleNamespace(test_only=True, resume_path=None)
    env = _EntryEnv()
    loaded_paths = []

    def load(path, **kwargs):
        loaded_paths.append(path)
        return _FakeModel(1.0 if path.endswith("leader.zip") else 2.0)

    monkeypatch.setattr(train, "build_train_arg_parser", lambda: SimpleNamespace(parse_args=lambda: args))
    monkeypatch.setattr(train, "prepare_training_bootstrap", lambda _args: bootstrap)
    monkeypatch.setattr(train, "print_training_bootstrap_summary", lambda _bootstrap: None)
    monkeypatch.setattr(train, "warn_execution_visual_rollout_memory", lambda _bootstrap: None)
    monkeypatch.setattr(train, "load_training_dependencies", lambda: SimpleNamespace(PPO=object()))
    monkeypatch.setattr(train, "build_cooperative_world_batch_vec_env", lambda _bootstrap: env)
    monkeypatch.setattr(train, "apply_initial_curriculum_stage", lambda *args, **kwargs: None)
    monkeypatch.setattr(train, "load_sb3_policy", load)

    assert train.main() == 0
    assert loaded_paths == [str(tmp_path / "leader.zip"), str(tmp_path / "execution.zip")]
    assert env.step_calls == 1000
    np.testing.assert_array_equal(env.last_actions[:, 0], [1.0, 2.0, 2.0])


def test_cooperative_eval_keeps_shared_model_and_supports_route_only_config(tmp_path, monkeypatch):
    from tools.eval import policy_execution_eval as evaluation

    monkeypatch.setattr(evaluation, "make_env_settings", lambda *args, **kwargs: {})
    monkeypatch.setattr(evaluation, "_apply_curriculum_stage", lambda *args: {"stage_index": None})
    monkeypatch.setattr(evaluation, "_cooperative_action_wrapper_kwargs", lambda _config: None)
    monkeypatch.setattr(evaluation, "write_json_output", lambda *args: None)
    for route_models in ({}, {"leader": "leader.zip", "execution": "execution.zip"}):
        env = _EntryEnv()
        config = {"cooperative_execution": {"policy_models": route_models}} if route_models else {}
        monkeypatch.setattr(evaluation, "load_json_config", lambda _path: config)
        monkeypatch.setattr(evaluation, "create_cooperative_backend", lambda **kwargs: env)
        monkeypatch.setattr(
            evaluation, "load_sb3_policy",
            lambda path, **kwargs: _FakeModel(1.0 if path.endswith("leader.zip") else 2.0),
        )
        argv = ["--mode", "cooperative", "--scenario", "scene.json", "--train_config",
                str(tmp_path / "config.json"), "--episodes", "1"]
        if not route_models:
            argv += ["--model", "shared.zip"]
        assert evaluation._run_cooperative_eval(evaluation.parse_args(argv)) == 0
        assert env.step_calls == 1
        assert env.closed
        np.testing.assert_array_equal(
            env.last_actions[:, 0], [1.0, 2.0, 2.0] if route_models else [2.0, 2.0, 2.0]
        )
