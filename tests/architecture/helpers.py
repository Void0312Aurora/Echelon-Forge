from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import uuid
from collections.abc import Iterable
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON_EXECUTABLE = sys.executable


def repo_path(*parts: str | os.PathLike[str]) -> Path:
  path = REPO_ROOT
  for part in parts:
    path /= part
  return path


def read_repo_text(*parts: str | os.PathLike[str]) -> str:
  return repo_path(*parts).read_text(encoding="utf-8")


def read_json(path: Path) -> Any:
  return json.loads(path.read_text(encoding="utf-8"))


def ensure_repo_root_on_sys_path() -> None:
  repo = str(REPO_ROOT)
  if repo not in sys.path:
    sys.path.insert(0, repo)


def _candidate_build_dirs() -> list[Path]:
  from python.testing.runtime import build_dirs

  return [Path(path) for path in build_dirs(str(REPO_ROOT))]


def dependency_include_path(dependency: str) -> Path:
  for build_dir in _candidate_build_dirs():
    include_dir = build_dir / "_deps" / f"{dependency}-src" / "include"
    if include_dir.is_dir():
      return include_dir
  raise AssertionError(
    f"Could not find include directory for CMake dependency {dependency!r}"
  )


def dependency_link_args(dependency: str) -> list[str]:
  for build_dir in _candidate_build_dirs():
    lib_dir = build_dir / "_deps" / f"{dependency}-build"
    static_lib = lib_dir / f"lib{dependency}_static.a"
    if static_lib.is_file():
      return [str(static_lib)]
    shared_lib = lib_dir / f"lib{dependency}.so"
    if shared_lib.is_file():
      return ["-L", str(lib_dir), f"-l{dependency}", f"-Wl,-rpath,{lib_dir}"]
  return []


def compile_cpp_snippet(
  source: str,
  *,
  include_paths: Iterable[Path] = (),
  link_args: Iterable[str | os.PathLike[str]] = (),
  syntax_only: bool = False,
  binary_prefix: str = "architecture_cpp_snippet",
) -> subprocess.CompletedProcess[str]:
  command = [
    "g++",
    "-std=c++20",
  ]
  if syntax_only:
    command.append("-fsyntax-only")
  command.extend(["-I", str(repo_path("src"))])
  for include_path in include_paths:
    command.extend(["-I", str(include_path)])
  command.extend(["-x", "c++", "-"])

  binary: Path | None = None
  if not syntax_only:
    safe_prefix = re.sub(r"[^A-Za-z0-9_.-]+", "_", binary_prefix)
    binary = Path(tempfile.gettempdir()) / f"{safe_prefix}_{uuid.uuid4().hex}"
    command.extend(["-x", "none", "-o", str(binary)])
    command.extend(str(arg) for arg in link_args)

  compile_result = subprocess.run(
    command,
    input=source,
    text=True,
    capture_output=True,
    check=False,
    cwd=REPO_ROOT,
  )
  assert compile_result.returncode == 0, compile_result.stderr
  if syntax_only:
    return compile_result

  assert binary is not None
  run_result = subprocess.run(
    [str(binary)],
    text=True,
    capture_output=True,
    check=False,
    cwd=REPO_ROOT,
  )
  try:
    binary.unlink()
  except OSError:
    pass
  return run_result
