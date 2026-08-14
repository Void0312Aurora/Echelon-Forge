from __future__ import annotations

import os
import subprocess
import sys
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


def _stub_entrypoint(monkeypatch, main) -> None:
  monkeypatch.setattr(cli, "_load_entrypoint", lambda script_path: main)


def test_in_process_variant_resolves_the_maintenance_package_module(
  monkeypatch,
) -> None:
  requested: list[str] = []

  class _Entrypoint:
    @staticmethod
    def main(argv):
      return 0

  class _Importlib:
    """Local stand-in so the patch cannot leak into unrelated imports."""

    @staticmethod
    def import_module(name: str):
      requested.append(name)
      return _Entrypoint

  monkeypatch.setattr(cli, "importlib", _Importlib)

  cli.run_maintenance_cli_in_process("dto_schema/generate.py --check")

  assert requested == ["tools.maintenance.dto_schema.generate"]


def test_in_process_variant_returns_a_subprocess_shaped_result(monkeypatch) -> None:
  received: list[list[str]] = []

  def main(argv):
    received.append(list(argv))
    print("emitted")
    return 0

  _stub_entrypoint(monkeypatch, main)

  result = cli.run_maintenance_cli_in_process(
    "dto_schema/generate.py --check",
    "--manifest",
    Path("candidate.json"),
  )

  assert received == [["--check", "--manifest", "candidate.json"]]
  assert isinstance(result, subprocess.CompletedProcess)
  assert result.returncode == 0
  assert result.stdout == "emitted\n"
  assert result.stderr == ""
  assert result.args == [
    cli.PYTHON_EXECUTABLE,
    str(cli.MAINTENANCE_ROOT / "dto_schema" / "generate.py"),
    "--check",
    "--manifest",
    "candidate.json",
  ]


def test_in_process_variant_gives_the_entrypoint_a_spawned_process_view(
  monkeypatch, tmp_path: Path
) -> None:
  observed: dict[str, object] = {}

  def main(argv):
    observed["cwd"] = Path.cwd()
    observed["argv"] = list(sys.argv)
    return 0

  _stub_entrypoint(monkeypatch, main)
  monkeypatch.chdir(tmp_path)
  sentinel_argv = list(sys.argv)

  cli.run_maintenance_cli_in_process("dto_schema/generate.py --check", "--dry-run")

  assert observed["cwd"] == cli.REPO_ROOT
  assert observed["argv"] == [
    str(cli.MAINTENANCE_ROOT / "dto_schema" / "generate.py"),
    "--check",
    "--dry-run",
  ]
  # The pytest process keeps the state it had before the call.
  assert Path(os.getcwd()) == tmp_path
  assert sys.argv == sentinel_argv


def test_in_process_variant_restores_process_state_after_a_crash(
  monkeypatch, tmp_path: Path
) -> None:
  def main(argv):
    raise RuntimeError("producer exploded")

  _stub_entrypoint(monkeypatch, main)
  monkeypatch.chdir(tmp_path)
  sentinel_argv = list(sys.argv)

  with pytest.raises(RuntimeError, match="producer exploded"):
    cli.run_maintenance_cli_in_process("dto_schema/generate.py --check")

  assert Path(os.getcwd()) == tmp_path
  assert sys.argv == sentinel_argv


def test_in_process_variant_translates_argparse_exits(monkeypatch) -> None:
  def main(argv):
    print("usage: generate.py", file=sys.stderr)
    raise SystemExit(2)

  _stub_entrypoint(monkeypatch, main)

  with pytest.raises(subprocess.CalledProcessError) as failure:
    cli.run_maintenance_cli_in_process("dto_schema/generate.py bogus-domain")

  assert failure.value.returncode == 2
  assert failure.value.stderr == "usage: generate.py\n"

  tolerated = cli.run_maintenance_cli_in_process(
    "dto_schema/generate.py bogus-domain", check=False
  )
  assert tolerated.returncode == 2


def test_in_process_variant_reports_a_string_exit_like_the_interpreter(
  monkeypatch,
) -> None:
  def main(argv):
    raise SystemExit("fail-closed: missing evidence")

  _stub_entrypoint(monkeypatch, main)

  result = cli.run_maintenance_cli_in_process(
    "dto_schema/generate.py bogus", check=False
  )

  assert result.returncode == 1
  assert result.stderr == "fail-closed: missing evidence\n"


def test_in_process_variant_leaves_output_uncaptured_on_request(
  monkeypatch, capsys
) -> None:
  def main(argv):
    print("straight through")
    return 0

  _stub_entrypoint(monkeypatch, main)

  result = cli.run_maintenance_cli_in_process(
    "dto_schema/generate.py --check", capture_output=False
  )

  assert result.stdout is None
  assert result.stderr is None
  assert "straight through" in capsys.readouterr().out


def test_in_process_json_variant_parses_stdout(monkeypatch) -> None:
  def main(argv):
    print('{"status": "clean"}')
    return 0

  _stub_entrypoint(monkeypatch, main)

  assert cli.run_maintenance_json_cli_in_process("dto_schema/generate.py") == {
    "status": "clean"
  }


@pytest.mark.parametrize(
  "script",
  [
    "  ",
    "../diagnostics/calibration_admission_audit.py",
    str(cli.REPO_ROOT / "outside_maintenance.py"),
  ],
)
def test_in_process_variant_keeps_the_maintenance_path_boundary(script: str) -> None:
  with pytest.raises(ValueError):
    cli.run_maintenance_cli_in_process(script)
