"""Admit authored stage-0 settings before the first reset or policy update."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def apply_initial_curriculum_stage(
    vec_env: Any, curriculum: Any, *, agent_layer: str, evidence_dir: str
) -> None:
    if curriculum is None:
        return
    if not isinstance(curriculum, dict):
        raise ValueError("curriculum must be an object")
    stages = curriculum.get("stages", [])
    if not isinstance(stages, list):
        raise ValueError("curriculum.stages must be a list")
    if not stages:
        return
    stage = stages[0]
    if not isinstance(stage, dict):
        raise ValueError("curriculum.stages[0] must be an object")

    # Validate both inputs before applying either one. Missing settings are
    # optional; explicitly authored settings must succeed on every target.
    operations = []
    randomization_key = (
        "randomization_overrides" if "randomization_overrides" in stage else "randomization"
    )
    for key, method in (
        (randomization_key, "set_randomization_overrides"),
        ("leader_env_overrides", "set_leader_overrides"),
    ):
        if key not in stage:
            continue
        value = stage[key]
        if not isinstance(value, dict):
            raise ValueError(f"curriculum.stages[0].{key} must be an object")
        if key == "leader_env_overrides" and not value:
            continue
        operations.append((key, method, value))

    completed = []
    for key, method, value in operations:
        try:
            vec_env.env_method(method, value)
        except Exception as exc:
            raise RuntimeError(
                f"initial curriculum stage 0 failed for {agent_layer}: "
                f"curriculum.stages[0].{key} ({method}); "
                f"already applied={completed}; training has not started"
            ) from exc
        completed.append(key)

    receipt = {
        "schema_version": 1,
        "stage_index": 0,
        "agent_layer": agent_layer,
        "admitted_overrides": {key: value for key, _, value in operations},
    }
    Path(evidence_dir, "curriculum_stage0.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
