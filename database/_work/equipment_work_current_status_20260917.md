# Equipment Work Current Status

Status: `2026-09-17` measured state of the equipment tree under the reduced write set.

Parent: [README.md](README.md)

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/_work/equipment_work_current_status_20260917.md`
Owner: `database/equipment-data`
Last verified: `2026-09-17`

## Branch And Divergence

| Item | Value |
| --- | --- |
| Branch | `codex/database-scaffold` |
| HEAD | `3fc57c7e` |
| Base | `d1ebb5d3` |
| Own commits | 1 (`3fc57c7e data: add source-backed equipment research catalog`) |
| Behind `origin/main` | 218 commits |
| Ahead of `origin/main` | 1 commit |
| `origin/main` files under `database/` | 0 |
| Tracked files under `database/` | 405, all introduced by `3fc57c7e` |
| Untracked files under `database/` | 108 files, 125,160 bytes |
| Merge dry-run conflicts (`HEAD` vs `origin/main`) | 0 |

The untracked set is the whole `database/` navigation skeleton plus the template layer:
`README.md`, `README.zh.md`, `_templates/**`, `platforms/**`, `modules/**`, `weapons/**`,
`sources/**`. Only `database/research/equipment/**` was committed. Nothing under `database/` is
present on `origin/main`, so this whole tree is branch-local and conflict-free.

## Measured Equipment State

| Metric | Value |
| --- | --- |
| Catalog READMEs | 190 |
| Leaf records (carry `## Parameters`) | 85 |
| Navigation-only nodes | 102 |
| Identity-only nodes | 3 |
| Leaves carrying `Equipment ID` | 55 / 85 |
| Distinct source ids referenced by leaves | 169 |
| Source packages on disk | 193 |
| Referenced-but-missing source packages | 0 |
| On-disk-but-unreferenced source packages | 0 |
| Backlog rows | 118 |
| Coverage rows | 47 |
| Single-source leaves | 30, all under `catalog/air/` |

## Backlog State Distribution

| Domain | Rows | `parameter_complete` | `cataloged` | `held` |
| --- | --- | --- | --- | --- |
| air | 70 | 10 | 51 | 9 |
| ground | 31 | 20 | 11 | 0 |
| weapon | 9 | 9 | 0 | 0 |
| naval | 5 | 5 | 0 | 0 |
| module | 3 | 3 | 0 | 0 |
| **total** | **118** | **47** | **62** | **9** |

## Open Deviations

| Id | Deviation | Evidence | State |
| --- | --- | --- | --- |
| `D1` | Dangling source reference | `catalog/ground/vehicles/m1-abrams/m1a2-sepv3/README.md` cites `p5-us-ground-m1a2sepv3-armytechnology` 4x in the parameter table; no such package exists. Its `Source References` list names `gdls` / `army-peogcs` / `weaponspecs`, two of which never appear in the table. `Last verified` is absent. | open |
| `D2` | Parallel naval namespace | `catalog/naval/ships/surface-combatant/` (tracked, 3 leaves) and the empty untracked `catalog/naval/surface-combatants/` coexist. | open |
| `D3` | Coverage status not trustworthy | `coverage.csv` marks all 47 rows `parameter_complete`; air carries only 10 rows against 70 in `air.csv`, so it is neither a superset nor a status mirror. | open |
| `D4` | Parameter table shape split | 57 leaves use `Field \| Value \| Source \| Tier \| Configuration/uncertainty`; 28 use `Parameter \| Value \| Source \| Confidence`. | open |
| `D5` | `Equipment ID` not backfilled | 63 backlog rows resolve to a leaf with no `Equipment ID`, so catalog-to-backlog binding is one-way only. | open |
| `D6` | Ledger not materialized | `sources/ledger/` holds a README only; `common.schema.json` has no source `$defs` while `FIELDS.md` describes 12 ledger fields. | open |
| `D7` | Source admission fields missing | The 193 manifests carry no rights or redistribution field and no reasonableness assessment, which `docs/research/standards/public_data_source_admission.md` requires of a ledger row. | open |
| `D8` | No automated validation | No file under `tests/` or `tools/` references this tree; the violations above are invisible to the existing CI. | open |

## Admission Boundary

Every deviation above is inside the reduced write set. `D7` is the only one that depends on a
maintained standard owned outside this tree; under the reduced scope the resolution is to complete
the missing fields at the manifest level rather than to amend
`docs/research/standards/public_data_source_admission.md`.

## Explicit Overclaim Refusals

- The 47 `parameter_complete` rows are research drafts. They are not calibrated, not cross-checked,
  and not runtime-eligible.
- No file in this tree is consumed by the runtime loader.
- Family names remain grouping nodes; only concrete variant leaves count as records.
- `cataloged` means a draft leaf exists. It does not mean the parameter set is complete.

## Next Action Order

1. `D1` repair — a wrong citation on an otherwise complete leaf is the highest-severity defect.
2. `D5` backfill — required before any mechanical leaf-to-backlog check can run.
3. `D3` recompute — required before backlog status can be trusted as the completion count.
4. `D4` converge — required before new leaves are added, otherwise the split widens.
5. `D2` cleanup — one empty untracked directory.
6. `D6` and `D7` — ledger materialization and source-admission fields.
7. Domain expansion — only after 1 through 4 are green.
