from __future__ import annotations

import os
import subprocess
import sys
import uuid
from collections.abc import Iterable
from pathlib import Path

from tests.support.paths import (
  PYTHON_EXECUTABLE,
  REPO_ROOT,
  read_json,
  read_repo_text,
  repo_path,
)


def ensure_repo_root_on_sys_path() -> None:
  repo = str(REPO_ROOT)
  if repo not in sys.path:
    sys.path.insert(0, repo)


def _candidate_build_dirs() -> list[Path]:
  from python.testing.runtime import build_dirs

  return [Path(path) for path in build_dirs(str(REPO_ROOT))]


def _dependency_source_dirs(build_dir: Path, dependency: str) -> list[Path]:
  candidates = [build_dir / "_deps" / f"{dependency}-src"]
  cache_path = build_dir / "CMakeCache.txt"
  if cache_path.is_file():
    cache_keys = {
      f"FETCHCONTENT_SOURCE_DIR_{dependency.upper()}",
      f"{dependency}_SOURCE_DIR",
    }
    for line in cache_path.read_text(encoding="utf-8", errors="replace").splitlines():
      if not line or line.startswith(("#", "//")) or "=" not in line:
        continue
      key_with_type, value = line.split("=", 1)
      key = key_with_type.split(":", 1)[0]
      if key not in cache_keys or not value.strip():
        continue
      source_dir = Path(value.strip())
      if not source_dir.is_absolute():
        source_dir = build_dir / source_dir
      candidates.append(source_dir)

  ordered: list[Path] = []
  seen: set[Path] = set()
  for candidate in candidates:
    resolved = candidate.resolve()
    if resolved in seen:
      continue
    seen.add(resolved)
    ordered.append(resolved)
  return ordered


def dependency_include_path(dependency: str) -> Path:
  for build_dir in _candidate_build_dirs():
    for source_dir in _dependency_source_dirs(build_dir, dependency):
      include_dir = source_dir / "include"
      if include_dir.is_dir():
        return include_dir
  raise AssertionError(
    f"Could not find include directory for CMake dependency {dependency!r}"
  )


def dependency_link_args(dependency: str) -> list[str]:
  for build_dir in _candidate_build_dirs():
    library_dirs = [build_dir / "_deps" / f"{dependency}-build", build_dir]
    static_names = [f"lib{dependency}_static.a", f"lib{dependency}.a"]
    if dependency == "flecs":
      static_names.insert(0, "libef_flecs.a")
    for lib_dir in library_dirs:
      for static_name in static_names:
        static_lib = lib_dir / static_name
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
    suffix = ".exe" if os.name == "nt" else ""
    binary_dir = repo_path("build-local-win", "_cpp_snippets")
    binary_dir.mkdir(parents=True, exist_ok=True)
    binary = binary_dir / f"cpp_snippet_{uuid.uuid4().hex}{suffix}"
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
