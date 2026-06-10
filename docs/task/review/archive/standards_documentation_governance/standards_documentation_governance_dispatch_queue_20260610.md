# Standards Documentation Governance Dispatch Queue

Status: `2026-06-10` dispatch queue for the first standards governance remediation batches.

Parent subproject: [Standards Documentation Governance](README.md)

Language:

- English canonical: `standards_documentation_governance_dispatch_queue_20260610.md`
- Chinese companion: [standards_documentation_governance_dispatch_queue_20260610.zh.md](standards_documentation_governance_dispatch_queue_20260610.zh.md)

## Dispatch Boundary

This queue expands the P1 triage ledger into bounded work packets. It does not
authorize new conversation threads, production demo domains, broad source
refactors, or premature standards admission for unaccepted task work.

Each packet must return the standard worker packet:

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## Queue

| Packet | Gap | Owner | Goal | Write set | Non-goals | Required validation | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SDG-A1` | GAP-001 | main thread | Resolve ground `TASK_MOVE` vs prior static-hold naming without releasing dynamic ground movement. | `src/components/domains/ground/tasking/**`, `docs/standards/ground/minimal_task_structure*`, affected tests/docs | Full ground movement, terrain, fires, sensing, runtime owner release | Ground tasking architecture tests; focused C++ build/test if headers change; bilingual audit; `git diff --check` | P1 ledger accepted | Code and standard names agree, and G0 static limitation remains explicit | pass |
| `SDG-A2` | GAP-003 | main thread | Register active `MissionCommandCore` threat/target fields in the joint command standard. | `docs/standards/joint/command_link_and_reporting_baseline*`; affected command docs/tests if evidence requires | New command fields, codec changes unless mismatch discovered | Mission command roundtrip tests or existing focused command tests; bilingual audit; markdown inspection | P1 ledger accepted | Four fields have ownership classification and no broader sensor/track claim | pass |
| `SDG-B1` | GAP-002 | documentation worker | Register active mission observation modes under air/naval specialization owners. | `docs/standards/air/obs*`, naval observation standard or naval README section, affected standards indexes | Observation redesign, training/model changes | Focused mission observation import/test; bilingual audit; standards link check | SDG-A2 may run in parallel; avoid same-file edits with SDG-B2 | Air/naval observation mode ownership is explicit | pass |
| `SDG-B2` | GAP-004 | documentation worker | Refresh stale status/date headers after same-file content updates land. | Stale air, bridge, joint, naval standards headers and nearest indexes | Field contract edits assigned to other packets | Markdown inspection; bilingual audit | SDG-B1 and SDG-A2 complete for overlapping files | Readers can tell whether each page is current contract, planning, or held | pass |
| `SDG-C1` | GAP-005 | integration worker | Reconcile modularization planning with current `src/*/domains` roots. | `docs/standards/planning/modularization_plan*`, `docs/standards/README*`, `docs/standards/overview/document_alignment_map*` | New source module tree, broad refactor | Structural boundary tests, markdown inspection, bilingual audit | Domain roots stay stable after current split | Planning page has current-layout section or is archived with pointer | pass |
| `SDG-D1` | GAP-006 | held future worker | Admit weapon-effects standards only after MLF-3 task acceptance. | Future `docs/standards/air/*weapon*` or `docs/standards/weapons/**`; accepted MLF-3 evidence docs | Standards entry from an unaccepted or untracked test alone | MLF-3 acceptance evidence; source admission gates; standards link check | MLF-3 acceptance exists | Standards owner exists or held state remains explicit | held |
| `SDG-V1` | all | main thread | Integrate status, validation evidence, and residuals after remediation batches. | Subproject README/status/queue, parent review index, touched standards indexes | Hide partials, claim overall acceptance before held items are resolved | Focused pytest, bilingual audit, `git diff --check` | One or more remediation packets returned | Accepted slice and residual map match evidence | planned |

## Batch Commit Guidance

- Commit `SDG-A1` separately from documentation-only packets if it changes C++
  identifiers.
- Commit `SDG-A2` and `SDG-B1` separately when they touch different standards
  owners.
- Commit `SDG-B2` only after overlapping content updates are in place.
- Keep `SDG-C1` separate because it changes planning authority and reader
  expectations.
- Do not commit `SDG-D1` until its acceptance trigger exists.

## Forced Review Triggers

Stop and re-scope if any packet discovers:

- a standards contract that conflicts with an active runtime test
- a required code rename that crosses public Python bindings or serialized
  scenario/config fields
- a missing bilingual peer in a Tier-A touched standards file
- a need to create a new standards top-level directory
- MLF-3 evidence that is still unaccepted but being used as current authority

## Integration Notes

- The broader governance pytest suite currently has unrelated failures from
  absent simulation-architecture WP paths. Use the focused standards governance
  test as the local gate for this subproject unless those older tests are being
  repaired in the same batch.
- The default bilingual audit currently reports one pre-existing missing
  English peer outside this subproject:
  `docs/standards/foundation/realism_authority_boundary.zh.md`.
