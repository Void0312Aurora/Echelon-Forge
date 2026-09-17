# Equipment Work Task Clusters

Status: `2026-09-17` finite task-cluster plan for the reduced write set declared in [README.md](README.md).

Parent: [README.md](README.md)
State input: [equipment_work_current_status_20260917.md](equipment_work_current_status_20260917.md)

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/_work/equipment_work_task_clusters_20260917.md`
Owner: `database/equipment-data`
Last verified: `2026-09-17`

## Boundary Decision

This plan may only modify `database/research/equipment/**` and `database/_templates/**`. It must not
imply runtime consumption, calibrated authority, or whole-domain maturity. It does not create a
parallel documentation route: if a cluster needs a maintained standard outside `database/`, the
cluster stops and returns `blocked` rather than widening the write set.

## Finite Task Cluster List

| Cluster | Owner | Capability tier / model ID / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `E0-COMMIT` | main thread | n/a | Bring the 108 untracked `database/` files under version control so the navigation and template layers cannot be lost and the next merge stays clean. | `database/README.md`, `database/README.zh.md`, `database/_templates/**`, `database/platforms/**`, `database/modules/**`, `database/weapons/**`, `database/sources/**` | No content edits; no new records; no deletions. | `git status --porcelain -- database` is empty after commit; `git ls-files database` grows by 108. | All 108 files tracked. | Serial first; nothing else can be trusted until the tree is tracked. | 1 | planned |
| `E1-DANGLE` | main thread | n/a | Repair the dangling source citation on the M1A2 SEP v3 leaf and record the evidence boundary. | `catalog/ground/vehicles/m1-abrams/m1a2-sepv3/README.md` | No value changes to the parameter rows; only source ids are corrected. | Every `p5-*` in the leaf resolves to a `Source ID:` line under `raw/sources/`. | Zero dangling ids in the leaf; `Last verified` set. | Independent; can run beside `E2` with a disjoint file set. | 1 | planned |
| `E2-IDENTITY` | main thread | n/a | Backfill `Equipment ID` into the 63 leaves that lack it, using the backlog CSV as the id source. | 60 leaves under `catalog/air/**`, 3 leaves under `catalog/module/**` | No parameter edits; no status changes in the CSVs. | Each backlog `catalog_path` leaf carries an `Equipment ID` equal to the CSV `equipment_id`. | 63/63 bound; the catalog-to-backlog check becomes mechanical. | Independent of `E1`. | 2 | planned |
| `E3-COVERAGE` | main thread | n/a | Re-derive `coverage.csv` from the backlog queues so its status column stops contradicting them. | `coverage/coverage.csv`, `coverage/README.md` | No new candidates; no parameter extraction. | Row count and per-row `status` agree with the five backlog CSVs for every shared id. | Every shared candidate's status matches; the file states what it is derived from. | After `E2`. | 1 | planned |
| `E4-SHAPE` | main thread | n/a | Converge the two parameter-table shapes onto one five-column header. | 57 leaves using the `Field` header | No value rewrites; header and column mapping only. | Every leaf exposes `Parameter \| Value \| Source \| Confidence \| Evidence and uncertainty`. | 85/85 leaves share one shape. | After `E1` and `E2`; must not run concurrently with either on a shared leaf. | 2 | planned |
| `E5-LEDGER` | main thread | n/a | Materialize the source ledger and close the admission-field gap without touching maintained standards. | `sources/ledger/**`, `_templates/common.schema.json` | No edits under `docs/`; no source rejection decisions; no tier reassignment. | Ledger rows carry `source_id`, tier, `source_ref`, holder, rights, scope, cross-validation, reasonableness, ingest status, authority status, residuals. | 193/193 packages have a ledger row with non-empty rights and reasonableness fields. | After `E0`; independent of `E1`-`E4`. | 2 | planned |
| `E6-CHECK` | main thread | n/a | Make the five closure-gate conditions runnable instead of manual. | `database/_work/**` | No `tools/`, `tests/`, or CI files — the check stays inside the reduced write set. | The check reports per-condition pass or fail over the tree. | All five conditions report green. | After `E1`-`E5`; serial. | 1 | planned |

## Dispatch Rules

- Every execution maps to exactly one cluster above. Do not open a `E7` wave without re-baselining this list.
- The six normative tables under `coverage/` and `backlog/` are single-writer. Two clusters must not edit one of them concurrently.
- `E0-COMMIT` is serial and first: until the untracked layer is committed, any later work sits on unversioned ground.
- If a cluster needs to touch a file outside the write set, return `blocked` and re-scope. Do not widen silently.
- Follow the repository subagent usage policy when the work is delegated: one bounded scope per worker, no shared normative table.

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
git status --porcelain -- database
git diff --check -- database

# condition 1: every referenced source id resolves to a manifest
# condition 2: every backlog catalog_path leaf carries a matching Equipment ID
# condition 3: backlog status agrees with coverage.csv status
# condition 4: no D-tier source, no package without a retention note
# condition 5: no change outside database/research/equipment and database/_templates
```

Conditions 1 through 5 are performed by `E6-CHECK`; until it lands they are manual inspection.

## Acceptance Criteria

- All six clusters reach `pass` or an honestly named `blocked`.
- `git status --porcelain -- database` shows no untracked file.
- No file outside `database/**` is modified by this plan.
- No equipment record is promoted above its backlog status.
- No text in this tree claims runtime consumption or calibrated authority.

## Residual Map

Immediate:

- `D1` through `D8` in the current-status document remain open until their clusters land.

Follow-on:

- `E6-CHECK` is the prerequisite for any domain expansion: without a runnable gate, new leaves cannot be proven correct.
- Domain expansion order stays ground, air, naval, weapon, module, with the 9 `held` air rows as the first unlock candidates.

Deferred:

- Runtime JSON downlink of any leaf. It requires `examples/config/database/**` and the runtime-facing whitelist, both outside the reduced write set.
- Bilingual companions for catalog leaves. There are 190 English-only records and zero companion pairs; adding them would touch the documentation cluster registry, which is outside `database/`.
- Re-homing this work under `docs/research/work/active/`. Deferred until the branch catches up with `origin/main`.
- The superseded `database/{platforms,modules,weapons,sources}/` trees and their 27 `.gitkeep` placeholders. Held read-only.
