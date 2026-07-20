from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from python.testing.runtime import repo_root as runtime_repo_root


REPO_ROOT = Path(runtime_repo_root()).resolve()
PYTHON_EXECUTABLE = sys.executable


def repo_path(*parts: str | os.PathLike[str]) -> Path:
  path = REPO_ROOT
  for part in parts:
    path /= part
  return path


def read_repo_text(*parts: str | os.PathLike[str]) -> str:
  return repo_path(*parts).read_text(encoding="utf-8")


def read_json(path: str | os.PathLike[str]) -> Any:
  return json.loads(Path(path).read_text(encoding="utf-8"))
