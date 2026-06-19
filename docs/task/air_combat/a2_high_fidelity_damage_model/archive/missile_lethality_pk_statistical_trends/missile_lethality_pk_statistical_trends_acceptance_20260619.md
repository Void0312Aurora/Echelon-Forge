# MLF-9 Pk Statistical Trends Acceptance Record

Status: `2026-06-19` accepted / archived for the bounded simulation-trend
slice. P0 through P6 are satisfied for deterministic row-level trend extraction
and retained diagnostics/report exposure.

Chinese companion:
[missile_lethality_pk_statistical_trends_acceptance_20260619.zh.md](missile_lethality_pk_statistical_trends_acceptance_20260619.zh.md).

## Acceptance Scope

This record marks the bounded MLF-9 slice accepted. `[x]` = met. `[~]` =
intentionally held outside MLF-9.

Accepted:

- Deterministic trend extraction from explicit `lethality_chain_rows`.
- Honest denominator and outcome buckets for simulation trend reports.
- Wilson-style interval fields and sample/source labels.
- Process-probe retained diagnostics payloads and optional standalone JSON
  report output.
- `structural_breakup` visibility in the Python diagnostics row/snapshot
  surface.

Held:

- Real-world Pk.
- Weapon-specific lethality.
- Target-specific lethality.
- Public-outcome calibration or validation.
- Reward shaping or training success claims.
- Entity deletion, direct crash rules, and debris physics.

## P0 Boundary

- [x] MLF-9 owns Pk/statistical trend reporting only.
- [x] Parent A2 README links the MLF-9 working surface.
- [x] Forbidden claims are listed in README/status/contract docs.
- [x] MLF-10 remains reserved for calibration gates.

## P1 Evidence Inventory

- [x] Inventory names accepted upstream inputs from MLF-5 through MLF-8.
- [x] Inventory separates accepted row facts from calibration, reward, and
  debris-physics residuals.
- [x] Safe write sets are limited to MLF-9 docs, diagnostics rows/reporting, and
  focused tests.

## P2 Metric Contract

- [x] Contract defines row source, accepted stages, denominators, outcome
  buckets, grouping fields, and uncertainty labels.
- [x] `structural_breakup` is part of the Python diagnostics row contract.
- [x] Contract refuses calibrated Pk and real weapon/target truth.

## P3 Trend Harness

- [x] `tools/diagnostics/mlf9_statistical_trends.py` consumes explicit row lists
  or JSON objects containing `lethality_chain_rows`.
- [x] It groups by chain, derives denominator/outcome counts, and emits bounded
  rate records.
- [x] Focused tests cover deterministic fixture summaries, grouping, intervals,
  and non-claim flags.

## P4 Report Integration

- [x] Process probe embeds `mlf9_statistical_trends` in its result payload.
- [x] Process probe can write `--mlf9_report_json_out` as a standalone retained
  diagnostics artifact.
- [x] Report metadata records `sample_source` and `report_surface`.
- [x] Report authority flags keep real-world Pk, weapon/target lethality,
  calibration, reward, and entity deletion false.

## P5 Focused Validation

- [x] `py_compile` passed for the MLF-9 diagnostics/probe/test files.
- [x] Focused pytest reported `50 passed`.
- [x] `git diff --check` passed.
- [x] Local Markdown link inspection covered 22 files with 0 missing local
  links.

## P6 Closeout

- [x] README, current status, task clusters, dispatch queue, validation, and
  acceptance docs agree on accepted/held boundaries.
- [x] Parent A2 README describes MLF-9 as accepted / archived.
- [x] MLF-9 evidence packet is physically archived under the parent A2 local
  archive.
- [x] The old active path contains only a lightweight compatibility pointer.
- [x] Final closeout local Markdown link inspection covered 30 files with 0
  missing local links.

## Retained Boundaries

The accepted MLF-9 output should be read as:

```text
Within this synthetic scenario / fixture population, among rows satisfying this
explicit denominator, this fraction reached this simulated outcome bucket.
```

It must not be read as:

```text
This real weapon has this probability of kill against this real target.
```

## Residuals

- MLF-10 must own calibration gates, public-source outcome admission, and any
  real weapon/target probability discussion.
- Future report consumers must preserve the `synthetic_simulation_trend`
  framing and the false authority flags.
- Archive registry and archive index updates identify the physical evidence
  path.
