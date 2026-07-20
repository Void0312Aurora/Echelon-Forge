from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from python.experiment.report_envelope import (
  ENVELOPE_SCHEMA_VERSION,
  add_report_envelope_arg,
  apply_report_envelope,
  build_report_envelope,
  git_revision,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_bare_import_pulls_no_runtime_gym_or_sb3() -> None:
  """Zero-bootstrap-side-effect precedent (I30): standard library only."""
  probe = (
    "import sys\n"
    "before = set(sys.modules)\n"
    "import python.experiment.report_envelope\n"
    "after = set(sys.modules)\n"
    "new_roots = {m.split('.')[0] for m in after - before}\n"
    "forbidden = {'ef_py', 'gymnasium', 'stable_baselines3', 'torch'}\n"
    "assert not (new_roots & forbidden), new_roots & forbidden\n"
    "print('OK')\n"
  )
  result = subprocess.run(
    [sys.executable, "-c", probe],
    cwd=str(REPO_ROOT),
    capture_output=True,
    text=True,
    check=False,
  )
  assert result.returncode == 0, result.stdout + result.stderr
  assert result.stdout.strip() == "OK"


class TestBuildReportEnvelope:
  FIXED_TIME = datetime(2026, 1, 1, 12, 30, 0, tzinfo=timezone.utc)

  def test_schema_has_exactly_the_declared_top_level_keys_in_order(self) -> None:
    envelope = build_report_envelope(
      {"a": 1},
      tool_id="tools.demo",
      generated_at=self.FIXED_TIME,
      git_rev="deadbeef",
    )
    assert list(envelope) == [
      "envelope_schema_version",
      "tool_id",
      "generated_at",
      "git_rev",
      "experiment_ref",
      "payload",
    ]

  def test_schema_version_matches_module_constant(self) -> None:
    envelope = build_report_envelope(
      {"a": 1}, tool_id="tools.demo", generated_at=self.FIXED_TIME, autodetect_git_rev=False
    )
    assert envelope["envelope_schema_version"] == ENVELOPE_SCHEMA_VERSION
    assert isinstance(ENVELOPE_SCHEMA_VERSION, str)

  def test_payload_is_embedded_verbatim_same_object(self) -> None:
    payload = {"z": 1, "a": [1, 2, float("nan")]}
    envelope = build_report_envelope(payload, tool_id="tools.demo", autodetect_git_rev=False)
    assert envelope["payload"] is payload

  def test_payload_may_be_any_type_not_just_a_mapping(self) -> None:
    envelope = build_report_envelope([1, 2, 3], tool_id="tools.demo", autodetect_git_rev=False)
    assert envelope["payload"] == [1, 2, 3]

  def test_generated_at_is_naive_datetime_coerced_to_utc(self) -> None:
    naive = datetime(2026, 1, 1, 12, 30, 0)
    envelope = build_report_envelope({}, tool_id="tools.demo", generated_at=naive, autodetect_git_rev=False)
    assert envelope["generated_at"] == "2026-01-01T12:30:00+00:00"

  def test_generated_at_defaults_to_now_when_omitted(self) -> None:
    before = datetime.now(timezone.utc)
    envelope = build_report_envelope({}, tool_id="tools.demo", autodetect_git_rev=False)
    after = datetime.now(timezone.utc)
    generated_at = datetime.fromisoformat(envelope["generated_at"])
    assert before <= generated_at <= after

  def test_git_rev_explicit_value_is_used_verbatim_without_shelling_out(self) -> None:
    envelope = build_report_envelope(
      {}, tool_id="tools.demo", generated_at=self.FIXED_TIME, git_rev="cafef00d"
    )
    assert envelope["git_rev"] == "cafef00d"

  def test_git_rev_autodetects_when_omitted(self) -> None:
    envelope = build_report_envelope({}, tool_id="tools.demo", generated_at=self.FIXED_TIME)
    assert envelope["git_rev"] == git_revision()

  def test_git_rev_stays_none_when_autodetect_disabled(self) -> None:
    envelope = build_report_envelope(
      {}, tool_id="tools.demo", generated_at=self.FIXED_TIME, autodetect_git_rev=False
    )
    assert envelope["git_rev"] is None

  def test_experiment_ref_defaults_to_none_and_round_trips_when_supplied(self) -> None:
    default_envelope = build_report_envelope({}, tool_id="tools.demo", autodetect_git_rev=False)
    assert default_envelope["experiment_ref"] is None

    tagged_envelope = build_report_envelope(
      {}, tool_id="tools.demo", experiment_ref="air_combat_1v1_hmoe_execution_v1", autodetect_git_rev=False
    )
    assert tagged_envelope["experiment_ref"] == "air_combat_1v1_hmoe_execution_v1"

  @pytest.mark.parametrize("bad_tool_id", ["", "   ", None])
  def test_rejects_empty_or_missing_tool_id(self, bad_tool_id) -> None:
    with pytest.raises(ValueError):
      build_report_envelope({}, tool_id=bad_tool_id, autodetect_git_rev=False)

  @pytest.mark.parametrize("bad_ref", ["", "   "])
  def test_rejects_blank_experiment_ref(self, bad_ref) -> None:
    with pytest.raises(ValueError):
      build_report_envelope({}, tool_id="tools.demo", experiment_ref=bad_ref, autodetect_git_rev=False)


class TestGitRevision:
  def test_returns_the_checked_out_head_hash_in_this_repo(self) -> None:
    rev = git_revision(REPO_ROOT)
    assert rev is not None
    assert len(rev) == 40
    assert all(c in "0123456789abcdef" for c in rev)

  def test_returns_none_outside_any_git_work_tree(self, tmp_path: Path) -> None:
    assert git_revision(tmp_path) is None

  def test_returns_none_when_git_binary_is_unresolvable(self, monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*args, **kwargs):
      raise FileNotFoundError("git not found")

    monkeypatch.setattr(subprocess, "run", _boom)
    assert git_revision(REPO_ROOT) is None


class TestApplyReportEnvelope:
  def test_disabled_returns_the_identical_payload_object(self) -> None:
    payload = {"a": 1}
    result = apply_report_envelope(payload, enabled=False, tool_id="tools.demo")
    assert result is payload

  def test_disabled_ignores_extra_envelope_kwargs(self) -> None:
    payload = {"a": 1}
    result = apply_report_envelope(
      payload, enabled=False, tool_id="tools.demo", experiment_ref="whatever-not-validated"
    )
    assert result is payload

  def test_enabled_wraps_with_the_requested_tool_id(self) -> None:
    payload = {"a": 1}
    result = apply_report_envelope(payload, enabled=True, tool_id="tools.demo", autodetect_git_rev=False)
    assert result["tool_id"] == "tools.demo"
    assert result["payload"] is payload


class TestAddReportEnvelopeArg:
  def test_flag_defaults_to_disabled(self) -> None:
    parser = argparse.ArgumentParser()
    add_report_envelope_arg(parser)
    args = parser.parse_args([])
    assert args.report_envelope is False

  def test_flag_enables_when_passed(self) -> None:
    parser = argparse.ArgumentParser()
    add_report_envelope_arg(parser)
    args = parser.parse_args(["--report-envelope"])
    assert args.report_envelope is True

  def test_custom_default_and_help_are_honored(self) -> None:
    parser = argparse.ArgumentParser()
    add_report_envelope_arg(parser, default=True, help="custom help text")
    args = parser.parse_args([])
    assert args.report_envelope is True
    action = next(a for a in parser._actions if "--report-envelope" in a.option_strings)
    assert action.help == "custom help text"

  def test_flag_has_no_short_form_and_no_underscore_alias(self) -> None:
    parser = argparse.ArgumentParser()
    add_report_envelope_arg(parser)
    action = next(a for a in parser._actions if a.dest == "report_envelope")
    assert action.option_strings == ["--report-envelope"]
