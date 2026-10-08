# Carrier Strike Group Engagement Current Status

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/domains/naval/work/active/carrier_strike_group_engagement/carrier_strike_group_engagement_current_status_20260928.md`
Owner: `domains/naval`
Last verified: `2026-10-08`

Status: `2026-10-08` runtime checkpoint for
[Carrier Strike Group Engagement](README.md). `S0-A`..`S0-X` are accepted;
S0-X closes with native replay and agent-free visualization evidence. See the
[stage gate](carrier_strike_group_engagement_acceptance_20260928.md#csg-s0-runtime-checkpoint-2026-09-30).
S1-A/B implementations are validated pending integration review; see the
[A/B checkpoint](carrier_strike_group_engagement_acceptance_20260928.md#csg-s1-ab-runtime-checkpoint-2026-10-08).
S1-C/D/X remain dependency-blocked.

## Initial Baseline (`2026-09-28`)

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
| CSG placement / static scenario | S0-B and S0-X verified `2026-09-30` | `087c1928`; named and mirror scenarios run 240 steps / 120 s; hulls stay fixed; replay artifacts and profiles pass | inventory aircraft are not live entities; deck cycle remains S2 |
| Ship motion | S1-B bounded maneuvering, validated | `ship_motion_system.h`, `ship_maneuvering.h`, native tests | quadratic surge, bounded Nomoto yaw and damage response; full hydrodynamics and source calibration for proxy hulls remain out of scope |
| Group command | S1-A surface formation / guide route, validated | `NavalCommandIntent`, `station_keeping.h`, `csg_transit.py`; full-duration named/mirror tests | true-bearing stations; scenario-owned waypoints; Joint group hierarchy remains S1-D |
| Carrier aviation | absent | none | whole surface missing |
| Aircraft fuel | present in air dynamics | air domain components | no carrier recovery fuel logic; aerial refuelling is only a supply-radius stub in `src/components/systems/logistics.h` |
| Surface sensing | bounded | sea clutter, ducting, horizon proxy | truth-read removal not verified for group scenarios |
| Undersea sensing | passive, truth-reading | `src/models/systems/default_acoustic_model.cpp` iterates true Ship/Submarine positions | no active sonar, propagation profile, towed array, sonobuoy |
| Data links | present, unqualified for CSG scale | command-link and data-link components | latency and capacity not exercised at group scale |
| Electronic warfare | component skeleton | `Jammer`, `Countermeasures`, `RWR` in `src/components/systems/ew.h` | no naval soft-kill or stand-off jamming path |
| Naval damage | synthetic, live mobility consumed | `DM-N1`, registered damage and motion systems; flooding response test | real-world compartment calibration remains open; motion consumes mobility capability directly |
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
opened on `2026-09-28` for the first stages' needs:

- [Geodetic Frame](../../../../../systems/physics/work/active/geodetic_frame/README.md) (`systems/physics`) — `P3-A` / `P3-B` accepted and consumed by `CSG-S0`; package regression closure remains pending;
- [Environment Runtime](../../../../../systems/environment/work/active/environment_runtime/README.md) (`systems/environment`) — layered land, freshwater, sea, and atmosphere runtime; needed by `CSG-S1`. Its later ocean data line supplies bathymetry, temperature/salinity, and sea state.

The remaining owner packages open at the stage that needs them; see the README's
System Dependency Register.

## Compute

The S0 checkpoint used Windows MSVC Release, `build-independent-win`, with
`CMO_BUILD_DIR` pinned to that directory. The S0 runtime has 24 live entities in
the named variant and 22 in the mirror, including stowed helicopters; each runs
120 simulated seconds in about 0.11 s of native stepping. This excludes the
inventory air wing, loading, and visualization.

The `2026-10-08` S1-A/B checkpoint uses a clean local MSVC Release build in
`build-s1-win-verified-20261008` and an isolated HEI source snapshot at
`/home/void0312/work/naval-s1-20261008`, accessed through `ssh HEI` and built
with `-j32`. `CMO_BUILD_DIR` explicitly selects each current extension.
Both hosts pass all 284 native tests. After the N-1 ship-state review repair,
the candidate state-transfer target passes 72 tests / 1993 assertions on both
hosts, including legacy hull import followed by native movement. The initial
focused Python set passes 135 tests and 16 subtests; post-review S1 transit and
migration-evidence validation passes 15 tests on each host.
S1 live entity counts remain 24 / 22; each variant runs one simulated hour.
Timing scope and replay/profile evidence are in the A/B checkpoint.

## Residual Register

| Residual | Owner | Entry condition |
| --- | --- | --- |
| S0 replay artifact and spectator visualization | visualization / runtime evidence, via this package | S0-X accepted; S1/U1 may dispatch |
| ship fuel burn/endurance and shared logistics contract absent | `systems/physics` | deliver and accept the shared owner contract before S1-C; current NavalStores transfer is insufficient |
| layered maritime/bathymetry query absent; Environment Runtime P3-A undelivered | `systems/environment` | accept P3-A before S1-D; then add naval seakeeping and Joint hierarchy execution |
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
   scenarios). `S0-B` is accepted after current validation at `087c1928`.
4. `S0-X` has full-duration native runs, side/count/stability regression checks,
   a measured throughput record, maintained composition and replay contracts,
   two checked-in native replay artifacts, two replay profiles, and two native
   spectator profiles. The stage is accepted; S1/U1's S0 prerequisite is closed.
5. S1-A/B implementations are validated on `origin/main` baseline `cedfa01c3`:
   bounded maneuvering, damage-to-mobility, and one-hour named/mirror surface
   transit with terminal settling. Integration review remains open.
6. Deliver the shared ship logistics contract and Environment Runtime `P3-A`
   through their system owners, then integrate S1-C and S1-D. Dispatch Rules
   prohibit local stand-ins for these undelivered prerequisites.
7. Run the complete S1-X stage gate only after S1-C/D closure.

## Overclaim Refusals

Nothing in this package's current state establishes carrier aviation, anti-ship
engagement, undersea warfare, Joint group command hierarchy, endurance or UNREP
scheduling, layered maritime environment response, or any learned-policy result.
