"""Check opted-in training inputs against the experiment owner's frozen lock.

This is a preflight for the current invocation, not a run recorder or completion
claim. The native host still owns admission, execution evidence and RunReceipt.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any


def _execution_config(config: dict[str, Any]) -> dict[str, Any]:
    result = dict(config)
    if "runtime" in result:
        runtime = dict(result["runtime"])
        runtime.pop("production_evidence", None)
        runtime.pop("run_recorder", None)
        if runtime:
            result["runtime"] = runtime
        else:
            result.pop("runtime")
    return result


def assert_training_input_lock(bootstrap: Any, *, repo_root: str | Path | None = None) -> str | None:
    """Reject a lock for different effective inputs before runtime construction.

    Evidence locations are transport settings and are excluded from the config
    comparison. Scenario compilation/dependency projection and environment
    defaults reuse their existing owners. No lock means the existing path.
    """

    recorder = bootstrap.runtime_cfg.get("run_recorder")
    evidence = recorder if isinstance(recorder, dict) and recorder.get("enabled", False) else (
        bootstrap.runtime_cfg.get("production_evidence")
    )
    if not isinstance(evidence, dict) or not evidence.get("resolved_input_lock_path"):
        return None

    from python.env_config import resolve_env_settings
    from python.experiment.resolved_input_lock import (
        InputLockError,
        canonical_json_bytes,
        load_resolved_input_lock_path,
        project_compiled_scenario_dependencies,
    )
    from python.scenario.compiler import ScenarioCompiler

    candidate = load_resolved_input_lock_path(evidence["resolved_input_lock_path"])
    locked = candidate.as_dict()["input_lock"]
    config = _execution_config(bootstrap.train_config)
    locked_config = _execution_config(locked["config"])
    if canonical_json_bytes(config) != canonical_json_bytes(locked_config):
        raise InputLockError("input_lock.training_config_mismatch")
    if bootstrap.n_envs != locked_config.get("n_envs", 1):
        raise InputLockError("input_lock.training_world_count_mismatch")
    if bootstrap.training_seed is None or bootstrap.training_seed not in locked["effective_seed_set"]:
        raise InputLockError("input_lock.training_seed_mismatch")
    if bootstrap.env_settings != resolve_env_settings(locked_config, SimpleNamespace()):
        raise InputLockError("input_lock.training_env_settings_mismatch")

    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[2]
    scenario_path = Path(bootstrap.scenario_path).resolve()
    if scenario_path != (root / locked["scenario"]["path"]).resolve():
        raise InputLockError("input_lock.training_scenario_mismatch")
    compiled = ScenarioCompiler.compile_path(str(scenario_path))
    dependencies = project_compiled_scenario_dependencies(compiled, repo_root=root)
    if any(locked["dependencies"].get(path) != value for path, value in dependencies.items()):
        raise InputLockError("input_lock.training_scenario_dependencies_mismatch")
    return candidate.digest


def training_run_recorder_config(bootstrap: Any) -> dict[str, Any] | None:
    """Validate the two lock file roles and supply native admission inputs."""
    from python.experiment.input_lock_artifacts import load_resolved_input_lock_artifacts
    from python.experiment.resolved_input_lock import InputLockError

    raw = bootstrap.runtime_cfg.get("run_recorder")
    if raw is None:
        return None
    if not isinstance(raw, dict) or type(raw.get("enabled", False)) is not bool:
        raise InputLockError("input_lock.recorder_enabled_invalid")
    if not raw.get("enabled", False):
        return None
    if not bootstrap.runtime_cfg.get("world_batch_vec_env", False):
        raise InputLockError("input_lock.recorder_requires_world_batch")
    required = (
        "run_id", "writer_id", "ledger_root", "header_path", "receipt_template_path",
        "resolved_input_lock_path", "run_receipt_path",
    )
    if any(not isinstance(raw.get(key), str) or not raw[key].strip() for key in required):
        raise InputLockError("input_lock.recorder_configuration_incomplete")
    sources = raw.get("execution_sources")
    if not isinstance(sources, dict) or not sources.get("resolved_input_lock_path"):
        raise InputLockError("input_lock.recorder_execution_sources_incomplete")
    candidate = load_resolved_input_lock_artifacts(
        projection_path=raw["resolved_input_lock_path"],
        native_input_lock_path=raw["execution_sources"]["resolved_input_lock_path"],
    )
    return {
        **{key: raw[key] for key in (
            "run_id", "writer_id", "ledger_root", "header_path", "receipt_template_path",
            "execution_sources", "resolved_input_lock_path", "run_receipt_path",
        )},
        "training_config": _execution_config(bootstrap.train_config),
        "training_seed": bootstrap.training_seed,
        "input_lock_digest": candidate.digest,
    }


def reopen_training_input_lock(config: dict[str, Any], *, native_facade_type: Any = None):
    """Reopen through the native read-only ledger, then join its owner artifacts.

    The exported receipt contains the exact native bytes; no Python receipt or
    completion status is created. The observation artifact owns the outcome.
    """
    import json
    import os
    import tempfile
    from python.experiment.resolved_input_lock import (
        InputLockError, join_run_receipt_path, load_resolved_input_lock_path,
    )
    from python.tasking_contracts.failure_domains import (
        BatchOperationOutcome, BatchResult, FailureDomain, RecoveryAdmission,
        WorldOutcome, WorldState,
    )
    if native_facade_type is None:
        import ef_py
        native_facade_type = ef_py.RuntimeFacade
    try:
        receipt_bytes = native_facade_type.reopen_recorded_run(config["ledger_root"], config["run_id"])
        receipt = json.loads(receipt_bytes)
        from tools.maintenance.runtime_run_receipt import validate_run_receipt

        validate_run_receipt(receipt)
        if receipt["payload"]["run_id"] != config["run_id"]:
            raise InputLockError("input_lock.training_run_identity_mismatch")
        if receipt["payload"]["terminal_state"] != "completed":
            raise InputLockError("input_lock.training_run_not_completed")
        artifacts = {item["name"]: item for item in receipt["payload"]["results"]["output_artifacts"]}
        root = Path(config["ledger_root"]) / "blobs"
        def artifact_path(name):
            return root / (artifacts[name]["digest"] + ".data")
        observation_path = artifact_path("runtime-training-observation")
        from python.experiment.resolved_input_lock import _read_receipt_evidence_artifact
        observation_bytes = _read_receipt_evidence_artifact(
            receipt, observation_path, name="runtime-training-observation",
            media="application/vnd.echelon-forge.training-run-observation.v1+json",
            claimed_digest=artifacts["runtime-training-observation"]["digest"],
            error_prefix="input_lock.training_observation",
        )
        observation = json.loads(observation_bytes)
        if (observation["schema_version"] != "echelon_forge.training_run_observation.v1"
                or observation["run_id"] != config["run_id"]
                or observation["input_lock_digest"] != config["input_lock_digest"]
                or artifacts["runtime-training-observation"]["digest"] != receipt["payload"]["results"]["result_digest"]
                or observation["expected_batch_steps"] <= 0
                or observation["batch_steps"] < observation["expected_batch_steps"]
                or observation["input_lock_digest"] != receipt["payload"]["inputs"]["artifacts"]["resolved_input_lock"]
                or observation["input_lock_semantics_executed"] is not True):
            raise InputLockError("input_lock.training_observation_mismatch")
        outcome_data = observation["outcome"]
        outcome = BatchOperationOutcome(
            batch_generation_ref=outcome_data["batch_generation_ref"],
            operation_ref=outcome_data["operation_ref"], operation=outcome_data["operation"],
            domain=FailureDomain(outcome_data["domain"]), result=BatchResult(outcome_data["result"]),
            recovery_admission=RecoveryAdmission(outcome_data["recovery_admission"]),
            worlds=tuple(WorldOutcome(world_index=item["world_index"], state=WorldState(item["state"]),
                                      step_committed=item["step_committed"]) for item in outcome_data["worlds"]),
            expected_world_indices=tuple(outcome_data["expected_world_indices"]),
        )
        destination = Path(config["run_receipt_path"])
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(receipt_bytes.encode("utf-8"))
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, destination)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        return join_run_receipt_path(
            load_resolved_input_lock_path(config["resolved_input_lock_path"]),
            receipt_path=destination, native_runtime=observation["native_runtime"], outcome=outcome,
            native_topology_path=artifact_path("runtime-cpu-scheduler-topology"),
            native_world_scope_path=artifact_path("runtime-world-scope-binding"),
        )
    except InputLockError:
        raise
    except (OSError, RuntimeError, ValueError, KeyError, TypeError) as exc:
        raise InputLockError(f"input_lock.training_reopen_failed:{exc}") from exc
