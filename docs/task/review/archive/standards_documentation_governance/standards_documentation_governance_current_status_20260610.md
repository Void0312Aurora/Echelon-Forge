# Standards Documentation Governance Current Status

Status: `2026-06-10` archived accepted status for standards drift governance.

Parent subproject: [Standards Documentation Governance](README.md)

Language:

- English canonical: `standards_documentation_governance_current_status_20260610.md`
- Chinese companion: [standards_documentation_governance_current_status_20260610.zh.md](standards_documentation_governance_current_status_20260610.zh.md)

## Status Summary

P0 is complete: the governance lane, standards maintenance policy, review
indexes, bilingual registry entry, and guard test are present.

This archived status records the accepted closure surface. The six gaps from the
[Standards-Implementation Alignment Review 2026-06-10](../standards_implementation_alignment_review_20260610.md)
remain classified by drift type, owner, write set, dependency, validation, and
closure gate. GAP-001 through GAP-005 are closed. GAP-006 remains explicitly
held pending MLF-3 acceptance. This status page keeps the accepted slice and
held residual bounded instead of turning governance into an open-ended
standards rewrite.

## Gap Control Ledger

| Gap | Drift class | Standards owner | Implementation owner | Governance decision | Required write set | Validation gate | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| GAP-001 | Semantic mismatch | `docs/standards/ground/minimal_task_structure*` | `src/components/domains/ground/tasking/**` | Closed by renaming the static move task mode to `MoveStatic` while preserving numeric value `1`; G0/G1 static limitation remains explicit. | Ground tasking enum, affected docs, affected tests | Ground architecture tests, focused C++ build/test if headers change, bilingual audit | closed |
| GAP-002 | Implementation ahead of standard | `docs/standards/air/obs*`; `docs/standards/naval/obs*` | `python/mission_obs_taxonomy.py`; mission observation runtime/tests | Closed by registering `air_combat_c2_roe_v1/v2` under air specialization and `naval_screen_station_v1` under naval specialization; no observation taxonomy redesign was needed. | Air obs standard, naval obs standard, naval standards README, affected indexes | Focused mission observation import/test, standards link check, bilingual audit | closed |
| GAP-003 | Implementation ahead of standard | `docs/standards/joint/command_link_and_reporting_baseline*` | `src/components/command/common/mission_command_core.h`; codec/tests | Closed by classifying the four fields as command-context target provenance metadata that supports ROE/assignment without making common core own track fusion. | Joint command-link baseline pair, affected command docs/tests if needed | Mission command roundtrip tests, markdown inspection, bilingual audit | closed |
| GAP-004 | Status/date stale | Standards headers in air, bridge, joint, naval | No direct runtime owner | Closed by refreshing stale or missing status lines for air action, air observation, bridge runtime workflow, joint command/modeling, joint command-link, naval minimal tasking, and naval observation entrypoints. | Stale standards headers and nearest indexes | Markdown inspection, bilingual audit | closed |
| GAP-005 | Planning supplement drift | `docs/standards/planning/modularization_plan*`; standards overview/alignment map | `src/components/domains/**`, `src/systems/domains/**`, `src/models/domains/**` | Closed by retaining the plan as an active planning supplement and adding current-layout notes for realized `domains/` roots, including held ground runtime boundaries and no-empty-owner rules. | Modularization plan pair, standards overview, document alignment map, governance guard test | Structural boundary tests, markdown inspection, bilingual audit | closed |
| GAP-006 | Held standards admission | Future air weapon-effects or weapons standards owner | MLF-3 task docs and tests | Hold until MLF-3 warhead-effects task acceptance exists; do not create a production standards owner from an untracked or unaccepted test alone. | None until acceptance trigger; later standards entry if accepted | MLF-3 acceptance evidence, source admission gates, standards link check | held |

Archive location: `docs/task/review/archive/standards_documentation_governance/`.

## Batch Order

Recommended remediation batches:

1. `Batch A`: GAP-001 and GAP-003.
   - Status: closed.
   - GAP-001 renamed the active task mode to `MoveStatic` without changing its
     numeric wire value.
   - GAP-003 registered active `MissionCommandCore` threat/target provenance
     fields in the joint command-link standard.
2. `Batch B`: GAP-002 then GAP-004.
   - Status: closed.
   - Registered the air-combat C2/ROE and naval screen/station observation
     modes under domain specialization owners, then refreshed status lines that
     touched the same files.
   - Completed the remaining status/header refresh for air action, bridge
     runtime workflow, joint command/modeling, and naval minimal tasking.
3. `Batch C`: GAP-005.
   - Status: closed.
   - Retained the modularization plan as active planning, but added current
     `src/*/domains` layout notes so it no longer reads as a purely future
     target map.
4. `Batch D`: GAP-006.
   - Keep held until MLF-3 acceptance evidence exists.

## Governance Rules In Force

- No production `demo` domain or empty owner shell may be added as a teaching
  artifact.
- No standards page may claim implementation maturity unless code, test,
  scenario, or accepted task evidence is named.
- Planning supplements must say when they are not current runtime contracts.
- Bilingual Tier-A standards governance files must be updated as pairs.
- Gap closure requires validation evidence, not only prose edits.

## Current Residuals

- The default bilingual audit still reports a pre-existing missing English peer
  for `docs/standards/foundation/realism_authority_boundary.zh.md`.
- The broader `tests/architecture/governance` suite has pre-existing failures
  from absent simulation-architecture WP paths.
- GAP-005 is closed; the modularization plan now distinguishes realized domain
  owner roots from still-planned interfaces.
- GAP-006 remains intentionally held pending MLF-3 acceptance.

## Validation Evidence

Batch A:

```text
cmake --build build-workshop --target ef_py -j2: pass
python -m pytest -q tests/architecture/ground/test_tasking_component_boundary.py tests/runtime/mission/test_mission_command_ground_fields_roundtrip.py tests/leader/test_tasking_profile_contracts.py tests/runtime/mission/test_mission_command_roe_fields.py: pass, 24 passed
python -m pytest -q tests/architecture/governance/test_standards_documentation_governance.py: pass, 5 passed
python3 tools/maintenance/translate_docs_batch.py audit --root docs --registry docs/standards/bilingual_document_clusters.json: pass, 66 registry pairs synced, no registry drift; pre-existing missing English peer remains for docs/standards/foundation/realism_authority_boundary.zh.md
```

Batch B:

```text
python -m pytest -q tests/runtime/mission/test_mission_obs_taxonomy.py tests/runtime/air_combat/test_air_combat_c2_roe_mission_observation.py tests/runtime/naval/test_naval_station_policy_surface.py: pass, 31 passed
python -m pytest -q tests/architecture/governance/test_standards_documentation_governance.py: pass, 7 passed
python3 tools/maintenance/translate_docs_batch.py clusters --root docs --write: pass, registry pair_count 67
python3 tools/maintenance/translate_docs_batch.py audit --root docs --registry docs/standards/bilingual_document_clusters.json: pass, 67 registry pairs synced, no registry drift; pre-existing missing English peer remains for docs/standards/foundation/realism_authority_boundary.zh.md
git diff --check for touched Batch B standards/governance paths: pass
```

Batch C and final status/header closure:

```text
python -m pytest -q tests/architecture/governance/test_standards_documentation_governance.py: pass, 9 passed
python3 tools/maintenance/translate_docs_batch.py clusters --root docs --write: pass, registry pair_count 67
python3 tools/maintenance/translate_docs_batch.py audit --root docs --registry docs/standards/bilingual_document_clusters.json: pass, 67 registry pairs synced, no registry drift; pre-existing missing English peer remains for docs/standards/foundation/realism_authority_boundary.zh.md
git diff --check -- docs/standards docs/task/review/standards_documentation_governance tests/architecture/governance/test_standards_documentation_governance.py: pass
```
