from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from tools.maintenance.documentation_impact import evaluate, load_matrix


pytestmark = pytest.mark.governance_audit


def test_documentation_impact_matrix_covers_named_high_impact_owners() -> None:
  rules = {rule.id: rule for rule in load_matrix()}

  assert {
    "runtime-application-contract",
    "simulation-provider-boundary",
    "domain-system-owner",
    "python-dependency-groups",
  } <= rules.keys()
  assert evaluate(["python/simulation/backend.py"]).status == "review-required"
  assert evaluate(["pyproject.toml"]).status == "review-required"


def test_documentation_update_is_a_valid_impact_decision() -> None:
  report = evaluate(
    [
      "src/runtime/host/runtime_host_candidate.h",
      "src/runtime/README.md",
    ],
    decision="docs-updated",
  )

  assert report.status == "pass"
  assert "src/runtime/README.md" in report.changed_documentation
  assert report.changed_documentation_by_rule[0][0] == "runtime-application-contract"


def test_safe_candidate_change_can_explain_why_no_doc_edit_is_needed() -> None:
  report = evaluate(
    ["src/runtime/host/runtime_host_candidate.h"],
    decision="candidate-or-historical",
    reason="The host candidate remains non-production and the maintained boundary already states that scope.",
  )

  assert report.status == "pass"
  assert report.changed_documentation == ()


def test_docs_updated_without_a_target_is_rejected() -> None:
  report = evaluate(["python/simulation/backend.py"], decision="docs-updated")

  assert report.status == "invalid"
  assert "requires a changed documentation target" in report.message


def test_docs_updated_requires_each_impacted_owner_target() -> None:
  report = evaluate(
    [
      "src/runtime/facade/runtime_facade.h",
      "pyproject.toml",
      "README.md",
    ],
    decision="docs-updated",
  )

  assert report.status == "invalid"
  assert "runtime-application-contract" in report.message
  assert report.changed_documentation_by_rule == (
    ("runtime-application-contract", ()),
    ("python-dependency-groups", ("README.md",)),
  )


def test_unrelated_change_has_no_impact_decision() -> None:
  report = evaluate(["tests/fixtures/sample.json"])

  assert report.status == "no-impact"


def test_dot_directory_paths_keep_their_repository_prefix() -> None:
  report = evaluate([".github/codex/review-boundaries.md"])

  assert report.changed_paths == (".github/codex/review-boundaries.md",)


def test_cli_reports_a_deletion_only_change(tmp_path: Path) -> None:
  repo = tmp_path / "repo"
  repo.mkdir()
  contract = repo / "src" / "runtime" / "deleted_contract.h"
  contract.parent.mkdir(parents=True)
  contract.write_text("// removed contract\n", encoding="utf-8")

  def git(*args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)

  git("init")
  git("config", "user.email", "test@example.invalid")
  git("config", "user.name", "Documentation Impact Test")
  git("add", ".")
  git("commit", "-m", "add contract")
  contract.unlink()
  git("commit", "-am", "delete contract")

  script = Path(__file__).resolve().parents[3] / "tools" / "maintenance" / "documentation_impact.py"
  result = subprocess.run(
    [
      sys.executable,
      str(script),
      "--repo",
      str(repo),
      "--base",
      "HEAD^",
      "--head",
      "HEAD",
      "--check",
      "--decision",
      "still-accurate",
      "--reason",
      "The deleted contract is retired and the owner documentation remains accurate.",
      "--json",
    ],
    cwd=repo,
    check=False,
    capture_output=True,
    text=True,
  )

  assert result.returncode == 0, result.stdout + result.stderr
  assert "src/runtime/deleted_contract.h" in result.stdout
  assert '"runtime-application-contract"' in result.stdout
