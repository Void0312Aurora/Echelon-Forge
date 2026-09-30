# Carrier Strike Group Engagement Current Status

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/domains/naval/work/active/carrier_strike_group_engagement/carrier_strike_group_engagement_current_status_20260928.md`
Owner: `domains/naval`
Last verified: `2026-09-30`

Status: `2026-09-28` planning baseline for
[Carrier Strike Group Engagement](README.md). This is the first checkpoint; there
is no prior state to diff against.

## Baseline

Measured on branch `work/naval-mechanisms` at `5fa7fc9e` (rebased on
`origin/main` `9ee4558e`), Windows MSVC 14.44 Release, `build-independent-win`:

| Check | Outcome |
| --- | --- |
| `ef_test.exe` | 176 / 176 test cases, 19651 assertions |
| `ef_composition_evidence_test.exe` | 7 / 7 |
| naval-surface pytest set | 145 passed, 2 skipped, 59 subtests passed |
| composition + command-tasking architecture tests | pass |
| bilingual audit | 74 / 74 synced |
| governance suite | 3 failures, identical on clean `origin/main` (archive retirement, owner-local metadata, diagnostics sprawl); not introduced by the naval branch |

## Maturity Matrix

| Surface | State | Evidence | Gap against this package |
| --- | --- | --- | --- |
| Named naval platforms | complete for `CSG-S0` (`S0-C`, `2026-09-30`) | 15 ship and submarine classes under `examples/config/database/ships/units/csg/` | anti-ship, torpedo, and deck-cycle loads are content-only until `CSG-S2`/`S4`/`U3` |
| Carrier aircraft | complete for `CSG-S0` | 16 types under `examples/config/database/aircraft/units/csg/`, each with a component damage model | no deck cycle (`CSG-S2`) |
| Naval weapons | records complete; mechanisms partial | 33 weapon records; SAM, gun, and CIWS mounts function | anti-ship, land-attack, ASW-rocket, torpedo mechanisms absent (`CSG-S4`, `CSG-U3`) |
| World frame | geodetic core, sensing horizon, scenario anchor | `src/components/physics/geodesy.h`; every non-sonar sensor and the data link are gated on the smooth-earth horizon (`P3-A`); scenarios declare `environment.geodetic_anchor` and EGI reads it (`P3-B`, `2026-09-29`) | terrain LOS has no earth bulge; `P4-A` regression pending |
| Ship motion | kinematic | `src/systems/domains/naval/ship_motion_system.h` | no turning circle, route following, or damage coupling |
| Group command | single screen station | `NavalCommandIntent` | no formation or group command hierarchy |
| Carrier aviation | absent | none | whole surface missing |
| Aircraft fuel | present in air dynamics | air domain components | no carrier recovery fuel logic; aerial refuelling is only a supply-radius stub in `src/components/systems/logistics.h` |
| Surface sensing | bounded | sea clutter, ducting, horizon proxy | truth-read removal not verified for group scenarios |
| Undersea sensing | passive, truth-reading | `src/models/systems/default_acoustic_model.cpp` iterates true Ship/Submarine positions | no active sonar, propagation profile, towed array, sonobuoy |
| Data links | present, unqualified for CSG scale | command-link and data-link components | latency and capacity not exercised at group scale |
| Electronic warfare | component skeleton | `Jammer`, `Countermeasures`, `RWR` in `src/components/systems/ew.h` | no naval soft-kill or stand-off jamming path |
| Naval damage | synthetic | `DM-N1` profile | seeds only on hitbox hits; motion ignores it |
| Learned naval policy | absent | smoke entries only | out of scope for this package |

## Parameter Sources

The unmerged `origin/codex/database-scaffold` catalog already covers, as draft
class-baseline records: Nimitz-class carrier, Ticonderoga-class cruiser,
Type 052D, Los Angeles-class SSN, F/A-18E, F-35C, EA-18G, E-2D, J-15, KJ-500,
Z-20, AGM-158C LRASM, and AIM-120D. It does not cover the Ford class, the
Fujian, Type 055, J-35, J-15T, KJ-600, the Chinese anti-ship and ship-air-defense
missile families, torpedoes, or Chinese replenishment ships. Those need
public-web research under `S0-A`.

## System Owner Packages

Cross-domain mechanisms are owned by `docs/systems/` owners. Two owner packages
opened on `2026-09-28` for the first stages' needs, both in planning:

- [Geodetic Frame](../../../../../systems/physics/work/active/geodetic_frame/README.md) (`systems/physics`) — needed by `CSG-S0`;
- [Environment Runtime](../../../../../systems/environment/work/active/environment_runtime/README.md) (`systems/environment`) — layered land, freshwater, sea, and atmosphere runtime; needed by `CSG-S1`. Its later ocean data line supplies bathymetry, temperature/salinity, and sea state.

The remaining owner packages open at the stage that needs them; see the README's
System Dependency Register.

## Compute

Local host: Windows, MSVC. Offload host: HEI (`ssh HEI-WIRED`), 88 cores, 121 GB,
RTX 3090, Ubuntu 24.04, gcc 13.3. Its checkout needs a rebuild before use and
its root filesystem is 91 % full.

## Residual Register

| Residual | Owner | Entry condition |
| --- | --- | --- |
| uniform high-fidelity stepping may not carry the full order of battle | this package | throughput records at `CSG-S1`/`CSG-S2` |
| no flight-deck contact surface: embarked aircraft stay inventory (the gear-contact step-size limit was closed `2026-09-30` by [Semi-Implicit Ground Contact](../../../../../systems/physics/reviews/semi_implicit_ground_contact_20260930/README.md)) | `systems/physics` with this package | `CSG-S2` deck cycle |
| Air-domain seams for carrier aviation | Air owner, via this package | `S2-B` dispatch |
| the unmerged scripted-agent stack may be required for group scripting | architecture owner | `S5-B` dispatch |

## Next Action Order

1. `P0-A` accepted here and in both owner packages (`2026-09-28`).
2. `S0-A` accepted: [Ford OOB](../../../reviews/csg_order_of_battle_20260928/csg_order_of_battle_ford_20260928.md)
   (7 ships, 74 aircraft, 312 sourced rows), [Fujian OOB](../../../reviews/csg_order_of_battle_20260928/csg_order_of_battle_fujian_20260928.md)
   (6 ships, about 48 aircraft, 408 sourced rows), and the [source ledger](../../../reviews/csg_order_of_battle_20260928/csg_source_ledger_20260928.md)
   (305 sources, 22 pending). Geodetic Frame `P1-A`, `P2`, and `P3-A` are accepted;
   `P3-A` moves surface detection to the curvature horizon (SPY-1D against a
   surface target: 43.9 km + declared ducting, not the configured 185 km), and
   `P3-B` lets CSG scenarios declare their geodetic anchor.
3. `S0-C` accepted `2026-09-30` (115 records; see the task clusters' S0-C
   Record). `S0-D` accepted `2026-09-30` (group schema, named and mirror
   scenarios). Next: `S0-B` frame integration, then `S0-X`.

## Overclaim Refusals

Nothing in this package's current state establishes carrier aviation, anti-ship
engagement, undersea warfare, group command, or any learned-policy result.
