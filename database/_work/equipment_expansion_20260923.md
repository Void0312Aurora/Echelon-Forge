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
| New records required | 8 | 32 |

## Current iteration ledger

| Batch | Scope | State | Commit |
| --- | --- | --- | --- |
| R-1 | Mirage 2000D RMV completion and run setup | complete | `cc4628c9` |
| R-2 | C-5M, AC-130J, CV-22B, HC-130J and E-2D expansion | complete | `fb401b7c` |
| R-3 | Su-35S, Su-34E and Su-30SME completion | complete | `96d44c72` |
| R-4 | J-16, Tu-160M and Il-76MD-90A completion | complete | `d4be0b69` |
| R-5 | AIM-9X Block II, AIM-120D and GBU-39A/B weapon expansion | complete | `5d960a4a` |
| R-6 | P-3C, F/A-18C and UH-1Y official U.S. naval-aircraft expansion | complete | `c7220e60` |
| R-7 | J-11B/BS, J-15 and H-6K parameter completion from named secondary packages | complete | `cf2baabe` |
| R-8 | KJ-500, YY-20A and Z-20 parameter completion with named government/specialist packages | complete | `efc7760f` |
| R-9 | M4A1, AK-74M, FN SCAR-L Mk2 STD and HK416 A5 small-arms expansion | complete | `198118b4` |
| R-10 | M249, PKM, MG3 and MG4 machine-gun expansion | complete | `318368e2` |
| R-11 | M2A1, M240B, Mk 19 Mod 3 and AGS-17 crew-served weapon expansion | complete | `76368bee` |
| R-12 | M777A2, CAESAR 6x6 and BM-21 Grad artillery expansion | complete | `1523e990` |
| R-13 | Carl-Gustaf M4, AT4CS HP and M72A5-C1 anti-armour expansion | complete | `2065de21` |
| R-14 | Panzerfaust 3, RPG-7 and SPIKE LR II anti-armour expansion | complete | `3f69c480` |
| R-15 | MiG-31BM held-record completion from a named variant profile | complete | `aa9d0135` |
| R-16 | Su-57 held-record completion from official programme and bounded baseline profiles | complete | `466ffb4e` |
| R-17 | Tu-95MS held-record completion from a named variant profile | complete | `b1fc0c1e` |

## Blocker / skip ledger

| Candidate | Blocker | Alternative tried | Decision |
| --- | --- | --- | --- |
| `eq-cn-air-y20` | Official Chinese material confirms role/family status but does not publish variant-level dimensions, mass, speed, range or crew; public figures mix Y-20A/Y-20B and tanker configurations | Official MND family page plus current secondary Y-20A references checked; no single base-Y-20 variant package found | Keep `cataloged`; defer until a variant-named technical package is found |
| `eq-us-ground-stryker-m1252-mcvv` | Variant-level propulsion/mobility remains unknown; family M1129/M1252 values would be cross-model substitution | Army TB/TRADOC, mortar ATP, GDLS brochure, AFV Database and MDEX family pages checked | Keep cataloged and skip this pass; do not copy family powerpack or speed |

## Acceptance gate

The run is not considered complete until the backlog reaches 150 rows, all 150
rows are `parameter_complete`, every new leaf has a source-backed parameter table,
and C1–C6 pass after the final pushed batch.
