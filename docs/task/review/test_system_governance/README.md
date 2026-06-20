# Test System Governance

Status: `2026-06-21` accepted governance slice for reducing redundant tests
while preserving maintained coverage; residual blockers are tracked in
[Test System Residual Governance](../../issues/test_system_residual_governance/README.md).

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- Parent review index: [../README.md](../README.md)
- Test-system intent: [../../../tests/README.md](../../../../tests/README.md)
- Agent authority map: [../../../agent/rules/document_authority_map.md](../../../agent/rules/document_authority_map.md)
- Subproject creation standard: [../../../agent/rules/subproject_creation_standard.md](../../../agent/rules/subproject_creation_standard.md)
- Audit runner: [../../../../tools/runners/audit_test_system.py](../../../../tools/runners/audit_test_system.py)

## Purpose

This subproject owns the durable execution surface for the test-system
governance work started on 2026-06-20. The work exists because the active test
tree contains valuable coverage, but also contains oversized snapshot-style
tests, source-scan guardrails, hidden mixin tests, and uneven smoke/contract
promotion.

The goal is not to reduce test count for its own sake. The goal is to keep
business coverage explicit, make CI gates intentional, and convert redundant or
hardcoded checks into smaller invariants, JSON contracts, focused suites, or
manual/local governance checks.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Audit tooling | accepted for current slice | [audit_test_system.py](../../../../tools/runners/audit_test_system.py), [test_audit_test_system.py](../../../../tests/runners/test_audit_test_system.py) | Static audit only; it does not replace pytest collection or coverage reports. |
| Active pytest surface | inventoried / residual tracked | Audit summary: 343 active tracked test files, 256 active tracked Python files, 1990 corrected static test items, 152 risk-flagged Python files; pytest working-tree collect: 2000 tests. | Counts exclude `archive` paths but do not prove semantic redundancy by themselves. |
| Smoke promotion | accepted for current slice | Audit summary: 51 pytest smoke entries across 49 files, 10 JSON contract smoke specs; smoke suite remained green. | Smoke membership is a gate decision, not a full coverage statement. |
| Coverage baseline | accepted as scoped evidence | Current local `.coverage` over Python roots: 34376 statements, 11916 missed, 65% covered. | Does not cover C++ `src/`, branch coverage, or every Python business surface. |
| Test simplification | accepted with tracked residuals | Two largest `tests/tools` airframe geometry tests and ten high-risk damage-model files are split into smaller semantic tests. | Airframe behavior and remaining literal/source-scan concentration are tracked in the residual issue. |
| Mixin collection | accepted documentation / behavior residual | [P2-C evidence](test_system_governance_p2c_mixin_evidence_20260621.md) records 192 collected `weapon_guidance_realism` tests through five wrappers. | Full package run currently fails; this package remains local/focused, not smoke. |

## Scope

In scope:

- Maintain a repeatable active-test audit that excludes `archive` / `Archive`
  paths and separates pytest, JSON contract, smoke, and risk surfaces.
- Classify tests into smoke, focused, local, manual, contract, or archive
  candidates using evidence from the audit runner and existing suite manifests.
- Convert selected hardcoded snapshot tests into smaller invariant checks or
  data-driven contract checks while preserving the behavior they actually guard.
- Reduce hidden or confusing collection patterns when doing so improves
  maintainability without losing coverage.
- Update test documentation and task status whenever governance rules or
  acceptance boundaries change.

Out of scope:

- Claiming the whole test system is healthy because one audit runner passes.
- Deleting tests solely because they are long or not in smoke.
- Treating coverage percentage as capability acceptance without business-surface
  mapping.
- Rewriting runtime behavior, model algorithms, or domain contracts as part of a
  test cleanup cluster.
- Promoting archived evidence as current authority unless a maintained README or
  status document explicitly does so.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Freeze scope, authority, and active-test definition. | User requested a durable task subproject. | Parent README, standards, tests README, and archive exclusions are linked. | pass |
| `P1 Evidence` | Establish repeatable audit and baseline measurements. | Active non-archive test tree exists. | Audit, pytest collection, and coverage semantics are separated. | pass |
| `P2 Consolidation` | Convert or split the highest-risk test clusters. | P1 audit identifies concrete files and risk flags. | Selected clusters preserve behavior with smaller invariants or contract data. | accepted with tracked residuals |
| `P3 Suite Tiers` | Align smoke/focused/local/manual promotion with suite manifests. | P2 candidates have stable replacement checks. | Manifest and README tier decisions match the maintained surface. | pass for current slice |
| `P4 Validation` | Run acceptance commands and compare coverage/risk deltas. | P2/P3 changes are staged by cluster. | Pytest runner tests, affected domain tests, audit report, and coverage notes pass. | pass for current slice |
| `P5 Closure` | Sync indexes, residuals, and archive/current boundaries. | Acceptance evidence exists for scoped clusters. | README/status/acceptance and parent indexes are current. | pass for current slice |

## Task Clusters

- Task cluster plan: [test_system_governance_task_clusters_20260620.md](test_system_governance_task_clusters_20260620.md)
- Current status: [test_system_governance_current_status_20260620.md](test_system_governance_current_status_20260620.md)
- Dispatch queue: [test_system_governance_dispatch_queue_20260620.md](test_system_governance_dispatch_queue_20260620.md)
- Acceptance record: [test_system_governance_acceptance_20260620.md](test_system_governance_acceptance_20260620.md)
- P1-B evidence: [test_system_governance_p1b_evidence_20260621.md](test_system_governance_p1b_evidence_20260621.md)
- P2-C mixin evidence: [test_system_governance_p2c_mixin_evidence_20260621.md](test_system_governance_p2c_mixin_evidence_20260621.md)

## Outputs And Evidence

- `tools/runners/audit_test_system.py`: repeatable active-test audit runner.
- `tests/runners/test_audit_test_system.py`: runner unit tests for archive
  exclusion, smoke/contract counting, and risk flags.
- `tests/README.md`: audit runner usage and interpretation rules.
- [test_system_governance_p1b_evidence_20260621.md](test_system_governance_p1b_evidence_20260621.md):
  reconciled static audit, pytest collection, and coverage evidence.
- [test_system_governance_p2c_mixin_evidence_20260621.md](test_system_governance_p2c_mixin_evidence_20260621.md):
  wrapper/mixin collection decision for `weapon_guidance_realism`.

## Acceptance Gate

This subproject is accepted for the current governance slice because:

- The audit runner remains tested and documented.
- At least one high-risk test cluster is simplified, re-tiered, or converted
  with explicit before/after evidence.
- Smoke and contract suite manifests reflect intentional gate membership.
- Coverage statements are scoped to their measured source roots.
- Residual tests that remain hardcoded, long, or source-scan based are either
  justified by tier or moved to follow-on work.
- No status document claims whole-project test health from a narrow slice.

## Residuals And Next Steps

The remaining blockers are retained in
[Test System Residual Governance](../../issues/test_system_residual_governance/README.md):

- dependency-complete execution for the split `tests/tools/` airframe checks;
- file-level literal/source-scan closeout for the remaining
  `tests/architecture/damage_model/` focused guards;
- `tests/runtime/air_combat/weapon_guidance_realism/` behavior reconciliation
  before any smoke promotion;
- separate Python/C++ coverage records with measured roots and no overclaim.

## Archive

Superseded status snapshots, obsolete risk reports, and closed cluster packets
move under [archive/README.md](archive/README.md). Archive files are provenance
only and are not default authority for current test-system health.
