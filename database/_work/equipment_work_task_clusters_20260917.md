# Equipment Work Task Clusters

Status: `2026-09-19` finite task-cluster plan for the reduced write set declared in [README.md](README.md).

Parent: [README.md](README.md)
State input: [equipment_work_current_status_20260917.md](equipment_work_current_status_20260917.md)

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/_work/equipment_work_task_clusters_20260917.md`
Owner: `database/equipment-data`
Last verified: `2026-09-19`

## Boundary Decision

This plan may only modify `database/research/equipment/**` and `database/_templates/**`. It must not
imply runtime consumption, calibrated authority, or whole-domain maturity. It does not create a
parallel documentation route: if a cluster needs a maintained standard outside `database/`, the
cluster stops and returns `blocked` rather than widening the write set.

## Finite Task Cluster List

| Cluster | Owner | Capability tier / model ID / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `E0-COMMIT` | main thread | n/a | Bring the previously untracked `database/` files under version control so the navigation and template layers cannot be lost and the next merge stays clean. | `database/README.md`, `database/README.zh.md`, `database/_templates/**`, `database/platforms/**`, `database/modules/**`, `database/weapons/**`, `database/sources/**` | No content edits; no new records; no deletions. | `git status --porcelain -- database` is empty after commit; `git ls-files database` confirms the write set is tracked. | All initial untracked files tracked. | Serial first; nothing else can be trusted until the tree is tracked. | 1 | pass |
| `E1-CHECK` | main thread | n/a | Make the closure-gate conditions runnable, then re-measure and correct the status ledger from its output. | `database/_work/**` | No `tools/`, `tests/`, or CI files — the check stays inside the reduced write set. | The check reports per-condition pass or fail; the status ledger cites its output. | The check runs and its six automated conditions are reported honestly, including advisory residuals. | After `E0`; blocks `E2` because the binding gate must exist first. | 2 | pass |
| `E2-IDENTITY` | main thread | n/a | Backfill `Equipment ID` into the leaves that lacked it, using the backlog CSV as the id source. Gate: the derived id must not conflict with the path it points at, and each leaf's `Identity` block must accept it without contradicting its own family/variant text. | Catalog leaves under `catalog/**` | No parameter edits; no status changes in the CSVs; no leaf keeps an id that disagrees with its own path. | `python database/_work/check_equipment_tree.py` reports `C2` PASS. | `C2` PASS with 0 unbound rows and 0 missing catalog paths. | Independent of `E1`; must not run on a leaf that `E4` is editing. | 2 | pass |
| `E3-RETENTION` | main thread | n/a | Add the missing `Retention:` note to source packages that lack it, in the form the raw-source rule requires. | `raw/sources/**` | No tier reassignment; no source rejection; no change to any extracted value. | `python database/_work/check_equipment_tree.py` reports `C4` PASS. | `C4` PASS with 0 packages missing a retention note. | Independent of `E2`; disjoint file set. | 1 | pass |
| `E4-SHAPE` | main thread | n/a | Converge the two parameter-table shapes onto one five-column header. | Leaves currently using the `Field` header | No value rewrites; header and column mapping only. | Every leaf exposes `Parameter \| Value \| Source \| Confidence \| Evidence and uncertainty`. | 109/109 leaves share one shape. | After `E2`; must not run concurrently with `E2` on a shared leaf. | 2 | planned |
| `E5-COVERAGE-DOC` | main thread | n/a | Reconcile `coverage/README.md` with what `coverage.csv` actually is: an extract of completed rows, not a pre-backlog discovery queue. | `coverage/README.md` | No change to `coverage.csv` rows; no new candidates. | The README names the file's real derivation and stops defining `status` as starting at `queued`. | The README's stated role and status vocabulary match the data. | Independent of `E2` and `E3`; disjoint file set. | 1 | planned |
| `E6-LEDGER` | main thread | n/a | Materialize the source ledger and close the rights gap without touching maintained standards. | `sources/ledger/**`, `_templates/common.schema.json` | No edits under `docs/`; no source rejection decisions; no tier reassignment. | Ledger rows carry `source_id`, tier, `source_ref`, holder, rights, scope, cross-validation, reasonableness, ingest status, authority status, residuals. | 273/273 packages have a ledger row with non-empty rights and reasonableness fields. | After `E3`; the ledger consumes the retained packages, not the other way round. | 2 | planned |
| `E7-EXPAND` | main thread | n/a | Add new equipment records. Entry gate: `E2`, `E3`, `E4` green, because a new leaf written against a split header or an unbound queue row deepens both defects. | New leaf directories under `catalog/**` plus their backlog rows | No family-level parameter tables; no runtime JSON; no promotion of any record above its backlog status. | `check_equipment_tree.py` stays green after each addition. | Every new leaf is bound (`C2`), shape-conformant, and cited to a retained package. | Serial after `E4`; each batch is its own commit. | 3 | held |

## Dispatch Rules

- Every execution maps to exactly one cluster above. Do not open an `E8` wave without re-baselining this list.
- The six normative tables under `coverage/` and `backlog/` are single-writer. Two clusters must not edit one of them concurrently.
- `E2` must not edit a leaf that `E4` is reshaping. Run them serial or split the leaf set explicitly.
- `E7-EXPAND` stays held until `E2`, `E3`, and `E4` are green. A new leaf written against a split header or an unbound queue row deepens both defects.
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
python database/_work/check_equipment_tree.py            # C1-C6, exit 1 on any failure
python database/_work/check_equipment_tree.py --verbose  # per-condition findings
git status --porcelain -- database                       # separate write-set containment check
git diff --check -- database
```

All six numbered conditions are automated by the tree checker. Write-set
containment remains separate because it needs the git index rather than the data
tree.

## Acceptance Criteria

- All listed clusters reach `pass` or an honestly named `blocked`.
- `git status --porcelain -- database` shows no untracked file.
- No file outside `database/**` is modified by this plan.
- No equipment record is promoted above its backlog status.
- No text in this tree claims runtime consumption or calibrated authority.

## Residual Map

Immediate:

- `D2` through `D9` in the current-status document remain open until their clusters land.

Follow-on:

- The runnable equipment check is the prerequisite for any domain expansion: without a green gate, new leaves cannot be proven correct.
- Domain expansion order stays ground, air, naval, weapon, module, with the 8 `held` rows as the first unlock candidates.

Deferred:

- Runtime JSON downlink of any leaf. It requires `examples/config/database/**` and the runtime-facing whitelist, both outside the reduced write set.
- Bilingual companions for catalog leaves. There are 190 English-only records and zero companion pairs; adding them would touch the documentation cluster registry, which is outside `database/`.
- Re-homing this work under `docs/research/work/active/`. Deferred until the branch catches up with `origin/main`.
- The superseded `database/{platforms,modules,weapons,sources}/` trees and their 27 `.gitkeep` placeholders. Held read-only.
