from __future__ import annotations

import contextlib
import importlib
import io
import json
import os
import shlex
import subprocess
import sys
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path
from typing import Any

from tests.support.paths import PYTHON_EXECUTABLE, REPO_ROOT, repo_path


MAINTENANCE_ROOT = repo_path("tools", "maintenance").resolve()
MAINTENANCE_PACKAGE = "tools.maintenance"


def _resolve_invocation(
  script: str,
  args: tuple[str | Path, ...],
) -> tuple[Path, list[str]]:
  """Split ``script`` into an entrypoint path plus its argument vector.

  The path boundary is the security-relevant half: callers may name a script
  plus leading sub-command words in one string, but the resolved file must
  still live under ``tools/maintenance``.
  """
  script_args = shlex.split(script, posix=os.name != "nt")
  if not script_args:
    raise ValueError("maintenance script must not be empty")

  script_path = (MAINTENANCE_ROOT / script_args[0]).resolve()
  try:
    script_path.relative_to(MAINTENANCE_ROOT)
  except ValueError as exc:
    raise ValueError(
      "maintenance script must stay within tools/maintenance"
    ) from exc

  return script_path, [*script_args[1:], *(str(arg) for arg in args)]


def run_maintenance_cli(
  script: str,
  *args: str | Path,
  capture_output: bool = True,
) -> subprocess.CompletedProcess[str]:
  script_path, cli_args = _resolve_invocation(script, args)

  return subprocess.run(
    [
      PYTHON_EXECUTABLE,
      str(script_path),
      *cli_args,
    ],
    cwd=REPO_ROOT,
    check=True,
    text=True,
    capture_output=capture_output,
  )


def run_maintenance_json_cli(script: str, *args: str | Path) -> Any:
  return json.loads(run_maintenance_cli(script, *args).stdout)


def _load_entrypoint(script_path: Path) -> Callable[[list[str]], Any]:
  relative = script_path.relative_to(MAINTENANCE_ROOT).with_suffix("")
  module_name = ".".join((MAINTENANCE_PACKAGE, *relative.parts))
  module = importlib.import_module(module_name)
  entrypoint = getattr(module, "main", None)
  if not callable(entrypoint):
    raise ValueError(f"{module_name} exposes no callable main() entrypoint")
  return entrypoint


@contextlib.contextmanager
def _spawned_process_scope(argv: Sequence[str]) -> Iterator[None]:
  """Give in-process runs the ambient state a spawned CLI would have.

  ``run_maintenance_cli`` spawns with ``cwd=REPO_ROOT`` and an argv that names
  only the CLI, so producers resolving relative paths or reading ``sys.argv``
  must not observe the pytest process instead. Both are restored even when the
  entrypoint raises.
  """
  previous_argv = sys.argv
  previous_cwd = os.getcwd()
  sys.argv = list(argv)
  os.chdir(REPO_ROOT)
  try:
    yield
  finally:
    os.chdir(previous_cwd)
    sys.argv = previous_argv


def run_maintenance_cli_in_process(
  script: str,
  *args: str | Path,
  capture_output: bool = True,
  check: bool = True,
) -> subprocess.CompletedProcess[str]:
  """Drive a maintenance CLI through ``main(argv)`` in the current interpreter.

  Same call shape and same ``CompletedProcess`` result as
  ``run_maintenance_cli``, without restarting the interpreter and re-importing
  the whole producer stack per assertion.
  """
  script_path, cli_args = _resolve_invocation(script, args)
  command = [PYTHON_EXECUTABLE, str(script_path), *cli_args]
  entrypoint = _load_entrypoint(script_path)

  stdout = io.StringIO()
  stderr = io.StringIO()
  with contextlib.ExitStack() as scope:
    scope.enter_context(_spawned_process_scope([str(script_path), *cli_args]))
    if capture_output:
      scope.enter_context(contextlib.redirect_stdout(stdout))
      scope.enter_context(contextlib.redirect_stderr(stderr))
    try:
      raw_code = entrypoint(cli_args)
    except SystemExit as exc:
      # argparse (and any hard-failing producer) exits instead of returning;
      # mirror the interpreter's own translation of the exit argument.
      raw_code = exc.code
      if raw_code is not None and not isinstance(raw_code, int):
        print(raw_code, file=sys.stderr)
        raw_code = 1

  completed = subprocess.CompletedProcess(
    command,
    0 if raw_code is None else int(raw_code),
    stdout.getvalue() if capture_output else None,
    stderr.getvalue() if capture_output else None,
  )
  if check and completed.returncode != 0:
    raise subprocess.CalledProcessError(
      completed.returncode,
      command,
      completed.stdout,
      completed.stderr,
    )
  return completed


def run_maintenance_json_cli_in_process(script: str, *args: str | Path) -> Any:
  return json.loads(run_maintenance_cli_in_process(script, *args).stdout)
