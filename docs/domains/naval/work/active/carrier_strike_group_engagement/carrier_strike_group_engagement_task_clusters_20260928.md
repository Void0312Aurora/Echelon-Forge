# Carrier Strike Group Engagement Task Clusters

Document kind: `task`
Lifecycle: `maintained`
Canonical: `docs/domains/naval/work/active/carrier_strike_group_engagement/carrier_strike_group_engagement_task_clusters_20260928.md`
Owner: `domains/naval`
Last verified: `2026-10-08`

Status: `2026-10-08` finite task-cluster plan for
[Carrier Strike Group Engagement](README.md). `P0-A` and `S0-A`..`S0-X`
accepted; replay and agent-free visualization close S0-X. S1-A/B implementations
are validated pending integration review. S1-C/D and S1-X remain dependency-blocked.

## Boundary Decision

This package may add naval, carrier-aviation, and undersea platforms and
mechanisms, the shared mechanisms each stage names, and the `CSG-*` scenario
ladder with its contracts and tests.

Mechanisms that other domains also use are built by their cross-domain system
owners (see the README's System Dependency Register). Clusters here integrate
those deliverables and build only the naval-owned part.

It must not:

- build cross-domain mechanisms (geodesy, environment, generic sensing, data
  links, EW, weapon families, generic effects, shared logistics) in the naval
  tree;
- re-own Air-domain flight, guidance, or effects mechanisms; carrier aviation
  consumes them through the Air owner's maintained surfaces, and any change to
  them goes through that owner;
- redefine Joint common-core fields; group command relationships use the Joint
  baseline and the Navy service profile;
- claim learned-policy quality or real-world operational prediction;
- invent calibrated-looking coefficients. A parameter without an admissible
  source is recorded as an engineering estimate with its uncertainty, or is left
  unset with a named residual.

Clusters are grouped by stage. A stage's acceptance cluster (`*-X`) is serial and
closes the stage; implementation clusters within a stage may run in parallel only
where the dependency column says so.

## Finite Task Cluster List

Model and reasoning are chosen per the
[Subagent Usage Policy](../../../../../engineering/automation/standards/subagent_usage_policy.md)
at dispatch; `n/a` means not yet dispatched.

| Cluster | Owner | Capability tier / model ID / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `P0-A` | main thread | main thread / session model / high | Freeze scope, ladder, claim ceilings, and provenance policy. | this directory; naval owner README index | runtime code | doc link audit; bilingual audit | owner approves README, clusters, acceptance | first | 1 | accepted |
| `S0-A` | future worker | moderate (public-source research) / sonnet for integration; research ran on default / medium | Order-of-battle research: both groups' ship, submarine, aircraft, weapon, and sensor lists with sources. | `docs/domains/naval/reviews/csg_order_of_battle_20260928/` | runtime content | provenance check: every row has source ID, tier, uncertainty | both sides' OOB tables complete | after `P0-A`; parallel with `S0-B` | 2 | accepted |
| `S0-B` | main thread | moderate / sonnet / medium | Integrate [Geodetic Frame](../../../../../systems/physics/work/active/geodetic_frame/README.md): scenarios declare a geodetic anchor; OOB placement and ranges use the shared frame. | scenario compiler, `scenarios/naval/csg/`, stateless geodesy bindings; naval scenario tests | building the frame (owned by `systems/physics`) | scenario anchor tests | CSG scenarios place both groups through the shared frame | after Geodetic Frame `P3-B` accepted | 1 + 1 repair | accepted `2026-09-30` (`087c1928`); see S0-B Record |
| `S0-C` | future worker | moderate / sonnet / medium for schema mapping and the four authoring packets (US naval, US air, PLAN naval, PLAN air); main thread integrates and fixes; no independent review (database content, not code) | Named unit content for both groups from `S0-A`, at full fidelity in one pass (owner decision `2026-09-29`): aircraft carry component damage models at the F-16C standard. A parameter without an `S0-A` or web source is a labelled `proxy` value with its reasoning, never a silent default. | `examples/config/database/**` (ships, submarines, aircraft, weapons, sensors) | new mechanisms | content-compile tests; unit spawn tests | every OOB row spawns with provenance | after `S0-A` | 2 + 1 repair | accepted `2026-09-30` (see S0-C Record) |
| `S0-D` | main thread | moderate / main thread / medium (a design worker was stopped by owner decision; no subagents from `2026-09-30`) | Group-composition scenario schema plus `CSG-S0` named and mirror scenarios. | scenario compiler (`group_composition.py`), `scenarios/naval/csg/`, `tests/scenario/test_csg_group_composition.py`, `tests/content/test_csg_unit_content.py` | motion | scenario and content tests | both variants load and spawn the full OOB | after `S0-C` | 2 | accepted `2026-09-30` (`48aa6eb4`) |
| `S0-X` | main thread | high (stage acceptance) / main thread / high; serial, no subagents under the `2026-09-30` owner decision | Accept `CSG-S0`; first throughput record; verify replay and spectator playback. | stage acceptance record; full-duration scenario tests; replay artifacts, contracts, and profiles | new simulation mechanisms | stage validation plan | `G0` and all Stage Gates met | after `S0-B`, `S0-D` | 1 | accepted `2026-09-30`; [runtime checkpoint](carrier_strike_group_engagement_acceptance_20260928.md#csg-s0-runtime-checkpoint-2026-09-30) |
| `S1-A` | main thread | main thread / session model / high | Group formation and screen geometry; route following. | naval command/formation components and systems | fleet doctrine beyond formation | formation-keeping tests | formation holds under turns | after `S0-X` | 2 + 1 repair | validated `2026-10-08`; pending integration review; see S1-A/B Record |
| `S1-B` | main thread | main thread / session model / high | Ship turning-circle and speed response; damage-to-mobility coupling. | `ship_motion_system.h`, platform fields | full hydrodynamics | motion tests against sourced turning data | damaged ship loses speed through the maintained path | after `S0-X`; parallel with `S1-A` if write sets split | 2 + 1 repair | validated `2026-10-08`; pending integration review; see S1-A/B Record |
| `S1-C` | future worker | n/a | Ship endurance and group replenishment scheduling on the shared logistics components. | naval logistics system; naval stores content | shared fuel/logistics components (owned by `systems/physics`) | logistics tests | endurance and replenishment observable in the scenario | after `S0-X` and the shared-logistics owner package | 2 | blocked: shared ship endurance/fuel contract not delivered |
| `S1-D` | future worker | n/a | Integrate [Environment Runtime](../../../../../systems/environment/work/active/environment_runtime/README.md); ship seakeeping response to sea state; group command hierarchy on Joint relationships with naval formation roles. | ship motion response; naval command hierarchy content | environment state (owned by `systems/environment`); new Joint common-core fields | environment-consumer and hierarchy tests | sea state, day/night, and bathymetry reach ship motion through the environment query | after `S0-X` and Environment Runtime `P3-A` | 2 | blocked: Environment Runtime P3-A not delivered; hierarchy integration remains open |
| `S1-X` | main thread | n/a | Accept `CSG-S1`; throughput record; fidelity decision input. | stage acceptance record | — | stage validation plan | `G1`-`G2` gate met | after `S1-A..D` | 1 | blocked by S1-C/D; A/B checkpoint only |
| `S2-A` | future worker | n/a | Catapult and arresting-gear cycle; deck, elevator, hangar capacity. | carrier-aviation components/systems | aircraft flight model changes | deck-cycle tests | launch/recovery rates bounded by deck resources | after `S1-X` | 2 + 1 repair | planned |
| `S2-B` | future worker | n/a | Sortie generation, launch waves, recovery pattern, carrier landing. | carrier-aviation systems; Air-owner seam if needed | new Air flight dynamics | wave/CAP tests; landing tests | CAP stations sustained across cycles | after `S2-A` | 2 + 1 repair | planned |
| `S2-C` | future worker | n/a | Embarked helicopter operations; aircraft recovery fuel limits consumed from the shared fuel components. | embarked air ops | shared fuel and aerial-refuelling components (owned by `systems/physics`) | helicopter and recovery-fuel tests | fuel limits sortie radius through the shared path | after `S1-X`; parallel with `S2-A` | 2 | planned |
| `S2-X` | main thread | n/a | Accept `CSG-S2`; throughput record. | stage acceptance record | — | stage validation plan | `G3` gate met | after `S2-A..C` | 1 | planned |
| `S3-A` | future worker | n/a | Naval sensor platform adapters and group track reporting on the shared sensing and data-link deliverables; AEW content. | naval sensor adapters; AEW unit content | sensor physics and data-link mechanics (owned by `systems/sensing`, `systems/command-tasking`) | adapter and reporting tests | group picture forms through shared sensing and links | after `S2-X` and the sensing / command-tasking owner packages | 2 | planned |
| `S3-B` | future worker | n/a | Naval emission-control doctrine and ship ESM platform content on the shared EW deliverable. | naval EMCON doctrine; ship ESM content | EW mechanics (owned by `systems/sensing`) | EMCON doctrine tests | group emission state follows doctrine | after `S2-X` and the EW owner package; parallel with `S3-A` | 2 | planned |
| `S3-C` | main thread | n/a | Integrate the shared identification deliverable into naval ROE handling. | naval ROE/identity use sites | identification mechanics (owned by `systems/command-tasking`) | ROE-identity tests | ROE decisions read identity confidence | after `S3-A` | 1 + 1 repair | planned |
| `S3-D` | main thread | n/a | Verify no truth reads remain in naval surface sensing paths used by CSG scenarios. | naval sensor adapters | removal work in shared sensing (owned by `systems/sensing`) | truth-read guard test | guard passes for all `G4` CSG scenario paths | after `S3-A..C` | 1 + 1 repair | planned |
| `S3-X` | main thread | n/a | Accept `CSG-S3`; throughput record. | stage acceptance record | — | stage validation plan | `G4` gate met | after `S3-A..D` | 1 | planned |
| `S4-A` | future worker | n/a | Naval launch seams and platform loadouts for anti-ship missiles on the shared weapon families. | naval launch seams; weapon loadout content | missile guidance, fuze, and family models (owned by `systems/weapons`) | launch and engagement tests | ship- and air-launched missiles engage a ship through shared weapons | after `S3-X` and the weapons owner package | 2 + 1 repair | planned |
| `S4-B` | future worker | n/a | Ship fire-control channels, VLS, and layered air-defense doctrine. | naval air-defense systems; VLS path | interceptor missile models (owned by `systems/weapons`); new radar physics | interception and saturation tests | channel limits govern leak-through | after `S3-X`; parallel with `S4-A` | 2 + 1 repair | planned |
| `S4-C` | future worker | n/a | Ship decoy launchers and self-protection doctrine on the shared soft-kill deliverable. | ship decoy content and doctrine | soft-kill mechanics (owned by `systems/sensing` / `systems/weapons`) | soft-kill doctrine tests | ship decoys change terminal outcome through the shared path | after `S4-A` | 2 | planned |
| `S4-D` | future worker | n/a | Ship compartments and flight-deck capacity loss on the shared damage deliverable; retire the `DM-N1` synthetic profile or bind it to the shared path. | ship compartment content; naval damage profile | generic damage and damage control (owned by `systems/effects`) | damage chain tests | a hit degrades mobility, sensors, and deck capacity | after `S4-A` and the effects owner package | 2 + 1 repair | planned |
| `S4-X` | main thread | n/a | Accept `CSG-S4`; throughput record. | stage acceptance record | — | stage validation plan | `G5` gate met | after `S4-A..D` | 1 | planned |
| `S5-A` | future worker | n/a | Group fighter escort and intercept tasking on Air-owner seams; group use of stand-off jamming. | naval group tasking | air-combat mechanics (Air owner); jamming mechanics (`systems/sensing`) | escort/intercept tests | escort changes strike survival | after `S4-X` | 2 + 1 repair | planned |
| `S5-B` | future worker | n/a | Group strike planning and target assignment; magazine depletion. | scripted C2 for the group | learned planning | assignment tests | two-sided strikes run with depletion | after `S4-X`; parallel with `S5-A` | 2 + 1 repair | planned |
| `S5-C` | future worker | n/a | Downed-aircrew search and rescue by embarked helicopters. | embarked air ops; SAR task | ground combat | SAR tests | a downed crew can be located and recovered | after `S4-X`; parallel | 2 | planned |
| `S5-X` | main thread | n/a | Accept `CSG-S5`; throughput record. | stage acceptance record | — | stage validation plan | `G6` gate met | after `S5-A..C` | 1 | planned |
| `U1-A` | future worker | n/a | Submarine depth, speed, self-noise coupling; quiet running. | `submarine_motion_system.h`, platform fields | propagation | submarine motion tests | noise tracks speed and depth | after `S0-X`; parallel with `S1-*` | 2 | planned |
| `U1-X` | main thread | n/a | Accept `CSG-U1`. | stage acceptance record | — | stage validation plan | `G1`-`G2` gate met | after `U1-A` | 1 | planned |
| `U2-A` | future worker | n/a | Sonar platforms: hull, towed array, dipping sonar, sonobuoy fields, on the shared acoustic deliverable. | naval sonar platform adapters and content | propagation physics (owned by `systems/sensing`); acoustic environment ([Environment Runtime](../../../../../systems/environment/work/active/environment_runtime/README.md)) | sonar platform tests | detection depends on geometry and environment through shared paths | after `U1-X`, `S3-X`, and the undersea-sensing owner package | 2 + 1 repair | planned |
| `U2-B` | main thread | n/a | Verify no truth reads remain in undersea sensing paths used by CSG scenarios. | naval sonar adapters | removal work in shared sensing (owned by `systems/sensing`) | truth-read guard | guard passes for undersea paths | after `U2-A` | 1 + 1 repair | planned |
| `U2-X` | main thread | n/a | Accept `CSG-U2`. | stage acceptance record | — | stage validation plan | `G4` gate met | after `U2-A..B` | 1 | planned |
| `U3-A` | future worker | n/a | Torpedo tubes, launch, and submarine/ship loadouts on the shared torpedo family. | naval launch seams; loadout content | torpedo guidance, run, fuze, and countermeasure models (owned by `systems/weapons`) | torpedo engagement tests | torpedo engages and can be decoyed | after `U2-X`, `S4-X`, and the weapons owner package | 2 + 1 repair | planned |
| `U3-B` | future worker | n/a | Below-waterline compartments on the shared damage deliverable. | ship and submarine compartment content | flooding mechanics (owned by `systems/effects`) | damage tests | torpedo hit floods through the shared path | after `U3-A` | 2 | planned |
| `U3-X` | main thread | n/a | Accept `CSG-U3`. | stage acceptance record | — | stage validation plan | `G5` gate met | after `U3-A..B` | 1 | planned |
| `S6-A` | future worker | n/a | CSG outcome conditions on the shared adjudication and replay deliverables. | CSG scenario termination rules | generic adjudication and replay tooling (owned by `systems/weapons` and architecture) | termination tests | episodes end on adjudicated CSG outcomes | after `S5-X`, `U3-X`, and the adjudication owner package | 2 | planned |
| `S6-B` | future worker | n/a | Freeze reserved RL observation, action, and termination-event boundaries; scripted controller exercises them. | boundary docs; adapter seams | training | boundary tests | boundaries exercised end-to-end | after `S6-A` | 2 | planned |
| `S6-X` | main thread | n/a | Accept `CSG-S6` named and mirror. | stage acceptance record | — | stage validation plan | `G6` gate met | after `S6-A..B` | 1 | planned |
| `P5-A` | main thread | n/a | Close the package; sync indexes; archive. | this directory; naval owner README | late implementation | doc audits | acceptance record complete | after `S6-X` | 1 | planned |

## S0-C Record (`2026-09-30`)

Commits `be628032`..`e3e192dd` on `work/naval-mechanisms`: 115 records,
about 18,500 lines of database JSON under `examples/config/database/**/csg/{us,cn}/`.
No runtime code changed.

| Family | US (Ford CSG) | PLAN (Fujian group) |
| --- | --- | --- |
| Ships and submarines | CVN-78, DDG-51 Flight IIA and II, Virginia Block III/IV, T-AO-205, T-AOE-6 (branch) | Fujian, Type 055, 052D, 054A, 054B (branch), 093B, 093A, 901, 903A (branch) |
| Aircraft | F/A-18E/F Block III, EA-18G, E-2D, MH-60R, MH-60S, C-2A, F-35C (branch), CMV-22B (branch) | J-35, J-15T, J-15D, KJ-600, Z-20F, Z-20J, GJ-21 (branch) |
| Weapons | SM-2, SM-6, ESSM, RAM, Tomahawk TLAM and MST, Harpoon (ship and air), Mk 48, Mk 54, VLA, AIM-120D, AIM-9X, LRASM, AARGM, Hellfire | YJ-18A, YJ-20, YJ-83, HHQ-9B, HHQ-16, HHQ-10, Yu-6, Yu-7, Yu-11, CY-5, PL-15, PL-10, PL-17, YJ-12, YJ-83K, YJ-15, light ASM |

Rules the content follows (authoring standard, scratch
`_csg_research_scratch/s0c/`):

- every scalar runtime field carries a `_provenance.parameters` entry marked
  `sourced`, `engineering_estimate`, or `proxy` with its source or reasoning;
- every damage-model component `system` tag routes to a damage axis;
- aircraft carry component damage models at the F-16C standard; ships and
  submarines carry explicit compartment hitboxes;
- `vls_sam` mounts hold SAM rounds only, one mount per SAM type with that
  missile's own envelope, because the runtime fires the first ready `vls_sam`
  mount and its envelope overrides the missile record;
- anti-ship, land-attack, ASW-rocket, and torpedo loads are
  `content_only_no_mechanism` in `_real_world.weapon_inventory` until `CSG-S4`
  and `CSG-U3`; carrier deck-cycle data sits in `_real_world.aviation_facilities`
  until `CSG-S2`;
- each sensor is listed once (the factory attaches `sensor_refs` and then
  `sensor_ref` without de-duplication).

Validation: `check_units.py` (load, unique names, resolved refs, full
provenance coverage, routed components, spawn) 115 passed; naval runtime tests
73 passed; HEI full regression at `4fb66f35` 1511 passed with the three
inherited reds. No independent review: the review threshold counts code logic
only (owner decision `2026-09-30`).

Residuals for later clusters:

- highest-risk proxies: J-35 frontal RCS, GJ-21 engine (reuses WS-10H for a
  WS-13-class UCAV), the Z-20F light ASM, YJ-15 range, VLS SAM speeds and
  CIWS ranges on both sides (mostly not public);
- `select_ready_vls_mount` ignores target range, so layered air defence is not
  modelled (`CSG-S4`);
- `vls_sam` `hit_probability` and `damage_per_hit` are not read on the missile
  path, and a missile-capable CIWS has Pk 1.0 inside 0.75 of its range
  (engagement adjudication owner, `CSG-S4`);
- the scratch authoring standard and `check_units.py` are not yet repository
  tools; promoting the check to a content test belongs to `S0-D`.

## S0-D Record (`2026-09-30`)

Commit `48aa6eb4`: 461 lines of code and tests plus two scenario files.

- Schema: a top-level `groups` list, expanded by the compiler into plain
  `entities` and popped, so both spawn paths are unchanged and a recompile
  cannot expand twice. Each group declares `group_id`, `side` (Blue or Red
  only: the side resolver maps anything else to Neutral), `oob_ref` (an
  existing page), a `guide` with a threat axis, optional `branches`, and
  `members`. Members carry `oob_row`, `type`, `count`, `role`, provenance
  with a count basis, and either a `station` (range and bearing from the
  axis; `depth_m` for submarines) or `embarked_on`.
- Embarked aircraft are inventory in `meta.csg.groups[*].embarked_inventory`,
  not entities, because two things are missing. (1) No deck contact surface:
  ground contact reads only terrain elevation, so an aircraft cannot rest on a
  ship's flight deck (about 18-20 m above the waterline on CVN-78). (2) The
  gear spring-damper in `ground_contact_system.h` (k = 2.0e6 N/m,
  c = 3.5e5 N s/m) is integrated explicitly; with a light airframe its natural
  period is about 0.4 s, so the stable step is about 0.12-0.17 s, while the
  naval scenarios step at 0.5 s. Measured: with no command and zero throttle,
  an F/A-18E, F-16C, and MH-60R placed at gear height stay put for 10 s at
  dt = 0.05 s but are thrown up by the first contact step at dt = 0.5 s (the
  MH-60R diverges). The aircraft are not driven by any policy or autopilot.
  (Corrected `2026-09-30`: an earlier version of this record said the flight
  models lack a parked state; that was wrong.) Reason (2) is closed
  `2026-09-30` by [Semi-Implicit Ground Contact](../../../../../systems/physics/reviews/semi_implicit_ground_contact_20260930/README.md)
  (`systems/physics`): the same four airframes now hold still at dt 0.05, 0.2,
  and 0.5 s. Reason (1), the deck surface, remains and keeps the inventory
  form until `CSG-S2`. Each hangar ship's own stowed
  helicopter (`embarked_air_ops`) still spawns and is pinned by
  `EmbarkedAirOpsSystem`. `CSG-S2` consumes the inventory as the deck cycle's
  initial condition.
- Scenarios: `csg_s0_ford_vs_fujian_named_v1.json` (Ford CSG-12, 7 hulls and
  74 aircraft, against Fujian CV-18, 7 hulls, the 48-aircraft wing and 7
  organic helicopters) and `csg_s0_ford_mirror_v1.json` (the Ford platform
  set on both sides). Branches: T-AOE for T-AO, F-35C squadron, CMV-22B;
  Type 054B, 903A for 901, GJ-21. Both declare a geodetic anchor
  (21 N, 125 E). Station geometry is a labelled estimate; the S0-A pages
  give no screen distances. Reserved RL boundary names sit in
  `meta.csg.reserved`.
- The S0-C content rules are now a repository test
  (`tests/content/test_csg_unit_content.py`).

Validation: the two new test files 16 passed; scenario, naval, environment,
content, and runtime-facade suites 358 passed; governance the three inherited
reds.

Residuals: the helicopter split moves one MH-60R detachment from the carrier
to the doctrinal 4th DDG (squadron total unchanged); the 054A and 901 organic
helicopters are Z-20F/Z-20J proxies for Z-9 and Z-8/Z-18.

## S0-B Record (`2026-09-30`)

Commit `087c1928` places both CSG variants through the Geodetic Frame owner's
azimuthal-equidistant projection, exposed by stateless `ef_py.geodesy_*`
bindings. Geodetic guides require a declared scenario anchor; local guides
retain the existing flat layout. Stations follow a great circle from the guide
before projection, with axes facing the other group along the great circle.
`meta.csg` is `csg.group_composition.v2` and records the anchor and separation.

Current validation: 21 scenario/content tests and 12 subtests passed with
`CMO_BUILD_DIR=build-independent-win`. The scenario test now runs both variants
for all 240 steps at 0.5 s, verifies hull sides and positions, and accounts for
the runtime-spawned stowed helicopters. The named variant has 24 runtime
entities; the mirror has 22. Both remain static after the first tick pins the
helicopters to their hosts. See the S0-X checkpoint for measured throughput and
the remaining stage gates.

## S1-A/B Record (`2026-10-08`)

Integrated on `origin/main` baseline `cedfa01c3`, without importing the legacy
S1 branch's unrelated ancestry. The native maneuvering law uses quadratic surge
resistance, bounded Nomoto yaw, turn speed loss, and live damage capability.
Native relative station keeping and scenario-owned waypoint orders use the
maintained command projection. Named and mirror variants each run three legs,
two turns, and terminal settling for 7200 steps at 0.5 s.

The [A/B checkpoint](carrier_strike_group_engagement_acceptance_20260928.md#csg-s1-ab-runtime-checkpoint-2026-10-08)
records tests, throughput, provenance and the exact claim boundary. Route and
formation geometry are true-bearing referenced; no Joint group hierarchy,
fuel endurance, replenishment scheduler or layered-environment integration is
claimed. Implementation validation is pending integration review; it does not
accept S1-X.

## Dispatch Rules

- Every worker packet maps to exactly one cluster above.
- A cluster that consumes a system-owner deliverable waits for that owner's
  package to reach the named phase; it does not build a stand-in.
- Clusters that touch an Air-owner seam or `src/runtime/contracts/**` run
  serially.
- Do not let two workers edit the same scenario contract, public API, component
  schema, or status line at once.
- Acceptance clusters (`*-X`) and `P5-A` are serial and run on the main thread.
- If a cluster exceeds its round cap, stop and re-scope before any follow-up.
- Follow the [Subagent Usage Policy](../../../../../engineering/automation/standards/subagent_usage_policy.md).

## Worker Packet Requirements

```md
status: pass | partial | blocked | failed
cluster:
touched files:
commands/outcomes:
throughput (if the cluster runs a scenario): entities / step / sim duration / wall-clock / host
provenance (if the cluster adds content): source IDs, tiers, uncertainty
remaining paths:
behavior risks:
integration notes:
```

## Validation Plan

Docs-only clusters:

```bash
python tools/maintenance/translate_docs_batch.py audit
python -m pytest -q tests/architecture/governance/test_document_link_audit.py
```

Implementation clusters (Windows host, from the worktree root):

```bash
cmake --build build-independent-win --target ef_test ef_py ef_composition_evidence_test
build-independent-win/ef_test.exe
python -m pytest -q tests/runtime/naval tests/architecture/composition tests/architecture/command_tasking
```

Stage scenarios that the local host cannot complete run on HEI; the packet
records the host.

## Acceptance Criteria

- Each stage acceptance record names its claim ceiling, validation outcomes,
  throughput record, and residuals.
- Each stage's named and mirror scenarios run on the maintained runtime.
- No stage claims a realism level higher than its evidence supports.

## Residual Map

Immediate:

- `S0-X` is accepted: the CSG composition and replay contract surface is
  covered by the CI contract smoke suite, and both visualization profiles are
  runnable without an agent. S1/U1 may dispatch.

Follow-on:

- a learned-policy package consuming the `S6-B` boundaries;
- mixed-rate stepping, only if the throughput records show uniform stepping
  cannot carry the full order of battle.

Deferred:

- land-based aviation, long-range anti-ship ballistic missiles, shore batteries,
  and space assets;
- deception and decoy networks beyond self-protection soft-kill.
