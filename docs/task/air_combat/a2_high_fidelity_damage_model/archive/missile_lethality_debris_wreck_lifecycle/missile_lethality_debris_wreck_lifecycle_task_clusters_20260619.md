# MLF-8 Debris And Wreck Lifecycle Task Clusters

Status: `2026-06-19` accepted / archived finite task-cluster record for
[README.md](README.md). All MLF-8 clusters are complete for the bounded
diagnostics-only lifecycle slice.

Parent subproject links:

- English canonical: [README.md](README.md)
- Chinese companion:
  [missile_lethality_debris_wreck_lifecycle_task_clusters_20260619.zh.md](missile_lethality_debris_wreck_lifecycle_task_clusters_20260619.zh.md)

## Boundary Decision

MLF-8 may add bounded lifecycle representation for terminal wrecks and detached
parts. It must not add Pk authority, calibrated debris throw, weapon-specific
lethality, or default reward authority. First implementation output should be
diagnostics-only unless a later accepted contract changes that visibility.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MLF-8-P0` | main thread | n/a | Create subproject entry, status, contract surface, dispatch queue, archive placeholder, and parent navigation. | `docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_debris_wreck_lifecycle/**`; parent A2 and air-combat README files | Runtime edits, tests, reward changes | Markdown links, `git diff --check` | Subproject is navigable and scope-limited | first, serial | 1 | complete / link-pass |
| `MLF-8-P1` | read-only diagnostics worker | n/a | Inventory structural breakup outputs, lifecycle fields, entity active semantics, event store, facade, bindings, diagnostics, and reward consumers. | inventory/status docs under this subproject | Code changes, authority changes | Cited source/test inventory; local link check | Inventory names reusable fields and gaps | after P0, parallel with P2 draft review only after read-only pass | 1 | complete / inventory-pass |
| `MLF-8-P2` | contract worker | n/a | Define lifecycle contract for original airframe, wreck fact, detached-part debris fact, and optional future debris entities. | contract/status docs | Runtime edits, selected TP-21 output authority, Pk | Contract table inspection; consistency with MLF-7 residuals | Contract states producers, consumers, visibility, and acceptance gates | after P1 | 1 | complete / contract-pass |
| `MLF-8-P3` | integration worker | n/a | Implement bounded lifecycle state/event writing for accepted contract rows. | `src/components/**`, `src/systems/**`, `src/core/engine/**`, focused C++ tests | Physics debris throw, visual particles, reward shaping | `cmake --build build-workshop --target ef_test -j 2`; focused CTest | Runtime emits only accepted lifecycle facts and preserves active-state semantics | after P2, serial | 2 | complete / focused-pass |
| `MLF-8-P4` | diagnostics/facade worker | n/a | Expose lifecycle facts through bindings, facade packets, and diagnostics probes. | `src/interfaces/**`, `src/runtime/facade/**`, `tools/diagnostics/**`, tests | Reward authority, Pk, calibration claims | focused Python and facade/binding tests | MLF-8 lifecycle rows are inspectable and chain-linked | after P3 | 2 | complete / focused-pass |
| `MLF-8-P5` | validation worker | n/a | Cover no-breakup, single detached part, multi-part breakup, terminal wreck, and diagnostics-only reward non-leakage. | `src/tests/**`, `tests/runtime/**`, status docs | New model scope, broad refactors | focused CTest, targeted pytest lanes | Tests prove accepted lifecycle behavior and no false positives | after P3/P4 | 2 | complete / focused-pass |
| `MLF-8-P6` | main thread | n/a | Run broader smoke and update evidence. | status/acceptance docs | Scope expansion | `ctest --test-dir build-workshop --output-on-failure`; targeted air-combat pytest | Regression smoke is green or residuals are explicitly held | after P5, serial | 1 | complete / smoke-pass |
| `MLF-8-P7` | main thread | n/a | Accept or hold MLF-8, synchronize parent navigation, and archive if accepted. | README/status/acceptance/archive files; parent indexes | Runtime edits | docs link checks, `git diff --check` | Acceptance states exact claims and deferrals | after P6, serial | 1 | complete / archived |

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- No worker may edit archived MLF-1 through MLF-8 packages except to fix a
  broken link or upstream fact bug explicitly called out by the main thread.
- No two workers may edit the same normative table, lifecycle contract, event
  binding, or status line concurrently.
- Runtime implementation must follow the accepted P2 lifecycle contract.
- P2 must resolve the lifecycle-event reward filtering gap before P3 emits
  diagnostics-only lifecycle rows.
- Acceptance and archive changes remain serial on the main thread.
- If a cluster exceeds its round cap, stop and re-scope before adding another
  repair wave.

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
git diff --check
cmake --build build-workshop --target ef_test -j 2
ctest --test-dir build-workshop --output-on-failure
PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/ tests/runtime/engagement/
```

Use narrower commands inside implementation clusters, then run broad smoke only
for P6 or high-blast-radius changes.

## Acceptance Criteria

- Lifecycle outputs are chain-linked to structural/consequence evidence.
- Terminal original-entity retirement and debris/wreck facts are not confused.
- Diagnostics-only lifecycle facts do not enter reward shaping.
- No Pk, selected debris-output, real debris throw, or weapon-specific
  authority is introduced.
- Parent navigation and residual map remain current.

## Residual Map

| Residual | Destination | Notes |
| --- | --- | --- |
| Pk/statistical trend projection | MLF-9 | Requires separate trend contract and validation data. |
| Calibrated debris throw or real-world debris damage | MLF-10 or later evidence gate | Existing debris evidence remains fail-closed until selected outputs are admitted. |
| Debris-to-secondary-damage interactions | Future MLF-8 extension only after base lifecycle acceptance | Do not combine with P3 base representation. |
| Visual debris rendering | Future visual/runtime task | Not part of lethality authority. |
