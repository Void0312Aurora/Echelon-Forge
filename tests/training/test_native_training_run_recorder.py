"""Actual maintained WorldBatch owner integration; works with recorder ON or OFF."""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from python.env_config import resolve_env_settings
from python.experiment.definition import (
    ConfigComposition, EvaluationProtocol, Experiment, ExperimentRegistry, ScenarioRef, SeedSpec,
)
from python.experiment.input_lock_artifacts import write_resolved_input_lock_artifacts
from python.experiment.resolved_input_lock import (
    InputLockError, build_resolved_input_lock, compare_resolved_input_locks,
    project_compiled_scenario_dependencies,
)
from python.scenario.compiler import ScenarioCompiler
from python.training.input_lock import reopen_training_input_lock, training_run_recorder_config
from tools.maintenance.runtime_authority_contracts import (
    authority_digest_sha256, canonical_json_bytes,
)
from tools.maintenance.runtime_run_receipt import validate_run_receipt

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/architecture/composition/fixtures"


def _fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _native_type():
    import ef_py
    return ef_py.RuntimeFacade


def _require_enabled():
    facade = _native_type()
    if not facade.training_run_recorder_enabled():
        pytest.skip("EF_ENABLE_TRAINING_RUN_RECORDER=OFF; disabled contract tested separately")
    return facade


def _case(directory, *, policy="MultiInputPolicy", run="training-native"):
    directory.mkdir(parents=True, exist_ok=True)
    config = {"n_envs": 2, "total_timesteps": 4, "policy": policy,
              "runtime": {"world_batch_vec_env": True, "world_batch_threads": 1}}
    scenario = ROOT / "scenarios/test/test_free_fall.json"
    registry = ExperimentRegistry()
    registry.register_config_base("training_native_base", config)
    registry.register_evaluation_protocol(EvaluationProtocol("smoke", "native training owner smoke"))
    experiment = Experiment("native_training", ScenarioRef(scenario.relative_to(ROOT).as_posix()),
                            ConfigComposition("training_native_base"), SeedSpec((239,)), "smoke")
    candidate = build_resolved_input_lock(
        experiment, registry, repo_root=ROOT, policy={"id": policy},
        dependencies=project_compiled_scenario_dependencies(
            ScenarioCompiler.compile_path(str(scenario)), repo_root=ROOT),
    )
    projection, payload = directory / "resolved.json", directory / "input.json"
    write_resolved_input_lock_artifacts(candidate, projection_path=projection,
                                       native_input_lock_path=payload)
    receipt = json.loads(_fixture("run_receipt.v1.json")["canonical_envelope_json"])
    plan_path = FIXTURES / "default_resolved_execution_plan.v1.json"
    plan = json.loads(plan_path.read_bytes())
    release = json.loads(_fixture("authority_cross_language_vector.v1.json")["envelope_json"])
    rollout = json.loads(_fixture("authority_rollout_decision.v1.json")["envelope_json"])
    rollout["payload"]["plan_sha256"] = plan["plan_sha256"]
    rollout["payload_sha256"] = authority_digest_sha256(
        rollout["domain"], rollout["media_type"], canonical_json_bytes(rollout["payload"]))
    p = receipt["payload"]
    request_sha = plan["input_bindings"]["request_sha256"]
    plan_blob = hashlib.sha256(plan_path.read_bytes()).hexdigest()
    p["plan_binding"] = {
        "compiler_identity": "PlanCompiler", "compiler_version": "1.0.0",
        "plan_canonical_sha256": plan["plan_sha256"], "plan_generation": plan["writer_generation"],
        "plan_id": plan["plan_id"], "plan_location": f"ledger://blob-{plan_blob}",
        "plan_sha256": plan["plan_sha256"], "request_canonical_sha256": request_sha,
        "request_location": f"ledger://blob-{request_sha}", "request_sha256": request_sha,
    }
    p["reader_generation_min"] = plan["reader_generation_min"]
    p["reader_generation_max"] = plan["reader_generation_max"]
    p["inputs"]["artifacts"] = {"request": request_sha, "resolved_execution_plan": plan_blob}
    p["release_binding"] = {
        "release_id": release["payload"]["release_id"], "release_manifest_sha256": release["payload_sha256"],
        "rollout_decision_id": rollout["payload"]["decision_id"],
        "rollout_decision_sha256": rollout["payload_sha256"],
        "provenance_sha256": release["payload"]["provenance_sha256"],
        "sbom_sha256": release["payload"]["sbom_sha256"],
        "attestation_sha256": p["release_binding"]["attestation_sha256"],
    }
    bindings = {key: p[key] for key in (
        "receipt_id", "attempt_id", "plan_binding", "release_binding", "executable", "package",
        "build", "platform", "inputs", "backend", "reader_generation_min", "reader_generation_max")}
    bindings["release_manifest_envelope_json"] = canonical_json_bytes(release).decode()
    bindings["rollout_decision_envelope_json"] = canonical_json_bytes(rollout).decode()
    header_path, template_path = directory / "header.json", directory / "template.json"
    header_path.write_bytes(canonical_json_bytes({"receipt_bindings": bindings}))
    template_path.write_bytes(canonical_json_bytes(receipt))
    raw = {
        "enabled": True, "run_id": run, "writer_id": f"writer-{run}",
        "ledger_root": str(directory / "ledger"), "header_path": str(header_path),
        "receipt_template_path": str(template_path), "resolved_input_lock_path": str(projection),
        "run_receipt_path": str(directory / "receipt.json"),
        "execution_sources": {
            "resolved_execution_plan_path": str(plan_path),
            "request_path": str(FIXTURES / "default_runtime_composition_request.v1.json"),
            "package_path": str(FIXTURES / "candidate_release_package.v1.bin"),
            "wheel_path": str(FIXTURES / "candidate_release_package.v1.bin"),
            "resolved_input_lock_path": str(payload),
            "owner_facts": {"build_mode": "Release", "build_dirty": True, "linker": "link.exe",
                            "cxx_abi": "msvc-native", "python_abi": sys.implementation.cache_tag,
                            "node_abi": "training-no-node"},
        },
    }
    config["runtime"]["run_recorder"] = raw
    bootstrap = SimpleNamespace(
        train_config=config, runtime_cfg=config["runtime"], training_seed=239, n_envs=2,
        scenario_path=str(scenario), env_settings=resolve_env_settings(config, SimpleNamespace()),
    )
    return bootstrap, candidate


def _execute(bootstrap):
    from python.training.vec_env_factory import build_execution_world_batch_vec_env

    env = build_execution_world_batch_vec_env(bootstrap)
    env.reset()
    for _ in range(2):
        env.step(np.stack([env.action_space.sample() for _ in range(2)]))
    env.close()
    env.close()  # Closing again must not issue another receipt or replay work.
    return env.resolved_training_run


def test_default_off_native_contract_preserves_ordinary_runtime(tmp_path):
    facade = _native_type()
    ordinary = facade(2)
    assert ordinary.world_count() == 2
    assert isinstance(facade.training_run_recorder_enabled(), bool)
    if facade.training_run_recorder_enabled():
        return
    with pytest.raises(RuntimeError, match="training_recorder.disabled"):
        facade(2, "{}")
    with pytest.raises(RuntimeError, match="training_recorder.disabled"):
        facade.reopen_recorded_run(str(tmp_path / "unused"), "missing")
    assert not (tmp_path / "unused").exists()


def test_world_batch_training_repeat_and_policy_only_comparison(tmp_path):
    _require_enabled()
    # Load the maintained Python training modules before native provenance admission.
    from python.training.deps import load_training_dependencies
    load_training_dependencies()
    runs = []
    for index, policy in enumerate(("MultiInputPolicy", "MultiInputPolicy", "SquashedMultiInputPolicy")):
        bootstrap, candidate = _case(tmp_path / str(index), policy=policy, run=f"training-{index}")
        joined = _execute(bootstrap)
        assert joined.digest == candidate.digest
        assert joined.as_dict()["status"] == "completed"
        runs.append(joined)
        config = training_run_recorder_config(bootstrap)
        native_bytes = _native_type().reopen_recorded_run(config["ledger_root"], config["run_id"])
        assert Path(config["run_receipt_path"]).read_bytes() == native_bytes.encode()
        receipt = json.loads(native_bytes)
        validate_run_receipt(receipt)
        assert len(receipt["payload"]["execution_scope"]["world_ids"]) == 2
        assert {a["name"] for a in receipt["payload"]["results"]["output_artifacts"]} == {
            "runtime-cpu-scheduler-topology", "runtime-world-scope-binding",
            "runtime-training-observation", "runtime-training-validation",
        }
    assert compare_resolved_input_locks(runs[0], runs[1]).comparable
    assert not compare_resolved_input_locks(runs[0], runs[2]).comparable
    assert compare_resolved_input_locks(runs[0], runs[2], intentional_axes=frozenset({"policy"})).comparable


def _files(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_training_receipt_reopens_in_fresh_process_without_ledger_mutation(tmp_path):
    _require_enabled()
    bootstrap, _ = _case(tmp_path)
    _execute(bootstrap)
    config = training_run_recorder_config(bootstrap)
    root = Path(config["ledger_root"])
    before = _files(root)
    script = (
        "from python.runtime_bootstrap import ensure_repo_imports; ensure_repo_imports(); "
        "import ef_py,sys; print(ef_py.RuntimeFacade.reopen_recorded_run(sys.argv[1],sys.argv[2]))"
    )
    result = subprocess.run([sys.executable, "-c", script, config["ledger_root"], config["run_id"]],
                            cwd=ROOT, env=os.environ.copy(), capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["payload"]["terminal_state"] == "completed"
    assert _files(root) == before


@pytest.mark.parametrize("target", ["receipt", "input", "runtime-cpu-scheduler-topology",
                                    "runtime-world-scope-binding", "runtime-training-observation"])
@pytest.mark.parametrize("damage", ["missing", "corrupt"])
def test_training_reopen_rejects_missing_or_corrupt_owner_bytes(tmp_path, target, damage):
    _require_enabled()
    bootstrap, _ = _case(tmp_path)
    _execute(bootstrap)
    config = training_run_recorder_config(bootstrap)
    root = Path(config["ledger_root"])
    receipt_bytes = _native_type().reopen_recorded_run(str(root), config["run_id"])
    receipt = json.loads(receipt_bytes)
    if target == "receipt":
        paths = list(root.rglob("receipt.json"))
        assert len(paths) == 1
        path = paths[0]
    else:
        digest = (receipt["payload"]["inputs"]["artifacts"]["resolved_input_lock"] if target == "input"
                  else next(a["digest"] for a in receipt["payload"]["results"]["output_artifacts"]
                            if a["name"] == target))
        path = root / "blobs" / f"{digest}.data"
    if damage == "missing":
        path.unlink()
    else:
        path.write_bytes(b"corrupt")
    with pytest.raises(InputLockError, match="training_reopen_failed"):
        reopen_training_input_lock(config)


@pytest.mark.parametrize("mode", ["uninitialized", "incomplete", "generation", "failed"])
def test_training_failed_or_missing_generations_never_join_completed(tmp_path, mode):
    facade_type = _require_enabled()
    bootstrap, _ = _case(tmp_path)
    config = training_run_recorder_config(bootstrap)
    if mode == "uninitialized":
        native = facade_type(2, json.dumps(config))
        with pytest.raises(RuntimeError, match="training_recorder"):
            native.step_batch()
    else:
        from python.training.vec_env_factory import build_execution_world_batch_vec_env
        env = build_execution_world_batch_vec_env(bootstrap)
        env.reset()
        native = env._runtime_adapter.facade
        if mode == "generation":
            env.step(np.stack([env.action_space.sample() for _ in range(2)]))
            native.resize(1)
            native.resize(2)
            with pytest.raises(RuntimeError, match="training_recorder"):
                native.step_batch()
        if mode == "failed":
            native.fail_recorded_run("controlled training failure")
    native.finish_recorded_run()
    receipt = json.loads(facade_type.reopen_recorded_run(config["ledger_root"], config["run_id"]))
    assert receipt["payload"]["terminal_state"] == "failed"
    with pytest.raises(InputLockError, match="training_run_not_completed"):
        reopen_training_input_lock(config)
