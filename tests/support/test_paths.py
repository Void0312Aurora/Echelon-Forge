from __future__ import annotations

import json
import sys
from pathlib import Path

from python.runtime_bootstrap import repo_root as runtime_repo_root
from tests.architecture import helpers as architecture_helpers
from tests.support.paths import (
  PYTHON_EXECUTABLE,
  REPO_ROOT,
  read_json,
  read_repo_text,
  repo_path,
)


def test_shared_paths_match_runtime_authority() -> None:
  assert REPO_ROOT == Path(runtime_repo_root()).resolve()
  assert PYTHON_EXECUTABLE == sys.executable
  assert repo_path() == REPO_ROOT
  assert repo_path("tests", Path("support")) == REPO_ROOT / "tests" / "support"


def test_shared_readers_accept_pathlike_inputs(tmp_path: Path) -> None:
  text_path = tmp_path / "utf8.txt"
  text_path.write_text("空战校准\n", encoding="utf-8")
  json_path = tmp_path / "payload.json"
  json_path.write_text(json.dumps({"status": "retained"}), encoding="utf-8")

  assert read_repo_text(text_path) == "空战校准\n"
  assert read_json(json_path) == {"status": "retained"}


def test_architecture_helpers_reexport_shared_path_api() -> None:
  assert architecture_helpers.REPO_ROOT is REPO_ROOT
  assert architecture_helpers.PYTHON_EXECUTABLE is PYTHON_EXECUTABLE
  assert architecture_helpers.repo_path is repo_path
  assert architecture_helpers.read_repo_text is read_repo_text
  assert architecture_helpers.read_json is read_json
