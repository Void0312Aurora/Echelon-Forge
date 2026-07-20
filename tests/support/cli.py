from __future__ import annotations

import json
import os
import shlex
import subprocess
from pathlib import Path
from typing import Any

from tests.support.paths import PYTHON_EXECUTABLE, REPO_ROOT, repo_path


MAINTENANCE_ROOT = repo_path("tools", "maintenance").resolve()


def run_maintenance_cli(
  script: str,
  *args: str | Path,
  capture_output: bool = True,
) -> subprocess.CompletedProcess[str]:
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

  return subprocess.run(
    [
      PYTHON_EXECUTABLE,
      str(script_path),
      *script_args[1:],
      *(str(arg) for arg in args),
    ],
    cwd=REPO_ROOT,
    check=True,
    text=True,
    capture_output=capture_output,
  )


def run_maintenance_json_cli(script: str, *args: str | Path) -> Any:
  return json.loads(run_maintenance_cli(script, *args).stdout)
