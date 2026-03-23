from __future__ import annotations

import os
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parent.parent

_ARTIFACT_ALIASES = {
    "experiments_tmp/20260318_p5_takeoff_to_landing_continuous_v3_retrain_v1/final_model.zip": (
        "experiments/_archive_20260322_test_results/root_level/experiments_tmp/"
        "20260318_p5_takeoff_to_landing_continuous_v3_retrain_v1/final_model.zip"
    ),
    "experiments/20260319_p7_leader_c2_reporting_smoke_v2/final_model.zip": (
        "experiments/_archive_20260322_test_results/20260319_p7_leader_c2_reporting_smoke_v2/final_model.zip"
    ),
    "experiments/20260319_p7_leader_c2_task_chain_earlystop_v1/checkpoints/best_ema_model.zip": (
        "experiments/_archive_20260322_test_results/20260319_p7_leader_c2_task_chain_earlystop_v1/checkpoints/best_ema_model.zip"
    ),
    "experiments/20260319_p7_leader_c2_task_chain_baseline_v1_formal/final_model.zip": (
        "experiments/20260319_p7_leader_c2_task_chain_retrain_fix_v1/final_model.zip"
    ),
}


def _repo_relative(path: Path) -> str | None:
    try:
        return path.resolve().relative_to(_REPO_ROOT).as_posix()
    except Exception:
        return None


def resolve_artifact_path(path: str | os.PathLike[str] | None) -> str | None:
    if not path:
        return None

    raw_path = Path(str(path))
    direct = raw_path if raw_path.is_absolute() else (_REPO_ROOT / raw_path)
    if direct.exists():
        return str(direct.resolve())

    rel = raw_path.as_posix() if not raw_path.is_absolute() else _repo_relative(raw_path)
    if not rel:
        return str(direct.resolve())

    alias = _ARTIFACT_ALIASES.get(rel)
    if alias:
        candidate = (_REPO_ROOT / alias).resolve()
        if candidate.exists():
            return str(candidate)

    if rel.startswith("experiments_tmp/"):
        candidate = (_REPO_ROOT / "experiments" / "_archive_20260322_test_results" / "root_level" / rel).resolve()
        if candidate.exists():
            return str(candidate)
    if rel.startswith("experiments/"):
        candidate = (_REPO_ROOT / "experiments" / "_archive_20260322_test_results" / rel[len("experiments/") :]).resolve()
        if candidate.exists():
            return str(candidate)

    return str(direct.resolve())
