from __future__ import annotations

import re
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TARGET_ROOTS = {
  "architecture",
  "domains",
  "engineering",
  "learning",
  "operations",
  "project",
  "research",
  "systems",
}
ACTIVE_LEGACY_ROOTS = {
  "plan",
  "standards",
  "task",
}
ARCHIVE_ONLY_ROOTS = {
  "Archive",
  "evaluation",
  "manual",
}


def _tracked_docs_paths() -> list[str]:
  result = subprocess.run(
    ["git", "ls-files", "--", "docs"],
    cwd=REPO_ROOT,
    check=True,
    capture_output=True,
    text=True,
  )
  return [line for line in result.stdout.splitlines() if line]


def test_tracked_docs_use_registered_top_level_roots() -> None:
  tracked = _tracked_docs_paths()
  roots = {
    parts[1]
    for path in tracked
    if len(parts := Path(path).parts) > 2
  }

  assert TARGET_ROOTS <= roots
  assert roots <= TARGET_ROOTS | ACTIVE_LEGACY_ROOTS | ARCHIVE_ONLY_ROOTS
  assert {"agent", "archive", "book", "forward", "log"}.isdisjoint(roots)


def test_archive_only_legacy_roots_contain_archives_only() -> None:
  tracked = _tracked_docs_paths()

  for root in ("evaluation", "manual"):
    legacy_paths = [
      path for path in tracked if path.startswith(f"docs/{root}/")
    ]
    assert legacy_paths
    assert all(path.startswith(f"docs/{root}/archive/") for path in legacy_paths)


def test_legacy_governance_root_has_moved_to_engineering_owners() -> None:
  tracked = _tracked_docs_paths()

  assert not any(path.startswith("docs/standards/governance/") for path in tracked)
  assert "docs/standards/bilingual_document_clusters.json" not in tracked
  for required in (
    "docs/engineering/automation/standards/subagent_usage_policy.md",
    "docs/engineering/documentation/reference/bilingual_document_clusters.json",
    "docs/engineering/documentation/standards/document_lifecycle_policy.md",
    "docs/engineering/release/standards/release_and_dependency_policy.md",
  ):
    assert required in tracked


def test_automation_governance_uses_capability_tiers_not_versioned_model_ids() -> None:
  automation_docs = [
    path
    for path in _tracked_docs_paths()
    if path.startswith("docs/engineering/automation/") and path.endswith(".md")
  ]

  assert automation_docs
  for relative in automation_docs:
    text = (REPO_ROOT / relative).read_text(encoding="utf-8")
    assert re.search(r"\bgpt-\d", text, re.IGNORECASE) is None, relative


def test_legacy_joint_standards_have_moved_to_the_domain_owner() -> None:
  tracked = _tracked_docs_paths()

  assert not any(path.startswith("docs/standards/joint/") for path in tracked)
  for required in (
    "docs/domains/joint/README.md",
    "docs/domains/joint/README.zh.md",
    "docs/domains/joint/standards/command_and_modeling_baseline.md",
    "docs/domains/joint/standards/command_link_and_reporting_baseline.md",
  ):
    assert required in tracked


def test_air_ground_and_service_profile_standards_are_owner_local() -> None:
  tracked = _tracked_docs_paths()

  for legacy_prefix in (
    "docs/standards/air/",
    "docs/standards/ground/",
    "docs/standards/services/",
  ):
    assert not any(path.startswith(legacy_prefix) for path in tracked)

  for required in (
    "docs/domains/air/README.md",
    "docs/domains/air/README.zh.md",
    "docs/domains/air/standards/mission_command_and_tasking_contract.md",
    "docs/domains/air/standards/mission_command_and_tasking_contract.zh.md",
    "docs/domains/air/standards/pilot_action_contract.md",
    "docs/domains/air/standards/pilot_action_contract.zh.md",
    "docs/domains/air/standards/pilot_observation_contract.md",
    "docs/domains/air/standards/pilot_observation_contract.zh.md",
    "docs/domains/air/standards/pilot_reporting_contract.md",
    "docs/domains/air/standards/pilot_reporting_contract.zh.md",
    "docs/domains/air/work/issues/kill_chain_expectation_envelope.md",
    "docs/domains/air/work/issues/kill_chain_expectation_envelope.zh.md",
    "docs/domains/ground/README.md",
    "docs/domains/ground/README.zh.md",
    "docs/domains/ground/standards/minimal_task_structure.md",
    "docs/domains/ground/standards/minimal_task_structure.zh.md",
    "docs/domains/ground/standards/specialization_baseline.md",
    "docs/domains/ground/standards/specialization_baseline.zh.md",
    "docs/domains/joint/service_profiles/README.md",
    "docs/domains/joint/service_profiles/README.zh.md",
    "docs/domains/joint/service_profiles/standards/air_force_profile.md",
    "docs/domains/joint/service_profiles/standards/air_force_profile.zh.md",
    "docs/domains/joint/service_profiles/standards/army_profile.md",
    "docs/domains/joint/service_profiles/standards/army_profile.zh.md",
    "docs/domains/joint/service_profiles/standards/marine_corps_profile.md",
    "docs/domains/joint/service_profiles/standards/marine_corps_profile.zh.md",
    "docs/domains/joint/service_profiles/standards/navy_profile.md",
    "docs/domains/joint/service_profiles/standards/navy_profile.zh.md",
  ):
    assert required in tracked


def test_naval_model_and_modularization_sources_are_owner_local() -> None:
  tracked = _tracked_docs_paths()

  for legacy_prefix in (
    "docs/standards/model/",
    "docs/standards/naval/",
    "docs/standards/planning/",
  ):
    assert not any(path.startswith(legacy_prefix) for path in tracked)

  for required in (
    "docs/architecture/work/issues/modularization_plan.md",
    "docs/architecture/work/issues/modularization_plan.zh.md",
    "docs/domains/naval/README.md",
    "docs/domains/naval/README.zh.md",
    "docs/domains/naval/reference/ship_unit_references.md",
    "docs/domains/naval/reference/ship_unit_references.zh.md",
    "docs/domains/naval/standards/minimal_task_structure.md",
    "docs/domains/naval/standards/minimal_task_structure.zh.md",
    "docs/domains/naval/standards/observation_contract.md",
    "docs/domains/naval/standards/observation_contract.zh.md",
    "docs/learning/standards/policy_execution_architecture.md",
    "docs/learning/standards/policy_execution_architecture.zh.md",
  ):
    assert required in tracked


def test_owner_local_standards_declare_minimum_metadata() -> None:
  governed = [
    path
    for path in _tracked_docs_paths()
    if path.endswith(".md")
    and len(Path(path).parts) > 2
    and Path(path).parts[1] in TARGET_ROOTS
    and "/standards/" in path
  ]

  assert governed
  for relative in governed:
    text = (REPO_ROOT / relative).read_text(encoding="utf-8")
    for field in (
      "Document kind:",
      "Lifecycle:",
      "Canonical:",
      "Owner:",
      "Last verified:",
    ):
      assert field in text, f"{relative} is missing {field}"


def test_domain_chinese_companions_point_to_english_canonical() -> None:
  companions = [
    path
    for path in _tracked_docs_paths()
    if path.startswith("docs/domains/") and path.endswith(".zh.md")
  ]

  assert companions
  for relative in companions:
    expected = relative.removesuffix(".zh.md") + ".md"
    text = (REPO_ROOT / relative).read_text(encoding="utf-8")
    assert f"Canonical: `{expected}`" in text, relative


def test_owner_local_work_and_reviews_declare_minimum_metadata() -> None:
  governed = [
    path
    for path in _tracked_docs_paths()
    if path.endswith(".md")
    and Path(path).parts[1] in TARGET_ROOTS
    and ("/work/issues/" in path or "/reviews/" in path)
  ]

  assert governed
  for relative in governed:
    text = (REPO_ROOT / relative).read_text(encoding="utf-8")
    for field in (
      "Document kind:",
      "Lifecycle:",
      "Canonical:",
      "Owner:",
      "Last verified:",
    ):
      assert field in text, f"{relative} is missing {field}"
