from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from python.training.curriculum import apply_initial_curriculum_stage


def test_success_records_admitted_stage_before_training(tmp_path):
    env = Mock()
    stage = {"randomization_overrides": {"wind": 3}, "leader_env_overrides": {"speed": 180}}
    apply_initial_curriculum_stage(env, {"stages": [stage]}, agent_layer="leader", evidence_dir=str(tmp_path))
    assert [call.args[0] for call in env.env_method.call_args_list] == [
        "set_randomization_overrides", "set_leader_overrides"
    ]
    receipt = json.loads((tmp_path / "curriculum_stage0.json").read_text())
    assert receipt["admitted_overrides"] == stage


@pytest.mark.parametrize("curriculum", [None, {}, {"stages": []}, {"stages": [{}]}])
def test_missing_settings_do_not_require_optional_methods(tmp_path, curriculum):
    env = Mock()
    apply_initial_curriculum_stage(env, curriculum, agent_layer="execution", evidence_dir=str(tmp_path))
    env.env_method.assert_not_called()


def test_invalid_second_setting_is_rejected_before_any_application(tmp_path):
    env = Mock()
    with pytest.raises(ValueError, match="leader_env_overrides"):
        apply_initial_curriculum_stage(env, {"stages": [{"randomization": {}, "leader_env_overrides": []}]},
                                       agent_layer="leader", evidence_dir=str(tmp_path))
    env.env_method.assert_not_called()


@pytest.mark.parametrize("failure_index", [0, 1])
def test_entry_never_constructs_or_learns_model_after_override_failure(tmp_path, failure_index):
    import train

    env = Mock(num_envs=1)
    env.env_method.side_effect = [RuntimeError("rejected")] if failure_index == 0 else [None, AttributeError("unsupported")]
    policy = Mock()
    bootstrap = SimpleNamespace(
        train_config={"curriculum": {"stages": [{"randomization": {"wind": 1}, "leader_env_overrides": {"speed": 180}}]}},
        agent_layer="execution", env_settings={}, scenario_path="scene.json", train_cfg_path="train.json",
        exp_dir=str(tmp_path), run_name="test", ckpt_dir=str(tmp_path), log_dir=str(tmp_path),
        training_seed=42, n_envs=1, exp_lock=Mock(),
    )
    parser = Mock()
    parser.parse_args.return_value = SimpleNamespace(test_only=False)
    with patch.object(train, "build_train_arg_parser", return_value=parser), \
         patch.object(train, "prepare_training_bootstrap", return_value=bootstrap), \
         patch.object(train, "print_training_bootstrap_summary"), \
         patch.object(train, "warn_execution_visual_rollout_memory"), \
         patch.object(train, "load_training_dependencies", return_value=SimpleNamespace(PPO=policy)), \
         patch.object(train, "build_execution_world_batch_vec_env", return_value=env):
        with pytest.raises(RuntimeError, match="training has not started") as failure:
            train.main()
    assert failure.value.__cause__ is not None
    assert ("randomization" if failure_index == 1 else "[]") in str(failure.value)
    policy.assert_not_called()
    policy.return_value.learn.assert_not_called()
    env.close.assert_called_once()
    bootstrap.exp_lock.close.assert_called_once()
    assert not (tmp_path / "curriculum_stage0.json").exists()


@pytest.fixture
def leader_vec_env():
    # Leader admission requires the optional training extras. The lightweight
    # smoke/coverage lanes deliberately install only the core test dependencies.
    pytest.importorskip("gymnasium")
    pytest.importorskip("torch")
    pytest.importorskip("stable_baselines3")
    from gym_envs.leader_env import LeaderTrainingEnv
    from stable_baselines3.common.env_util import make_vec_env
    from stable_baselines3.common.vec_env import DummyVecEnv
    from tests.support._leader_env_runtime_test_support import FakeExecutionRuntime

    runtime = FakeExecutionRuntime()
    with patch.object(LeaderTrainingEnv, "_build_execution_runtime", return_value=runtime), \
         patch.object(LeaderTrainingEnv, "_build_execution_policy", return_value=object()):
        vec = make_vec_env(LeaderTrainingEnv, n_envs=1, vec_env_cls=DummyVecEnv,
                           env_kwargs={"scenario_path": "scenarios/combined/takeoff_to_landing_continuous_train_v1.json"})
    try:
        yield vec, runtime
    finally:
        vec.close()


@pytest.mark.parametrize("stage", [
    {"leader_env_overrides": {"unknown": 1}},
    {"leader_env_overrides": {"teacher_keep_deadband": "bad"}},
    {"leader_env_overrides": {"teacher_keep_deadband": 1.0}},
    {"leader_env_overrides": {"speed_bias_limit_mps": float("nan")}},
    {"randomization": {"unknown": 1}},
    {"randomization": {"wind_speed_range": [1, "bad"]}},
    {"randomization": {"wind_speed_range": [3, 1]}},
    {"randomization": {"wind_shear_range": [0, float("inf")]}},
])
def test_real_leader_vec_env_rejects_authored_settings_before_training(tmp_path, leader_vec_env, stage):
    import train

    vec, _ = leader_vec_env
    policy = Mock()
    bootstrap = SimpleNamespace(
        train_config={"curriculum": {"stages": [stage]}}, agent_layer="leader", env_settings={},
        scenario_path="scene.json", train_cfg_path="train.json", exp_dir=str(tmp_path), run_name="test",
        ckpt_dir=str(tmp_path), log_dir=str(tmp_path), training_seed=42, n_envs=1, exp_lock=Mock(),
    )
    parser = Mock()
    parser.parse_args.return_value = SimpleNamespace(test_only=False)
    with patch.object(train, "build_train_arg_parser", return_value=parser), \
         patch.object(train, "prepare_training_bootstrap", return_value=bootstrap), \
         patch.object(train, "print_training_bootstrap_summary"), \
         patch.object(train, "warn_execution_visual_rollout_memory"), \
         patch.object(train, "load_training_dependencies", return_value=SimpleNamespace(PPO=policy)), \
         patch.object(train, "build_leader_vec_env", return_value=vec):
        with pytest.raises(RuntimeError, match="training has not started"):
            train.main()
    policy.assert_not_called()
    bootstrap.exp_lock.close.assert_called_once()
    assert not (tmp_path / "curriculum_stage0.json").exists()


def test_real_leader_vec_env_propagates_runtime_refusal(tmp_path, leader_vec_env):
    vec, runtime = leader_vec_env
    runtime.set_randomization_overrides = Mock(side_effect=RuntimeError("runtime refused"))
    with pytest.raises(RuntimeError, match="training has not started") as failure:
        apply_initial_curriculum_stage(vec, {"stages": [{"randomization": {"wind_speed_range": [1, 2]}}]},
                                       agent_layer="leader", evidence_dir=str(tmp_path))
    assert str(failure.value.__cause__) == "runtime refused"
    assert not (tmp_path / "curriculum_stage0.json").exists()


def test_real_leader_vec_env_receipt_matches_applied_settings(tmp_path, leader_vec_env):
    vec, runtime = leader_vec_env
    stage = {"randomization": {"wind_speed_range": [1, 2]},
             "leader_env_overrides": {"teacher_keep_deadband": 0.4, "speed_bias_limit_mps": 25}}
    apply_initial_curriculum_stage(vec, {"stages": [stage]}, agent_layer="leader", evidence_dir=str(tmp_path))
    assert runtime.last_overrides == stage["randomization"]
    assert vec.get_attr("teacher_keep_deadband") == [0.4]
    assert vec.get_attr("speed_bias_limit_mps") == [25.0]
    assert json.loads((tmp_path / "curriculum_stage0.json").read_text())["admitted_overrides"] == stage


def test_real_leader_setter_validates_all_fields_before_mutation(leader_vec_env):
    vec, _ = leader_vec_env
    original = vec.get_attr("teacher_keep_deadband")
    with pytest.raises(ValueError, match="finite number"):
        vec.env_method("set_leader_overrides", {"teacher_keep_deadband": 0.4, "speed_bias_limit_mps": "bad"})
    assert vec.get_attr("teacher_keep_deadband") == original
