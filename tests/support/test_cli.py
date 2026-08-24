from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests.support import cli


def test_run_maintenance_cli_preserves_script_and_argument_order(monkeypatch) -> None:
  calls: list[tuple[list[str], dict[str, object]]] = []

  def fake_run(command: list[str], **kwargs):
    calls.append((command, kwargs))
    return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

  monkeypatch.setattr(cli.subprocess, "run", fake_run)

  result = cli.run_maintenance_cli(
    "dto_schema/generate.py --check",
    "--manifest",
    Path("candidate.json"),
    capture_output=False,
  )

  assert result.stdout == "ok\n"
  assert calls == [
    (
      [
        cli.PYTHON_EXECUTABLE,
        str(cli.MAINTENANCE_ROOT / "dto_schema" / "generate.py"),
        "--check",
        "--manifest",
        "candidate.json",
      ],
      {
        "cwd": cli.REPO_ROOT,
        "check": True,
        "text": True,
        "capture_output": False,
      },
    )
  ]


def test_run_maintenance_json_cli_parses_stdout(monkeypatch) -> None:
  completed = subprocess.CompletedProcess(
    ["maintenance"],
    0,
    stdout='{"status": "clean"}',
    stderr="",
  )
  monkeypatch.setattr(cli, "run_maintenance_cli", lambda *args, **kwargs: completed)

  assert cli.run_maintenance_json_cli("dto_schema/generate.py") == {"status": "clean"}


def test_run_maintenance_cli_rejects_empty_script() -> None:
  with pytest.raises(ValueError, match="must not be empty"):
    cli.run_maintenance_cli("  ")


@pytest.mark.parametrize(
  "script",
  [
    "../diagnostics/calibration_admission_audit.py",
    str(cli.REPO_ROOT / "outside_maintenance.py"),
  ],
)
def test_run_maintenance_cli_rejects_scripts_outside_maintenance(script: str) -> None:
  with pytest.raises(ValueError, match="must stay within tools/maintenance"):
    cli.run_maintenance_cli(script)
