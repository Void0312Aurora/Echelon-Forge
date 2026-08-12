from __future__ import annotations

import json
import re
import shlex
from pathlib import Path

import pytest

pytestmark = pytest.mark.governance_audit


REPO_ROOT = Path(__file__).resolve().parents[3]
GOVERNANCE_ARCHIVE_PARTS = (
  "docs",
  "task",
  "review",
  "archive",
  "standards_documentation_governance",
)


def _text(*parts: str) -> str:
  return REPO_ROOT.joinpath(*parts).read_text(encoding="utf-8")


def _governance_text(filename: str) -> str:
  return _text(*GOVERNANCE_ARCHIVE_PARTS, filename)


def _constrained_workflow_packages(workflow: str) -> set[str]:
  commands: list[str] = []
  current = ""
  for raw_line in workflow.splitlines():
    line = raw_line.strip()
    command_part = line[:-1].rstrip() if line.endswith("\\") else line
    if current:
      current = f"{current} {command_part}"
      if not line.endswith("\\"):
        commands.append(current)
        current = ""
    elif "-m pip install" in line:
      current = command_part
      if not line.endswith("\\"):
        commands.append(current)
        current = ""

  packages: set[str] = set()
  for command in commands:
    if "-c requirements/constraints-smoke.txt" not in command:
      continue
    tokens = shlex.split(command)
    install_index = tokens.index("install")
    skip_constraint_path = False
    for token in tokens[install_index + 1:]:
      if skip_constraint_path:
        skip_constraint_path = False
      elif token in {"-c", "--constraint"}:
        skip_constraint_path = True
      elif not token.startswith("-"):
        packages.add(token.lower().replace("_", "-"))
  return packages


def test_standards_maintenance_policy_is_registered() -> None:
  documentation_readme = _text("docs", "engineering", "documentation", "README.md")
  documentation_readme_zh = _text("docs", "engineering", "documentation", "README.zh.md")
  policy = _text(
    "docs", "engineering", "documentation", "standards", "standards_maintenance_policy.md"
  )
  policy_zh = _text(
    "docs", "engineering", "documentation", "standards", "standards_maintenance_policy.zh.md"
  )

  assert "standards/standards_maintenance_policy.md" in documentation_readme
  assert "standards/standards_maintenance_policy.zh.md" in documentation_readme_zh
  assert "retired `docs/plan/` and `docs/task/` roots contain archives only" in policy
  assert "已退役的 `docs/plan/` 与 `docs/task/` 根只包含归档" in policy_zh


def test_standards_governance_tracks_all_alignment_gaps() -> None:
  readme = _governance_text("README.md")
  clusters = _governance_text("standards_documentation_governance_task_clusters_20260610.md")
  status = _governance_text("standards_documentation_governance_current_status_20260610.md")
  dispatch = _governance_text("standards_documentation_governance_dispatch_queue_20260610.md")

  assert "standards_implementation_alignment_review_20260610.md" in readme
  assert "standards_documentation_governance_current_status_20260610.md" in readme
  assert "standards_documentation_governance_dispatch_queue_20260610.md" in readme
  assert "archived accepted governance slice" in readme
  assert "SG-P1" in clusters
  for gap_id in ("GAP-001", "GAP-002", "GAP-003", "GAP-004", "GAP-005", "GAP-006"):
    assert gap_id in clusters
    assert gap_id in status
    assert gap_id in dispatch

  assert "SG-G6" in clusters
  assert "held pending MLF-3 acceptance evidence" in clusters
  assert "No production `demo` domain" in status
  assert "SDG-D1" in dispatch
  assert "unaccepted or untracked test alone" in dispatch


def test_standards_governance_status_assigns_drift_classes_and_batches() -> None:
  status = _governance_text("standards_documentation_governance_current_status_20260610.md")

  for drift_class in (
    "Semantic mismatch",
    "Implementation ahead of standard",
    "Status/date stale",
    "Planning supplement drift",
    "Held standards admission",
  ):
    assert drift_class in status

  for batch in ("Batch A", "Batch B", "Batch C", "Batch D"):
    assert batch in status

  assert "MoveStatic" in status
  assert "G0/G1 static limitation" in status


def test_standards_governance_batch_a_closure_is_backed_by_code_and_standard() -> None:
  status = _governance_text("standards_documentation_governance_current_status_20260610.md")
  ground_enums = _text(
    "src",
    "components",
    "domains",
    "ground",
    "tasking",
    "ground_tasking_enums.h",
  )
  # The command binding surface is decomposed into per-domain translation
  # units; read the slices joined in registration order.
  from tests.architecture.structural_boundaries.helpers import bindings_command_text

  bindings = bindings_command_text()
  command_standard = _text(
    "docs",
    "domains",
    "joint",
    "standards",
    "command_link_and_reporting_baseline.md",
  )

  assert "GAP-001" in status
  assert "closed" in status
  assert "MoveStatic = 1" in ground_enums
  assert "HoldStatic" not in ground_enums
  assert '.value("MoveStatic", GroundTaskMode::MoveStatic)' in bindings
  assert "HoldStatic" not in bindings

  for field in (
    "threat_state",
    "assigned_target_track_id",
    "assigned_target_source_id",
    "assigned_target_snapshot_time_s",
  ):
    assert field in command_standard

  assert "track fusion" in command_standard


def test_standards_governance_batch_b_observation_modes_are_registered() -> None:
  status = _governance_text("standards_documentation_governance_current_status_20260610.md")
  dispatch = _governance_text("standards_documentation_governance_dispatch_queue_20260610.md")
  clusters = _governance_text("standards_documentation_governance_task_clusters_20260610.md")
  air_obs = _text(
    "docs",
    "domains",
    "air",
    "standards",
    "pilot_observation_contract.md",
  )
  naval_obs = _text(
    "docs",
    "domains",
    "naval",
    "standards",
    "observation_contract.md",
  )
  naval_readme = _text("docs", "domains", "naval", "README.md")
  alignment_map = _text(
    "docs", "engineering", "documentation", "reference", "document_alignment_map.md"
  )

  assert "GAP-002" in status
  assert "Closed by registering `air_combat_c2_roe_v1/v2`" in status
  sdg_b1_row = next(line for line in dispatch.splitlines() if line.startswith("| `SDG-B1`"))
  sg_g2_row = next(line for line in clusters.splitlines() if line.startswith("| `SG-G2`"))
  assert sdg_b1_row.endswith("| pass |")
  assert sg_g2_row.endswith("| pass |")

  for required in (
    "air_combat_c2_roe_v1",
    "air_combat_c2_roe_v2",
    "assigned_target_snapshot_time_s",
    "fire_mask_open",
    "target_track_age_s",
  ):
    assert required in air_obs

  for required in (
    "naval_screen_station_v1",
    "station_error_m",
    "support_track_present",
    "report_chain_seen",
    "reference_relative_slot_code",
  ):
    assert required in naval_obs

  assert "Naval Observation Contract](standards/observation_contract.md)" in naval_readme
  assert "Naval Observation Contract](../../../domains/naval/standards/observation_contract.md)" in alignment_map


def test_standards_governance_gap_004_status_headers_are_refreshed() -> None:
  status = _governance_text("standards_documentation_governance_current_status_20260610.md")
  dispatch = _governance_text("standards_documentation_governance_dispatch_queue_20260610.md")
  clusters = _governance_text("standards_documentation_governance_task_clusters_20260610.md")
  air_act = _text(
    "docs",
    "domains",
    "air",
    "standards",
    "pilot_action_contract.md",
  )
  bridge = _text(
    "docs", "architecture", "standards", "runtime_workflow_and_contract_baseline.md"
  )
  joint = _text(
    "docs",
    "domains",
    "joint",
    "standards",
    "command_and_modeling_baseline.md",
  )
  naval = _text(
    "docs",
    "domains",
    "naval",
    "standards",
    "minimal_task_structure.md",
  )

  assert "GAP-004" in status
  assert "Closed by refreshing stale or missing status lines" in status
  sdg_b2_row = next(line for line in dispatch.splitlines() if line.startswith("| `SDG-B2`"))
  sg_g4_row = next(line for line in clusters.splitlines() if line.startswith("| `SG-G4`"))
  assert sdg_b2_row.endswith("| pass |")
  assert sg_g4_row.endswith("| pass |")

  assert "Status: specialization baseline for maintained air action input" in air_act
  assert "learned-policy behavior" in air_act
  assert "Status: maintained runtime workflow and contract baseline" in bridge
  assert "air_combat_c2_roe_v2" in bridge
  assert "naval_screen_station_v1" in bridge
  assert "Status: `2026-06-10` authoritative for maintained joint command and modeling" in joint
  assert "Status: maintained specialization baseline for the minimal naval" in naval


def test_modularization_issue_tracks_landed_interfaces_and_residuals() -> None:
  status = _governance_text("standards_documentation_governance_current_status_20260610.md")
  dispatch = _governance_text("standards_documentation_governance_dispatch_queue_20260610.md")
  clusters = _governance_text("standards_documentation_governance_task_clusters_20260610.md")
  plan = _text("docs", "architecture", "work", "issues", "modularization_plan.md")
  architecture_readme = _text("docs", "architecture", "README.md")
  alignment_map = _text(
    "docs", "engineering", "documentation", "reference", "document_alignment_map.md"
  )

  assert "GAP-005" in status
  assert "Closed by retaining the plan as an active planning supplement" in status
  sdg_c1_row = next(line for line in dispatch.splitlines() if line.startswith("| `SDG-C1`"))
  sg_g5_row = next(line for line in clusters.splitlines() if line.startswith("| `SG-G5`"))
  assert sdg_c1_row.endswith("| pass |")
  assert sg_g5_row.endswith("| pass |")

  for root in (
    ("src", "components", "domains"),
    ("src", "systems", "domains"),
    ("src", "models", "domains"),
  ):
    assert REPO_ROOT.joinpath(*root).is_dir()
    assert "/".join(root) in plan

  for interface in (
    "unit_factory.h",
    "effects_model.h",
    "sensor_model.h",
  ):
    assert REPO_ROOT.joinpath("src", "core", "interfaces", interface).is_file()
    assert interface in plan

  assert not REPO_ROOT.joinpath("src", "systems", "domains", "ground").exists()

  for required in (
    "Verified Current Domain Roots",
    "Existing Replaceable Interfaces",
    "`src/components/domains/`",
    "`src/systems/domains/`",
    "`src/models/domains/`",
    "does not authorize code moves",
    "There is no `src/systems/domains/ground/` owner",
    "consumer -> provider",
  ):
    assert required in plan

  assert "work/issues/modularization_plan.md" in architecture_readme
  assert "draft" in architecture_readme
  assert "does not authorize implementation" in alignment_map


def test_standards_policy_defines_drift_and_empty_owner_rules() -> None:
  policy = _text(
    "docs",
    "engineering",
    "documentation",
    "standards",
    "standards_maintenance_policy.md",
  )

  for required in (
    "Semantic mismatch",
    "Implementation ahead of standard",
    "Standard ahead of implementation",
    "Status/date stale",
    "Bilingual/index drift",
    "No empty owner rule",
    "docs/task/review/archive/standards_documentation_governance/README.md",
  ):
    assert required in policy


def test_standards_maintenance_policy_has_bilingual_registry_entry() -> None:
  registry = json.loads(
    _text(
      "docs",
      "engineering",
      "documentation",
      "reference",
      "bilingual_document_clusters.json",
    )
  )

  pairs = {record["pair_id"]: record for record in registry["pairs"]}
  record = pairs["engineering/documentation/standards/standards_maintenance_policy"]

  assert record["english"] == "docs/engineering/documentation/standards/standards_maintenance_policy.md"
  assert record["chinese"] == "docs/engineering/documentation/standards/standards_maintenance_policy.zh.md"
  assert record["source_of_truth"] == "english"


def test_smoke_constraints_cover_packages_installed_by_consuming_ci_lanes() -> None:
  constraints = _text("requirements", "constraints-smoke.txt")
  constrained = {
    match.group(1).lower().replace("_", "-")
    for line in constraints.splitlines()
    if (match := re.match(r"^([A-Za-z0-9_.-]+)", line))
  }
  installed: set[str] = set()
  for workflow in ("ci-smoke.yml", "coverage-baseline.yml"):
    installed |= _constrained_workflow_packages(
      _text(".github", "workflows", workflow)
    )

  assert {"pip", "pytest", "numpy", "ruff", "gymnasium", "coverage", "gcovr"} <= installed
  assert installed <= constrained
