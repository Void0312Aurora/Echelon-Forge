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
