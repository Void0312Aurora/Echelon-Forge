# Carrier Strike Group Engagement Current Status

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/domains/naval/work/active/carrier_strike_group_engagement/carrier_strike_group_engagement_current_status_20260928.md`
Owner: `domains/naval`
Last verified: `2026-09-28`

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
| Named naval platforms | partial | 5 ship units in `examples/config/database/ships/units/` | no carrier, cruiser, Type 055/052D, SSN, or Chinese replenishment ship |
| Carrier aircraft | absent | aircraft units: F-16C, Su-35S, E-3, MQ-9, MH-60R MVP | no F/A-18E/F, F-35C, EA-18G, E-2D, J-15T, J-35, KJ-600, Z-20 |
| Naval weapons | partial | VLS-SAM, Mk45, Phalanx mounts | no anti-ship missile, named SAM family, or torpedo |
| World frame | flat | radar horizon is a proxy flag in `src/components/systems/sensor.h` | no geodetic frame or earth curvature |
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

## Compute

Local host: Windows, MSVC. Offload host: HEI (`ssh HEI-WIRED`), 88 cores, 121 GB,
RTX 3090, Ubuntu 24.04, gcc 13.3. Its checkout needs a rebuild before use and
its root filesystem is 91 % full.

## Residual Register

| Residual | Owner | Entry condition |
| --- | --- | --- |
| uniform high-fidelity stepping may not carry the full order of battle | this package | throughput records at `CSG-S1`/`CSG-S2` |
| Air-domain seams for carrier aviation | Air owner, via this package | `S2-B` dispatch |
| the unmerged scripted-agent stack may be required for group scripting | architecture owner | `S5-B` dispatch |

## Next Action Order

1. Owner review of the `P0-A` documents.
2. `S0-A` order-of-battle research and `S0-B` geodetic frame, in parallel.
3. `S0-C` unit content, then `S0-D` scenarios, then `S0-X`.

## Overclaim Refusals

Nothing in this package's current state establishes carrier aviation, anti-ship
engagement, undersea warfare, group command, or any learned-policy result.
