# Standards Documentation Governance Task Clusters

Status: `2026-06-10` finite task-cluster plan for `standards_documentation_governance`.

Parent subproject: [Standards Documentation Governance](README.md)

## Boundary Decision

The standards tree remains the authority for naming, layering, service/domain
ownership, public-source admission, and documentation governance. This
subproject may update standards docs, related indexes, architecture tests, and
runtime code only when a specific gap requires an accepted implementation
decision.

It must not create a production `demo` domain, must not promote unaccepted task
work into a standard, and must not claim whole-domain maturity from narrow
field-level alignment.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SG-P0` | main thread | n/a | Register the governance lane and policy baseline. | `docs/task/review/standards_documentation_governance/**`, `docs/task/review/README*`, `docs/standards/governance/standards_maintenance_policy*`, `docs/standards/README*`, `tests/architecture/governance/test_standards_documentation_governance.py` | Close individual gaps, runtime behavior changes | `python -m pytest -q tests/architecture/governance/test_standards_documentation_governance.py`; bilingual audit; `git diff --check` | Subproject, policy, indexes, and guard test exist. | First; serial | 1 | pass |
| `SG-P1` | main thread | n/a | Publish the triage ledger and dispatch queue. | `standards_documentation_governance_current_status_20260610*`, `standards_documentation_governance_dispatch_queue_20260610*`, subproject README, governance guard test | Close individual gaps, run code remediation | Focused governance pytest; bilingual audit; `git diff --check` | Every GAP has drift class, owner, write set, validation, and dispatch packet. | After SG-P0; serial | 1 | pass |
| `SG-G1` | main thread | n/a | Resolve GAP-001 ground `TASK_MOVE` vs prior static-hold naming mismatch. | `src/components/domains/ground/tasking/**`, affected ground standards, affected ground tests | Full ground movement release, terrain/fires runtime | Ground architecture/runtime focused tests; C++ build if code changes | Enum/prose semantics agree without overclaiming dynamic movement. | After SG-P0; serial with ground runtime edits | 2 | pass |
| `SG-G2` | main thread | n/a | Resolve GAP-002 by registering implementation-backed mission observation modes. | `docs/standards/air/obs*`, naval observation standard if created, `python/mission_obs_taxonomy.py` only if docs reveal a naming error | Observation redesign, model retraining | Mission observation taxonomy tests or focused import check; link check | `air_combat_c2_roe_v1/v2` and `naval_screen_station_v1` have standards owners. | After SG-P0; parallel-safe with SG-G3 | 2 | pass |
| `SG-G3` | main thread | n/a | Resolve GAP-003 by documenting active `MissionCommandCore` targeting/threat fields. | `docs/standards/joint/command_link_and_reporting_baseline*`, affected command docs/tests if needed | New command fields, codec behavior changes unless mismatch found | Existing mission command roundtrip tests; markdown inspection | Four active core fields have ownership classification. | After SG-P0; parallel-safe with SG-G2 | 2 | pass |
| `SG-G4` | main thread | n/a | Resolve GAP-004 by refreshing stale standard status dates and authority notes. | `docs/standards/air/act*`, `docs/standards/air/obs*`, `docs/standards/bridge/runtime_workflow_and_contract_baseline*`, `docs/standards/joint/*`, `docs/standards/naval/minimal_task_structure*` | Field-level rewrites already assigned to SG-G1 through SG-G3 | Markdown inspection; bilingual audit | Headers tell readers whether the page reflects current runtime contract or planning status. | After or alongside SG-G2/SG-G3, avoid same-file overlap | 1 | pass |
| `SG-G5` | main thread | n/a | Resolve GAP-005 by deciding modularization plan disposition. | `docs/standards/planning/modularization_plan*`, `docs/standards/README*`, `docs/standards/overview/document_alignment_map*` | Large source refactor, new module tree | Markdown inspection; structural boundary tests if references change | Plan is either updated to current `domains/` layout or archived with a forward pointer. | After SG-P0; serial with any standards overview edits | 2 | pass |
| `SG-G6` | future worker | gpt-5.4 / high | Hold or admit GAP-006 weapon-effects standards entry after MLF-3 acceptance. | Future `docs/standards/air/*weapon*` or `docs/standards/weapons/**`, MLF-3 accepted task docs | Premature standardization of unaccepted MLF-3 tests | MLF-3 acceptance evidence; source admission gates; standards link check | Weapon-effects standard exists only after acceptance evidence, otherwise explicit held state remains. | Blocked on MLF-3 acceptance; serial | 2 | held |
| `SG-V` | main thread | n/a | Validate, update status, and prepare closure/archive state. | This subproject, parent review index, affected standards indexes, bilingual registry | Hide residuals, claim overall acceptance from partial fixes | Focused pytest, bilingual audit, `git diff --check` | Accepted slice and residual map match evidence. | Last; serial | 1 | planned |

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- Do not allow two workers to edit the same standards file, status line, field
  table, or bilingual pair concurrently.
- Keep SG-G1 serial because it may touch runtime semantics.
- Keep SG-G6 held until the MLF-3 task surface has acceptance evidence.
- If a cluster exceeds its round cap, stop and re-scope before adding another
  follow-up wave.
- Follow [Subagent Usage Policy](../../../../standards/governance/subagent_usage_policy.md).

## Worker Packet Requirements

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## Validation Plan

```bash
python -m pytest -q tests/architecture/governance/test_standards_documentation_governance.py
python3 tools/maintenance/translate_docs_batch.py audit --root docs \
  --registry docs/standards/bilingual_document_clusters.json
git diff --check -- docs/task/review/standards_documentation_governance \
  docs/task/review/README.md docs/task/review/README.zh.md \
  docs/standards tests/architecture/governance/test_standards_documentation_governance.py
```

Cluster-specific remediation should add affected runtime, architecture, or
contract tests to this list before a gap is closed.

## Acceptance Criteria

- SG-P0 is complete and registered in parent standards/review indexes.
- SG-P1 records the triage ledger and dispatch queue for all six gaps.
- GAP-001 through GAP-006 each have a closed, planned, or held state with a
  write set and closure gate.
- No standards page claims implementation maturity beyond the evidence named in
  code, tests, or accepted task documents.
- Bilingual companions and the maintained cluster registry are updated for
  touched Tier-A standards governance files.

## Validation Evidence

```text
python -m pytest -q tests/architecture/governance/test_standards_documentation_governance.py: pass, 4 passed
python3 tools/maintenance/translate_docs_batch.py audit --root docs --registry docs/standards/bilingual_document_clusters.json: pass, 66 registry pairs synced, no registry drift; pre-existing missing English peer remains for docs/standards/foundation/realism_authority_boundary.zh.md
git diff --check for touched standards governance paths: pass
python -m pytest -q tests/architecture/governance: fail, unrelated existing missing simulation-architecture WP paths expected by older governance tests
python -m pytest -q tests/architecture/governance/test_standards_documentation_governance.py after P1 expansion: pass, 5 passed
cmake --build build-workshop --target ef_py -j2 after Batch A: pass
python -m pytest -q tests/architecture/ground/test_tasking_component_boundary.py tests/runtime/mission/test_mission_command_ground_fields_roundtrip.py tests/leader/test_tasking_profile_contracts.py tests/runtime/mission/test_mission_command_roe_fields.py: pass, 24 passed
python -m pytest -q tests/runtime/mission/test_mission_obs_taxonomy.py tests/runtime/air_combat/test_air_combat_c2_roe_mission_observation.py tests/runtime/naval/test_naval_n4_reward_surface.py after Batch B: pass, 31 passed
python -m pytest -q tests/architecture/governance/test_standards_documentation_governance.py after Batch B expansion: pass, 7 passed
python3 tools/maintenance/translate_docs_batch.py audit --root docs --registry docs/standards/bilingual_document_clusters.json after Batch B: pass, 67 registry pairs synced, no registry drift; pre-existing missing English peer remains for docs/standards/foundation/realism_authority_boundary.zh.md
git diff --check for touched Batch B standards/governance paths: pass
python -m pytest -q tests/architecture/governance/test_standards_documentation_governance.py after Batch C/status closure: pass, 9 passed
python3 tools/maintenance/translate_docs_batch.py audit --root docs --registry docs/standards/bilingual_document_clusters.json after Batch C/status closure: pass, 67 registry pairs synced, no registry drift; pre-existing missing English peer remains for docs/standards/foundation/realism_authority_boundary.zh.md
git diff --check -- docs/standards docs/task/review/standards_documentation_governance tests/architecture/governance/test_standards_documentation_governance.py: pass
```

## Residual Map

Immediate:

- GAP-001 through GAP-005 are closed.
- GAP-006 remains held pending MLF-3 acceptance evidence.
- SG-G5 is closed; the planning page now records current `src/*/domains`
  roots while keeping unreleased interfaces in planning status.

Follow-on:

- Consider a read-only standards drift audit once the first remediation round
  proves the checklist is stable.

Deferred:

- Full standards-tree rewrite.
- Production demo or empty shell domain.
