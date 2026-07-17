from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize(
    "module_name",
    [
        "train",
        "evaluate",
        "_world_model_train_impl.bootstrap",
        "gym_envs.universal_env_parts.common",
        "gym_envs.leader_env",
        "scripts.benchmark_multi_agent",
    ],
)
def test_explicit_build_dir_without_extension_does_not_fall_back(
    tmp_path: Path,
    module_name: str,
) -> None:
    empty_build = tmp_path / "empty-build"
    empty_build.mkdir()
    env = os.environ.copy()
    env["CMO_BUILD_DIR"] = str(empty_build)

    result = subprocess.run(
        [sys.executable, "-c", f"import {module_name}"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "CMO_BUILD_DIR does not contain an ef_py artifact" in result.stderr
    assert str(empty_build) in result.stderr
