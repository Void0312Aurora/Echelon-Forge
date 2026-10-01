"""Curriculum stage runner for the native single-soldier Ground slice.

Stage configurations are data
(``examples/config/training/active/ground/eastern_plain_infantry_curriculum_stages_v1.json``).
Each stage admits a subset of the fixture-derived acceptance cases, and every
admission threshold is read by key from the retained field-acceptance report.
The runner records a scripted heading-to-goal baseline per stage and, when the
caller asks for one, a short SB3 PPO smoke on the stage's first case.

This is tooling with ``native_probe_only`` authority. It is not ``train.py``,
not a WorldBatch entry, and introduces no reward, termination, or speed
coefficient: the native env contract is reused unchanged.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .acceptance_matrix import (
    CONTRACT_GOAL_RADIUS_M,
    HELD_CLAIMS,
    case_failures,
    case_step_budget,
    matrix_row,
    run_case,
)
from .fixture_cases import ArnisInfantryFixture, FixtureCase, FixtureCaseError, derive_acceptance_cases


CURRICULUM_STAGES_CONTRACT_VERSION = "ground_infantry_curriculum_stages.v1"
CURRICULUM_RUN_CONTRACT_VERSION = "ground_infantry_curriculum_stage_run.v1"

_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_STAGES_PATH = (
    _REPO_ROOT
    / "examples"
    / "config"
    / "training"
    / "active"
    / "ground"
    / "eastern_plain_infantry_curriculum_stages_v1.json"
)


class CurriculumStageError(ValueError):
    """Raised when a stage config cannot be resolved (fail closed)."""


def load_stage_config(path: str | Path = DEFAULT_STAGES_PATH) -> dict[str, Any]:
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    if config.get("contract_version") != CURRICULUM_STAGES_CONTRACT_VERSION:
        raise CurriculumStageError("unsupported curriculum stage contract")
    if config.get("authority") != "native_probe_only":
        raise CurriculumStageError("curriculum stages must stay native_probe_only")
    return config


def _stage(config: Mapping[str, Any], stage_id: str) -> Mapping[str, Any]:
    for stage in config["stages"]:
        if stage["stage"] == stage_id:
            return stage
    raise CurriculumStageError(f"unknown curriculum stage {stage_id!r}")


def _sourced_value(fixture: ArnisInfantryFixture, reference: Mapping[str, Any] | None) -> Any:
    """Resolve ``{"source": "field_acceptance.<section>", "key": ...}``."""

    if reference is None:
        return None
    source = str(reference["source"])
    prefix = "field_acceptance."
    if not source.startswith(prefix):
        raise CurriculumStageError(f"unsupported threshold source {source!r}")
    section = fixture.field_acceptance.get(source[len(prefix) :])
    if not isinstance(section, Mapping) or reference["key"] not in section:
        raise CurriculumStageError(f"threshold {source}.{reference['key']} is missing")
    return section[reference["key"]]


def _admission_rejections(
    fixture: ArnisInfantryFixture,
    case: FixtureCase,
    admit: Mapping[str, Any],
) -> list[str]:
    rejections: list[str] = []
    if case.expected not in admit["expected"]:
        rejections.append(f"expected:{case.expected}")
    if case.category not in admit["categories"]:
        rejections.append(f"category:{case.category}")
    bridge = admit.get("requires_bridge_admission")
    if bridge is not None and case.requires_bridge_admission != bool(bridge):
        rejections.append("bridge_admission")
    cells = fixture.segment_cells(case)
    max_slope = _sourced_value(fixture, admit.get("max_segment_slope"))
    if max_slope is not None:
        worst = max(fixture.stride_slope_at(cell) for cell in cells)
        if worst > float(max_slope):
            rejections.append("segment_slope")
    codes = _sourced_value(fixture, admit.get("landcover_codes"))
    if codes is not None:
        allowed = {int(code) for code in codes}
        if any(int(fixture.landcover[cell]) not in allowed for cell in cells):
            rejections.append("landcover_codes")
    kinds = admit.get("exclude_overlay_kinds") or []
    if kinds:
        overlay = fixture.overlay_polygon_mask(tuple(kinds))
        if any(overlay[cell] for cell in cells):
            rejections.append("overlay_kinds")
    if admit.get("exclude_building_footprints") and any(fixture.building_mask[cell] for cell in cells):
        rejections.append("building_footprint")
    return rejections


def stage_cases(
    stage_id: str,
    *,
    config: Mapping[str, Any] | None = None,
    fixture: ArnisInfantryFixture | None = None,
) -> tuple[tuple[FixtureCase, ...], dict[str, list[str]]]:
    """Admitted cases for a stage, plus the rejection reasons of the rest."""

    config = config or load_stage_config()
    fixture = fixture or ArnisInfantryFixture()
    admit = _stage(config, stage_id)["admit"]
    admitted: list[FixtureCase] = []
    rejected: dict[str, list[str]] = {}
    for case in derive_acceptance_cases(fixture, goal_radius_m=CONTRACT_GOAL_RADIUS_M):
        reasons = _admission_rejections(fixture, case, admit)
        if reasons:
            rejected[case.case_id] = reasons
        else:
            admitted.append(case)
    if not admitted and _stage(config, stage_id)["acceptance"]["fail_closed_on_empty_stage"]:
        raise FixtureCaseError(f"{stage_id}: the fixture admits no case for this stage")
    return tuple(admitted), rejected


def _stage_failures(
    case: FixtureCase, row: Mapping[str, Any], acceptance: Mapping[str, Any]
) -> list[str]:
    failures = list(row["failures"])
    if acceptance["baseline_outcome"] == "reach" and row["outcome"] != "reach":
        failures.append(f"stage_outcome:{row['outcome']}")
    if not acceptance["allow_blocked_steps"] and row["blocked_reasons"]:
        failures.append("stage_blocked_steps")
    return list(dict.fromkeys(failures))


def ppo_smoke(case: FixtureCase, *, seed: int, total_timesteps: int) -> dict[str, Any]:
    """Short SB3 PPO rollout/update on one stage case (pipeline smoke only).

    PPO hyperparameters are the repository's ``default_ppo.json`` values,
    except that ``n_steps``/``batch_size`` are capped at ``total_timesteps``
    so the smoke completes one rollout. This proves the stage env can be
    consumed by the training stack; it is not a learning result.
    """

    from stable_baselines3 import PPO  # optional RL dependency

    from .native_env import GroundInfantryNativeEnv
    from .native_probe import GroundInfantryNativeProbe

    defaults = json.loads(
        (_REPO_ROOT / "examples" / "config" / "training" / "default_ppo.json").read_text(encoding="utf-8")
    )
    hyperparameters = dict(defaults["hyperparameters"])
    hyperparameters["n_steps"] = min(int(hyperparameters["n_steps"]), int(total_timesteps))
    hyperparameters["batch_size"] = min(int(hyperparameters["batch_size"]), hyperparameters["n_steps"])
    hyperparameters["n_epochs"] = 1
    env = GroundInfantryNativeEnv(
        GroundInfantryNativeProbe.from_fixture(
            start_xy_m=case.start_xy_m,
            waypoints_xy_m=case.waypoints_xy_m,
            max_steps=case_step_budget(case, seed=seed),
        )
    )
    model = PPO(
        defaults["policy"],
        env,
        seed=seed,
        device="cpu",
        verbose=0,
        **hyperparameters,
    )
    model.learn(total_timesteps=int(total_timesteps))
    return {
        "case_id": case.case_id,
        "algo": defaults["algo"],
        "policy": defaults["policy"],
        "hyperparameters": hyperparameters,
        "total_timesteps": int(model.num_timesteps),
        "claim": "pipeline_smoke_only_not_a_learning_result",
    }


def run_stage(
    stage_id: str,
    *,
    seed: int,
    config: Mapping[str, Any] | None = None,
    fixture: ArnisInfantryFixture | None = None,
    ppo_timesteps: int | None = None,
) -> dict[str, Any]:
    """Run the scripted baseline over every admitted case of a stage."""

    config = config or load_stage_config()
    fixture = fixture or ArnisInfantryFixture()
    stage = _stage(config, stage_id)
    cases, rejected = stage_cases(stage_id, config=config, fixture=fixture)
    rows = []
    for case in cases:
        rollout = run_case(case, seed=seed)
        row = matrix_row(case, rollout)
        row["failures"] = _stage_failures(case, row, stage["acceptance"])
        row["verdict"] = "pass" if not row["failures"] else "fail"
        row["episode_return"] = rollout.total_reward
        rows.append(row)
    passed = sum(1 for row in rows if row["verdict"] == "pass")
    report: dict[str, Any] = {
        "contract_version": CURRICULUM_RUN_CONTRACT_VERSION,
        "stage": stage_id,
        "authority": "native_probe_only",
        "production_boundary": "not_world_batch",
        "controller": "scripted_heading_to_goal",
        "seed": seed,
        "admitted_cases": len(rows),
        "rejected_cases": rejected,
        "baseline": {
            "pass": passed,
            "fail": len(rows) - passed,
            "reach": sum(1 for row in rows if row["outcome"] == "reach"),
            "block": sum(1 for row in rows if row["outcome"] == "block"),
            "steps": sum(row["steps"] for row in rows),
        },
        "valid": bool(rows) and passed == len(rows),
        "rows": rows,
        "held": sorted(set(HELD_CLAIMS) | set(config.get("held", []))),
        "open_decisions": [
            decision for decision in config.get("open_decisions", []) if decision.get("stage") == stage_id
        ],
    }
    if ppo_timesteps is not None:
        report["ppo_smoke"] = ppo_smoke(cases[0], seed=seed, total_timesteps=ppo_timesteps)
    return report


def run_curriculum(
    stage_ids: Sequence[str] | None = None,
    *,
    seed: int,
    config_path: str | Path = DEFAULT_STAGES_PATH,
    ppo_timesteps: int | None = None,
) -> dict[str, Any]:
    config = load_stage_config(config_path)
    fixture = ArnisInfantryFixture()
    stage_ids = list(stage_ids or [stage["stage"] for stage in config["stages"]])
    stages = [
        run_stage(stage_id, seed=seed, config=config, fixture=fixture, ppo_timesteps=ppo_timesteps)
        for stage_id in stage_ids
    ]
    return {
        "contract_version": CURRICULUM_RUN_CONTRACT_VERSION,
        "authority": "native_probe_only",
        "seed": seed,
        "valid": all(stage["valid"] for stage in stages),
        "stages": stages,
    }


__all__ = [
    "CURRICULUM_RUN_CONTRACT_VERSION",
    "CURRICULUM_STAGES_CONTRACT_VERSION",
    "CurriculumStageError",
    "DEFAULT_STAGES_PATH",
    "case_failures",
    "load_stage_config",
    "ppo_smoke",
    "run_curriculum",
    "run_stage",
    "stage_cases",
]
