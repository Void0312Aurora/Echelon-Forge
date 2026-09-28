# Carrier Strike Group Order Of Battle Research

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/domains/naval/reviews/csg_order_of_battle_20260928/README.md`
Owner: `domains/naval`
Last verified: `2026-09-28`

Language: English canonical only; no Chinese companion (dated research evidence).

Status: `2026-09-28` accepted as the `S0-A` research evidence for
[Carrier Strike Group Engagement](../../work/active/carrier_strike_group_engagement/README.md).
Research-grade and non-authoritative: these pages are parameter candidates with
provenance, not runtime authority, and no scenario outcome built on them is a
prediction about real forces.

## Contents

| Page | Scope | Rows |
| --- | --- | --- |
| [Ford-class CSG order of battle](csg_order_of_battle_ford_20260928.md) | CVN-78 Gerald R. Ford, CVW-8, DESRON escorts, doctrinal SSN and oiler fills, and their weapons (2025–2026 deployment) | 7 ships, 74 aircraft, 312 sourced parameter rows |
| [Fujian carrier group order of battle](csg_order_of_battle_fujian_20260928.md) | Fujian (Type 003), estimated air wing, Type 055 / 052D / 054A escorts, assumed Type 093B SSN, Type 901, and their weapons (2025–2026) | 6 ships, about 48 aircraft, 408 sourced parameter rows |
| [CSG source ledger](csg_source_ledger_20260928.md) | Every source cited by both pages, per the [public data source admission standard](../../../../research/standards/public_data_source_admission.md) | 305 sources (116 US, 189 PLAN), 22 pending |

## How These Pages Were Produced

- Parameters were researched from public sources in five packets (one US, three
  PLAN, one reuse of the draft catalog on `origin/codex/database-scaffold`).
- Each value carries a source ID, a tier (`A` official, `B` public-engineering,
  `C` sanity-check), and an uncertainty or conflict note. `C`-only values are
  marked; reasoned estimates are labelled `engineering_estimate`; values with no
  public source are `not public`.
- The main thread checked both pages against the research files: no sourced
  parameter row was dropped, and every source ID resolves in the ledger.

## Arbitrated Corrections (summary)

- USS Mahan (DDG-72) is Flight II, not Flight IIA and not the repository's
  Flight I record.
- Tongliao (554), the Fujian group's first frigate escort, is Type 054A, not
  Type 054B.
- The 2025–2026 Type 055 ship-launched hypersonic round is modelled as YJ-20,
  with YJ-21 kept as the 2022 assessment.
- The PLAN group's SSN and the US group's SSN and oiler are doctrinal fills;
  neither navy names them.

Each page lists its full corrections and residuals.

## Use In The Package

- `CSG-S0` unit content (`S0-C`) draws from these pages; each runtime value
  records its source ID.
- A Tier A or B source supersedes a `C`-only or estimate row. Updated research
  is recorded as a new dated package here, not by editing these pages in place.
