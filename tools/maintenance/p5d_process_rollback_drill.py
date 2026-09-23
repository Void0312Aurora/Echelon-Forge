"""Run one local supported-row runtime process for a P5-D rollback drill.

The parent process owns the rollout decision and the SQLite ArtifactLedger.
This module only starts a real Python process that imports the selected local
``ef_py`` build, constructs one ``RuntimeFacade``, and waits for an explicit
stop signal.  It is intentionally local and single-process; it does not add a
runtime publication authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Any
from uuid import uuid4


_WORKER_FLAG = "--p5d-runtime-worker"


def _find_native_binding(build_dir: Path) -> Path:
  candidates = sorted(build_dir.glob("Release/ef_py*.pyd"))
  if not candidates:
    candidates = sorted(build_dir.glob("RelWithDebInfo/ef_py*.pyd"))
  if not candidates:
    candidates = sorted(build_dir.glob("Debug/ef_py*.pyd"))
  if not candidates:
    raise RuntimeError(f"no local ef_py binding found under {build_dir}")
  return candidates[0]


def _sha256(path: Path) -> str:
  digest = hashlib.sha256()
  with path.open("rb") as handle:
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
      digest.update(chunk)
  return digest.hexdigest()


@dataclass(slots=True)
class RuntimeProcess:
  """A real local runtime process and its observed package identity."""

  process: subprocess.Popen[str]
  ready_path: Path
  stop_path: Path
  observation: dict[str, Any]

  def stop(self, *, timeout_s: float = 30.0) -> None:
    self.stop_path.write_text("stop\n", encoding="utf-8")
    try:
      self.process.wait(timeout=timeout_s)
    except subprocess.TimeoutExpired:
      self.process.kill()
      self.process.wait(timeout=timeout_s)
      raise RuntimeError("runtime process did not stop after the rollback signal")
    if self.process.returncode != 0:
      raise RuntimeError(f"runtime process exited with code {self.process.returncode}")


def launch_runtime_process(
  build_dir: str | Path,
  *,
  epoch: str,
  state_dir: str | Path,
  timeout_s: float = 30.0,
) -> RuntimeProcess:
  """Start and observe one actual local ``RuntimeFacade`` process."""

  resolved_build = Path(build_dir).resolve()
  binding = _find_native_binding(resolved_build)
  root = Path(__file__).resolve().parents[2]
  state = Path(state_dir)
  state.mkdir(parents=True, exist_ok=True)
  token = uuid4().hex
  ready_path = state / f"ready-{token}.json"
  stop_path = state / f"stop-{token}"
  environment = os.environ.copy()
  environment["CMO_BUILD_DIR"] = str(resolved_build)
  python_path = environment.get("PYTHONPATH", "")
  environment["PYTHONPATH"] = str(root) if not python_path else f"{root}{os.pathsep}{python_path}"
  command = [
    sys.executable,
    str(Path(__file__).resolve()),
    _WORKER_FLAG,
    "--build-dir", str(resolved_build),
    "--epoch", epoch,
    "--ready", str(ready_path),
    "--stop", str(stop_path),
  ]
  process = subprocess.Popen(
    command,
    cwd=root,
    env=environment,
    text=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
  )
  deadline = time.monotonic() + timeout_s
  while time.monotonic() < deadline:
    if ready_path.is_file():
      try:
        observation = json.loads(ready_path.read_text(encoding="utf-8"))
      except json.JSONDecodeError as error:
        process.kill()
        process.wait(timeout=timeout_s)
        raise RuntimeError("runtime process wrote malformed readiness evidence") from error
      if not isinstance(observation, dict):
        process.kill()
        process.wait(timeout=timeout_s)
        raise RuntimeError("runtime process readiness evidence is not an object")
      expected = {
        "build_dir": str(resolved_build),
        "epoch": epoch,
        "facade_type": "RuntimeFacade",
        "pyd_sha256": _sha256(binding),
      }
      for field, value in expected.items():
        if observation.get(field) != value:
          process.kill()
          process.wait(timeout=timeout_s)
          raise RuntimeError(f"runtime process readiness field {field!r} differs")
      return RuntimeProcess(process, ready_path, stop_path, observation)
    if process.poll() is not None:
      stdout, stderr = process.communicate()
      raise RuntimeError(
        f"runtime process exited before readiness: code={process.returncode}, "
        f"stdout={stdout[-1000:]!r}, stderr={stderr[-1000:]!r}"
      )
    time.sleep(0.02)
  process.kill()
  process.wait(timeout=timeout_s)
  raise RuntimeError("runtime process did not publish readiness evidence")


def _run_worker(args: argparse.Namespace) -> int:
  from python.runtime_bootstrap import ensure_repo_imports

  ensure_repo_imports()
  import ef_py

  build_dir = Path(args.build_dir).resolve()
  binding = _find_native_binding(build_dir)
  facade = ef_py.RuntimeFacade(1)
  ready = {
    "build_dir": str(build_dir),
    "epoch": args.epoch,
    "facade_type": type(facade).__name__,
    "pid": os.getpid(),
    "boot_identity": uuid4().hex,
    "pyd_sha256": _sha256(binding),
  }
  ready_path = Path(args.ready)
  ready_path.parent.mkdir(parents=True, exist_ok=True)
  ready_path.write_text(json.dumps(ready, sort_keys=True), encoding="utf-8")
  stop_path = Path(args.stop)
  while not stop_path.exists():
    time.sleep(0.02)
  del facade
  return 0


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument(_WORKER_FLAG, action="store_true")
  parser.add_argument("--build-dir", required=True)
  parser.add_argument("--epoch", required=True)
  parser.add_argument("--ready", required=True)
  parser.add_argument("--stop", required=True)
  args = parser.parse_args(argv)
  if not args.p5d_runtime_worker:
    parser.error("the worker entry point is internal; call launch_runtime_process from a drill")
  return _run_worker(args)


if __name__ == "__main__":
  raise SystemExit(main())
