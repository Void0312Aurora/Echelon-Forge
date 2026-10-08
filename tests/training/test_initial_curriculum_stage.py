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
