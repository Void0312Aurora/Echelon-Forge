from __future__ import annotations

from tools.maintenance.documentation_impact import evaluate, load_matrix


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


def test_unrelated_change_has_no_impact_decision() -> None:
  report = evaluate(["tests/fixtures/sample.json"])

  assert report.status == "no-impact"


def test_dot_directory_paths_keep_their_repository_prefix() -> None:
  report = evaluate([".github/codex/review-boundaries.md"])

  assert report.changed_paths == (".github/codex/review-boundaries.md",)
