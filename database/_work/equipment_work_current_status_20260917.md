# Equipment Work Current Status

Status: `2026-09-17` measured state of the equipment tree under the reduced write set.

Parent: [README.md](README.md)

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/_work/equipment_work_current_status_20260917.md`
Owner: `database/equipment-data`
Last verified: `2026-09-17`

This revision replaces the first measurement pass, which was produced by a
hand-written audit and reported three deviations that do not survive the runnable
check in [check_equipment_tree.py](check_equipment_tree.py). See
[Retracted Findings](#retracted-findings).

## Branch And Divergence

| Item | Value |
| --- | --- |
| Branch | `codex/database-scaffold` |
| Base | `d1ebb5d3` |
| Off-base commits | 4 |
| Behind `origin/main` | 218 commits |
| Ahead of `origin/main` | 4 commits |
| `origin/main` files under `database/` | 0 |
| Tracked files under `database/` | 511 |
| Merge dry-run conflicts (`HEAD` vs `origin/main`) | 0 |

`origin/main` carries no files under `database/`, so the tree this work touches is
branch-exclusive and the lag is conflict-free. Anything written outside `database/`
would land in the moving mainline surface instead; that is the reason the write set
is reduced.

## Automated Check Result

Command: `python database/_work/check_equipment_tree.py`

| Condition | Result |
| --- | --- |
| `C1` every referenced source id resolves | PASS, 0 dangling, 0 manifest/path mismatch |
| `C2` backlog leaf binding (`Equipment ID`) | FAIL, 63 of 118 queue rows point at a leaf with no `Equipment ID` |
| `C3` backlog vs coverage status | PASS, 47 of 47 coverage rows agree |
| `C4` source admission floor | FAIL, 0 D-tier but 43 packages lack a retention note |

Measured counts:

| Metric | Value |
| --- | --- |
| Source packages (manifests) | 193 |
| Catalog leaves (carry `## Parameters`) | 85 |
| Distinct source ids referenced by leaves | 169 |
| Leaves without `Equipment ID` | 30 |
| Backlog rows | 118 |
| Coverage rows | 47 |
| Status: `cataloged` / `parameter_complete` / `held` | 62 / 47 / 9 |

## Coverage Semantics

`coverage/README.md` describes `coverage.csv` as a discovery queue that feeds the
backlog, and defines its `status` column as starting at `queued`. The file does not
behave that way: its 47 rows are exactly the 47 `parameter_complete` rows of the
backlog, verified in both directions. It is an extract of the completed set, not a
pre-backlog discovery surface.

The content is therefore consistent; the documented role and the documented status
vocabulary are not. This is a documentation drift, not a data defect.

## Open Findings

| Id | Finding | Evidence | State |
| --- | --- | --- | --- |
| `D1` | 43 source packages carry no `Retention:` note | `C4` `missing_retention_note`; all 43 are air-domain packages | open |
| `D2` | No source package records a rights field | `C4` `missing_rights_field_advisory`, 193 of 193 | open; the admission standard requires it of a ledger row |
| `D3` | 63 backlog rows bind to a leaf with no `Equipment ID` | `C2` `leaf_missing_equipment_id` | open |
| `D4` | Parameter table shape split | 57 leaves use `Field \| Value \| Source \| Tier \| Configuration/uncertainty`; 28 use `Parameter \| Value \| Source \| Confidence` | open |
| `D5` | Disjoint naval namespaces | `catalog/naval/ships/surface-combatant/` (tracked, 3 leaves) and the empty untracked `catalog/naval/surface-combatants/` coexist | open |
| `D6` | Ledger not materialized | `sources/ledger/` holds a README only; `common.schema.json` has no source `$defs` while `FIELDS.md` describes 12 ledger fields | open |
| `D7` | `coverage.csv` role and status vocabulary contradict its own README | 47 of 47 rows are `parameter_complete`, not `queued` | open |
| `D8` | Four single-source-domain leaves carry one reference only | M1A2 SEP v3 cites one source from five of nine rows | open |

## Retracted Findings

The first pass reported these. All three are withdrawn.

| Withdrawn | Why it was reported | Why it is withdrawn |
| --- | --- | --- |
| Dangling citation `p5-us-ground-m1a2sepv3-armytechnology` on the M1A2 SEP v3 leaf | An audit script that resolved source packages by declared `Source ID` under only part of the `raw/sources/` tree | The package exists at `raw/sources/army_technology/p5-us-ground-m1a2sepv3-armytechnology/manifest.md`, its `Source ID` line matches, and its own text names the geometry, crew, AGT1500, M256, FLIR, data-link and APU statements the leaf cites it for. `C1` confirms 0 dangling ids across 193 manifests |
| `coverage.csv` status not trustworthy | The file marked all 47 rows `parameter_complete` and held only 10 air rows against 70 in `air.csv` | The `air.csv` comparison was the observation, the conclusion was wrong. Both directions of the coverage-to-backlog comparison agree, so `C3` passes. The real defect is documentary and is now `D7` |
| Source-reference count 169 against 193 on disk | The same partial-scan audit | The comparison mixed two denominators: 169 is the count of *distinct* ids leaves cite, against 193 *packages* on disk. Both are correct; the implied gap was not |

## Admission Boundary

Every open finding sits inside the reduced write set. `D2` is the only one that
depends on a maintained standard owned outside this tree
(`docs/research/standards/public_data_source_admission.md`); under the reduced scope
the repair is to complete the missing fields at the manifest level rather than to
amend that standard.

## Explicit Overclaim Refusals

- The 47 `parameter_complete` rows are research drafts. They are not calibrated, not
  cross-checked, and not runtime-eligible.
- No file in this tree is consumed by the runtime loader.
- Family names remain grouping nodes; only concrete variant leaves count as records.
- `cataloged` means a draft leaf exists. It does not mean the parameter set is complete.

## Next Action Order

1. `D3` backfill — the binding must exist before any further leaf verification can be mechanical.
2. `D1` retention notes — a documented source-package requirement that 43 packages miss.
3. `D4` shape convergence — required before new leaves are added, otherwise the split widens.
4. `D7` and `D6` — reconcile the coverage documentation and materialize the ledger.
5. `D2` source admission fields.
6. `D5` cleanup, `D8` evidence depth.
7. Domain expansion.
