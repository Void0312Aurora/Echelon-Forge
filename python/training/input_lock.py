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

    evidence = bootstrap.runtime_cfg.get("production_evidence")
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
