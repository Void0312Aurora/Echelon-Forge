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


@pytest.mark.skipif(os.name != "nt", reason="Windows multi-config build layout")
def test_windows_multi_config_extension_directory_is_importable(tmp_path: Path) -> None:
    build_dir = tmp_path / "build-local-win"
    package_dir = build_dir / "Release" / "ef_py"
    package_dir.mkdir(parents=True)
    (package_dir / "__init__.py").write_text(
        "LAYOUT_SENTINEL = 'multi-config-release'\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["CMO_BUILD_DIR"] = str(build_dir)

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from python.runtime_bootstrap import configure_repo_imports; "
                "configure_repo_imports(); import ef_py; print(ef_py.LAYOUT_SENTINEL)"
            ),
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "multi-config-release"
