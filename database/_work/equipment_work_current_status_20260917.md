# Equipment Work Current Status

Status: `2026-09-19` measured state of the equipment tree under the reduced write set.

Parent: [README.md](README.md)

Document kind: `reference`
Lifecycle: `draft`
Canonical: `database/_work/equipment_work_current_status_20260917.md`
Owner: `database/equipment-data`
Last verified: `2026-09-19`

This revision replaces the first measurement pass, which was produced by a
hand-written audit and reported three deviations that do not survive the runnable
check in [check_equipment_tree.py](check_equipment_tree.py). See
[Retracted Findings](#retracted-findings).

## Branch And Divergence

| Item | Value |
| --- | --- |
| Branch | `codex/database-scaffold` |
| Base | `d1ebb5d3` |
| Off-base commits | 35 |
| Behind `origin/main` | 218 commits |
| Ahead of `origin/main` | 35 commits |
| `origin/main` files under `database/` | 0 |
| Tracked files under `database/` | 602 |
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
| `C2` backlog leaf binding (`Equipment ID`) | PASS after the `E2` backfill |
| `C3` backlog vs coverage status | PASS, 58 of 58 coverage rows agree |
| `C4` source admission floor | PASS after the `E3` retention backfill |
| `C5` source-artifact consistency | PASS, no unnamed or aggregate package claims |
| `C6` retrieval record | PASS, 72 unretrieved citations remain advisory; 176 packages lack a retrieval block |

Measured counts:

| Metric | Value |
| --- | --- |
| Source packages (manifests) | 274 |
| Catalog leaves (carry `## Parameters`) | 109 |
| Distinct source ids referenced by leaves | 274 |
| Leaves without `Equipment ID` | 0 |
| Backlog rows | 118 |
| Coverage rows | 58 |
| Status: `cataloged` / `parameter_complete` / `held` | 41 / 69 / 8 |

## Leaf Completeness Against The Queue

The queue calls 41 rows `cataloged`, and all 41 now point at leaves carrying a
`## Parameters` table. The checker therefore reports `stub_rows_excluded: 0` for
the non-held queue rows. A separate catalog scan still finds 82 README leaves
without a parameter table; those are outside the current queue-binding defect and
remain a depth follow-up rather than evidence of completed extraction.

## Coverage Semantics

`coverage/README.md` describes `coverage.csv` as a discovery queue that feeds the
backlog, and defines its `status` column as starting at `queued`. The file does not
behave that way: its 58 rows are exactly the 58 `parameter_complete` rows of the
backlog, verified in both directions. It is an extract of the completed set, not a
pre-backlog discovery surface.

The content is therefore consistent; the documented role and the documented status
vocabulary are not. This is a documentation drift, not a data defect.

## Open Findings

| Id | Finding | Evidence | State |
| --- | --- | --- | --- |
| `D2` | No source package records a rights field | `C4` `missing_rights_field_advisory`, 274 of 274 | open; the admission standard requires it of a ledger row |
| `D3` | 82 catalog leaves outside the non-held queue have no parameter table | catalog scan: 191 README leaves, 109 with `## Parameters`, 82 without | open; scope and depth for these leaves still need a decision |
| `D4` | Parameter table shape split | 57 leaves use a `Field`-based table; 52 use `Parameter \| Value \| Source \| Confidence`; 82 have no parameter table | open |
| `D5` | Disjoint naval namespaces | `catalog/naval/ships/surface-combatant/` (tracked, 3 leaves) and the empty untracked `catalog/naval/surface-combatants/` coexist | open |
| `D6` | Ledger not materialized | `sources/ledger/` holds a README only; `common.schema.json` has no source `$defs` while `FIELDS.md` describes 12 ledger fields | open |
| `D7` | `coverage.csv` role and status vocabulary contradict its own README | 58 of 58 rows are `parameter_complete`, not `queued` | open |
| `D8` | Country rows share a variant leaf without a stated rule | `eq-us-air-c17a` and `eq-uk-air-c17a` both point at `c-17/c-17a`, which is now correct by the `tornado-ids` precedent but is not documented anywhere | open |
| `D9` | `Equipment ID` scheme is not declared | `eq-<country>-<domain>-<variant>`, country-less `module-*`, and country-less variant names such as `tornado-ids` all coexist with no stated rule | open |

## Repaired In This Pass

| Repair | What changed |
| --- | --- |
| `C2` binding | 32 leaves received an `Equipment ID` line derived from their queue row, inserted as additive metadata after `Last verified` rather than as a new `## Identity` section, so the change stays independent of the `D4` shape question |
| `C2` predicate | The check no longer demands a binding from a stub leaf or a `held` row, and no longer treats a shared variant leaf as a defect |
| C-17A operator gap | The leaf listed only the United States Air Force while a Royal Air Force queue row pointed at it. Added the RAF operator row citing `p5-uk-air-c17a-raf`, which was an acquired but unreferenced package. The UK queue row keeps its own id and now carries a note explaining the share |
| Leaf identity | The C-17A leaf had been given `eq-uk-air-c17a` by the backfill. Its parameters and operator table are United States; corrected to `eq-us-air-c17a` |
| `C4` retention | 43 manifests, all air-domain, received the `Retention:` line the raw-source rule requires. The wording follows the 146 packages that already carried it |
| F-35C completion | Added variant-specific propulsion, flight, fuel, armament and crew/ceiling fields; the latter two remain explicitly Tier C and are not copied from F-35A/B |
| KC-46A completion | Added propulsion, thrust, speed, ceiling, range, aircrew-seat semantics and refueling-system fields from the AMC fact sheet |
| C-17A completion | Added height, cargo compartment, ceiling, crew, troop/medical load and mission-conditioned range semantics from the Dover fact sheet |
| Retrieval records | Added or refreshed retrieval blocks for the three USAF/Navy packages and the F-35C manufacturer package; added one traceable HiWars secondary package for the remaining public F-35C crew/ceiling fields |

## Retracted Findings

The first pass reported these. All three are withdrawn.

| Withdrawn | Why it was reported | Why it is withdrawn |
| --- | --- | --- |
| Dangling citation `p5-us-ground-m1a2sepv3-armytechnology` on the M1A2 SEP v3 leaf | An audit script that resolved source packages by declared `Source ID` under only part of the `raw/sources/` tree | The package exists at `raw/sources/army_technology/p5-us-ground-m1a2sepv3-armytechnology/manifest.md`, its `Source ID` line matches, and its own text names the geometry, crew, AGT1500, M256, FLIR, data-link and APU statements the leaf cites it for. The then-current C1 run confirmed 0 dangling ids; the present tree also resolves all 274 manifests |
| `coverage.csv` status not trustworthy | The file marked all 55 rows `parameter_complete` and held only 18 air rows against 70 in `air.csv` | The `air.csv` comparison was the observation, the conclusion was wrong. Both directions of the coverage-to-backlog comparison agree, so `C3` passes. The real defect is documentary and is now `D7` |
| Source-reference count 169 against 193 on disk | The same partial-scan audit | The comparison mixed two denominators: 169 is the count of *distinct* ids leaves cite, against 193 *packages* on disk. Both are correct; the implied gap was not |

## Admission Boundary

Every open finding sits inside the reduced write set. `D2` is the only one that
depends on a maintained standard owned outside this tree
(`docs/research/standards/public_data_source_admission.md`); under the reduced scope
the repair is to complete the missing fields at the manifest level rather than to
amend that standard.

## Explicit Overclaim Refusals

- The 58 `parameter_complete` rows are research drafts. They are not calibrated, not
  cross-checked, and not runtime-eligible.
- No file in this tree is consumed by the runtime loader.
- Family names remain grouping nodes; only concrete variant leaves count as records.
- `cataloged` means a draft leaf exists. It does not mean the parameter set is complete.

## Next Action Order

All six machine-checkable conditions pass. What remains is not a defect the check
can see:

1. `D4` shape convergence — required before new leaves are added, otherwise the split widens.
2. `D7` and `D6` — reconcile the coverage documentation and materialize the ledger.
3. `D2` source admission fields — 273 packages need a rights field before any ledger row is honest.
4. `D8` and `D9` — write down the id and shared-leaf rules, in the form the tornado-ids and module precedents already imply.
5. `D5` cleanup, `D3` stub depth.
6. Domain expansion.
