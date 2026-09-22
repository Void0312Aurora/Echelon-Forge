# Equipment completion and expansion run

Status: `active`
Started: `2026-09-23`
Branch: `codex/database-scaffold`
Owner: `database/equipment-data`

## Objective

1. Bring every existing equipment row to `parameter_complete` where a
   traceable variant-level source can support the declared fields.
2. Add enough new concrete equipment records to reach **150 total backlog rows**.
   Every added row must enter the backlog as `parameter_complete`; a newly
   discovered candidate without a complete parameter package is recorded in the
   skip/blocker ledger instead of being counted toward the target.

The records remain research drafts. This run does not construct a runtime schema,
calibration package, inventory claim, or final simulation configuration.

## Unattended execution rules

- Work in small source-first batches.
- Keep each parameter row tied to a named source package and keep variant/family
  boundaries explicit.
- Do not copy a value across variants merely to close a field.
- If a source is blocked, try one bounded alternative (official mirror, specialist
  reference, or community record with the value stated). If the field still cannot
  be supported, log the blocker and skip that candidate without stopping the run.
- After every batch: run `check_equipment_tree.py`, inspect the diff, commit the
  verified batch, and push `codex/database-scaffold`.

## Baseline and target

| Measure | Baseline | Target |
| --- | ---: | ---: |
| Backlog rows | 118 | 150 |
| `parameter_complete` rows | 95 | 150 |
| `cataloged` rows | 15 | 0 |
| `held` rows | 8 | 0 where evidence can be obtained; otherwise retained with a blocker |
| New records required | 5 | 32 |

## Current iteration ledger

| Batch | Scope | State | Commit |
| --- | --- | --- | --- |
| R-1 | Mirage 2000D RMV completion and run setup | complete | `cc4628c9` |
| R-2 | C-5M, AC-130J, CV-22B, HC-130J and E-2D expansion | complete | `fb401b7c` |
| R-3 | Su-35S, Su-34E and Su-30SME completion | ready to commit | — |

## Blocker / skip ledger

| Candidate | Blocker | Alternative tried | Decision |
| --- | --- | --- | --- |
| — | — | — | — |

## Acceptance gate

The run is not considered complete until the backlog reaches 150 rows, all 150
rows are `parameter_complete`, every new leaf has a source-backed parameter table,
and C1–C6 pass after the final pushed batch.
