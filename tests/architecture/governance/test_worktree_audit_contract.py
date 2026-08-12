"""Classification contract for `tools/maintenance/audit_worktrees.py`.

Every case here builds a synthetic worktree inventory under `tmp_path` and
injects the status probe. The real repository is deliberately never audited:
its worktree layout is the thing the tool exists to report on, so asserting
against it would make this guard fail for the reason it was written.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

from tools.maintenance import audit_worktrees as audit


CLEAN = audit.StatusProbe(reachable=True, untracked=0)
DUBIOUS_OWNERSHIP = audit.StatusProbe(
  reachable=False,
  untracked=0,
  error="fatal: detected dubious ownership in repository at 'X'",
  needed_ownership_override=True,
)


def _entry(path: Path, branch: str = "refs/heads/topic") -> audit.WorktreeEntry:
  return audit.WorktreeEntry(path=path.as_posix(), head="0" * 40, branch=branch)


def _probe(mapping: dict[str, audit.StatusProbe]):
  def probe(path: str) -> audit.StatusProbe:
    return mapping.get(path, CLEAN)

  return probe


def _codes(result: audit.AuditResult) -> list[str]:
  return [finding.code for finding in result.findings]


def test_inventory_listing_falls_back_when_ownership_blocks_the_entry_point(
  monkeypatch: pytest.MonkeyPatch,
) -> None:
  """A dubious-ownership entry point must not abort the whole audit.

  When plain `git worktree list` dies on ownership, the restricted
  safe-directory override must still load the inventory so the per-worktree
  probes get their chance to report the ownership findings.
  """
  porcelain = (
    "worktree /repo\n"
    "HEAD 1111111111111111111111111111111111111111\n"
    "branch refs/heads/main\n"
    "\n"
  )

  class _Proc:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
      self.returncode = returncode
      self.stdout = stdout
      self.stderr = stderr

  calls: list[list[str]] = []

  def fake_run_git(args, *, timeout):
    calls.append(list(args))
    if args[:2] == ["-c", "safe.directory=*"]:
      return _Proc(0, stdout=porcelain)
    return _Proc(
      128,
      stderr="fatal: detected dubious ownership in repository at '/repo'",
    )

  monkeypatch.setattr(audit, "_run_git", fake_run_git)

  entries = audit.list_repository_worktrees(Path("/repo"))

  assert [entry.path for entry in entries] == ["/repo"]
  assert len(calls) == 2
  assert calls[1][:2] == ["-c", "safe.directory=*"]


def test_inventory_listing_raises_when_even_the_override_fails(
  monkeypatch: pytest.MonkeyPatch,
) -> None:
  class _Proc:
    returncode = 128
    stdout = ""
    stderr = "fatal: not a git repository"

  monkeypatch.setattr(audit, "_run_git", lambda args, *, timeout: _Proc())

  with pytest.raises(audit.WorktreeAuditError):
    audit.list_repository_worktrees(Path("/nowhere"))


def test_parse_worktree_list_reads_porcelain_records() -> None:
  text = (
    "worktree /repo\n"
    "HEAD 1111111111111111111111111111111111111111\n"
    "branch refs/heads/main\n"
    "\n"
    "worktree /repo/.worktrees/topic\n"
    "HEAD 2222222222222222222222222222222222222222\n"
    "detached\n"
    "locked reason with spaces\n"
    "\n"
  )

  entries = audit.parse_worktree_list(text)

  assert [entry.path for entry in entries] == ["/repo", "/repo/.worktrees/topic"]
  assert entries[0].branch == "refs/heads/main"
  assert entries[0].detached is False
  assert entries[1].branch == ""
  assert entries[1].detached is True
  assert entries[1].locked is True


def test_compliant_layout_produces_no_findings(tmp_path: Path) -> None:
  main_root = tmp_path / "repo"
  entries = [
    _entry(main_root, "refs/heads/main"),
    _entry(main_root / ".worktrees" / "topic"),
  ]

  result = audit.build_audit(entries, main_root=main_root.as_posix(), probe=_probe({}))

  assert result.findings == []
  assert result.worktrees_checked == 2
  assert all(report.inside_policy_root for report in result.worktrees)


def test_worktree_outside_the_policy_root_is_reported(tmp_path: Path) -> None:
  main_root = tmp_path / "repo"
  stray = tmp_path / "elsewhere" / "stray"
  nested_but_wrong = main_root / ".codex" / "worktrees" / "promotion"
  entries = [
    _entry(main_root, "refs/heads/main"),
    _entry(stray),
    _entry(nested_but_wrong),
  ]

  result = audit.build_audit(entries, main_root=main_root.as_posix(), probe=_probe({}))

  assert _codes(result) == ["worktree-outside-policy-root"] * 2
  assert {finding.worktree for finding in result.findings} == {
    stray.as_posix(),
    nested_but_wrong.as_posix(),
  }


def test_allowlisted_path_suppresses_the_placement_finding(tmp_path: Path) -> None:
  main_root = tmp_path / "repo"
  stray = tmp_path / "elsewhere" / "stray"
  entries = [_entry(main_root, "refs/heads/main"), _entry(stray)]

  result = audit.build_audit(
    entries,
    main_root=main_root.as_posix(),
    allowed_paths=[stray.as_posix()],
    probe=_probe({}),
  )

  assert result.findings == []


def test_unreadable_worktree_status_is_a_finding_rather_than_a_crash(tmp_path: Path) -> None:
  main_root = tmp_path / "repo"
  broken = main_root / ".worktrees" / "elevated"
  entries = [_entry(main_root, "refs/heads/main"), _entry(broken)]

  result = audit.build_audit(
    entries,
    main_root=main_root.as_posix(),
    probe=_probe({broken.as_posix(): DUBIOUS_OWNERSHIP}),
  )

  assert _codes(result) == ["worktree-status-unavailable"]
  assert "dubious ownership" in result.findings[0].detail
  report = next(item for item in result.worktrees if item.path == broken.as_posix())
  assert report.status_reachable is False
  assert report.needed_ownership_override is True


def test_untracked_residue_is_reported_against_the_budget(tmp_path: Path) -> None:
  main_root = tmp_path / "repo"
  dirty = main_root / ".worktrees" / "dirty"
  entries = [_entry(main_root, "refs/heads/main"), _entry(dirty)]
  probe = _probe({dirty.as_posix(): audit.StatusProbe(reachable=True, untracked=3)})

  result = audit.build_audit(entries, main_root=main_root.as_posix(), probe=probe)

  assert _codes(result) == ["worktree-untracked-residue"]
  assert "3 untracked entries" in result.findings[0].detail

  tolerated = audit.build_audit(
    entries,
    main_root=main_root.as_posix(),
    max_untracked=3,
    probe=probe,
  )

  assert tolerated.findings == []


def test_ownership_override_still_counts_untracked_residue(tmp_path: Path) -> None:
  main_root = tmp_path / "repo"
  broken = main_root / ".worktrees" / "elevated"
  entries = [_entry(main_root, "refs/heads/main"), _entry(broken)]
  probe = _probe(
    {
      broken.as_posix(): audit.StatusProbe(
        reachable=False,
        untracked=2,
        error="fatal: detected dubious ownership in repository at 'X'",
        needed_ownership_override=True,
      )
    }
  )

  result = audit.build_audit(entries, main_root=main_root.as_posix(), probe=probe)

  assert _codes(result) == ["worktree-status-unavailable", "worktree-untracked-residue"]


def test_missing_worktree_directory_is_probed_without_invoking_git(tmp_path: Path) -> None:
  probe = audit.probe_worktree_status((tmp_path / "gone").as_posix())

  assert probe.reachable is False
  assert probe.untracked == 0
  assert "missing on disk" in probe.error


def test_count_untracked_counts_only_untracked_entries() -> None:
  status = "?? scratch.py\n M tracked.py\n?? build/\nA  added.py\n"

  assert audit.count_untracked(status) == 2


def test_audit_repository_treats_the_first_entry_as_the_main_worktree(tmp_path: Path) -> None:
  main_root = tmp_path / "repo"
  entries = [_entry(main_root, "refs/heads/main"), _entry(main_root / ".worktrees" / "topic")]

  result = audit.audit_repository(
    main_root / ".worktrees" / "topic",
    probe=_probe({}),
    list_worktrees=lambda _repo_root: entries,
  )

  assert result.main_worktree == main_root.as_posix()
  assert result.policy_root == (main_root / ".worktrees").as_posix()
  assert result.findings == []


def test_audit_repository_rejects_an_empty_inventory(tmp_path: Path) -> None:
  with pytest.raises(audit.WorktreeAuditError):
    audit.audit_repository(tmp_path, probe=_probe({}), list_worktrees=lambda _repo_root: [])


@pytest.mark.parametrize(
  ("output_format", "expected_marker"),
  (("text", "findings: 0"), ("json", '"findings": []')),
)
def test_main_exits_zero_for_a_clean_inventory(
  tmp_path: Path,
  monkeypatch: pytest.MonkeyPatch,
  capsys: pytest.CaptureFixture[str],
  output_format: str,
  expected_marker: str,
) -> None:
  main_root = tmp_path / "repo"
  entries = [_entry(main_root, "refs/heads/main"), _entry(main_root / ".worktrees" / "topic")]
  monkeypatch.setattr(audit, "list_repository_worktrees", lambda _repo_root, **_kwargs: entries)
  monkeypatch.setattr(audit, "probe_worktree_status", _probe({}))

  exit_code = audit.main(["--repo-root", str(main_root), "--format", output_format])

  assert exit_code == 0
  assert expected_marker in capsys.readouterr().out


def test_main_exits_non_zero_when_a_finding_is_raised(
  tmp_path: Path,
  monkeypatch: pytest.MonkeyPatch,
  capsys: pytest.CaptureFixture[str],
) -> None:
  main_root = tmp_path / "repo"
  broken = main_root / ".worktrees" / "elevated"
  entries = [_entry(main_root, "refs/heads/main"), _entry(broken)]
  monkeypatch.setattr(audit, "list_repository_worktrees", lambda _repo_root, **_kwargs: entries)
  monkeypatch.setattr(audit, "probe_worktree_status", _probe({broken.as_posix(): DUBIOUS_OWNERSHIP}))

  exit_code = audit.main(["--repo-root", str(main_root)])
  output = capsys.readouterr().out

  assert exit_code == 1
  assert "worktree-status-unavailable" in output
  assert "findings: 1" in output


def test_main_reports_an_unreadable_inventory_without_traceback(
  tmp_path: Path,
  monkeypatch: pytest.MonkeyPatch,
  capsys: pytest.CaptureFixture[str],
) -> None:
  def explode(_repo_root: Path, **_kwargs: object) -> list[audit.WorktreeEntry]:
    raise audit.WorktreeAuditError("cannot list worktrees")

  monkeypatch.setattr(audit, "list_repository_worktrees", explode)

  exit_code = audit.main(["--repo-root", str(tmp_path)])

  assert exit_code == 2
  assert "worktree audit failed" in capsys.readouterr().err
