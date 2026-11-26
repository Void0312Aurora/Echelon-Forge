from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from python.env_config import resolve_env_settings
from python.experiment.definition import (
    ConfigComposition, EvaluationProtocol, Experiment, ExperimentRegistry, ScenarioRef, SeedSpec,
)
from python.experiment.input_lock_artifacts import write_resolved_input_lock_artifacts
from python.experiment.resolved_input_lock import (
    InputLockError, build_resolved_input_lock, project_compiled_scenario_dependencies,
)
from python.scenario.compiler import ScenarioCompiler
from python.training.input_lock import assert_training_input_lock


def _locked_training(tmp_path):
    imported = tmp_path / "imported.json"
    imported.write_text(json.dumps({"entities": [], "meta": {"label": "original"}}))
    scenario = tmp_path / "scenario.json"
    scenario.write_text(json.dumps({"imports": [{"file": str(imported)}], "entities": []}))
    config = {"n_envs": 2, "policy": "MultiInputPolicy", "runtime": {"world_batch_vec_env": True}}
    registry = ExperimentRegistry()
    registry.register_config_base("base", config)
    registry.register_evaluation_protocol(EvaluationProtocol("smoke", "training preflight"))
    experiment = Experiment("training", ScenarioRef("scenario.json"), ConfigComposition("base"),
                            SeedSpec((239,)), "smoke")
    compiled = ScenarioCompiler.compile_path(str(scenario))
    candidate = build_resolved_input_lock(
        experiment, registry, repo_root=tmp_path,
        dependencies=project_compiled_scenario_dependencies(compiled, repo_root=tmp_path),
    )
    projection = tmp_path / "resolved.json"
    write_resolved_input_lock_artifacts(
        candidate, projection_path=projection, native_input_lock_path=tmp_path / "payload.json"
    )
    config = copy.deepcopy(config)
    config["runtime"]["production_evidence"] = {"resolved_input_lock_path": str(projection)}
    bootstrap = SimpleNamespace(
        train_config=config, runtime_cfg=config["runtime"], scenario_path=str(scenario),
        training_seed=239, n_envs=2, env_settings=resolve_env_settings(config, SimpleNamespace()),
    )
    return bootstrap, candidate, imported


def test_training_lock_accepts_matching_inputs_and_transport_locations(tmp_path):
    bootstrap, candidate, _ = _locked_training(tmp_path)
    bootstrap.runtime_cfg["production_evidence"]["run_receipt_path"] = "owner-output.json"
    assert assert_training_input_lock(bootstrap, repo_root=tmp_path) == candidate.digest


@pytest.mark.parametrize("change,reason", [
    ("policy", "training_config"), ("worlds", "training_world_count"),
    ("seed", "training_seed"), ("environment", "training_env_settings"),
    ("scenario", "training_scenario"), ("import", "training_scenario_dependencies"),
])
def test_training_lock_rejects_current_invocation_drift(tmp_path, change, reason):
    bootstrap, _candidate, imported = _locked_training(tmp_path)
    if change == "policy":
        bootstrap.train_config["policy"] = "SquashedMultiInputPolicy"
    elif change == "worlds":
        bootstrap.n_envs = 3
    elif change == "seed":
        bootstrap.training_seed = 240
    elif change == "environment":
        bootstrap.env_settings["include_visual"] = not bootstrap.env_settings["include_visual"]
    elif change == "scenario":
        bootstrap.scenario_path = str(imported)
    else:
        imported.write_text(json.dumps({"entities": [], "meta": {"label": "changed"}}))
    with pytest.raises(InputLockError, match=reason):
        assert_training_input_lock(bootstrap, repo_root=tmp_path)


def test_training_factory_rejects_changed_lock_before_loading_runtime(tmp_path, monkeypatch):
    from python.training import vec_env_factory

    bootstrap, _candidate, _ = _locked_training(tmp_path)
    bootstrap.training_seed = 240
    original_check = assert_training_input_lock
    monkeypatch.setattr(vec_env_factory, "assert_training_input_lock",
                        lambda value: original_check(value, repo_root=tmp_path))

    def unexpected_runtime():
        pytest.fail("runtime dependencies must not load for mismatched inputs")

    monkeypatch.setattr(vec_env_factory, "load_training_dependencies", unexpected_runtime)
    with pytest.raises(InputLockError, match="training_seed"):
        vec_env_factory.build_execution_world_batch_vec_env(bootstrap)


def test_training_without_a_lock_keeps_existing_path():
    assert assert_training_input_lock(SimpleNamespace(runtime_cfg={})) is None


def test_maintained_air_matrix_lock_matches_its_actual_training_inputs(tmp_path):
    from python.experiment.air_combat_matrix import MATRIX_ENTRIES, REGISTRY, composed_config

    root = Path(__file__).resolve().parents[2]
    entry = MATRIX_ENTRIES[0]
    config = composed_config(entry)
    scenario = root / entry.experiment.scenario.path
    compiled = ScenarioCompiler.compile_path(str(scenario))
    candidate = build_resolved_input_lock(
        entry.experiment, REGISTRY, repo_root=root, effective_seeds=(239,),
        dependencies=project_compiled_scenario_dependencies(compiled, repo_root=root),
    )
    projection = tmp_path / "air-resolved.json"
    write_resolved_input_lock_artifacts(
        candidate, projection_path=projection, native_input_lock_path=tmp_path / "air-input.json"
    )
    config.setdefault("runtime", {})["production_evidence"] = {
        "resolved_input_lock_path": str(projection)
    }
    bootstrap = SimpleNamespace(
        train_config=config, runtime_cfg=config["runtime"], scenario_path=str(scenario),
        training_seed=239, n_envs=config.get("n_envs", 1),
        env_settings=resolve_env_settings(config, SimpleNamespace()),
    )
    assert assert_training_input_lock(bootstrap) == candidate.digest



def _enable_recorder(bootstrap, tmp_path):
    bootstrap.runtime_cfg.pop("production_evidence", None)
    raw = {
        "enabled": True, "run_id": "training-test", "writer_id": "writer-training-test",
        "ledger_root": str(tmp_path / "ledger"), "header_path": str(tmp_path / "header.json"),
        "receipt_template_path": str(tmp_path / "template.json"),
        "resolved_input_lock_path": str(tmp_path / "resolved.json"),
        "run_receipt_path": str(tmp_path / "receipt.json"),
        "execution_sources": {"resolved_input_lock_path": str(tmp_path / "payload.json")},
    }
    bootstrap.runtime_cfg["run_recorder"] = raw
    return raw


def test_training_recorder_opt_in_validates_lock_pair_before_runtime(tmp_path):
    from python.training.input_lock import training_run_recorder_config

    bootstrap, candidate, _ = _locked_training(tmp_path)
    raw = _enable_recorder(bootstrap, tmp_path)
    assert assert_training_input_lock(bootstrap, repo_root=tmp_path) == candidate.digest
    config = training_run_recorder_config(bootstrap)
    assert config["input_lock_digest"] == candidate.digest
    assert "run_recorder" not in config["training_config"]["runtime"]
    assert config["training_seed"] == 239
    Path(raw["execution_sources"]["resolved_input_lock_path"]).write_text("{}")
    with pytest.raises(InputLockError, match="native_artifact_digest_mismatch"):
        training_run_recorder_config(bootstrap)


@pytest.mark.parametrize("raw", [None, {}, {"enabled": False}])
def test_training_recorder_default_path_needs_no_native_module(raw):
    from python.training.input_lock import training_run_recorder_config

    assert training_run_recorder_config(SimpleNamespace(runtime_cfg={"run_recorder": raw})) is None


@pytest.mark.parametrize("raw", [True, [], "on", {"enabled": 1}, {"enabled": "true"}])
def test_training_recorder_rejects_invalid_enable_flag(raw):
    from python.training.input_lock import training_run_recorder_config

    with pytest.raises(InputLockError, match="recorder_enabled_invalid"):
        training_run_recorder_config(SimpleNamespace(runtime_cfg={"run_recorder": raw}))


def test_training_recorder_requires_world_batch_and_complete_configuration(tmp_path):
    from python.training.input_lock import training_run_recorder_config

    bootstrap, _, _ = _locked_training(tmp_path)
    raw = _enable_recorder(bootstrap, tmp_path)
    bootstrap.runtime_cfg["world_batch_vec_env"] = False
    with pytest.raises(InputLockError, match="recorder_requires_world_batch"):
        training_run_recorder_config(bootstrap)
    bootstrap.runtime_cfg["world_batch_vec_env"] = True
    del raw["run_receipt_path"]
    with pytest.raises(InputLockError, match="recorder_configuration_incomplete"):
        training_run_recorder_config(bootstrap)


def test_training_factory_rejects_tampered_native_payload_before_loading_runtime(tmp_path, monkeypatch):
    from python.training import vec_env_factory

    bootstrap, _, _ = _locked_training(tmp_path)
    raw = _enable_recorder(bootstrap, tmp_path)
    Path(raw["execution_sources"]["resolved_input_lock_path"]).write_text("{}")
    original_check = assert_training_input_lock
    monkeypatch.setattr(vec_env_factory, "assert_training_input_lock",
                        lambda value: original_check(value, repo_root=tmp_path))
    monkeypatch.setattr(vec_env_factory, "load_training_dependencies",
                        lambda: pytest.fail("tampered native inputs must reject before runtime import"))
    with pytest.raises(InputLockError, match="native_artifact_digest_mismatch"):
        vec_env_factory.build_execution_world_batch_vec_env(bootstrap)


def _run_train_entrypoint(monkeypatch, tmp_path, *, learn_outcome):
    import sys
    import train

    events = []
    exp_dir = tmp_path / "exp"
    ckpt_dir = exp_dir / "checkpoints"
    ckpt_dir.mkdir(parents=True)

    class _FakeLock:
        def close(self):
            events.append("exp_lock.close")

    bootstrap = SimpleNamespace(
        train_config={"total_timesteps": 4, "save_freq": 4, "hyperparameters": {}},
        agent_layer="execution",
        env_settings={"action_mode": "full"},
        scenario_path=str(tmp_path / "scenario.json"),
        train_cfg_path=str(tmp_path / "train.json"),
        exp_dir=str(exp_dir),
        run_name="test-run",
        ckpt_dir=str(ckpt_dir),
        log_dir=str(exp_dir / "logs"),
        training_seed=42,
        n_envs=2,
        exp_lock=_FakeLock(),
    )

    class _FakeVecEnv:
        num_envs = 2

        def mark_recorded_run_failed(self, reason):
            events.append(("mark_failed", reason))

        def close(self):
            events.append("vec_env.close")
            if learn_outcome != "success":
                raise InputLockError("input_lock.training_run_not_completed")

    class _FakeModel:
        rollout_buffer = object()

        def __init__(self, *args, **kwargs):
            pass

        def learn(self, **_kwargs):
            if learn_outcome == "interrupt":
                raise KeyboardInterrupt()
            if learn_outcome == "error":
                raise RuntimeError("boom")

        def save(self, path):
            events.append(("save", Path(path).name))

    fake_deps = SimpleNamespace(
        PPO=_FakeModel,
        AdaptiveKLPPO=_FakeModel,
        CheckpointCallback=type("_CheckpointCallback", (), {"__init__": lambda self, **_k: None}),
        CallbackList=lambda items: items,
        NonFiniteProbeError=type("_NonFiniteProbeError", (Exception,), {}),
    )
    monkeypatch.setattr(sys, "argv", ["train.py", "--scenario", str(tmp_path / "scenario.json")])
    monkeypatch.setattr(train, "prepare_training_bootstrap", lambda _args: bootstrap)
    monkeypatch.setattr(train, "print_training_bootstrap_summary", lambda _b: None)
    monkeypatch.setattr(train, "warn_execution_visual_rollout_memory", lambda _b: None)
    monkeypatch.setattr(train, "load_training_dependencies", lambda: fake_deps)
    monkeypatch.setattr(train, "build_execution_world_batch_vec_env", lambda _b: _FakeVecEnv())
    monkeypatch.setattr(train, "apply_initial_curriculum_stage", lambda *_a, **_k: None)
    monkeypatch.setattr(train, "apply_policy_kwargs_feature_extractor_classes", lambda _hp: None)
    monkeypatch.setattr(train, "apply_safe_action_bias", lambda *_a, **_k: None)
    monkeypatch.setattr(train, "maybe_initialize_hmoe_from_shared", lambda *_a, **_k: False)
    return train.main, events


def test_train_entrypoint_closes_recorder_env_on_success(monkeypatch, tmp_path):
    entrypoint, events = _run_train_entrypoint(monkeypatch, tmp_path, learn_outcome="success")
    assert entrypoint() == 0
    assert events == [("save", "final_model"), "vec_env.close", "exp_lock.close"]


def test_train_entrypoint_marks_failed_and_closes_on_exception(monkeypatch, tmp_path):
    entrypoint, events = _run_train_entrypoint(monkeypatch, tmp_path, learn_outcome="error")
    with pytest.raises(RuntimeError, match="boom"):
        entrypoint()
    assert events == [
        ("mark_failed", "training_exception:RuntimeError"),
        "vec_env.close",
        "exp_lock.close",
    ]


def test_train_entrypoint_marks_failed_and_closes_on_interrupt(monkeypatch, tmp_path):
    entrypoint, events = _run_train_entrypoint(monkeypatch, tmp_path, learn_outcome="interrupt")
    assert entrypoint() == 130
    assert events == [
        ("save", "interrupted_model"),
        ("mark_failed", "training_interrupted"),
        "vec_env.close",
        "exp_lock.close",
    ]
