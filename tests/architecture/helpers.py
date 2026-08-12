from __future__ import annotations

import os
import shutil
import subprocess
import sys
import uuid
from collections.abc import Iterable, Mapping
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

import pytest

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
  from python.runtime_bootstrap import build_dirs

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


class _CppCompiler(NamedTuple):
  """A snippet compiler plus where it was discovered."""

  kind: str  # "gnu" or "msvc"
  executable: str
  origin: str


_MISSING_CPP_COMPILER_REASON = (
  "no C++ snippet compiler available: neither 'g++' nor MSVC 'cl.exe' is on "
  "PATH, and no CMAKE_CXX_COMPILER entry in a reachable CMakeCache.txt "
  "(CMO_BUILD_DIR or a repository build directory) points at one"
)

_GNU_COMPILER_STEMS = frozenset({"g++", "c++", "clang++"})

# flecs.h resolves FLECS_API to `__declspec(dllimport)` under MSVC unless
# `flecs_STATIC` is defined, and the repository only ever links the CMake
# static library. Without the define every flecs-backed snippet fails to link
# with unresolved `__imp_Ecs*` externals; it is inert for the snippets that
# never include flecs. GCC needs no equivalent -- its FLECS_API is empty.
_MSVC_SNIPPET_DEFINES = ("flecs_STATIC",)

_VCVARS_SCRIPTS = {
  "x64": "vcvars64.bat",
  "amd64": "vcvars64.bat",
  "x86": "vcvars32.bat",
  "arm64": "vcvarsarm64.bat",
  "arm": "vcvarsarm.bat",
}


def _cmake_cache_dirs() -> list[Path]:
  """Build directories that may carry a CMakeCache.txt worth reading."""

  candidates: list[Path] = []
  env_build = os.environ.get("CMO_BUILD_DIR", "").strip()
  if env_build:
    candidates.append(Path(env_build))
  try:
    candidates.extend(_candidate_build_dirs())
  except RuntimeError:
    # An unusable CMO_BUILD_DIR is the extension loader's problem, not the
    # snippet compiler's; keep scanning the in-tree build directories.
    pass
  candidates.extend(sorted(path for path in REPO_ROOT.glob("build*") if path.is_dir()))

  ordered: list[Path] = []
  seen: set[Path] = set()
  for candidate in candidates:
    try:
      resolved = candidate.resolve()
    except OSError:
      continue
    if resolved in seen:
      continue
    seen.add(resolved)
    ordered.append(resolved)
  return ordered


def _cmake_cache_cxx_compiler(build_dir: Path) -> Path | None:
  cache_path = build_dir / "CMakeCache.txt"
  if not cache_path.is_file():
    return None
  for line in cache_path.read_text(encoding="utf-8", errors="replace").splitlines():
    # Both `CMAKE_CXX_COMPILER:FILEPATH=` and `:STRING=` occur in the wild;
    # the `CMAKE_CXX_COMPILER-ADVANCED` entry must not match.
    if not line.startswith("CMAKE_CXX_COMPILER:"):
      continue
    _, _, value = line.partition("=")
    compiler = Path(value.strip())
    if compiler.is_file():
      return compiler
  return None


@lru_cache(maxsize=1)
def _detect_cpp_compiler() -> _CppCompiler | None:
  """Resolve the compiler used for inline C++ contract snippets.

  ``g++`` stays first and is still invoked by bare name, so the Linux CI
  command line is unchanged. MSVC is the Windows fallback: developer machines
  configured against VS BuildTools have no GCC at all, which used to turn every
  snippet-backed contract guard into a ``FileNotFoundError``.
  """

  gnu = shutil.which("g++")
  if gnu:
    return _CppCompiler("gnu", "g++", f"PATH ({gnu})")

  msvc = shutil.which("cl")
  if msvc:
    return _CppCompiler("msvc", msvc, f"PATH ({msvc})")

  for build_dir in _cmake_cache_dirs():
    compiler = _cmake_cache_cxx_compiler(build_dir)
    if compiler is None:
      continue
    origin = f"CMAKE_CXX_COMPILER in {build_dir / 'CMakeCache.txt'}"
    if compiler.stem.lower() == "cl":
      return _CppCompiler("msvc", str(compiler), origin)
    if compiler.stem.lower() in _GNU_COMPILER_STEMS:
      return _CppCompiler("gnu", str(compiler), origin)
  return None


def _vcvars_script(cl_path: Path) -> Path | None:
  script_name = _VCVARS_SCRIPTS.get(cl_path.parent.name.lower(), "vcvars64.bat")
  for parent in cl_path.parents:
    if parent.name.upper() != "VC":
      continue
    script = parent / "Auxiliary" / "Build" / script_name
    if script.is_file():
      return script
  return None


def _captured_vcvars_environment(script: Path) -> dict[str, str] | None:
  result = subprocess.run(
    ["cmd", "/d", "/c", f'call "{script}" >nul && set'],
    text=True,
    capture_output=True,
    check=False,
    errors="replace",
  )
  if result.returncode != 0:
    return None

  environment: dict[str, str] = {}
  for line in result.stdout.splitlines():
    key, separator, value = line.partition("=")
    # `set` also lists the per-drive `=C:` cursors, which are not real vars.
    if not separator or not key or key.startswith("="):
      continue
    environment[key] = value
  return environment or None


def _newest_windows_sdk() -> tuple[Path, str] | None:
  roots = [
    Path(os.environ["WindowsSdkDir"]) if os.environ.get("WindowsSdkDir") else None,
    Path(r"C:\Program Files (x86)\Windows Kits\10"),
    Path(r"C:\Program Files\Windows Kits\10"),
  ]
  for root in roots:
    if root is None or not (root / "Include").is_dir():
      continue
    versions = sorted(
      (path.name for path in (root / "Include").iterdir() if (path / "um").is_dir()),
    )
    if versions:
      return root, versions[-1]
  return None


def _derived_msvc_environment(cl_path: Path) -> dict[str, str] | None:
  """Minimal INCLUDE/LIB derived straight from the cl.exe location.

  Only reached when the toolchain has no ``vcvars`` script to source; the
  layout is ``<msvc>/bin/Host<host>/<target>/cl.exe``.
  """

  if len(cl_path.parents) < 4:
    return None
  msvc_root = cl_path.parents[3]
  target = cl_path.parent.name
  include_dirs = [msvc_root / "include"]
  lib_dirs = [msvc_root / "lib" / target]
  if not include_dirs[0].is_dir() or not lib_dirs[0].is_dir():
    return None

  sdk = _newest_windows_sdk()
  if sdk is None:
    return None
  sdk_root, sdk_version = sdk
  include_dirs.extend(
    sdk_root / "Include" / sdk_version / part
    for part in ("ucrt", "shared", "um", "winrt")
  )
  lib_dirs.extend(
    sdk_root / "Lib" / sdk_version / part / target for part in ("ucrt", "um")
  )

  environment = dict(os.environ)
  environment["INCLUDE"] = os.pathsep.join(
    str(path) for path in include_dirs if path.is_dir()
  )
  environment["LIB"] = os.pathsep.join(str(path) for path in lib_dirs if path.is_dir())
  environment["PATH"] = os.pathsep.join(
    [str(cl_path.parent), environment.get("PATH", "")]
  )
  return environment


@lru_cache(maxsize=None)
def _msvc_environment(executable: str) -> dict[str, str] | None:
  """The INCLUDE/LIB/PATH environment cl.exe needs, or None if unresolvable."""

  if os.environ.get("INCLUDE") and os.environ.get("LIB"):
    # Already running inside a developer command prompt.
    return dict(os.environ)

  cl_path = Path(executable)
  script = _vcvars_script(cl_path)
  if script is not None:
    captured = _captured_vcvars_environment(script)
    if captured:
      return captured
  return _derived_msvc_environment(cl_path)


def _dependency_platform_link_args(dependency: str, *, msvc: bool) -> list[str]:
  # MinGW static flecs builds retain their Winsock imports; CMake normally
  # supplies this transitive dependency, while standalone snippet links do not.
  if dependency == "flecs" and os.name == "nt":
    return ["ws2_32.lib"] if msvc else ["-lws2_32"]
  return []


def _dependency_static_library_names(dependency: str, *, msvc: bool) -> list[str]:
  if msvc:
    names = [f"{dependency}_static.lib", f"{dependency}.lib"]
    if dependency == "flecs":
      names.insert(0, "ef_flecs.lib")
    return names
  names = [f"lib{dependency}_static.a", f"lib{dependency}.a"]
  if dependency == "flecs":
    names.insert(0, "libef_flecs.a")
  return names


def dependency_link_args(dependency: str) -> list[str]:
  compiler = _detect_cpp_compiler()
  msvc = compiler is not None and compiler.kind == "msvc"
  for build_dir in _candidate_build_dirs():
    library_dirs = [build_dir / "_deps" / f"{dependency}-build", build_dir]
    static_names = _dependency_static_library_names(dependency, msvc=msvc)
    for lib_dir in library_dirs:
      for static_name in static_names:
        static_lib = lib_dir / static_name
        if static_lib.is_file():
          return [
            str(static_lib),
            *_dependency_platform_link_args(dependency, msvc=msvc),
          ]
      if msvc:
        continue
      shared_lib = lib_dir / f"lib{dependency}.so"
      if shared_lib.is_file():
        return [
          "-L",
          str(lib_dir),
          f"-l{dependency}",
          f"-Wl,-rpath,{lib_dir}",
          *_dependency_platform_link_args(dependency, msvc=msvc),
        ]
  return []


def _snippet_dir() -> Path:
  binary_dir = repo_path("build-local-win", "_cpp_snippets")
  binary_dir.mkdir(parents=True, exist_ok=True)
  return binary_dir


def _run_snippet_binary(
  binary: Path,
  env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
  run_result = subprocess.run(
    [str(binary)],
    text=True,
    capture_output=True,
    check=False,
    cwd=REPO_ROOT,
    env=env,
  )
  try:
    binary.unlink()
  except OSError:
    pass
  return run_result


def _compile_cpp_snippet_gnu(
  executable: str,
  source: str,
  include_paths: Iterable[Path],
  link_args: Iterable[str | os.PathLike[str]],
  syntax_only: bool,
) -> subprocess.CompletedProcess[str]:
  command = [
    executable,
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
    binary = _snippet_dir() / f"cpp_snippet_{uuid.uuid4().hex}{suffix}"
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
  return _run_snippet_binary(binary)


def _compile_cpp_snippet_msvc(
  executable: str,
  source: str,
  include_paths: Iterable[Path],
  link_args: Iterable[str | os.PathLike[str]],
  syntax_only: bool,
) -> subprocess.CompletedProcess[str]:
  environment = _msvc_environment(executable)
  if environment is None:
    pytest.skip(
      f"MSVC compiler {executable!r} was found but its INCLUDE/LIB environment "
      "could not be resolved (no vcvars script and no derivable Windows SDK)"
    )

  snippet_dir = _snippet_dir()
  stem = f"cpp_snippet_{uuid.uuid4().hex}"
  # cl.exe cannot read a translation unit from stdin, so the snippet has to
  # land on disk before it can be compiled.
  snippet_source = snippet_dir / f"{stem}.cpp"
  snippet_source.write_text(source, encoding="utf-8")

  command = [executable, "/nologo", "/EHsc", "/std:c++20", "/MD"]
  command.extend(f"/D{define}" for define in _MSVC_SNIPPET_DEFINES)
  if syntax_only:
    command.append("/Zs")
  command.extend(["/I", str(repo_path("src"))])
  for include_path in include_paths:
    command.extend(["/I", str(include_path)])
  command.append(str(snippet_source))

  binary: Path | None = None
  object_file: Path | None = None
  if not syntax_only:
    binary = snippet_dir / f"{stem}.exe"
    object_file = snippet_dir / f"{stem}.obj"
    command.append(f"/Fo{object_file}")
    command.append(f"/Fe:{binary}")
    command.extend(str(arg) for arg in link_args)

  try:
    compile_result = subprocess.run(
      command,
      text=True,
      capture_output=True,
      check=False,
      cwd=snippet_dir,
      env=environment,
      errors="replace",
    )
    # cl.exe reports diagnostics on stdout, unlike GCC.
    assert compile_result.returncode == 0, (
      compile_result.stderr or compile_result.stdout
    )
  finally:
    for artifact in (snippet_source, object_file):
      if artifact is None:
        continue
      try:
        artifact.unlink()
      except OSError:
        pass

  if syntax_only:
    return compile_result

  assert binary is not None
  return _run_snippet_binary(binary, env=environment)


def compile_cpp_snippet(
  source: str,
  *,
  include_paths: Iterable[Path] = (),
  link_args: Iterable[str | os.PathLike[str]] = (),
  syntax_only: bool = False,
  binary_prefix: str = "architecture_cpp_snippet",
) -> subprocess.CompletedProcess[str]:
  compiler = _detect_cpp_compiler()
  if compiler is None:
    pytest.skip(_MISSING_CPP_COMPILER_REASON)

  if compiler.kind == "msvc":
    return _compile_cpp_snippet_msvc(
      compiler.executable, source, include_paths, link_args, syntax_only
    )
  return _compile_cpp_snippet_gnu(
    compiler.executable, source, include_paths, link_args, syntax_only
  )
