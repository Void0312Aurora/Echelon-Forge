# Standards Documentation Governance

Status: `2026-06-10` archived accepted governance slice for standards drift,
admission, and closure.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- [Review task area](../../README.md)
- [Standards-Implementation Alignment Review 2026-06-10](../standards_implementation_alignment_review_20260610.md)
- [Standards Documentation Overview](../../../../standards/README.md)
- [Document Alignment Map](../../../../standards/overview/document_alignment_map.md)
- [Standards Maintenance Policy](../../../../standards/governance/standards_maintenance_policy.md)
- [Agent Document Authority Map](../../../../agent/rules/document_authority_map.md)
- [Subproject Creation Standard](../../../../agent/rules/subproject_creation_standard.md)

## Purpose

This subproject turns the standards-implementation alignment review into a
durable governance lane. The standards tree is accepted as the project's
ownership map, but the review found that implementation changes can still
outpace standards entries, status dates, and planning supplements.

The goal is to keep `docs/standards/` current without letting task plans,
diagnostics, compatibility paths, or early runtime experiments redefine the
maintained ownership hierarchy by accident.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Standards authority | accepted | `docs/standards/README.md`, `docs/standards/overview/document_alignment_map.md` | Authority over names and layers does not mean every field-level contract is fresh. |
| Alignment review | archived provenance | `archive/standards_implementation_alignment_review_20260610.md` | Six gaps received owned closure or explicit held disposition. |
| Bilingual governance | accepted | `docs/standards/governance/bilingual_documentation_policy.md` | Language pairing checks do not prove semantic implementation alignment. |
| Maintenance policy | active | `docs/standards/governance/standards_maintenance_policy.md` | The policy defines gates; it does not close the six gaps by itself. |

## Scope

In scope:

- Maintain a finite closure lane for GAP-001 through GAP-006 from the
  `2026-06-10` alignment review.
- Define when standards documents must be updated after runtime, DTO, scenario,
  test, or task-acceptance changes.
- Keep standards status lines, indexes, bilingual companions, and current
  implementation claims synchronized.
- Record which gaps are closed, held, or deliberately deferred.

Out of scope:

- Claiming new runtime maturity for air, naval, ground, model, or weapon
  effects work.
- Creating a production `demo` or empty shell domain under `src/*/domains`.
- Promoting unaccepted MLF-3 warhead-effects work into a standards contract
  before the task surface reaches acceptance.
- Rewriting the full standards tree in one pass.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Record the governance lane and maintenance policy. | Alignment review exists. | Subproject, policy, and indexes are present. | pass |
| `P1 Triage` | Classify each GAP by owner, write set, and closure gate. | P0 complete. | All six gaps have serial or held clusters. | pass |
| `P2 Remediation` | Apply accepted standards/runtime fixes in small batches. | Triage complete. | Each changed contract has docs, tests, and bilingual sync as needed. | pass |
| `P3 Validation` | Run doc, architecture, and affected runtime gates. | Remediation batch complete. | Pass/fail evidence is recorded. | pass |
| `P4 Closure` | Update status, residuals, indexes, and archive readiness. | Validation complete. | Accepted slice and remaining held items are explicit. | closed |

## Task Clusters

- Task cluster plan: `standards_documentation_governance_task_clusters_20260610.md`
- Current status: `standards_documentation_governance_current_status_20260610.md`
- Dispatch queue: `standards_documentation_governance_dispatch_queue_20260610.md`

## Outputs And Evidence

- This review subproject.
- [Standards Maintenance Policy](../../../../standards/governance/standards_maintenance_policy.md).
- [Current status ledger](standards_documentation_governance_current_status_20260610.md).
- [Dispatch queue](standards_documentation_governance_dispatch_queue_20260610.md).
- Parent review archive index entries.
- Architecture governance tests that keep this lane registered.
- Later remediation commits for the individual GAP items.

Validation evidence for P0:

- `python -m pytest -q tests/architecture/governance/test_standards_documentation_governance.py` passed, 4 tests.
- `python3 tools/maintenance/translate_docs_batch.py audit --root docs --registry docs/standards/bilingual_document_clusters.json` reported 66 synced registry pairs and no registry drift. It still reports the pre-existing missing English peer for `docs/standards/foundation/realism_authority_boundary.zh.md`.
- `git diff --check` passed for the touched standards governance paths.
- `python -m pytest -q tests/architecture/governance` still has unrelated existing failures because several simulation-architecture WP paths expected by older governance tests are absent from the current tree.

Validation evidence for P1:

- `python -m pytest -q tests/architecture/governance/test_standards_documentation_governance.py` passed, 5 tests.
- `python3 tools/maintenance/translate_docs_batch.py audit --root docs --registry docs/standards/bilingual_document_clusters.json` reported 66 synced registry pairs and no registry drift; the pre-existing missing English peer remains outside this subproject.
- `git diff --check` passed for the expanded standards governance paths.

Validation evidence for Batch A remediation:

- `cmake --build build-workshop --target ef_py -j2` passed.
- `python -m pytest -q tests/architecture/ground/test_tasking_component_boundary.py tests/runtime/mission/test_mission_command_ground_fields_roundtrip.py tests/leader/test_ground_profile_semantics.py tests/runtime/mission/test_mission_command_roe_fields.py` passed, 24 tests.
- `python -m pytest -q tests/architecture/governance/test_standards_documentation_governance.py` passed after closure guard expansion.

Validation evidence for Batch B remediation:

- `python -m pytest -q tests/runtime/mission/test_mission_obs_taxonomy.py tests/runtime/air_combat/test_air_combat_c2_roe_mission_observation.py tests/runtime/naval/test_naval_n4_reward_surface.py` passed, 31 tests.
- `python -m pytest -q tests/architecture/governance/test_standards_documentation_governance.py` passed, 7 tests.
- `python3 tools/maintenance/translate_docs_batch.py clusters --root docs --write` refreshed the maintained registry to 67 pairs.
- `python3 tools/maintenance/translate_docs_batch.py audit --root docs --registry docs/standards/bilingual_document_clusters.json` reported 67 synced registry pairs and no registry drift. It still reports the pre-existing missing English peer for `docs/standards/foundation/realism_authority_boundary.zh.md`.
- `git diff --check` passed for the touched Batch B standards/governance paths.

Validation evidence for Batch C and final status/header closure:

- `python -m pytest -q tests/architecture/governance/test_standards_documentation_governance.py` passed, 9 tests.
- `python3 tools/maintenance/translate_docs_batch.py clusters --root docs --write` kept the maintained registry at 67 pairs.
- `python3 tools/maintenance/translate_docs_batch.py audit --root docs --registry docs/standards/bilingual_document_clusters.json` reported 67 synced registry pairs and no registry drift. It still reports the pre-existing missing English peer for `docs/standards/foundation/realism_authority_boundary.zh.md`.
- `git diff --check -- docs/standards docs/task/review/standards_documentation_governance tests/architecture/governance/test_standards_documentation_governance.py` passed.

## Acceptance Gate

This subproject can be marked accepted only when:

- GAP-001 through GAP-006 are either closed with evidence or explicitly held
  with a named owner and release trigger.
- Maintained standards changed by the remediation have bilingual companions or
  an explicit Tier-B delay statement.
- The standards README, document alignment map, and affected local READMEs no
  longer point readers at stale authority.
- Focused validation commands are recorded and pass, or any failure is listed
  as a blocking residual.

Current gate result: satisfied for GAP-001 through GAP-005; GAP-006 is an
explicit held item with MLF-3 acceptance as its release trigger.

## Residuals And Next Steps

- GAP-006 should stay held until MLF-3 warhead effects reaches task acceptance.
- A future maintenance helper may turn the review checklist into a read-only
  standards drift audit, but that is not required for this first governance
  slice.

## Archive

This subproject is archived under
`docs/task/review/archive/standards_documentation_governance/`. It remains the
accepted provenance record for the 2026-06-10 standards drift closure, not the
active default planning surface for future standards work.
