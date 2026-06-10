from __future__ import annotations

import json
from pathlib import Path


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


def test_standards_maintenance_policy_is_registered() -> None:
    standards_readme = _text("docs", "standards", "README.md")
    standards_readme_zh = _text("docs", "standards", "README.zh.md")
    review_readme = _text("docs", "task", "review", "README.md")
    review_readme_zh = _text("docs", "task", "review", "README.zh.md")
    review_archive = _text("docs", "task", "review", "archive", "README.md")
    review_archive_zh = _text("docs", "task", "review", "archive", "README.zh.md")
    review_archive_registry = _text("docs", "task", "review", "archive_registry.md")
    review_archive_registry_zh = _text("docs", "task", "review", "archive_registry.zh.md")

    assert "governance/standards_maintenance_policy.md" in standards_readme
    assert "governance/standards_maintenance_policy.zh.md" in standards_readme_zh
    assert "archive/standards_documentation_governance/README.md" in review_readme
    assert "archive/standards_documentation_governance/README.zh.md" in review_readme_zh
    assert "standards_documentation_governance/README.md" in review_archive
    assert "standards_documentation_governance/README.zh.md" in review_archive_zh
    assert "standards_documentation_governance/" in review_archive_registry
    assert "standards_documentation_governance/" in review_archive_registry_zh


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
    bindings = _text("src", "interfaces", "python", "bindings_command.cpp")
    command_standard = _text(
        "docs",
        "standards",
        "joint",
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
    air_obs = _text("docs", "standards", "air", "obs.md")
    naval_obs = _text("docs", "standards", "naval", "obs.md")
    naval_readme = _text("docs", "standards", "naval", "README.md")
    alignment_map = _text("docs", "standards", "overview", "document_alignment_map.md")

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

    assert "Naval Observation Contract](obs.md)" in naval_readme
    assert "Naval Observation Contract](../naval/obs.md)" in alignment_map


def test_standards_governance_gap_004_status_headers_are_refreshed() -> None:
    status = _governance_text("standards_documentation_governance_current_status_20260610.md")
    dispatch = _governance_text("standards_documentation_governance_dispatch_queue_20260610.md")
    clusters = _governance_text("standards_documentation_governance_task_clusters_20260610.md")
    air_act = _text("docs", "standards", "air", "act.md")
    bridge = _text("docs", "standards", "bridge", "runtime_workflow_and_contract_baseline.md")
    joint = _text("docs", "standards", "joint", "command_and_modeling_baseline.md")
    naval = _text("docs", "standards", "naval", "minimal_task_structure.md")

    assert "GAP-004" in status
    assert "Closed by refreshing stale or missing status lines" in status
    sdg_b2_row = next(line for line in dispatch.splitlines() if line.startswith("| `SDG-B2`"))
    sg_g4_row = next(line for line in clusters.splitlines() if line.startswith("| `SG-G4`"))
    assert sdg_b2_row.endswith("| pass |")
    assert sg_g4_row.endswith("| pass |")

    assert "Status: `2026-06-10` specialization baseline for maintained air action input" in air_act
    assert "learned-policy behavior" in air_act
    assert "Status: `2026-06-10` authoritative for maintained runtime workflow ownership" in bridge
    assert "air_combat_c2_roe_v2" in bridge
    assert "naval_screen_station_v1" in bridge
    assert "Status: `2026-06-10` authoritative for maintained joint command and modeling" in joint
    assert "Status: `2026-06-10` specialization baseline for the maintained minimal naval" in naval


def test_standards_governance_batch_c_modularization_plan_tracks_domain_roots() -> None:
    status = _governance_text("standards_documentation_governance_current_status_20260610.md")
    dispatch = _governance_text("standards_documentation_governance_dispatch_queue_20260610.md")
    clusters = _governance_text("standards_documentation_governance_task_clusters_20260610.md")
    plan = _text("docs", "standards", "planning", "modularization_plan.md")
    standards_readme = _text("docs", "standards", "README.md")
    alignment_map = _text("docs", "standards", "overview", "document_alignment_map.md")

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

    for required in (
        "Current Implemented Domain Roots",
        "`src/components/domains/`",
        "`src/systems/domains/`",
        "`src/models/domains/`",
        "Do not add empty production owner roots",
        "there is no released `ground/` runtime system owner",
    ):
        assert required in plan

    assert "with current" in standards_readme
    assert "`src/*/domains` layout notes" in standards_readme
    assert "realized owner roots from still-planned interfaces" in alignment_map


def test_standards_policy_defines_drift_and_empty_owner_rules() -> None:
    policy = _text("docs", "standards", "governance", "standards_maintenance_policy.md")

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
        _text("docs", "standards", "bilingual_document_clusters.json")
    )

    pairs = {record["pair_id"]: record for record in registry["pairs"]}
    record = pairs["standards/governance/standards_maintenance_policy"]

    assert record["english"] == "docs/standards/governance/standards_maintenance_policy.md"
    assert record["chinese"] == "docs/standards/governance/standards_maintenance_policy.zh.md"
    assert record["source_of_truth"] == "english"
